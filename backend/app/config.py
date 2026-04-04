"""
Application Configuration
=========================
Type-safe environment variable parsing via Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ─── Database ───
    MONGODB_URI: str = "mongodb://localhost:27017/recipe_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672"

    # ─── JWT ───
    JWT_SECRET: str = "this-is-a-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── Rate Limiting ───
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_RECIPE_GENERATE: str = "20/hour"
    RATE_LIMIT_IMAGE_SCAN: str = "10/hour"
    RATE_LIMIT_MEAL_PLAN: str = "3/hour"

    # ─── AI Services ───
    CNN_SERVICE_URL: str = "http://localhost:8001"
    GEMINI_API_KEY: str = "placeholder_until_teammate_provides"

    # ─── External ───
    CLOUDINARY_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
