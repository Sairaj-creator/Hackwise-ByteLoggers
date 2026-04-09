"""
Gemini-backed input refinement and compatibility wrappers for the recipe pipeline.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.services.gemini_common import generate_content_text, parse_json_payload

logger = logging.getLogger("uvicorn.error")


COMMON_FILLER_WORDS = {
    "some",
    "fresh",
    "few",
    "little",
    "a",
    "an",
    "the",
    "box",
    "packet",
    "pack",
    "bunch",
    "of",
    "with",
    "and",
}

INGREDIENT_SYNONYMS = {
    "capsicum": "bell pepper",
    "bell peppers": "bell pepper",
    "spaghetti noodles": "spaghetti",
    "tomatoes": "tomato",
    "onions": "onion",
    "potatoes": "potato",
    "chillies": "chili",
    "chilies": "chili",
    "garbanzo beans": "chickpeas",
    "curd": "yogurt",
}


class RefinementRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    raw_ingredients: str
    number_of_people: int = Field(default=2, validation_alias=AliasChoices("number_of_people", "servings"))
    dietary_preferences: List[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("dietary_preferences", "dietary_preference"),
    )
    cuisine_hint: Optional[str] = None

    @field_validator("raw_ingredients", mode="before")
    @classmethod
    def _coerce_raw_ingredients(cls, value):
        if isinstance(value, list):
            return ", ".join(str(item).strip() for item in value if str(item).strip())
        return str(value or "")

    @field_validator("dietary_preferences", mode="before")
    @classmethod
    def _coerce_dietary_preferences(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = [part.strip() for part in re.split(r"[,/]", value) if part.strip()]
        return [str(item).strip().lower() for item in value if str(item).strip()]


class RefinedInput(BaseModel):
    ingredients: List[str]
    number_of_people: int
    cuisine: Optional[str] = None
    dietary_preferences: List[str] = Field(default_factory=list)


class RefinedIngredient(BaseModel):
    name: str
    quantity: str = "as needed"
    category: str = "general"
    is_primary: bool = True


class RefinementResponse(BaseModel):
    refined_ingredients: List[RefinedIngredient]
    detected_cuisine: str
    detected_dietary: str
    suggested_additional: List[str]
    processing_time_ms: int
    source: str


def _normalize_ingredient_name(value: str) -> str:
    lowered = value.lower().strip()
    lowered = re.sub(r"\([^)]*\)", "", lowered)
    lowered = re.sub(r"\b\d+[\d\s/.-]*\b", " ", lowered)
    lowered = re.sub(
        r"\b(cup|cups|tbsp|tsp|teaspoon|teaspoons|tablespoon|tablespoons|gram|grams|g|kg|ml|l|oz|lb|pound|pounds|clove|cloves|slice|slices|piece|pieces|can|cans|pack|packet|box)\b",
        " ",
        lowered,
    )
    lowered = re.sub(r"[^a-zA-Z\s-]", " ", lowered)
    tokens = [token for token in lowered.split() if token and token not in COMMON_FILLER_WORDS]
    cleaned = " ".join(tokens).strip()
    return INGREDIENT_SYNONYMS.get(cleaned, cleaned)


def _guess_cuisine(text: str, ingredients: List[str]) -> Optional[str]:
    probe = f"{text} {' '.join(ingredients)}".lower()
    rules = {
        "Indian": ["paneer", "dal", "garam masala", "roti", "biryani", "ghee", "curry"],
        "Italian": ["pasta", "spaghetti", "parmesan", "mozzarella", "basil", "risotto"],
        "Chinese": ["soy sauce", "bok choy", "sesame", "ginger", "tofu", "noodle"],
        "Mediterranean": ["feta", "olive", "hummus", "pita", "quinoa", "cucumber"],
        "Mexican": ["tortilla", "jalapeno", "beans", "avocado", "salsa", "taco"],
        "Japanese": ["miso", "ramen", "dashi", "nori", "teriyaki", "wasabi"],
    }
    for cuisine, keywords in rules.items():
        if any(keyword in probe for keyword in keywords):
            return cuisine
    return None


def _guess_category(ingredient: str) -> str:
    probe = ingredient.lower()
    if probe in {"paneer", "milk", "yogurt", "butter", "ghee", "cream", "cheese"}:
        return "dairy"
    if probe in {"chicken", "beef", "fish", "shrimp", "tofu", "egg", "eggs", "beans", "lentils"}:
        return "protein"
    if probe in {"rice", "pasta", "spaghetti", "quinoa", "bread", "oats", "noodle", "noodles"}:
        return "grain"
    if probe in {"salt", "pepper", "garam masala", "turmeric", "cumin", "paprika", "oregano"}:
        return "spice"
    if probe in {"soy sauce", "vinegar", "olive oil", "sesame oil", "tomato sauce"}:
        return "condiment"
    return "vegetable"


def _suggest_supporting_ingredients(ingredients: List[str], cuisine: Optional[str]) -> List[str]:
    existing = {ingredient.lower() for ingredient in ingredients}
    suggestions: list[str] = []

    cuisine_defaults = {
        "Indian": ["garam masala", "cumin", "ginger", "garlic"],
        "Italian": ["olive oil", "garlic", "basil", "parmesan"],
        "Chinese": ["soy sauce", "ginger", "garlic", "sesame oil"],
        "Mediterranean": ["olive oil", "lemon", "oregano", "parsley"],
        "Mexican": ["cumin", "lime", "cilantro", "paprika"],
        "Japanese": ["soy sauce", "sesame", "ginger", "rice vinegar"],
    }

    for candidate in cuisine_defaults.get(cuisine or "", ["oil", "salt", "pepper"]):
        if candidate.lower() not in existing and candidate not in suggestions:
            suggestions.append(candidate)

    for candidate in ["oil", "salt", "pepper"]:
        if candidate.lower() not in existing and candidate not in suggestions:
            suggestions.append(candidate)
    return suggestions[:4]


def _fallback(request: RefinementRequest) -> RefinedInput:
    parts = re.split(r"[,\n]|\band\b|&", request.raw_ingredients)
    ingredients = []
    for part in parts:
        cleaned = _normalize_ingredient_name(part)
        if cleaned and cleaned not in ingredients:
            ingredients.append(cleaned)

    return RefinedInput(
        ingredients=ingredients,
        number_of_people=request.number_of_people,
        cuisine=request.cuisine_hint or _guess_cuisine(request.raw_ingredients, ingredients),
        dietary_preferences=request.dietary_preferences,
    )


def _build_prompt(request: RefinementRequest) -> str:
    cuisine_line = f"User cuisine hint: {request.cuisine_hint}" if request.cuisine_hint else "User cuisine hint: null"
    return f"""
