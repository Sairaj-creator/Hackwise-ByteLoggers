"""
RECIPE MODEL SERVICE — Stage 2: Gemini-Powered Recipe Generation
================================================================
Generates real recipes using Google Gemini based on user ingredients,
cuisine preference, dietary restrictions, and allergy information.
"""

import json
import re
import logging
from typing import List
from pydantic import BaseModel
from google import genai
from app.config import get_settings

logger = logging.getLogger("uvicorn.error")


# ============ INPUT/OUTPUT CONTRACTS ============

class ModelPredictionRequest(BaseModel):
    refined_ingredients: List[dict]         # [{"name": "Paneer", "quantity": "200g", "category": "dairy"}, ...]
    cuisine: str                            # "North Indian"
    dietary: str                            # "vegetarian"
    servings: int                           # 2
    spice_level: str                        # "mild" | "medium" | "hot"
    max_time_minutes: int                   # 30
    user_allergies: List[str] = []          # ["peanuts", "shellfish"]
    expiring_items: List[str] = []          # ["paneer", "tomato"]
    exclude_ingredients: List[str] = []     # Blocked by Allergy Guardian


class RecipeIngredient(BaseModel):
    name: str
    quantity: str


class RecipeStep(BaseModel):
    step: int
    instruction: str
    time_minutes: int


class GeneratedRecipe(BaseModel):
    title: str
    cuisine: str
    estimated_time_minutes: int
    difficulty: str
    servings: int
    ingredients: List[RecipeIngredient]
    preparation_steps: List[RecipeStep]
    youtube_search_query: str
    tags: List[str]


# ============ GEMINI IMPLEMENTATION ============

def _get_gemini_client():
    """Get a Gemini API client."""
    settings = get_settings()
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _build_recipe_prompt(request: ModelPredictionRequest) -> str:
    """Build the prompt for Gemini to generate a recipe."""
    ingredient_names = [ing.get("name", "") for ing in request.refined_ingredients]
    exclude_note = ""
    if request.exclude_ingredients:
        exclude_note = f"\nIMPORTANT: Do NOT use these allergens: {', '.join(request.exclude_ingredients)}"

    expiry_note = ""
    if request.expiring_items:
        expiry_note = f"\nPrioritize using these expiring items: {', '.join(request.expiring_items)}"

    return f"""Generate a creative, delicious recipe using these ingredients as the base:
Ingredients: {', '.join(ingredient_names)}

Requirements:
- Cuisine style: {request.cuisine or 'Any'}
- Dietary preference: {request.dietary or 'Any'}  
- Spice level: {request.spice_level}
- Servings: {request.servings}
- Maximum cooking time: {request.max_time_minutes} minutes
- Difficulty: appropriate for home cooking{exclude_note}{expiry_note}

You MUST respond with ONLY valid JSON matching this EXACT structure (no markdown, no explanation, no code fences):
{{
  "title": "Recipe Name",
  "cuisine": "Cuisine Type",
  "estimated_time_minutes": 25,
  "difficulty": "easy",
  "servings": {request.servings},
  "ingredients": [
    {{"name": "Ingredient 1", "quantity": "200g"}},
    {{"name": "Ingredient 2", "quantity": "1 cup"}}
  ],
  "preparation_steps": [
    {{"step": 1, "instruction": "Do this first", "time_minutes": 5}},
    {{"step": 2, "instruction": "Then do this", "time_minutes": 10}}
  ],
  "youtube_search_query": "recipe name easy home recipe",
  "tags": ["quick", "vegetarian", "indian"]
}}

Rules:
- Include the provided ingredients plus any common pantry items needed (oil, salt, spices)
- Make the recipe realistic, practical, and delicious
- Each step must have a clear instruction and realistic time estimate
- Total time across all steps should roughly match estimated_time_minutes
- Tags should include cuisine, dietary, and difficulty descriptors
- difficulty must be one of: "easy", "medium", "hard"
- Return ONLY the JSON object, nothing else"""


def _parse_recipe_json(raw_text: str, request: ModelPredictionRequest) -> GeneratedRecipe:
    """Parse the Gemini response into a GeneratedRecipe object."""
    text = raw_text.strip()
    # Robustly extract JSON object via regex (handles ```json fences, leading text, etc.)
    obj_match = re.search(r'\{[\s\S]*\}', text)
    if obj_match:
        data = json.loads(obj_match.group(0))
    else:
        data = json.loads(text)

    return GeneratedRecipe(
        title=data.get("title", "Generated Recipe"),
        cuisine=data.get("cuisine", request.cuisine),
        estimated_time_minutes=data.get("estimated_time_minutes", request.max_time_minutes),
        difficulty=data.get("difficulty", "easy"),
        servings=data.get("servings", request.servings),
        ingredients=[
            RecipeIngredient(name=ing["name"], quantity=ing["quantity"])
            for ing in data.get("ingredients", [])
        ],
        preparation_steps=[
            RecipeStep(
                step=s.get("step", i + 1),
                instruction=s["instruction"],
                time_minutes=s.get("time_minutes", 5),
            )
            for i, s in enumerate(data.get("preparation_steps", []))
        ],
        youtube_search_query=data.get("youtube_search_query", f"{data.get('title', '')} recipe"),
        tags=data.get("tags", []),
    )


