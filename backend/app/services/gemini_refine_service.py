"""
GEMINI REFINE SERVICE — Stage 1: Input Refinement
===================================================
Takes raw user input and uses Gemini to normalize ingredient names,
estimate quantities, detect cuisine, and suggest additional ingredients.
"""

import json
import logging
from typing import List
from pydantic import BaseModel
from google import genai
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")


# ============ INPUT/OUTPUT CONTRACTS ============

class RefinementRequest(BaseModel):
    raw_ingredients: List[str]             # ["paneer", "bell pepper", "onion"]
    servings: int                          # 2
    cuisine_hint: str = ""                 # "North Indian" or "" for auto-detect
    dietary_preference: str = ""           # "vegetarian", "vegan", etc.
    spice_level: str = "medium"            # "mild" | "medium" | "hot"
    max_time_minutes: int = 30


class RefinedIngredient(BaseModel):
    name: str                               # Normalized: "Paneer" not "paner"
    quantity: str                           # Scaled for servings: "200g"
    category: str                          # "dairy", "vegetable", "spice", etc.
    is_primary: bool = True                # Primary vs supporting ingredient


class RefinementResponse(BaseModel):
    refined_ingredients: List[RefinedIngredient]
    detected_cuisine: str                  # "North Indian"
    detected_dietary: str                  # "vegetarian"
    suggested_additional: List[str]        # ["garam masala", "oil", "salt"]
    processing_time_ms: int
    source: str                            # "gemini_api" | "fallback"


# ============ GEMINI IMPLEMENTATION ============

async def refine_user_input(request: RefinementRequest) -> RefinementResponse:
    """
    Uses Gemini to normalize and structure raw ingredient input.
    Falls back to simple normalization if Gemini fails.
    """
    try:
        settings = get_settings()
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are a cooking assistant. Given these raw ingredients, normalize and structure them.

Raw ingredients: {', '.join(request.raw_ingredients)}
Servings: {request.servings}
Cuisine hint: {request.cuisine_hint or 'auto-detect'}
Dietary preference: {request.dietary_preference or 'auto-detect'}
Spice level: {request.spice_level}
Max cooking time: {request.max_time_minutes} minutes

Respond with ONLY valid JSON (no markdown, no code fences):
{{
  "refined_ingredients": [
    {{"name": "Proper Name", "quantity": "200g", "category": "dairy", "is_primary": true}}
  ],
  "detected_cuisine": "North Indian",
  "detected_dietary": "vegetarian",
  "suggested_additional": ["oil", "salt", "garam masala"]
}}

Rules:
- Fix typos and use proper title-case names
- Estimate realistic quantities for the given servings
- Category must be one of: dairy, protein, vegetable, grain, spice, condiment, general
- Detect the most likely cuisine from the ingredients if no hint given
- Detect dietary type (vegetarian, non-vegetarian, vegan, etc.)
- Suggest 3-5 common supporting ingredients that pair well
- Return ONLY the JSON"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        raw_text = response.text.strip()
        # Clean markdown fences
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines)

        data = json.loads(raw_text)

        refined = [
            RefinedIngredient(
                name=ing.get("name", ""),
                quantity=ing.get("quantity", "as needed"),
                category=ing.get("category", "general"),
                is_primary=ing.get("is_primary", True),
            )
            for ing in data.get("refined_ingredients", [])
        ]

        return RefinementResponse(
            refined_ingredients=refined,
            detected_cuisine=data.get("detected_cuisine", request.cuisine_hint or "Fusion"),
            detected_dietary=data.get("detected_dietary", request.dietary_preference or "any"),
            suggested_additional=data.get("suggested_additional", []),
            processing_time_ms=500,
            source="gemini_api",
        )

    except Exception as e:
        logger.warning(f"Gemini refinement failed: {e}. Using fallback.")
        return _fallback_refine(request)


def _fallback_refine(request: RefinementRequest) -> RefinementResponse:
    """Simple fallback when Gemini is unavailable."""
    CATEGORY_MAP = {
        "paneer": "dairy", "cheese": "dairy", "milk": "dairy", "curd": "dairy",
        "yogurt": "dairy", "butter": "dairy", "ghee": "dairy", "cream": "dairy",
        "chicken": "protein", "fish": "protein", "mutton": "protein", "egg": "protein",
        "eggs": "protein", "prawns": "protein", "shrimp": "protein", "tofu": "protein",
        "rice": "grain", "atta": "grain", "bread": "grain", "noodles": "grain",
        "pasta": "grain", "quinoa": "grain", "oats": "grain",
        "salt": "spice", "pepper": "spice", "turmeric": "spice", "cumin": "spice",
        "chilli": "spice", "chili": "spice", "garam masala": "spice",
        "ginger": "spice", "garlic": "spice",
    }

    refined = []
    for ing in request.raw_ingredients:
        name = ing.strip().title()
        cat = CATEGORY_MAP.get(ing.lower().strip(), "vegetable")
        refined.append(RefinedIngredient(
            name=name,
            quantity="as needed",
            category=cat,
            is_primary=True,
        ))

    return RefinementResponse(
        refined_ingredients=refined,
        detected_cuisine=request.cuisine_hint or "Fusion",
        detected_dietary=request.dietary_preference or "any",
        suggested_additional=["Oil", "Salt", "Pepper"],
        processing_time_ms=10,
        source="fallback",
    )
