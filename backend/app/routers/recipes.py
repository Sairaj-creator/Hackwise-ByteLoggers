"""
Recipes Router
===============
Endpoints: generate, list my recipes, detail, nutrients, cooking mode, favorites.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import json
import re
from huggingface_hub import InferenceClient

from app.config import get_settings
from app.rate_limiter import limiter

from app.dependencies import get_current_user
from app.database.mongodb import get_database
from app.services.recipe_pipeline_service import generate_recipe_pipeline
from app.services.cache_service import get_cached, set_cached, make_cache_key, NUTRITION_CACHE_TTL
from app.models.recipe import RecipeGenerateRequest

router = APIRouter(prefix="/api/v1/recipes", tags=["Recipes"])
_log = __import__("logging").getLogger("uvicorn.error")

# ─── In-memory fallback cache (used when Redis is unavailable) ───
_mem_cache: dict = {}

# ─── Static fallback data (served when Gemini quota is exhausted) ───
_FALLBACK_INGREDIENTS = [
    {"id": "ing-1", "name": "Avocado", "calories_per_100g": 160, "protein_g": 2.0, "carbs_g": 8.5, "fats_g": 14.7,
     "benefits": ["Heart healthy fats", "Rich in fiber", "High in potassium", "Supports eye health", "Improves digestion", "Boosts brain function"]},
    {"id": "ing-2", "name": "Spinach", "calories_per_100g": 23, "protein_g": 2.9, "carbs_g": 3.6, "fats_g": 0.4,
     "benefits": ["High in iron", "Rich in vitamins A & C", "Supports bone health", "Anti-inflammatory", "Boosts immunity", "Improves eye health"]},
    {"id": "ing-3", "name": "Quinoa", "calories_per_100g": 368, "protein_g": 14.1, "carbs_g": 64.2, "fats_g": 6.1,
     "benefits": ["Complete protein source", "Gluten-free", "High in fiber", "Rich in magnesium", "Controls blood sugar", "Supports weight management"]},
    {"id": "ing-4", "name": "Blueberries", "calories_per_100g": 57, "protein_g": 0.7, "carbs_g": 14.5, "fats_g": 0.3,
     "benefits": ["High in antioxidants", "Improves brain function", "Supports heart health", "Anti-aging properties", "Reduces inflammation", "Boosts memory"]},
    {"id": "ing-5", "name": "Salmon", "calories_per_100g": 208, "protein_g": 20.0, "carbs_g": 0.0, "fats_g": 13.0,
     "benefits": ["Rich in omega-3", "High quality protein", "Supports heart health", "Reduces inflammation", "Boosts brain health", "Improves skin"]},
    {"id": "ing-6", "name": "Sweet Potato", "calories_per_100g": 86, "protein_g": 1.6, "carbs_g": 20.1, "fats_g": 0.1,
     "benefits": ["High in vitamin A", "Rich in fiber", "Antioxidant-rich", "Supports gut health", "Regulates blood sugar", "Boosts immunity"]},
    {"id": "ing-7", "name": "Greek Yogurt", "calories_per_100g": 59, "protein_g": 10.0, "carbs_g": 3.6, "fats_g": 0.4,
     "benefits": ["High in protein", "Rich in probiotics", "Supports gut health", "Strengthens bones", "Boosts immunity", "Low in calories"]},
    {"id": "ing-8", "name": "Turmeric", "calories_per_100g": 354, "protein_g": 7.8, "carbs_g": 64.9, "fats_g": 9.9,
     "benefits": ["Powerful anti-inflammatory", "Rich in antioxidants", "Improves brain function", "Reduces arthritis pain", "Supports heart health", "Natural detoxifier"]},
    {"id": "ing-9", "name": "Almonds", "calories_per_100g": 579, "protein_g": 21.2, "carbs_g": 21.6, "fats_g": 49.9,
     "benefits": ["Heart-healthy fats", "High in vitamin E", "Reduces cholesterol", "Supports weight control", "Boosts brain health", "Rich in magnesium"]},
    {"id": "ing-10", "name": "Broccoli", "calories_per_100g": 34, "protein_g": 2.8, "carbs_g": 6.6, "fats_g": 0.4,
     "benefits": ["Cancer-fighting compounds", "High in vitamin C", "Rich in fiber", "Supports bone health", "Boosts immunity", "Aids digestion"]},
]

_FALLBACK_TRENDING = [
    {"recipe_id": "trending-fallback-0", "title": "Butter Chicken", "cuisine": "Indian", "difficulty": "Medium", "total_time_minutes": 45},
    {"recipe_id": "trending-fallback-1", "title": "Avocado Toast with Poached Egg", "cuisine": "Modern", "difficulty": "Easy", "total_time_minutes": 15},
    {"recipe_id": "trending-fallback-2", "title": "Pasta Aglio e Olio", "cuisine": "Italian", "difficulty": "Easy", "total_time_minutes": 20},
    {"recipe_id": "trending-fallback-3", "title": "Thai Green Curry", "cuisine": "Thai", "difficulty": "Medium", "total_time_minutes": 35},
]


def _parse_gemini_json(raw_text: str):
    """
    Robustly parse JSON from a Gemini response that may contain markdown fences.
    Tries regex extraction of array or object before falling back to raw parse.
    """
    text = raw_text.strip()
    # Try to extract JSON array first (for list responses like trending/ingredients)
    array_match = re.search(r'\[[\s\S]*\]', text)
    if array_match:
        return json.loads(array_match.group(0))
    # Try JSON object
    obj_match = re.search(r'\{[\s\S]*\}', text)
    if obj_match:
        return json.loads(obj_match.group(0))
    # Last resort — parse as-is
    return json.loads(text)


# ─── Generate Recipe ───

@router.post("/generate")
@limiter.limit(get_settings().RATE_LIMIT_RECIPE_GENERATE)
async def generate_recipe(
    request: Request,
    payload: RecipeGenerateRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()

    if not payload.ingredients and not payload.raw_text_input:
        raise HTTPException(400, "Provide either ingredients or raw_text_input")

    merged_preferences = dict(payload.preferences or {})
    if payload.dietary_preferences and not merged_preferences.get("dietary_preferences"):
        merged_preferences["dietary_preferences"] = payload.dietary_preferences

    # Find expiring items if requested
    expiring_items = []
    if payload.prioritize_expiring:
        items = await db.fridge_items.find({
            "user_id": user["_id"],
            "is_used": False,
            "expiry_status": {"$in": ["warning", "critical"]},
        }).to_list(length=50)
        expiring_items = [i["ingredient_name"] for i in items]

    # Generate via the pipeline
    try:
        result = await generate_recipe_pipeline(
            ingredients=payload.ingredients,
            preferences=merged_preferences,
            user_allergies=user.get("allergies", []),
            expiring_items=expiring_items,
            servings=payload.servings,
            raw_text_input=payload.raw_text_input,
        )
    except Exception as exc:
        _log.error("generate_recipe_pipeline raised: %s", exc, exc_info=True)
        raise HTTPException(500, f"Recipe generation error: {exc}")

    recipe_data = result.get("recipe")
    if not recipe_data:
        _log.error("Pipeline returned no recipe: %s", result.get("error"))
        raise HTTPException(500, result.get("error", "Recipe generation failed"))

    # Mark which ingredients are from fridge
    fridge_items = await db.fridge_items.find({
        "user_id": user["_id"], "is_used": False,
    }).to_list(length=500)
    fridge_names = set(i["ingredient_name"].lower() for i in fridge_items)

    for ing in recipe_data.get("ingredients", []):
        ing["from_fridge"] = ing.get("name", "").lower() in fridge_names

    # Save to MongoDB
    recipe_doc = {
        **recipe_data,
        "user_id": user["_id"],
        "allergy_check": result.get("allergy_check", {}),
        "waste_impact": result.get("waste_impact", {}),
        "pipeline_stages": result.get("pipeline_stages", {}),
        "favorites_count": 0,
        "times_cooked": 0,
        "created_at": datetime.now(timezone.utc),
    }
    insert = await db.recipes.insert_one(recipe_doc)
    recipe_doc["recipe_id"] = str(insert.inserted_id)
    recipe_doc["id"] = str(insert.inserted_id)

    return {
        "recipe": _serialize_recipe(recipe_doc),
        "allergy_check": result.get("allergy_check", {}),
        "waste_impact": result.get("waste_impact", {}),
        "pipeline_stages": result.get("pipeline_stages", {}),
    }


# ─── Trending Local Recipes (Location Based) ───

@router.get("/trending")
async def get_trending_recipes(
    location: str = Query(default="Seattle, WA"),
    user: dict = Depends(get_current_user),
):
    """Generate or fetch 4 trending local recipes based on IP-location."""
    cache_key = make_cache_key("trending_recipes", location.strip().lower())

    # Check Redis cache first, then in-memory fallback
    cached = await get_cached(cache_key) or _mem_cache.get(cache_key)
    if cached:
        return {"location": location, "recipes": cached}

    try:
        settings = get_settings()
        client = InferenceClient(api_key=settings.HUGGINGFACE_API_KEY)
        model_id = "mistralai/Mistral-7B-Instruct-v0.3"

        prompt = f"""Generate 4 trending, popular, and authentic food recipes for {location}.
