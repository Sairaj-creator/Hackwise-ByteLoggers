'llm services.py'
"""
LLM SERVICE — RECIPE PREDICTION & GENERATION
==============================================
Status: LIVE

TWO-STAGE PIPELINE:
  Stage 1: Gemini API normalizes raw user input into structured JSON
  Stage 2: Custom TF-IDF model (recipe_model.joblib) finds best matching recipe
  Fallback: If custom model has no match, Gemini generates a full recipe

INTEGRATION POINT:
  Called by: POST /api/v1/recipes/generate endpoint (routers/recipes.py)

REQUIRES:
  - GOOGLE_API_KEY in backend/.env
  - recipe_model.joblib in backend/ai_models/
  - pip install google-generativeai joblib scikit-learn
"""

import json
import re
import os
import logging
import numpy as np
import joblib
from typing import List, Optional
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


# ============ PATHS ============

JOBLIB_MODEL_PATH = os.path.join(
    os.path.dirname(__file__),   # backend/app/services/
    "..", "..",                   # backend/
    "ai_models", "recipe_model.joblib"
)
JOBLIB_MODEL_PATH = os.path.abspath(JOBLIB_MODEL_PATH)


# ============ STAGE 1: GEMINI REFINER ============

class GeminiRefiner:
    """
    Takes raw/messy user input and normalizes it into structured JSON
    using Gemini API. Replaces the Colab userdata.get() with os.environ.
    """

    def __init__(self):
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found in environment. "
                "Add it to backend/.env file."
            )
        genai.configure(api_key=api_key)
        # gemini-2.0-flash is confirmed working (your notebook had 404 on 1.5-flash)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def refine_input(self, raw_ingredients: str, num_people: int, preferences: list) -> str:
        """Normalize messy user input into structured JSON string."""
        prompt = f"""
        Convert the following user cooking request into a strict JSON object.
        User Ingredients: {raw_ingredients}
        Number of People: {num_people}
        Dietary Preferences: {preferences}

        Output format:
        {{
            "ingredients": ["normalized_item1", "normalized_item2"],
            "number_of_people": {num_people},
            "cuisine": "detected_cuisine_or_null",
            "dietary_preferences": ["tag1", "tag2"]
        }}
        Only return valid JSON. No markdown, no backticks.
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json_match.group(0)
            return text.strip()
        except Exception as e:
            logger.warning(f"Gemini refiner failed: {e}, using fallback parsing")
            # Fallback — parse manually without Gemini
            return json.dumps({
                "ingredients": [i.strip() for i in str(raw_ingredients).split(",")],
                "number_of_people": num_people,
                "cuisine": None,
                "dietary_preferences": preferences if preferences else [],
            })


# ============ STAGE 2: CUSTOM TF-IDF MODEL ============

class RecipePredictor:
    """
    Loads the trained recipe_model.joblib and predicts best matching recipe
    using TF-IDF cosine similarity. Exact code from your notebook.
    """

    def __init__(self, model_path: str = None):
        path = model_path or JOBLIB_MODEL_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"recipe_model.joblib not found at {path}. "
                f"Run the training notebook and place the .joblib file in backend/ai_models/"
            )
        artifacts = joblib.load(path)
        self.vectorizer = artifacts["vectorizer"]
        self.tfidf_matrix = artifacts["tfidf_matrix"]
        self.df = artifacts["dataframe"]
        logger.info(f"RecipePredictor loaded: {len(self.df)} recipes from {path}")

    def predict(self, input_json: str) -> dict:
        """Predict best matching recipe from structured JSON input."""
        data = json.loads(input_json)
        user_ingredients = data.get("ingredients", [])

        raw_cuisine = data.get("cuisine")
        user_cuisine = (
            str(raw_cuisine).lower().strip()
            if raw_cuisine and str(raw_cuisine).lower() not in ["none", "null", "nan", ""]
            else None
        )

        user_dietary_prefs = [p.lower().strip() for p in data.get("dietary_preferences", [])]

        # Preprocess input
        proc_input = " ".join([i.lower().strip().replace(" ", "_") for i in user_ingredients])
        if not proc_input.strip():
            return {"status": "error", "message": "No ingredients provided."}

        input_vec = self.vectorizer.transform([proc_input])
        sims = cosine_similarity(input_vec, self.tfidf_matrix).flatten()

        # Create boolean mask for hard filters
        mask = np.ones(len(self.df), dtype=bool)

        for i in range(len(self.df)):
            if user_cuisine:
                if str(self.df.iloc[i]["cuisine"]).lower().strip() != user_cuisine:
                    mask[i] = False
            if user_dietary_prefs:
                tags = [t.lower() for t in self.df.iloc[i]["tags"]]
                if not all(p in tags for p in user_dietary_prefs):
                    mask[i] = False

        if not np.any(mask):
            return {"status": "no_match", "message": "No matching recipe in custom dataset."}

        valid_scores = sims.copy()
        valid_scores[~mask] = -1.0

        best_idx = np.argmax(valid_scores)

        if valid_scores[best_idx] <= 0:
            if user_cuisine or user_dietary_prefs:
                return {"status": "no_match", "message": "No matching recipe within filters."}

        res = self.df.iloc[best_idx]
        return {
            "status": "success",
            "recipe": res["title"],
            "cuisine": res["cuisine"],
            "ingredients": res["ingredients"],
            "steps": res["steps"],
            "tags": res["tags"],
            "servings": data.get("number_of_people", 1),
            "similarity_score": round(float(sims[best_idx]), 3),
        }


# ============ GEMINI FULL RECIPE GENERATION (FALLBACK) ============

async def generate_recipe_with_gemini(
    ingredients: List[str],
    cuisine: Optional[str] = None,
    dietary: Optional[str] = None,
    spice_level: str = "medium",
    max_time_minutes: int = 30,
    number_of_people: int = 2,
    user_allergies: Optional[List[str]] = None,
    expiring_ingredients: Optional[List[str]] = None,
) -> dict:
    """
    Full recipe generation using Gemini when custom model has no match.
    Returns structured recipe JSON matching your master prompt spec.
    """
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"status": "error", "message": "GOOGLE_API_KEY not configured in .env"}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""You are a professional chef. Generate a recipe in STRICT JSON format.

RULES:
1. Use ONLY the provided ingredients as primary items. Assume basic pantry staples available.
2. Match the requested cuisine and spice level.
3. Keep prep time within {max_time_minutes} minutes.
4. Each step must include time_minutes estimate.
5. If user has allergies, flag dangerous ingredients and suggest substitutions.
6. Prioritize ingredients marked as expiring soon.
7. Adjust quantities for {number_of_people} servings.

OUTPUT FORMAT (strict JSON, no markdown, no backticks):
{{
  "title": "string",
  "cuisine": "string",
  "estimated_time_minutes": number,
  "difficulty": "easy|medium|hard",
  "servings": {number_of_people},
  "ingredients": [{{"name": "string", "quantity": "string", "from_fridge": true}}],
  "preparation_steps": [{{"step": number, "instruction": "string", "time_minutes": number}}],
  "youtube_search_query": "string",
  "tags": ["string"],
  "allergy_check": {{
    "safe": true,
    "warnings": [],
    "substitutions": []
  }}
}}

USER ALLERGIES: {user_allergies or "None"}
EXPIRING SOON: {expiring_ingredients or "None"}
AVAILABLE INGREDIENTS: {", ".join(ingredients)}
CUISINE: {cuisine or "Any"}
SPICE LEVEL: {spice_level}
DIETARY: {dietary or "None"}
"""

    try:
        response = model.generate_content(prompt)
        text = response.text

        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            recipe_data = json.loads(json_match.group(0))
            # Mark which ingredients came from fridge
            for ing in recipe_data.get("ingredients", []):
                ing["from_fridge"] = ing.get("name", "").lower() in [
                    i.lower() for i in ingredients
                ]
            return {"status": "success", "source": "gemini", "recipe": recipe_data}
        else:
            return {"status": "error", "message": "Gemini returned non-JSON response"}

    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        error_msg = str(e)
        if "404" in error_msg:
            return {"status": "error", "message": "Gemini model not found. Check API key."}
        if "429" in error_msg:
            return {"status": "error", "message": "Rate limit exceeded. Try again shortly."}
        return {"status": "error", "message": f"Recipe generation failed: {error_msg}"}


