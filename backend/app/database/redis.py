"""
Redis Connection Manager
=========================
Async Redis connection for caching, sessions, and rate limiting.
"""

import redis.asyncio as aioredis
from app.config import get_settings

_redis: aioredis.Redis | None = None


async def connect_to_redis() -> None:
    """Initialize Redis connection."""
    global _redis
    settings = get_settings()
    _redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis_connection() -> None:
    """Gracefully close Redis connection."""
    global _redis
    if _redis:
        await _redis.close()


def get_redis() -> aioredis.Redis:
    """Get the active Redis instance."""
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call connect_to_redis() first.")
    return _redis