Respond with ONLY valid JSON (no markdown, no code fences). The structure must be a JSON array of objects:
[
  {{
    "recipe_id": "trending-local-1",
    "title": "Authentic local dish name",
    "cuisine": "Local category",
    "difficulty": "Medium",
    "total_time_minutes": 35
  }}
]"""
        raw_text = ""
        for message in client.chat_completion(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            stream=True,
        ):
            raw_text += message.choices[0].delta.content or ""
            
        raw_text = raw_text.strip()
        recipes_data = _parse_gemini_json(raw_text)

        # Add dynamic ids
        for idx, r in enumerate(recipes_data):
            r["recipe_id"] = f"trending-{location.lower().replace(' ', '')}-{idx}"
            r["total_time_minutes"] = r.get("total_time_minutes", r.get("estimated_time_minutes", 30))

        # Cache in Redis and in-memory
        await set_cached(cache_key, recipes_data, 86400)
        _mem_cache[cache_key] = recipes_data

        return {"location": location, "recipes": recipes_data}

    except Exception as e:
        import logging
        logging.warning(f"Trending recipes error: {e}")
        return {"location": location, "recipes": _FALLBACK_TRENDING}


# ─── Ingredients Feed ───

@router.get("/ingredients-feed")
async def get_ingredients_feed(
    user: dict = Depends(get_current_user),
):
    """Generate or fetch 10 healthy ingredients with nutritional info."""
    cache_key = "ingredients_feed_daily_v3"

    # Check Redis cache first, then in-memory fallback
    cached = await get_cached(cache_key) or _mem_cache.get(cache_key)
    if cached:
        return {"ingredients": cached}

    try:
        settings = get_settings()
        client = InferenceClient(api_key=settings.HUGGINGFACE_API_KEY)
        model_id = "mistralai/Mistral-7B-Instruct-v0.3"

        prompt = """Generate 10 trending, highly-nutritious "superfood" ingredients. Provide at least 5-6 detailed health benefits for each ingredient.