async def predict_recipe(request: ModelPredictionRequest) -> GeneratedRecipe:
    """
    Generate a recipe using the Gemini API based on user ingredients and preferences.
    Falls back to a simple recipe if Gemini fails.
    """
    try:
        client = _get_gemini_client()
        prompt = _build_recipe_prompt(request)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        raw_text = response.text
        if not raw_text:
            raise ValueError("Gemini returned empty response")
        logger.info(f"Gemini recipe generated: {raw_text[:100]}...")
        return _parse_recipe_json(raw_text, request)
    except Exception as e:
        logger.warning(f"Gemini recipe generation failed: {e}. Using fallback.")

    # Fallback is in a SEPARATE try so exceptions don't chain
    try:
        return _build_fallback_recipe(request)
    except Exception as fe:
        logger.error(f"Fallback recipe also failed: {fe}", exc_info=True)
        raise RuntimeError(f"Both Gemini and fallback recipe generation failed: {fe}") from fe


async def predict_quick_recipe(
    expiring_ingredients: List[str],
    user_allergies: List[str],
) -> GeneratedRecipe:
    """
    Generate a quick recipe for expiring ingredients using Gemini.
    """
    try:
        client = _get_gemini_client()

        allergy_note = ""
        if user_allergies:
            allergy_note = f"\nAvoid these allergens: {', '.join(user_allergies)}"

        prompt = f"""Generate a QUICK recipe (under 15 minutes) using these ingredients that are about to expire:
{', '.join(expiring_ingredients)}{allergy_note}

Respond with ONLY valid JSON (no markdown, no code fences):
{{
  "title": "Quick Recipe Name",
  "cuisine": "Fusion",
  "estimated_time_minutes": 10,
  "difficulty": "easy",
  "servings": 1,
  "ingredients": [{{"name": "Ingredient", "quantity": "amount"}}],
  "preparation_steps": [{{"step": 1, "instruction": "Step description", "time_minutes": 5}}],
  "youtube_search_query": "quick recipe name",
  "tags": ["quick", "waste-saver"]
}}"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        return _parse_recipe_json(response.text, ModelPredictionRequest(
            refined_ingredients=[{"name": i, "quantity": "as available", "category": "general"} for i in expiring_ingredients],
            cuisine="Fusion",
            dietary="",
            servings=1,
            spice_level="medium",
            max_time_minutes=15,
        ))

    except Exception as e:
        logger.warning(f"Gemini quick recipe failed: {e}. Using fallback.")
        return GeneratedRecipe(
            title=f"Quick {expiring_ingredients[0].title()} Stir Fry",
            cuisine="Fusion",
            estimated_time_minutes=10,
            difficulty="easy",
            servings=1,
            ingredients=[RecipeIngredient(name=item, quantity="as available") for item in expiring_ingredients],
            preparation_steps=[
                RecipeStep(step=1, instruction=f"Chop {', '.join(expiring_ingredients)}", time_minutes=3),
                RecipeStep(step=2, instruction="Heat oil and stir fry everything with salt and pepper", time_minutes=5),
                RecipeStep(step=3, instruction="Serve immediately", time_minutes=2),
            ],
            youtube_search_query=f"quick {expiring_ingredients[0]} recipe",
            tags=["quick", "waste-saver"],
        )


def _build_fallback_recipe(request: ModelPredictionRequest) -> GeneratedRecipe:
    """Build a simple fallback recipe from the ingredients when Gemini is unavailable."""
    ingredient_names = [ing.get("name", "Ingredient") for ing in request.refined_ingredients]
    main_ingredient = ingredient_names[0] if ingredient_names else "Mixed"

    return GeneratedRecipe(
        title=f"{main_ingredient} {request.cuisine or 'Home'} Style",
        cuisine=request.cuisine or "Fusion",
        estimated_time_minutes=request.max_time_minutes,
        difficulty="easy",
        servings=request.servings,
        ingredients=[
            RecipeIngredient(name=ing.get("name", ""), quantity=ing.get("quantity", "as needed"))
            for ing in request.refined_ingredients
        ] + [
            RecipeIngredient(name="Oil", quantity="2 tbsp"),
            RecipeIngredient(name="Salt", quantity="to taste"),
            RecipeIngredient(name="Pepper", quantity="to taste"),
        ],
        preparation_steps=[
            RecipeStep(step=1, instruction=f"Prepare and chop {', '.join(ingredient_names)}", time_minutes=5),
            RecipeStep(step=2, instruction="Heat oil in a pan on medium flame", time_minutes=2),
            RecipeStep(step=3, instruction=f"Cook the {main_ingredient} with seasoning until done", time_minutes=max(10, request.max_time_minutes - 10)),
            RecipeStep(step=4, instruction="Adjust salt and serve hot", time_minutes=2),
        ],
        youtube_search_query=f"{main_ingredient} {request.cuisine} recipe easy",
        tags=[request.cuisine.lower(), request.dietary.lower(), "homemade"] if request.cuisine else ["homemade"],
    )
