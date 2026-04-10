"""
Recipe generation orchestrator.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from app.services.allergy_guardian import allergy_check
from app.services.cache_service import RECIPE_CACHE_TTL, get_cached, make_cache_key, set_cached
from app.services.gemini_refine_service import RefinementRequest, refine_ingredients
from app.services.recipe_model_service import GeneratedRecipe, predict_quick_recipe, predict_recipe, to_generated_recipe

logger = logging.getLogger("uvicorn.error")


async def generate_recipe_pipeline(
    ingredients: List[str],
    preferences: dict,
    user_allergies: list,
    expiring_items: Optional[List[str]] = None,
    servings: int = 2,
    raw_text_input: Optional[str] = None,
) -> dict:
    expiring_items = expiring_items or []
    servings = max(int(servings or 1), 1)

    cache_key = make_cache_key(
        "recipe",
        *(ingredients or []),
        raw_text_input or "",
        str(preferences),
        str(servings),
    )
    cached = await get_cached(cache_key)
    if cached:
        return cached

    stage_1_status = "skipped_direct_input"
    if raw_text_input:
        refined = await refine_ingredients(
            RefinementRequest(
                raw_ingredients=raw_text_input,
                number_of_people=servings,
                dietary_preferences=preferences.get("dietary_preferences", preferences.get("dietary", [])),
                cuisine_hint=preferences.get("cuisine"),
            )
        )
        normalized_ingredients = refined.ingredients
        cuisine = refined.cuisine or preferences.get("cuisine")
        dietary_preferences = refined.dietary_preferences or _coerce_preferences(preferences.get("dietary_preferences", preferences.get("dietary", [])))
        stage_1_status = "gemini_refinement"
    else:
        normalized_ingredients = [_normalize_item(item) for item in ingredients if _normalize_item(item)]
        cuisine = preferences.get("cuisine")
        dietary_preferences = _coerce_preferences(preferences.get("dietary_preferences", preferences.get("dietary", [])))

    input_recipe = {"ingredients": [{"name": ingredient, "quantity": "as needed"} for ingredient in normalized_ingredients]}
    input_allergy_result = await allergy_check(input_recipe, user_allergies)
    excluded_from_input = [
        warning.get("ingredient", "")
        for warning in input_allergy_result.get("warnings", [])
        if warning.get("ingredient")
    ]
    safe_ingredients = [ingredient for ingredient in normalized_ingredients if ingredient not in {item.lower() for item in excluded_from_input}]
    prediction_ingredients = safe_ingredients or normalized_ingredients

    prediction = await predict_recipe(
        {
            "ingredients": prediction_ingredients,
            "cuisine": cuisine,
            "dietary_preferences": dietary_preferences,
            "number_of_people": servings,
            "max_time_minutes": int(preferences.get("max_time_minutes", 30) or 30),
            "spice_level": str(preferences.get("spice_level", "medium")),
            "user_allergies": [
                allergen.get("allergen", "") if isinstance(allergen, dict) else getattr(allergen, "allergen", "")
                for allergen in user_allergies
            ],
            "expiring_items": expiring_items,
            "exclude_ingredients": excluded_from_input,
        }
    )
    recipe = to_generated_recipe(prediction, max_time_minutes=int(preferences.get("max_time_minutes", 30) or 30))

    allergy_result = await allergy_check(recipe.model_dump(), user_allergies)
    if not allergy_result.get("safe", True):
        severe = [warning for warning in allergy_result.get("warnings", []) if warning.get("severity") == "severe"]
        if severe:
            excluded = [warning.get("ingredient", "") for warning in severe if warning.get("ingredient")]
            regenerated = await predict_recipe(
                {
                    "ingredients": [ingredient for ingredient in normalized_ingredients if ingredient not in {item.lower() for item in excluded}] or normalized_ingredients,
                    "cuisine": cuisine,
                    "dietary_preferences": dietary_preferences,
                    "number_of_people": servings,
                    "max_time_minutes": int(preferences.get("max_time_minutes", 30) or 30),
                    "spice_level": str(preferences.get("spice_level", "medium")),
                    "user_allergies": [
                        allergen.get("allergen", "") if isinstance(allergen, dict) else getattr(allergen, "allergen", "")
                        for allergen in user_allergies
                    ],
                    "expiring_items": expiring_items,
                    "exclude_ingredients": excluded,
                }
            )
            recipe = to_generated_recipe(regenerated, max_time_minutes=int(preferences.get("max_time_minutes", 30) or 30))
            allergy_result = await allergy_check(recipe.model_dump(), user_allergies)
            allergy_result["auto_regenerated"] = True

    if input_allergy_result.get("warnings"):
        existing_warnings = {
            (warning.get("ingredient"), warning.get("allergen"))
            for warning in allergy_result.get("warnings", [])
        }
        for warning in input_allergy_result.get("warnings", []):
            key = (warning.get("ingredient"), warning.get("allergen"))
            if key not in existing_warnings:
                allergy_result.setdefault("warnings", []).append(warning)
        for substitution in input_allergy_result.get("substitutions", []):
            if substitution not in allergy_result.get("substitutions", []):
                allergy_result.setdefault("substitutions", []).append(substitution)
        allergy_result["safe"] = False
        allergy_result["auto_regenerated"] = bool(excluded_from_input) or allergy_result.get("auto_regenerated", False)

    result = {
        "recipe": {
            **recipe.model_dump(),
            "status": prediction.status,
            "similarity_score": prediction.similarity_score,
        },
        "allergy_check": allergy_result,
        "waste_impact": _calculate_waste_impact(recipe, expiring_items),
        "pipeline_stages": {
            "stage_1": stage_1_status,
            "stage_2": "custom_model_prediction" if prediction.similarity_score not in (None, 1.0) else "gemini_generation_fallback",
            "stage_3": "allergy_guardian",
        },
    }
    await set_cached(cache_key, result, RECIPE_CACHE_TTL)
    return result


async def generate_quick_recipe_pipeline(expiring_ingredients: List[str], user_allergies: list) -> dict:
    allergy_list = [
        allergen.get("allergen", "") if isinstance(allergen, dict) else getattr(allergen, "allergen", "")
        for allergen in user_allergies
    ]
    recipe = await predict_quick_recipe(expiring_ingredients, allergy_list)
    allergy_result = await allergy_check(recipe.model_dump(), user_allergies)
    return {"recipe": recipe.model_dump(), "allergy_check": allergy_result}


def _normalize_item(value: str) -> str:
    import re

    cleaned = re.sub(r"[^a-zA-Z\s-]", " ", str(value or "").strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _coerce_preferences(value) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip().lower()] if value.strip() else []
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _calculate_waste_impact(recipe: GeneratedRecipe, expiring_items: List[str]) -> dict:
    expiring_lookup = {item.lower() for item in expiring_items}
    saved = [ingredient.name for ingredient in recipe.ingredients if ingredient.name.lower() in expiring_lookup]
    return {
        "ingredients_saved_from_expiry": saved,
        "waste_prevented_grams": len(saved) * 200,
    }
