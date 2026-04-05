"""
Recipe Pipeline Service — 2-Stage Orchestrator
================================================
Chains: Gemini Refinement (Stage 1) → TF-IDF Model (Stage 2) → Gemini Fallback
Also handles Allergy Guardian checks and Redis caching between stages.
"""

import json
import logging
from typing import List, Optional

from app.services.gemini_refine_service import (
    RefinementRequest,
    refine_user_input,
)
from app.services.recipe_model_service import (
    ModelPredictionRequest,
    GeneratedRecipe,
    RecipeIngredient,
    RecipeStep,
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

logger = logging.getLogger("uvicorn.error")

# ─── Lazy-load the TF-IDF predictor once ───
_tfidf_predictor = None


def _get_tfidf_predictor():
    global _tfidf_predictor
    if _tfidf_predictor is None:
        try:
            from app.services.llm_services import RecipePredictor
            _tfidf_predictor = RecipePredictor()
            logger.info("TF-IDF RecipePredictor loaded from recipe_model.joblib")
        except Exception as e:
            logger.warning(f"TF-IDF model unavailable: {e}. Will use Gemini only.")
            _tfidf_predictor = False  # Mark as failed so we don't retry
    return _tfidf_predictor if _tfidf_predictor else None


def _tfidf_to_generated_recipe(result: dict, servings: int) -> GeneratedRecipe:
    """
    Convert the TF-IDF predictor's output dict into a GeneratedRecipe.
    The DataFrame columns are: title, cuisine, ingredients, steps, tags.
    Each may be a list of strings, list of dicts, or a comma-separated string.
    """
    def _to_str_list(val) -> list:
        if isinstance(val, list):
            return [str(v) for v in val]
        if isinstance(val, str):
            return [v.strip() for v in val.split(",") if v.strip()]
        return []

    title = str(result.get("recipe", "Recipe"))
    cuisine = str(result.get("cuisine", "Fusion"))

    # --- Ingredients ---
    raw_ings = result.get("ingredients", [])
    if isinstance(raw_ings, str):
        try:
            raw_ings = json.loads(raw_ings)
        except Exception:
            raw_ings = [i.strip() for i in raw_ings.split(",") if i.strip()]

    ingredients = []
    for ing in (raw_ings if isinstance(raw_ings, list) else []):
        if isinstance(ing, dict):
            ingredients.append(RecipeIngredient(
                name=ing.get("name", str(ing)),
                quantity=ing.get("quantity", "as needed"),
            ))
        else:
            ingredients.append(RecipeIngredient(name=str(ing), quantity="as needed"))

    # --- Steps ---
    raw_steps = result.get("steps", [])
    if isinstance(raw_steps, str):
        try:
            raw_steps = json.loads(raw_steps)
        except Exception:
            raw_steps = [s.strip() for s in raw_steps.split(".") if s.strip()]

    steps = []
    for i, step in enumerate(raw_steps if isinstance(raw_steps, list) else []):
        if isinstance(step, dict):
            steps.append(RecipeStep(
                step=step.get("step", i + 1),
                instruction=step.get("instruction", str(step)),
                time_minutes=step.get("time_minutes", 5),
            ))
        else:
            steps.append(RecipeStep(step=i + 1, instruction=str(step), time_minutes=5))

    # --- Tags ---
    tags = _to_str_list(result.get("tags", []))

    return GeneratedRecipe(
        title=title,
        cuisine=cuisine,
        estimated_time_minutes=max(len(steps) * 5, 20),
        difficulty="medium",
        servings=servings,
        ingredients=ingredients,
        preparation_steps=steps,
        youtube_search_query=f"{title} {cuisine} recipe",
        tags=tags,
    )


async def generate_recipe_pipeline(
    ingredients: List[str],
    preferences: dict,
    user_allergies: list,
    expiring_items: Optional[List[str]] = None,
    servings: int = 2,
) -> dict:
    """
    Full 3-stage pipeline:
      1. Gemini refines raw input → structured JSON
      2. TF-IDF model (recipe_model.joblib) tries to find best match
      3. If no match → Gemini generates a full recipe
      + Allergy Guardian check + Redis cache

    Returns: dict with "recipe", "allergy_check", and "waste_impact" keys.
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

    # ─── Stage 2: TF-IDF Model ───
    recipe: Optional[GeneratedRecipe] = None
    tfidf_source = False

    predictor = _get_tfidf_predictor()
    if predictor is not None:
        try:
            ingredient_names = [ri.name for ri in refined.refined_ingredients]
            # Don't pass generic/null dietary values — they mask all dataset recipes
            _skip_dietary = {"any", "none", "no preference", ""}
            dietary_pref = refined.detected_dietary.lower().strip() if refined.detected_dietary else ""
            structured_json = json.dumps({
                "ingredients": ingredient_names,
                "number_of_people": servings,
                "cuisine": refined.detected_cuisine if refined.detected_cuisine.lower() not in {"fusion", "", "any"} else None,
                "dietary_preferences": [refined.detected_dietary] if dietary_pref and dietary_pref not in _skip_dietary else [],
            })
            tfidf_result = predictor.predict(structured_json)
            if tfidf_result.get("status") == "success":
                recipe = _tfidf_to_generated_recipe(tfidf_result, servings)
                tfidf_source = True
                logger.info(f"TF-IDF matched: '{recipe.title}'")
            else:
                logger.info(f"TF-IDF no match: {tfidf_result.get('message')} — falling back to Gemini")
        except Exception as e:
            logger.warning(f"TF-IDF prediction error: {e} — falling back to Gemini")

    # ─── Stage 3: Gemini Generation (fallback) ───
    if recipe is None:
        cuisine_val = (refined.detected_cuisine or "Fusion").strip()
        dietary_val = (refined.detected_dietary or "any").strip()
        max_time = 30
        try:
            max_time = int(preferences.get("max_time_minutes", 30))
        except (ValueError, TypeError):
            max_time = 30

        model_request = ModelPredictionRequest(
            refined_ingredients=[
                {"name": ri.name, "quantity": ri.quantity, "category": ri.category}
                for ri in refined.refined_ingredients
            ],
            cuisine=cuisine_val,
            dietary=dietary_val,
            servings=servings,
            spice_level=str(preferences.get("spice_level", "medium")),
            max_time_minutes=max_time,
            user_allergies=[
                a.get("allergen", "") if isinstance(a, dict) else getattr(a, "allergen", "")
                for a in user_allergies
            ],
            expiring_items=expiring_items,
            exclude_ingredients=[],
        )
        try:
            recipe = await predict_recipe(model_request)
        except Exception as e:
            logger.error("predict_recipe raised unexpectedly: %s", e, exc_info=True)
            return {
                "recipe": None,
                "error": f"Recipe generation failed: {e}",
                "allergy_check": {"safe": True, "warnings": [], "substitutions": []},
                "waste_impact": {},
            }

    # ─── Allergy Guardian check ───
    allergy_result = await allergy_check(recipe.model_dump(), user_allergies)

    # Auto-regenerate via Gemini if severe allergens found (only if TF-IDF was used)
    if not allergy_result["safe"] and tfidf_source:
        severe = [w for w in allergy_result["warnings"] if w["severity"] == "severe"]
        if severe:
            try:
                excluded = [w["ingredient"] for w in severe]
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
                    exclude_ingredients=excluded,
                )
                recipe = await predict_recipe(model_request)
                allergy_result = await allergy_check(recipe.model_dump(), user_allergies)
                allergy_result["auto_regenerated"] = True
            except Exception:
                pass  # Keep original with warnings
    elif not allergy_result["safe"]:
        severe = [w for w in allergy_result["warnings"] if w["severity"] == "severe"]
        if severe:
            excluded = [w["ingredient"] for w in severe]
            model_request_regen = ModelPredictionRequest(
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
                exclude_ingredients=excluded,
            )
            try:
                recipe = await predict_recipe(model_request_regen)
                allergy_result = await allergy_check(recipe.model_dump(), user_allergies)
                allergy_result["auto_regenerated"] = True
            except Exception:
                pass

    # ─── Calculate waste impact ───
    waste_impact = _calculate_waste_impact(recipe, expiring_items)

    # ─── Assemble & cache result ───
    result = {
        "recipe": recipe.model_dump(),
        "allergy_check": allergy_result,
        "waste_impact": waste_impact,
    }
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
        "waste_prevented_grams": len(saved) * 200,
    }
