"""
Recipe retrieval service backed by a trained TF-IDF model with Gemini and heuristic fallbacks.
"""

from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sklearn.metrics.pairwise import cosine_similarity

from app.services.gemini_common import generate_content_text, parse_json_payload

logger = logging.getLogger("uvicorn.error")


MODEL_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "model", "recipe_model.joblib")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ai_models", "recipe_model.joblib")),
]


class PredictedRecipe(BaseModel):
    status: str
    title: Optional[str] = None
    cuisine: Optional[str] = None
    ingredients: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    servings: int = 1
    similarity_score: Optional[float] = None
    message: Optional[str] = None


class ModelPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    refined_ingredients: List[dict] = Field(default_factory=list)
    cuisine: Optional[str] = None
    dietary: Any = ""
    servings: int = 1
    spice_level: str = "medium"
    max_time_minutes: int = 30
    user_allergies: List[str] = Field(default_factory=list)
    expiring_items: List[str] = Field(default_factory=list)
    exclude_ingredients: List[str] = Field(default_factory=list)

    @field_validator("refined_ingredients", mode="before")
    @classmethod
    def _coerce_refined_ingredients(cls, value):
        if isinstance(value, list):
            return value
        return []


class RecipeIngredient(BaseModel):
    name: str
    quantity: str = "as needed"


class RecipeStep(BaseModel):
    step: int
    instruction: str
    time_minutes: int = 5


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


def _normalize_name(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z\s-]", " ", str(value or "").strip().lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    replacements = {
        "capsicum": "bell pepper",
        "bell peppers": "bell pepper",
        "tomatoes": "tomato",
        "onions": "onion",
        "chillies": "chili",
        "chilies": "chili",
        "garbanzo beans": "chickpeas",
    }
    return replacements.get(cleaned, cleaned)


def _normalize_text_tokens(values: List[str]) -> str:
    return " ".join(_normalize_name(value).replace(" ", "_") for value in values if _normalize_name(value))


def _normalize_input(input_data: Dict[str, Any] | ModelPredictionRequest) -> Dict[str, Any]:
    if isinstance(input_data, ModelPredictionRequest):
        ingredients = [_normalize_name(item.get("name", "")) for item in input_data.refined_ingredients]
        dietary_preferences = input_data.dietary
        if isinstance(dietary_preferences, str):
            dietary_preferences = [dietary_preferences] if dietary_preferences.strip() else []
        return {
            "ingredients": [item for item in ingredients if item],
            "cuisine": input_data.cuisine,
            "dietary_preferences": [str(item).strip().lower() for item in dietary_preferences if str(item).strip()],
            "number_of_people": max(int(input_data.servings or 1), 1),
            "spice_level": input_data.spice_level,
            "max_time_minutes": input_data.max_time_minutes,
            "user_allergies": input_data.user_allergies,
            "expiring_items": input_data.expiring_items,
            "exclude_ingredients": [_normalize_name(item) for item in input_data.exclude_ingredients],
        }

    ingredients = [_normalize_name(item) for item in input_data.get("ingredients", [])]
    dietary_preferences = input_data.get("dietary_preferences", [])
    if isinstance(dietary_preferences, str):
        dietary_preferences = [dietary_preferences] if dietary_preferences.strip() else []
    return {
        "ingredients": [item for item in ingredients if item],
        "cuisine": input_data.get("cuisine"),
        "dietary_preferences": [str(item).strip().lower() for item in dietary_preferences if str(item).strip()],
        "number_of_people": max(int(input_data.get("number_of_people", input_data.get("servings", 1)) or 1), 1),
        "spice_level": str(input_data.get("spice_level", "medium")),
        "max_time_minutes": int(input_data.get("max_time_minutes", 30) or 30),
        "user_allergies": [str(item).strip().lower() for item in input_data.get("user_allergies", []) if str(item).strip()],
        "expiring_items": [_normalize_name(item) for item in input_data.get("expiring_items", []) if str(item).strip()],
        "exclude_ingredients": [_normalize_name(item) for item in input_data.get("exclude_ingredients", []) if str(item).strip()],
    }


def _artifact_records(dataframe_like) -> List[dict]:
    if dataframe_like is None:
        return []
    if hasattr(dataframe_like, "to_dict"):
        try:
            return list(dataframe_like.to_dict(orient="records"))
        except TypeError:
            pass
    if isinstance(dataframe_like, list):
        return [record for record in dataframe_like if isinstance(record, dict)]
    return []


