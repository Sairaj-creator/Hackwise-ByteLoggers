"""
Recipe Pipeline Service — 2-Stage Orchestrator
================================================
Chains: Gemini Refinement (Stage 1) → Custom Model Prediction (Stage 2)
Also handles Allergy Guardian checks and Redis caching between stages.
"""

from typing import List, Optional
from app.services.gemini_refine_service import (
    RefinementRequest,
    refine_user_input,
)
from app.services.recipe_model_service import (
    ModelPredictionRequest,
    GeneratedRecipe,
    predict_recipe,
    predict_quick_recipe,
)
from app.services.allergy_guardian import allergy_check
from app.services.cache_service import (
    get_cached,
    set_cached,
    make_cache_key,
    RECIPE_CACHE_TTL,
)


async def generate_recipe_pipeline(
    ingredients: List[str],
    preferences: dict,
    user_allergies: list,
    expiring_items: Optional[List[str]] = None,
    servings: int = 2,
) -> dict:
    """
    Full 2-stage pipeline:
      1. Gemini refines raw input → structured JSON
      2. Custom model predicts recipe from structured JSON
      3. Allergy Guardian checks the result
      4. Auto-regenerate if severe allergens detected
      5. Cache the result

    Returns: dict with "recipe" and "allergy_check" and "waste_impact" keys.
    """
    expiring_items = expiring_items or []

    # ─── Check cache first ───
    cache_key = make_cache_key(
        "recipe",
        *ingredients,
        str(preferences),
        str(servings),
    )
    cached = await get_cached(cache_key)
    if cached:
        return cached

    # ─── Stage 1: Gemini Refinement ───
    refinement_request = RefinementRequest(
        raw_ingredients=ingredients,
        servings=servings,
        cuisine_hint=preferences.get("cuisine", ""),
        dietary_preference=preferences.get("dietary", ""),
        spice_level=preferences.get("spice_level", "medium"),
        max_time_minutes=int(preferences.get("max_time_minutes", 30)),
    )

    refined = await refine_user_input(refinement_request)

    # ─── Stage 2: Custom Model Prediction ───
    model_request = ModelPredictionRequest(
        refined_ingredients=[
            {"name": ri.name, "quantity": ri.quantity, "category": ri.category}
            for ri in refined.refined_ingredients
        ],
        cuisine=refined.detected_cuisine,
        dietary=refined.detected_dietary,
        servings=servings,
        spice_level=preferences.get("spice_level", "medium"),
        max_time_minutes=int(preferences.get("max_time_minutes", 30)),
        user_allergies=[
            a.get("allergen", "") if isinstance(a, dict) else getattr(a, "allergen", "")
            for a in user_allergies
        ],
        expiring_items=expiring_items,
        exclude_ingredients=[],
    )

    try:
        recipe = await predict_recipe(model_request)
    except Exception:
        # Model failed — return a fallback
        return {
            "recipe": None,
            "error": "Recipe generation failed. Please try again.",
            "allergy_check": {"safe": True, "warnings": [], "substitutions": []},
            "waste_impact": {},
        }

    # ─── Allergy Guardian check ───
    allergy_result = await allergy_check(recipe.model_dump(), user_allergies)

    # Auto-regenerate if severe allergens found
    if not allergy_result["safe"]:
        severe = [w for w in allergy_result["warnings"] if w["severity"] == "severe"]
        if severe:
            excluded = [w["ingredient"] for w in severe]
            model_request.exclude_ingredients = excluded
            try:
                recipe = await predict_recipe(model_request)
                allergy_result = await allergy_check(recipe.model_dump(), user_allergies)
                allergy_result["auto_regenerated"] = True
            except Exception:
                pass  # Keep original recipe with warnings

    # ─── Calculate waste impact ───
    waste_impact = _calculate_waste_impact(recipe, expiring_items)

    # ─── Assemble result ───
    result = {
        "recipe": recipe.model_dump(),
        "allergy_check": allergy_result,
        "waste_impact": waste_impact,
    }

    # ─── Cache it ───
    await set_cached(cache_key, result, RECIPE_CACHE_TTL)

    return result


async def generate_quick_recipe_pipeline(
    expiring_ingredients: List[str],
    user_allergies: list,
) -> dict:
    """Quick recipe for waste tracker smart suggestions."""
    allergy_list = [
        a.get("allergen", "") if isinstance(a, dict) else getattr(a, "allergen", "")
        for a in user_allergies
    ]

    try:
        recipe = await predict_quick_recipe(expiring_ingredients, allergy_list)
    except Exception:
        return {"recipe": None, "error": "Could not generate quick recipe."}

    allergy_result = await allergy_check(recipe.model_dump(), user_allergies)

    return {
        "recipe": recipe.model_dump(),
        "allergy_check": allergy_result,
    }


def _calculate_waste_impact(recipe: GeneratedRecipe, expiring_items: List[str]) -> dict:
    """Calculate how much waste this recipe prevents by using expiring items."""
    if not expiring_items:
        return {"ingredients_saved_from_expiry": [], "waste_prevented_grams": 0}

    saved = []
    for ing in recipe.ingredients:
        if ing.name.lower() in [e.lower() for e in expiring_items]:
            saved.append(ing.name)

    return {
        "ingredients_saved_from_expiry": saved,
        "waste_prevented_grams": len(saved) * 200,  # rough estimate
    }
