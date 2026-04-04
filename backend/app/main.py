"""
FastAPI Main Application
=========================
Entry point for the AI Recipe Generator backend.
Sets up CORS, rate limiting, routing, and database lifecycle events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.database.redis import connect_to_redis, close_redis_connection

# ─── Routers ───
from app.routers import auth, fridge, recipes, meal_planner, waste_tracker, social, websocket


# ─── Lifespan: startup / shutdown ───

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: connect to MongoDB and Redis. Shutdown: close connections."""
    await connect_to_mongo()
    await connect_to_redis()
    yield
    await close_mongo_connection()
    await close_redis_connection()


# ─── App Initialization ───

app = FastAPI(
    title="AI Recipe Generator API",
    description="Backend API for the AI-Based Recipe Generator with Allergy Guardian, Smart Meal Planner, and Food Waste Tracker.",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── Rate Limiting ───

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ───

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include Routers ───

app.include_router(auth.router)
app.include_router(fridge.router)
app.include_router(recipes.router)
app.include_router(meal_planner.router)
app.include_router(waste_tracker.router)
app.include_router(social.router)
app.include_router(websocket.router)


# ─── Health Check ───

@app.get("/api/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    from datetime import datetime, timezone
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


# ─── Root ───

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Recipe Generator API",
        "docs": "/docs",
        "health": "/api/health",
    }
