"""
MongoDB Connection Manager
===========================
Async Motor client with index creation on startup.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> None:
    """Initialize MongoDB connection and create indexes."""
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _db = _client.get_default_database()  # uses db name from URI

    # If URI has no db name, fall back
    if _db is None:
        _db = _client["recipe_db"]

    await _create_indexes()


async def close_mongo_connection() -> None:
    """Gracefully close MongoDB connection."""
    global _client
    if _client:
        _client.close()


def get_database() -> AsyncIOMotorDatabase:
    """Get the active database instance."""
    if _db is None:
        raise RuntimeError("MongoDB not initialized. Call connect_to_mongo() first.")
    return _db


async def _create_indexes() -> None:
    """Create performance-critical indexes as specified in the schema."""
    db = get_database()
    import logging

    try:
        # Users
        await db.users.create_index("email", unique=True)

        # Fridge items
        await db.fridge_items.create_index([("user_id", 1), ("expiry_status", 1)])
        await db.fridge_items.create_index([("user_id", 1), ("is_used", 1)])
        await db.fridge_items.create_index("expiry_date")

        # Recipes
        await db.recipes.create_index("tags")
        await db.recipes.create_index("cuisine")
        await db.recipes.create_index("favorites_count", -1)
        await db.recipes.create_index("ingredients.name")

        # Meal plans
        await db.meal_plans.create_index([("user_id", 1), ("status", 1)])

        # Waste logs
        await db.waste_logs.create_index([("user_id", 1), ("logged_at", -1)])
        await db.waste_logs.create_index([("user_id", 1), ("action", 1)])

        # Waste suggestions
        await db.waste_suggestions.create_index("user_id", unique=True)

        # Social posts
        await db.social_posts.create_index([("created_at", -1)])
        await db.social_posts.create_index([("user_id", 1), ("created_at", -1)])
    except Exception as e:
        logging.getLogger("uvicorn.error").warning(f"Could not create MongoDB indexes (is MongoDB running?): {e}")