class RecipeRetriever:
    def __init__(self, model_path: str):
        artifacts = joblib.load(model_path)
        self.vectorizer = artifacts["vectorizer"]
        self.tfidf_matrix = artifacts["tfidf_matrix"]
        dataframe_like = artifacts.get("dataframe")
        if dataframe_like is None:
            dataframe_like = artifacts.get("records")
        self.records = _artifact_records(dataframe_like)
        if not self.records:
            raise ValueError("Recipe model artifact does not include recipe records")
        logger.info("Loaded recipe model with %s recipes from %s", len(self.records), model_path)

    def predict(self, input_data: Dict[str, Any]) -> PredictedRecipe:
        ingredients = input_data["ingredients"]
        if not ingredients:
            return PredictedRecipe(
                status="error",
                servings=input_data["number_of_people"],
                message="No ingredients provided.",
            )

        query = _normalize_text_tokens(ingredients)
        if not query:
            return PredictedRecipe(
                status="error",
                servings=input_data["number_of_people"],
                message="No usable ingredients provided.",
            )

        input_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(input_vec, self.tfidf_matrix).flatten()
        cuisine = str(input_data.get("cuisine") or "").strip().lower()
        dietary_preferences = {item.lower() for item in input_data.get("dietary_preferences", [])}
        excluded = set(input_data.get("exclude_ingredients", []))
        expiring = set(input_data.get("expiring_items", []))
        query_set = set(ingredients)

        filtered_scores = scores.copy()
        for index, record in enumerate(self.records):
            record_cuisine = str(record.get("cuisine") or "").strip().lower()
            record_tags = {str(tag).strip().lower() for tag in record.get("tags", [])}
            record_ingredients = {_normalize_name(item) for item in record.get("ingredients", [])}

            if cuisine and record_cuisine and record_cuisine != cuisine:
                filtered_scores[index] = -1.0
                continue
            if dietary_preferences and not dietary_preferences.issubset(record_tags):
                filtered_scores[index] = -1.0
                continue
            if excluded and record_ingredients.intersection(excluded):
                filtered_scores[index] = -1.0
                continue

            overlap = len(query_set.intersection(record_ingredients)) / max(len(query_set), 1)
            boost = 0.25 * overlap
            if dietary_preferences:
                boost += 0.05 * len(dietary_preferences.intersection(record_tags))
            if expiring:
                boost += 0.05 * len(expiring.intersection(record_ingredients))
            filtered_scores[index] += boost

        if np.all(filtered_scores < 0):
            return PredictedRecipe(
                status="error",
                servings=input_data["number_of_people"],
                message="No recipe matched the cuisine or dietary filters.",
            )

        best_index = int(np.argmax(filtered_scores))
        best_score = float(filtered_scores[best_index])
        base_score = float(scores[best_index])

        if best_score < 0.18 and base_score < 0.12:
            return PredictedRecipe(
                status="error",
                servings=input_data["number_of_people"],
                similarity_score=round(base_score, 3),
                message="No sufficiently similar recipe found in the trained model.",
            )

        record = self.records[best_index]
        recipe_ingredients = [_normalize_name(item) for item in record.get("ingredients", [])]
        steps = [str(step).strip() for step in record.get("steps", []) if str(step).strip()]

        return PredictedRecipe(
            status="success",
            title=str(record.get("title", "Recipe")).strip(),
            cuisine=str(record.get("cuisine") or input_data.get("cuisine") or "Other"),
            ingredients=recipe_ingredients,
            steps=steps,
            tags=[str(tag).strip().lower() for tag in record.get("tags", []) if str(tag).strip()],
            servings=input_data["number_of_people"],
            similarity_score=round(max(base_score, 0.0), 3),
        )


@lru_cache(maxsize=1)
def _get_retriever() -> Optional[RecipeRetriever]:
    for path in MODEL_PATHS:
        if os.path.exists(path):
            try:
                return RecipeRetriever(path)
            except Exception as exc:
                logger.warning("Failed to load recipe model from %s: %s", path, exc)
    logger.warning("No trained recipe model artifact found in expected locations")
    return None


def _build_generation_prompt(input_data: Dict[str, Any]) -> str:
    cuisine = input_data.get("cuisine") or "Any"
    dietary = input_data.get("dietary_preferences") or []
    exclude = input_data.get("exclude_ingredients") or []
    expiring = input_data.get("expiring_items") or []
    return f"""
You are a professional chef. Generate a recipe based on:
Available ingredients: {input_data["ingredients"]}
Cuisine: {cuisine}
Dietary: {dietary}
Servings: {input_data["number_of_people"]}
Avoid ingredients: {exclude}
Prioritize expiring ingredients: {expiring}

Return ONLY strict JSON:
{{
  "title": "Recipe Name",
  "cuisine": "Detected Cuisine",
  "ingredients": ["item1 with quantity", "item2 with quantity"],
  "steps": ["Step 1 instruction", "Step 2 instruction"],
  "tags": ["vegetarian", "gluten-free"]
}}

Use only the provided ingredients as primary items and assume basic pantry staples.
Each step must be actionable. No markdown and no explanation.
""".strip()


