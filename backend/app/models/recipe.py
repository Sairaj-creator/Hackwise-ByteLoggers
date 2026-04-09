"""
Recipe Models
==============
Pydantic models for recipe generation, detail, and nutrition.
"""

from pydantic import AliasChoices, BaseModel, Field, field_validator
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
    warnings: List[Dict] = Field(default_factory=list)
    substitutions: List[Dict] = Field(default_factory=list)
    checked_against: List[str] = Field(default_factory=list)
    auto_regenerated: bool = False


class WasteImpact(BaseModel):
    ingredients_saved_from_expiry: List[str] = Field(default_factory=list)
    waste_prevented_grams: int = 0


class NutritionData(BaseModel):
    total_calories: int = 0
    per_serving: Dict[str, float] = Field(default_factory=dict)
    health_benefits: List[str] = Field(default_factory=list)
    source: str = "mock"


# ─── Request Models ───

class RecipeGenerateRequest(BaseModel):
    ingredients: List[str] = Field(default_factory=list)
    raw_text_input: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    dietary_preferences: List[str] = Field(default_factory=list)
    prioritize_expiring: bool = True
    servings: int = Field(default=2, validation_alias=AliasChoices("servings", "number_of_people"))

    @field_validator("dietary_preferences", mode="before")
    @classmethod
    def _coerce_dietary_preferences(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return [str(item).strip() for item in value if str(item).strip()]


# ─── Response Models ───

class RecipeResponse(BaseModel):
    id: str = ""
    recipe_id: str = ""
    title: str
    cuisine: str = ""
    estimated_time_minutes: int = 0
    difficulty: str = "easy"
    servings: int = 2
    ingredients: List[RecipeIngredient] = Field(default_factory=list)
    preparation_steps: List[RecipeStep] = Field(default_factory=list)
    youtube_search_query: str = ""
    tags: List[str] = Field(default_factory=list)
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