Respond with ONLY valid JSON (no markdown, no code fences). The structure must be a JSON array of objects:
[
  {
    "id": "ing-1",
    "name": "Avocado",
    "calories_per_100g": 160,
    "protein_g": 2.0,
    "carbs_g": 8.5,
    "fats_g": 14.7,
    "benefits": ["Heart healthy", "Rich in fiber", "High in potassium", "Supports eye health", "Improves digestion", "Boosts brain function"]
  }
]"""
        raw_text = ""
        for message in client.chat_completion(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            stream=True,
        ):
            raw_text += message.choices[0].delta.content or ""
            
        raw_text = raw_text.strip()
        feed_data = _parse_gemini_json(raw_text)

        # Cache in Redis and in-memory
        await set_cached(cache_key, feed_data, 86400)
        _mem_cache[cache_key] = feed_data

        return {"ingredients": feed_data}

    except Exception as e:
        import logging
        logging.warning(f"Ingredients feed error: {e}")
        return {"ingredients": _FALLBACK_INGREDIENTS}


# ─── My Recipes ───

@router.get("/my")
async def get_my_recipes(user: dict = Depends(get_current_user)):
    db = get_database()
    recipes = await db.recipes.find({"user_id": user["_id"]}).sort(
        "created_at", -1
    ).to_list(length=100)

    return {
        "recipes": [_serialize_recipe(r) for r in recipes],
        "total": len(recipes),
    }


# ─── Favorites ───

@router.get("/favorites")
async def get_favorites(user: dict = Depends(get_current_user)):
    db = get_database()
    fav_ids = user.get("favorite_recipe_ids", [])
    recipes = []
    if fav_ids:
        recipes = await db.recipes.find({"_id": {"$in": fav_ids}}).to_list(length=100)

    return {
        "recipes": [_serialize_recipe(r, is_favorited=True) for r in recipes],
    }


@router.post("/{recipe_id}/favorite")
async def toggle_favorite(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    oid = ObjectId(recipe_id)
    fav_ids = user.get("favorite_recipe_ids", [])

    if oid in fav_ids:
        # Unfavorite
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$pull": {"favorite_recipe_ids": oid}},
        )
        await db.recipes.update_one({"_id": oid}, {"$inc": {"favorites_count": -1}})
        return {"favorited": False}
    else:
        # Favorite
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$addToSet": {"favorite_recipe_ids": oid}},
        )
        await db.recipes.update_one({"_id": oid}, {"$inc": {"favorites_count": 1}})
        recipe = await db.recipes.find_one({"_id": oid})
        total = recipe.get("favorites_count", 1) if recipe else 1
        return {"favorited": True, "total_favorites": total}


# ─── Recipe Detail ───

@router.get("/{recipe_id}")
async def get_recipe_detail(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    try:
        oid = ObjectId(recipe_id)
        recipe = await db.recipes.find_one({"_id": oid})
    except InvalidId:
        if recipe_id.startswith("mock-") or recipe_id.startswith("trending-"):
            return _serialize_recipe({
                "_id": recipe_id,
                "title": "Trending Recipe Detail",
                "cuisine": "Local",
                "estimated_time_minutes": 30,
                "difficulty": "Medium",
                "ingredients": [
                    {"name": "Fresh Produce", "quantity": "2", "unit": "cups"},
                    {"name": "Spices", "quantity": "1", "unit": "tbsp"}
                ],
                "preparation_steps": [
                    {"step": 1, "instruction": "Gather the ingredients.", "time_minutes": 5},
                    {"step": 2, "instruction": "Cook until done.", "time_minutes": 25}
                ]
            })
        raise HTTPException(404, "Invalid recipe ID format")
        
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    is_fav = oid in user.get("favorite_recipe_ids", [])
    return _serialize_recipe(recipe, is_favorited=is_fav)


# ─── Nutrients (on demand — calls Gemini nutrition stub) ───

@router.get("/{recipe_id}/nutrients")
async def get_recipe_nutrients(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    try:
        oid = ObjectId(recipe_id)
        recipe = await db.recipes.find_one({"_id": oid})
    except InvalidId:
        return {"calories": 400, "protein_g": 20, "carbs_g": 40, "fat_g": 15, "fiber_g": 5}
        
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    # Check cache
    cache_key = make_cache_key("nutrition", recipe_id)
    cached = await get_cached(cache_key)
    if cached:
        return cached

    # Call Gemini nutrition stub
    from app.services.gemini_nutrition_service import get_nutrition_data, NutritionRequest
    from app.database.redis import get_redis

    try:
        ingredients = [
            {"name": ing.get("name", ""), "quantity": ing.get("quantity", "")}
            for ing in recipe.get("ingredients", [])
        ]
        try:
            redis_client = get_redis()
        except Exception:
            redis_client = None
        nutrition = await get_nutrition_data(NutritionRequest(
            ingredients=ingredients,
            servings=recipe.get("servings", 2),
        ), redis_client=redis_client)
        result = nutrition.model_dump()
    except Exception:
        return {"error": "Nutrition data unavailable. Try again later."}

    # Cache for 7 days
    await set_cached(cache_key, result, NUTRITION_CACHE_TTL)
    return result


# ─── Cooking Mode ───

@router.get("/{recipe_id}/cook")
async def cooking_mode(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    try:
        oid = ObjectId(recipe_id)
        recipe = await db.recipes.find_one({"_id": oid})
    except InvalidId:
        recipe = {
            "title": "Mock Cooking Session",
            "preparation_steps": [
                {"step": 1, "instruction": "Gather the ingredients.", "time_minutes": 5},
                {"step": 2, "instruction": "Cook until done.", "time_minutes": 25}
            ]
        }
        
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    steps = []
    for step in recipe.get("preparation_steps", []):
        time_min = step.get("time_minutes", 0)
        steps.append({
            "step": step.get("step", 0),
            "instruction": step.get("instruction", ""),
            "timer_seconds": time_min * 60,
            "has_timer": time_min > 0,
        })

    total_time = sum(s.get("time_minutes", 0) for s in recipe.get("preparation_steps", []))
    query = recipe.get("youtube_search_query", "")
    youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}" if query else ""

    return {
        "title": recipe.get("title", ""),
        "image_url": recipe.get("image_url", ""),
        "steps": steps,
        "total_time_minutes": total_time,
        "youtube_embed_url": youtube_url,
    }

# ─── Done Cooking ───

@router.post("/{recipe_id}/done-cooking")
async def done_cooking(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    now = datetime.now(timezone.utc)
    
    try:
        oid = ObjectId(recipe_id)
    except InvalidId:
        return {"status": "success", "message": "Mock cooking counted"}
        
    result = await db.recipes.update_one(
        {"_id": oid},
        {"$inc": {"times_cooked": 1}, "$set": {"last_cooked_at": now}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Recipe not found")
        
    return {"status": "success", "message": "Cooking counted"}



# ─── Helper ───

def _serialize_recipe(doc: dict, is_favorited: bool = False) -> dict:
    """Convert a MongoDB recipe document to a JSON-safe dict."""
    return {
        "id": str(doc.get("_id", "")),
        "recipe_id": str(doc.get("_id", "")),
        "title": doc.get("title", ""),
        "description": doc.get("description", ""),
        "image_url": doc.get("image_url", ""),
        "status": doc.get("status"),
        "cuisine": doc.get("cuisine", ""),
        "estimated_time_minutes": doc.get("estimated_time_minutes", 0),
        "difficulty": doc.get("difficulty", "easy"),
        "servings": doc.get("servings", 2),
        "ingredients": doc.get("ingredients", []),
        "preparation_steps": doc.get("preparation_steps", []),
        "steps": doc.get("preparation_steps", []),
        "youtube_search_query": doc.get("youtube_search_query", ""),
        "tags": doc.get("tags", []),
        "similarity_score": doc.get("similarity_score"),
        "allergy_check": doc.get("allergy_check", {}),
        "waste_impact": doc.get("waste_impact", {}),
        "nutrition_data": doc.get("nutrition_data"),
        "nutrition_per_serving": (doc.get("nutrition_data") or {}).get("per_serving", doc.get("nutrition_data")),
        "is_favorited": is_favorited,
        "favorites_count": doc.get("favorites_count", 0),
        "times_cooked": doc.get("times_cooked", 0),
        "last_cooked_at": str(doc.get("last_cooked_at", "")) if doc.get("last_cooked_at") else None,
        "created_at": str(doc.get("created_at", "")) if doc.get("created_at") else None,
    }