async def _generate_with_gemini(input_data: Dict[str, Any]) -> PredictedRecipe:
    raw_text = await generate_content_text(_build_generation_prompt(input_data), model_name="gemini-2.5-flash")
    parsed = parse_json_payload(raw_text)

    ingredient_lines = []
    for ingredient in parsed.get("ingredients", []):
        cleaned = str(ingredient).strip()
        if cleaned:
            ingredient_lines.append(cleaned)

    steps = [str(step).strip() for step in parsed.get("steps", []) if str(step).strip()]
    if not ingredient_lines or not steps:
        raise ValueError("Gemini returned incomplete recipe data")

    return PredictedRecipe(
        status="success",
        title=str(parsed.get("title", "Generated Recipe")).strip(),
        cuisine=str(parsed.get("cuisine") or input_data.get("cuisine") or "Fusion"),
        ingredients=ingredient_lines,
        steps=steps,
        tags=[str(tag).strip().lower() for tag in parsed.get("tags", []) if str(tag).strip()],
        servings=input_data["number_of_people"],
        similarity_score=1.0,
    )


def _heuristic_recipe(input_data: Dict[str, Any]) -> PredictedRecipe:
    ingredients = input_data["ingredients"] or ["mixed vegetables"]
    main = ingredients[0]
    cuisine = input_data.get("cuisine") or "Fusion"
    tags = list(dict.fromkeys([*input_data.get("dietary_preferences", []), cuisine.lower(), "quick"]))

    return PredictedRecipe(
        status="success",
        title=f"{main.title()} {cuisine} Skillet",
        cuisine=cuisine,
        ingredients=[*ingredients, "oil", "salt", "pepper"],
        steps=[
            f"Prep the ingredients: {', '.join(ingredients)}.",
            "Heat oil in a pan and saute the aromatics or vegetables first.",
            f"Add {main} and the remaining ingredients, season well, and cook until tender.",
            "Taste, adjust seasoning, and serve hot.",
        ],
        tags=tags[:5],
        servings=input_data["number_of_people"],
        similarity_score=None,
    )


async def predict_recipe(input_data: Dict[str, Any] | ModelPredictionRequest) -> PredictedRecipe:
    normalized = _normalize_input(input_data)

    try:
        retriever = _get_retriever()
        if retriever is not None:
            result = retriever.predict(normalized)
            if result.status == "success":
                return result
    except Exception as exc:
        logger.warning("Trained recipe model prediction failed: %s", exc)

    try:
        return await _generate_with_gemini(normalized)
    except Exception as exc:
        logger.warning("Gemini recipe generation failed: %s", exc)
        return _heuristic_recipe(normalized)


def to_generated_recipe(recipe: PredictedRecipe, max_time_minutes: int = 30) -> GeneratedRecipe:
    ingredients = []
    for ingredient in recipe.ingredients or []:
        name, quantity = _split_quantity(str(ingredient))
        ingredients.append(RecipeIngredient(name=name, quantity=quantity))
    preparation_steps = [
        RecipeStep(step=index + 1, instruction=step, time_minutes=max(3, max_time_minutes // max(len(recipe.steps or []), 1)))
        for index, step in enumerate(recipe.steps or [])
    ]
    return GeneratedRecipe(
        title=recipe.title or "Recipe",
        cuisine=recipe.cuisine or "Fusion",
        estimated_time_minutes=max(len(preparation_steps) * 5, min(max_time_minutes, 30)),
        difficulty="easy" if len(preparation_steps) <= 4 else "medium",
        servings=recipe.servings,
        ingredients=ingredients,
        preparation_steps=preparation_steps,
        youtube_search_query=f"{recipe.title or 'recipe'} {recipe.cuisine or 'fusion'} recipe",
        tags=recipe.tags or [],
    )


def _split_quantity(ingredient: str) -> tuple[str, str]:
    text = ingredient.strip()
    match = re.match(r"^([\d./]+\s*[a-zA-Z]+)\s+(.*)$", text)
    if match:
        return match.group(2).strip(), match.group(1).strip()
    return text, "as needed"


async def predict_quick_recipe(expiring_ingredients: List[str], user_allergies: List[str]) -> GeneratedRecipe:
    filtered = [item for item in (_normalize_name(ingredient) for ingredient in expiring_ingredients) if item]
    predicted = await predict_recipe(
        {
            "ingredients": filtered,
            "cuisine": None,
            "dietary_preferences": [],
            "number_of_people": 1,
            "exclude_ingredients": user_allergies,
            "max_time_minutes": 15,
            "expiring_items": filtered,
        }
    )
    return to_generated_recipe(predicted, max_time_minutes=15)
