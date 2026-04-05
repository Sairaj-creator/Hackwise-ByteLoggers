"""
Recipes Router
===============
Endpoints: generate, list my recipes, detail, nutrients, cooking mode, favorites.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone
from bson import ObjectId
import json
from google import genai

from app.config import get_settings

from app.dependencies import get_current_user
from app.database.mongodb import get_database
from app.services.recipe_pipeline_service import generate_recipe_pipeline
from app.services.cache_service import get_cached, set_cached, make_cache_key, NUTRITION_CACHE_TTL
from app.models.recipe import RecipeGenerateRequest

router = APIRouter(prefix="/api/v1/recipes", tags=["Recipes"])


# ─── Generate Recipe ───

@router.post("/generate")
async def generate_recipe(
    request: RecipeGenerateRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()

    # Find expiring items if requested
    expiring_items = []
    if request.prioritize_expiring:
        items = await db.fridge_items.find({
            "user_id": user["_id"],
            "is_used": False,
            "expiry_status": {"$in": ["warning", "critical"]},
        }).to_list(length=50)
        expiring_items = [i["ingredient_name"] for i in items]

    # Generate via the 2-stage pipeline
    result = await generate_recipe_pipeline(
        ingredients=request.ingredients,
        preferences=request.preferences,
        user_allergies=user.get("allergies", []),
        expiring_items=expiring_items,
        servings=request.servings,
    )

    recipe_data = result.get("recipe")
    if not recipe_data:
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
        "favorites_count": 0,
        "times_cooked": 0,
        "created_at": datetime.now(timezone.utc),
    }
    insert = await db.recipes.insert_one(recipe_doc)
    recipe_doc["recipe_id"] = str(insert.inserted_id)
    recipe_doc["id"] = str(insert.inserted_id)

    return {
        "recipe": _serialize_recipe(recipe_doc),
    }


# ─── Trending Local Recipes (Location Based) ───

@router.get("/trending")
async def get_trending_recipes(
    location: str = Query(default="Seattle, WA"),
    user: dict = Depends(get_current_user),
):
    """Generate or fetch 4 trending local recipes based on IP-location."""
    cache_key = make_cache_key("trending_recipes", location.strip().lower())
    cached = await get_cached(cache_key)
    if cached:
        return {"location": location, "recipes": cached}

    try:
        settings = get_settings()
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines)
            
        recipes_data = json.loads(raw_text)
        
        # Add dynamic ids
        for idx, r in enumerate(recipes_data):
            r["recipe_id"] = f"trending-{location.lower().replace(' ', '')}-{idx}"
            r["total_time_minutes"] = r.get("total_time_minutes", r.get("estimated_time_minutes", 30))

        # Cache for 24 hours (86400 seconds)
        await set_cached(cache_key, recipes_data, 86400)

        return {"location": location, "recipes": recipes_data}

    except Exception as e:
        import logging
        logging.warning(f"Trending recipes fallback: {e}")
        # Fallback payload
        fallback = [
             {"recipe_id": "mock-1", "title": "Local Artisan Bread", "cuisine": "Bakery", "difficulty": "Hard", "total_time_minutes": 120},
             {"recipe_id": "mock-2", "title": "Farmhouse Salad", "cuisine": "Healthy", "difficulty": "Easy", "total_time_minutes": 15},
             {"recipe_id": "mock-3", "title": "Regional Stew", "cuisine": "Comfort", "difficulty": "Medium", "total_time_minutes": 60},
             {"recipe_id": "mock-4", "title": "Heritage Pasta", "cuisine": "Italian Fusion", "difficulty": "Medium", "total_time_minutes": 45},
        ]
        return {"location": location, "recipes": fallback}


# ─── Ingredients Feed ───

@router.get("/ingredients-feed")
async def get_ingredients_feed(
    user: dict = Depends(get_current_user),
):
    """Generate or fetch 10 healthy ingredients with nutritional info."""
    cache_key = "ingredients_feed_daily_v3"
    cached = await get_cached(cache_key)
    if cached:
        return {"ingredients": cached}

    try:
        settings = get_settings()
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

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
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines)
            
        feed_data = json.loads(raw_text)
        
        # Cache for 24 hours
        await set_cached(cache_key, feed_data, 86400)

        return {"ingredients": feed_data}

    except Exception as e:
        import logging
        logging.warning(f"Ingredients feed fallback: {e}")
        # Fallback payload
        fallback = [
             {"id": "mock-1", "name": "Quinoa", "calories_per_100g": 120, "protein_g": 4.1, "carbs_g": 21.3, "fats_g": 1.9, "benefits": ["High protein", "Gluten-free", "Rich in iron"]},
             {"id": "mock-2", "name": "Chia Seeds", "calories_per_100g": 486, "protein_g": 16.5, "carbs_g": 42.1, "fats_g": 30.7, "benefits": ["Omega-3 rich", "High fiber", "Antioxidants"]},
        ]
        return {"ingredients": fallback}


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
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    is_fav = ObjectId(recipe_id) in user.get("favorite_recipe_ids", [])
    return _serialize_recipe(recipe, is_favorited=is_fav)


# ─── Nutrients (on demand — calls Gemini nutrition stub) ───

@router.get("/{recipe_id}/nutrients")
async def get_recipe_nutrients(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if not recipe:
        raise HTTPException(404, "Recipe not found")

    # Check cache
    cache_key = make_cache_key("nutrition", recipe_id)
    cached = await get_cached(cache_key)
    if cached:
        return cached

    # Call Gemini nutrition stub
    from app.services.gemini_nutrition_service import get_nutrition_data, NutritionRequest

    try:
        ingredients = [
            {"name": ing.get("name", ""), "quantity": ing.get("quantity", "")}
            for ing in recipe.get("ingredients", [])
        ]
        nutrition = await get_nutrition_data(NutritionRequest(
            ingredients=ingredients,
            servings=recipe.get("servings", 2),
        ))
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
    recipe = await db.recipes.find_one({"_id": ObjectId(recipe_id)})
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
        "steps": steps,
        "total_time_minutes": total_time,
        "youtube_embed_url": youtube_url,
    }

# ─── Done Cooking ───

@router.post("/{recipe_id}/done-cooking")
async def done_cooking(recipe_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    
    result = await db.recipes.update_one(
        {"_id": ObjectId(recipe_id)},
        {"$inc": {"times_cooked": 1}}
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
        "cuisine": doc.get("cuisine", ""),
        "estimated_time_minutes": doc.get("estimated_time_minutes", 0),
        "difficulty": doc.get("difficulty", "easy"),
        "servings": doc.get("servings", 2),
        "ingredients": doc.get("ingredients", []),
        "preparation_steps": doc.get("preparation_steps", []),
        "steps": doc.get("preparation_steps", []),
        "youtube_search_query": doc.get("youtube_search_query", ""),
        "tags": doc.get("tags", []),
        "allergy_check": doc.get("allergy_check", {}),
        "waste_impact": doc.get("waste_impact", {}),
        "nutrition_data": doc.get("nutrition_data"),
        "nutrition_per_serving": doc.get("nutrition_data"),
        "is_favorited": is_favorited,
        "favorites_count": doc.get("favorites_count", 0),
        "times_cooked": doc.get("times_cooked", 0),
        "created_at": str(doc.get("created_at", "")) if doc.get("created_at") else None,
    }
