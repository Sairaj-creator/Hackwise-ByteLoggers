"""
Gemini-backed nutrition service with Redis caching and deterministic fallback estimates.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from typing import Dict, List

from pydantic import BaseModel, Field

from app.services.gemini_common import generate_content_text, parse_json_payload

logger = logging.getLogger("uvicorn.error")


class NutritionRequest(BaseModel):
    ingredients: List[Dict[str, str]]
    servings: int = 1


class NutritionData(BaseModel):
    total_calories: int
    per_serving: Dict[str, float]
    health_benefits: List[str]
    source: str


NUTRITION_DB = {
    "paneer": {"calories": 265, "protein_g": 18.3, "carbs_g": 1.2, "fats_g": 20.8, "fiber_g": 0.0},
    "tofu": {"calories": 144, "protein_g": 17.3, "carbs_g": 3.0, "fats_g": 8.7, "fiber_g": 2.3},
    "chicken": {"calories": 239, "protein_g": 27.3, "carbs_g": 0.0, "fats_g": 13.6, "fiber_g": 0.0},
    "rice": {"calories": 130, "protein_g": 2.7, "carbs_g": 28.2, "fats_g": 0.3, "fiber_g": 0.4},
    "pasta": {"calories": 157, "protein_g": 5.8, "carbs_g": 30.9, "fats_g": 0.9, "fiber_g": 1.8},
    "spaghetti": {"calories": 157, "protein_g": 5.8, "carbs_g": 30.9, "fats_g": 0.9, "fiber_g": 1.8},
    "tomato": {"calories": 18, "protein_g": 0.9, "carbs_g": 3.9, "fats_g": 0.2, "fiber_g": 1.2},
    "onion": {"calories": 40, "protein_g": 1.1, "carbs_g": 9.3, "fats_g": 0.1, "fiber_g": 1.7},
    "bell pepper": {"calories": 31, "protein_g": 1.0, "carbs_g": 6.0, "fats_g": 0.3, "fiber_g": 2.1},
    "broccoli": {"calories": 34, "protein_g": 2.8, "carbs_g": 6.6, "fats_g": 0.4, "fiber_g": 2.6},
    "carrot": {"calories": 41, "protein_g": 0.9, "carbs_g": 9.6, "fats_g": 0.2, "fiber_g": 2.8},
    "spinach": {"calories": 23, "protein_g": 2.9, "carbs_g": 3.6, "fats_g": 0.4, "fiber_g": 2.2},
    "potato": {"calories": 77, "protein_g": 2.0, "carbs_g": 17.5, "fats_g": 0.1, "fiber_g": 2.2},
    "mushroom": {"calories": 22, "protein_g": 3.1, "carbs_g": 3.3, "fats_g": 0.3, "fiber_g": 1.0},
    "garlic": {"calories": 149, "protein_g": 6.4, "carbs_g": 33.1, "fats_g": 0.5, "fiber_g": 2.1},
    "ginger": {"calories": 80, "protein_g": 1.8, "carbs_g": 17.8, "fats_g": 0.8, "fiber_g": 2.0},
    "olive oil": {"calories": 884, "protein_g": 0.0, "carbs_g": 0.0, "fats_g": 100.0, "fiber_g": 0.0},
    "butter": {"calories": 717, "protein_g": 0.9, "carbs_g": 0.1, "fats_g": 81.1, "fiber_g": 0.0},
    "cheese": {"calories": 402, "protein_g": 25.0, "carbs_g": 1.3, "fats_g": 33.1, "fiber_g": 0.0},
    "egg": {"calories": 155, "protein_g": 13.0, "carbs_g": 1.1, "fats_g": 11.0, "fiber_g": 0.0},
    "beans": {"calories": 127, "protein_g": 8.7, "carbs_g": 22.8, "fats_g": 0.5, "fiber_g": 6.4},
    "chickpeas": {"calories": 164, "protein_g": 8.9, "carbs_g": 27.4, "fats_g": 2.6, "fiber_g": 7.6},
    "lentils": {"calories": 116, "protein_g": 9.0, "carbs_g": 20.1, "fats_g": 0.4, "fiber_g": 7.9},
    "quinoa": {"calories": 120, "protein_g": 4.4, "carbs_g": 21.3, "fats_g": 1.9, "fiber_g": 2.8},
    "avocado": {"calories": 160, "protein_g": 2.0, "carbs_g": 8.5, "fats_g": 14.7, "fiber_g": 6.7},
    "yogurt": {"calories": 61, "protein_g": 3.5, "carbs_g": 4.7, "fats_g": 3.3, "fiber_g": 0.0},
}

UNIT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "ml": 1.0,
    "l": 1000.0,
    "cup": 240.0,
    "cups": 240.0,
    "tbsp": 15.0,
    "tablespoon": 15.0,
    "tablespoons": 15.0,
    "tsp": 5.0,
    "teaspoon": 5.0,
    "teaspoons": 5.0,
    "piece": 80.0,
    "pieces": 80.0,
    "clove": 5.0,
    "cloves": 5.0,
}


def _cache_key(request: NutritionRequest) -> str:
    payload = json.dumps(
        {"ingredients": sorted(request.ingredients, key=lambda item: item.get("name", "")), "servings": request.servings},
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"nutrition:{digest}"


def _parse_quantity(quantity: str) -> float:
    text = (quantity or "").lower().strip()
    if not text:
        return 100.0

    match = re.search(r"(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?", text)
    if not match:
        return 100.0

    amount = float(match.group(1))
    unit = (match.group(2) or "g").lower()
    return amount * UNIT_TO_GRAMS.get(unit, 100.0)


def _lookup_nutrients(name: str) -> Dict[str, float]:
    cleaned = (name or "").strip().lower()
    if cleaned in NUTRITION_DB:
        return NUTRITION_DB[cleaned]

    for candidate, macros in NUTRITION_DB.items():
        if candidate in cleaned or cleaned in candidate:
            return macros

    return {"calories": 90.0, "protein_g": 3.0, "carbs_g": 10.0, "fats_g": 3.0, "fiber_g": 1.5}


def _build_health_benefits(ingredients: List[Dict[str, str]]) -> List[str]:
    names = [ingredient.get("name", "").lower() for ingredient in ingredients]
    benefits = []

    if any(name in {"paneer", "tofu", "chicken", "egg", "lentils", "beans", "chickpeas"} for name in names):
        benefits.append("High in protein from the main ingredients, which supports muscle maintenance.")
    if any(name in {"broccoli", "spinach", "carrot", "bell pepper", "tomato"} for name in names):
        benefits.append("Provides vitamins and antioxidants from colorful vegetables.")
    if any(name in {"beans", "lentils", "chickpeas", "quinoa", "avocado", "broccoli"} for name in names):
        benefits.append("Includes fiber-rich ingredients that support digestion and satiety.")
    if any(name in {"olive oil", "avocado", "salmon"} for name in names):
        benefits.append("Contains healthy fats that support heart health.")

    if not benefits:
        benefits.append("Balanced nutrition estimate generated from the listed ingredients.")
    return benefits[:3]


def _fallback_nutrition(request: NutritionRequest) -> NutritionData:
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fats_g": 0.0, "fiber_g": 0.0}

    for ingredient in request.ingredients:
        grams = _parse_quantity(ingredient.get("quantity", "100g"))
        nutrients = _lookup_nutrients(ingredient.get("name", ""))
        factor = grams / 100.0
        for field_name in totals:
            totals[field_name] += nutrients[field_name] * factor

    servings = max(int(request.servings or 1), 1)
    per_serving = {
        "calories": round(totals["calories"] / servings, 1),
        "protein_g": round(totals["protein_g"] / servings, 1),
        "carbs_g": round(totals["carbs_g"] / servings, 1),
        "fats_g": round(totals["fats_g"] / servings, 1),
        "fiber_g": round(totals["fiber_g"] / servings, 1),
    }

    return NutritionData(
        total_calories=max(0, int(math.ceil(totals["calories"]))),
        per_serving=per_serving,
        health_benefits=_build_health_benefits(request.ingredients),
        source="mock",
    )


def _build_prompt(request: NutritionRequest) -> str:
    ingredient_list = ", ".join(
        f"{ingredient.get('name', '').strip()} ({ingredient.get('quantity', 'standard portion')})"
        for ingredient in request.ingredients
    )
    return f"""