Convert this cooking request into strict JSON.

User Ingredients: {request.raw_ingredients}
People: {request.number_of_people}
Dietary Preferences: {request.dietary_preferences}
{cuisine_line}

Return ONLY JSON:
{{
  "ingredients": ["item1", "item2"],
  "number_of_people": {request.number_of_people},
  "cuisine": "detected_or_null",
  "dietary_preferences": ["tag1"]
}}

Rules:
- Normalize ingredients to simple singular cooking words.
- Remove packaging, quantity, and descriptive filler words.
- Keep cuisine null if it is unclear.
- Preserve dietary preferences unless clearly incompatible.
- No markdown and no explanation.
""".strip()


async def _refine_ingredients_internal(request: RefinementRequest) -> tuple[RefinedInput, str]:
    try:
        raw_text = await generate_content_text(_build_prompt(request), model_name="gemini-2.5-flash")
        parsed = parse_json_payload(raw_text)

        ingredients = []
        for item in parsed.get("ingredients", []):
            cleaned = _normalize_ingredient_name(str(item))
            if cleaned and cleaned not in ingredients:
                ingredients.append(cleaned)

        if not ingredients:
            raise ValueError("Gemini returned no usable ingredients")

        cuisine = parsed.get("cuisine") or request.cuisine_hint or _guess_cuisine(request.raw_ingredients, ingredients)
        if isinstance(cuisine, str) and cuisine.lower() in {"null", "none", ""}:
            cuisine = None

        dietary_preferences = parsed.get("dietary_preferences", request.dietary_preferences)
        if isinstance(dietary_preferences, str):
            dietary_preferences = [dietary_preferences]

        return RefinedInput(
            ingredients=ingredients,
            number_of_people=int(parsed.get("number_of_people", request.number_of_people) or request.number_of_people),
            cuisine=cuisine,
            dietary_preferences=[
                str(item).strip().lower()
                for item in dietary_preferences
                if str(item).strip()
            ],
        ), "gemini_api"
    except Exception as exc:
        logger.warning("Gemini refinement failed: %s", exc)
        return _fallback(request), "fallback"


async def refine_ingredients(request: RefinementRequest) -> RefinedInput:
    refined, _ = await _refine_ingredients_internal(request)
    return refined


async def refine_user_input(request: RefinementRequest) -> RefinementResponse:
    refined, source = await _refine_ingredients_internal(request)
    refined_ingredients = [
        RefinedIngredient(
            name=ingredient.title(),
            quantity="as needed",
            category=_guess_category(ingredient),
            is_primary=True,
        )
        for ingredient in refined.ingredients
    ]

    detected_cuisine = refined.cuisine or request.cuisine_hint or "Fusion"
    detected_dietary = refined.dietary_preferences[0] if refined.dietary_preferences else "any"

    return RefinementResponse(
        refined_ingredients=refined_ingredients,
        detected_cuisine=detected_cuisine,
        detected_dietary=detected_dietary,
        suggested_additional=_suggest_supporting_ingredients(refined.ingredients, refined.cuisine),
        processing_time_ms=0,
        source=source,
    )
