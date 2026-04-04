"""
Cache Service
==============
Centralized Redis caching wrapper for all cache operations.
Provides get/set/invalidate with typed JSON serialization.
"""

import json
import hashlib
from typing import Any, Optional
from app.database.redis import get_redis


async def get_cached(key: str) -> Optional[Any]:
    """Get a cached value by key, returns deserialized JSON or None."""
    try:
        redis = get_redis()
        value = await redis.get(key)
        if value:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
    except Exception:
        # Redis unavailable — skip cache gracefully
        pass
    return None


async def set_cached(key: str, value: Any, ttl_seconds: int = 86400) -> None:
    """Set a cached value with a TTL (default 24 hours)."""
    try:
        redis = get_redis()
        serialized = json.dumps(value, default=str)
        await redis.setex(key, ttl_seconds, serialized)
    except Exception:
        # Redis unavailable — skip cache gracefully
        pass


async def invalidate(key: str) -> None:
    """Delete a cached key."""
    try:
        redis = get_redis()
        await redis.delete(key)
    except Exception:
        pass


async def invalidate_pattern(pattern: str) -> None:
    """Delete all keys matching a glob pattern."""
    try:
        redis = get_redis()
        cursor = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
    except Exception:
        pass


def make_cache_key(prefix: str, *args: str) -> str:
    """
    Generate a deterministic cache key.
    Example: make_cache_key("recipe", "paneer", "onion", "North Indian")
    → "recipe:a3f2b8c1..."
    """
    raw = "|".join(sorted(str(a).lower().strip() for a in args))
    h = hashlib.md5(raw.encode()).hexdigest()
    return f"{prefix}:{h}"


# ─── Cache TTL Constants ───
RECIPE_CACHE_TTL = 86400        # 24 hours
NUTRITION_CACHE_TTL = 604800    # 7 days
TRENDS_CACHE_TTL = 300          # 5 minutes
SESSION_CACHE_TTL = 900         # 15 minutes
MEAL_PLAN_STATUS_TTL = 3600     # 1 hour
