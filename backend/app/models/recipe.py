"""
Recipe Models
==============
Pydantic models for recipe generation, detail, and nutrition.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Sub-models ───

class RecipeIngredient(BaseModel):
    name: str
    quantity: str
    from_fridge: bool = False


class RecipeStep(BaseModel):
    step: int
    instruction: str
    time_minutes: int


class AllergyCheckResult(BaseModel):
    safe: bool = True
    warnings: List[Dict] = []
    substitutions: List[Dict] = []
    checked_against: List[str] = []
    auto_regenerated: bool = False


class WasteImpact(BaseModel):
    ingredients_saved_from_expiry: List[str] = []
    waste_prevented_grams: int = 0


class NutritionData(BaseModel):
    total_calories: int = 0
    per_serving: Dict[str, float] = {}
    health_benefits: List[str] = []
    source: str = "stub"


# ─── Request Models ───

class RecipeGenerateRequest(BaseModel):
    ingredients: List[str]
    preferences: Dict[str, Any] = {}
    prioritize_expiring: bool = True
    servings: int = 2


# ─── Response Models ───

class RecipeResponse(BaseModel):
    id: str = ""
    recipe_id: str = ""
    title: str
    cuisine: str = ""
    estimated_time_minutes: int = 0
    difficulty: str = "easy"
    servings: int = 2
    ingredients: List[RecipeIngredient] = []
    preparation_steps: List[RecipeStep] = []
    youtube_search_query: str = ""
    tags: List[str] = []
    allergy_check: AllergyCheckResult = AllergyCheckResult()
    waste_impact: WasteImpact = WasteImpact()
    nutrition_data: Optional[NutritionData] = None
    is_favorited: bool = False
    favorites_count: int = 0
    times_cooked: int = 0
    created_at: Optional[datetime] = None


class RecipeListResponse(BaseModel):
    recipes: List[RecipeResponse]
    total: int = 0


class CookingModeResponse(BaseModel):
    steps: List[Dict]
    total_time_minutes: int
    youtube_embed_url: str = ""
