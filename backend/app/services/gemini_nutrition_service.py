"""
GEMINI NUTRITION SERVICE — Nutritional Data Enrichment
=======================================================
Uses Gemini to estimate nutritional information for recipe ingredients.
Called on-demand when user views nutrition details for a recipe.
"""

import json
import logging
from typing import List, Dict
from pydantic import BaseModel
from google import genai
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")


# ============ INPUT/OUTPUT CONTRACTS ============

class NutritionRequest(BaseModel):
    ingredients: List[Dict[str, str]]   # [{"name": "Paneer", "quantity": "200g"}, ...]
    servings: int                       # recipe servings count


class NutritionData(BaseModel):
    total_calories: int
    per_serving: Dict[str, float]       # {"calories": 242, "protein_g": 18.5, ...}
    health_benefits: List[str]
    source: str                         # "gemini_api" | "fallback"


# ============ GEMINI IMPLEMENTATION ============

async def get_nutrition_data(request: NutritionRequest) -> NutritionData:
    """
    Uses Gemini to estimate nutritional data for recipe ingredients.
    """
    try:
        settings = get_settings()
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        ingredients_text = "\n".join(
            f"- {ing.get('name', '?')}: {ing.get('quantity', '?')}"
            for ing in request.ingredients
        )

        prompt = f"""Estimate the total nutritional content for this recipe (all ingredients combined, {request.servings} servings):

{ingredients_text}

Respond with ONLY valid JSON (no markdown, no code fences):
{{
  "total_calories": 485,
  "per_serving": {{
    "calories": 242.5,
    "protein_g": 18.5,
    "carbs_g": 12.3,
    "fats_g": 15.2,
    "fiber_g": 3.1
  }},
  "health_benefits": [
    "High in protein — supports muscle health",
    "Rich in vitamins — boosts immunity"
  ]
}}

Rules:
- Estimate realistic nutritional values based on standard food databases
- per_serving should be total divided by {request.servings} servings
- Provide 3-5 specific health benefits based on the actual ingredients
- Return ONLY the JSON"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines)

        data = json.loads(raw_text)

        return NutritionData(
            total_calories=data.get("total_calories", 0),
            per_serving=data.get("per_serving", {}),
            health_benefits=data.get("health_benefits", []),
            source="gemini_api",
        )

    except Exception as e:
        logger.warning(f"Gemini nutrition estimation failed: {e}. Using fallback.")
        # Simple fallback estimate
        estimated_cal = len(request.ingredients) * 80
        return NutritionData(
            total_calories=estimated_cal,
            per_serving={
                "calories": round(estimated_cal / max(request.servings, 1), 1),
                "protein_g": round(len(request.ingredients) * 3.5, 1),
                "carbs_g": round(len(request.ingredients) * 5.0, 1),
                "fats_g": round(len(request.ingredients) * 2.5, 1),
                "fiber_g": round(len(request.ingredients) * 1.0, 1),
            },
            health_benefits=["Nutritional data estimated — exact values may vary"],
            source="fallback",
        )