Calculate nutrition for a recipe serving {request.servings} people.
Ingredients: {ingredient_list}

Return ONLY JSON:
{{
  "total_calories": 540,
  "per_serving": {{
    "calories": 270.0,
    "protein_g": 18.0,
    "carbs_g": 22.0,
    "fats_g": 11.0,
    "fiber_g": 4.0
  }},
  "health_benefits": ["benefit 1", "benefit 2", "benefit 3"]
}}

Use realistic values and ensure per_serving is total divided by {request.servings}.
No markdown and no explanation.
""".strip()


async def get_nutrition_data(request: NutritionRequest, redis_client=None) -> NutritionData:
    cache_key = _cache_key(request)

    if redis_client is not None:
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                data["source"] = "cached"
                return NutritionData(**data)
        except Exception as exc:
            logger.warning("Nutrition Redis read failed: %s", exc)

    try:
        raw_text = await generate_content_text(_build_prompt(request), model_name="gemini-2.5-flash")
        parsed = parse_json_payload(raw_text)
        result = NutritionData(
            total_calories=int(parsed["total_calories"]),
            per_serving={
                "calories": float(parsed["per_serving"]["calories"]),
                "protein_g": float(parsed["per_serving"]["protein_g"]),
                "carbs_g": float(parsed["per_serving"]["carbs_g"]),
                "fats_g": float(parsed["per_serving"]["fats_g"]),
                "fiber_g": float(parsed["per_serving"]["fiber_g"]),
            },
            health_benefits=[str(item) for item in parsed.get("health_benefits", [])][:5],
            source="gemini_api",
        )

        if redis_client is not None:
            try:
                await redis_client.setex(cache_key, 604800, json.dumps(result.model_dump()))
            except Exception as exc:
                logger.warning("Nutrition Redis write failed: %s", exc)

        return result
    except Exception as exc:
        logger.warning("Gemini nutrition estimation failed: %s", exc)
        fallback = _fallback_nutrition(request)

        if redis_client is not None:
            try:
                await redis_client.setex(cache_key, 604800, json.dumps(fallback.model_dump()))
            except Exception as cache_exc:
                logger.warning("Nutrition fallback Redis write failed: %s", cache_exc)

        return fallback