# ============ MAIN PIPELINE (called by recipes.py router) ============

# Cache instances so they're loaded once, not per request
_refiner = None
_predictor = None


def _get_refiner():
    global _refiner
    if _refiner is None:
        _refiner = GeminiRefiner()
    return _refiner


def _get_predictor():
    global _predictor
    if _predictor is None:
        try:
            _predictor = RecipePredictor()
        except FileNotFoundError:
            logger.warning("recipe_model.joblib not found — will use Gemini only")
            _predictor = None
    return _predictor


async def run_recipe_pipeline(
    ingredients: List[str],
    cuisine: Optional[str] = None,
    dietary_preferences: Optional[List[str]] = None,
    number_of_people: int = 2,
    spice_level: str = "medium",
    max_time_minutes: int = 30,
    user_allergies: Optional[List[str]] = None,
    expiring_ingredients: Optional[List[str]] = None,
) -> dict:
    """
    Two-stage recipe pipeline:
      Stage 1: Gemini normalizes raw input
      Stage 2: Custom TF-IDF model tries to find a match
      Fallback: If no match, Gemini generates a full recipe

    Called by: routers/recipes.py
    Usage:    result = await run_recipe_pipeline(ingredients=["tomato", "pasta"], ...)
    """

    raw_ingredients = ", ".join(ingredients)

    # ── Stage 1: Gemini refines input ──
    try:
        refiner = _get_refiner()
        structured_json = refiner.refine_input(
            raw_ingredients, number_of_people, dietary_preferences or []
        )
        logger.info(f"Stage 1 (Gemini refine): {structured_json[:200]}")
    except Exception as e:
        logger.warning(f"Gemini refiner failed: {e}, building input manually")
        structured_json = json.dumps({
            "ingredients": ingredients,
            "number_of_people": number_of_people,
            "cuisine": cuisine,
            "dietary_preferences": dietary_preferences or [],
        })

    # ── Stage 2: Custom model prediction ──
    predictor = _get_predictor()
    if predictor is not None:
        try:
            result = predictor.predict(structured_json)
            if result.get("status") == "success":
                result["source"] = "custom_model"
                logger.info(f"Stage 2 (custom model): matched '{result.get('recipe')}'")
                return result
            else:
                logger.info(f"Stage 2: no match — {result.get('message')}")
        except Exception as e:
            logger.warning(f"Custom model prediction failed: {e}")

    # ── Fallback: Gemini generates full recipe ──
    logger.info("Falling back to Gemini full recipe generation")
    return await generate_recipe_with_gemini(
        ingredients=ingredients,
        cuisine=cuisine,
        dietary=dietary_preferences[0] if dietary_preferences else None,
        spice_level=spice_level,
        max_time_minutes=max_time_minutes,
        number_of_people=number_of_people,
        user_allergies=user_allergies,
        expiring_ingredients=expiring_ingredients,
    )