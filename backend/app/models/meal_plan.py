"""
Meal Plan Models
=================
Pydantic models for meal plan generation, status polling, and shopping lists.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ─── Request Models ───

class MealPlanGenerateRequest(BaseModel):
    duration_days: int = Field(default=7, ge=1, le=7)
    meals_per_day: int = Field(default=3, ge=1, le=5)
    dietary_goal: str = "balanced"  # weight_loss | muscle_gain | balanced | diabetic_friendly
    calorie_target_per_day: int = 1800
    use_fridge_ingredients: bool = True
    budget_level: str = "medium"  # low | medium | high
    cuisine_preferences: List[str] = []
    exclude_repeated_recipes: bool = True


class MealSwapRequest(BaseModel):
    day: int
    meal: str  # breakfast | lunch | dinner
    reason: str = "not_in_mood"


# ─── Response Models ───

class MealEntry(BaseModel):
    recipe_id: str = ""
    title: str
    calories: int = 0
    prep_time_minutes: int = 0
    uses_fridge_items: List[str] = []
    allergy_safe: bool = True
    allergy_warnings: List[Dict] = []
    substitutions: List[Dict] = []
    ingredients: List[Dict] = []
    preparation_steps: List[Dict] = []
    tags: List[str] = []


class DayPlan(BaseModel):
    day: int
    date: Optional[str] = None
    meals: Dict[str, MealEntry]
    snack_suggestion: str = ""
    total_calories: int = 0
    total_protein_g: float = 0


class ShoppingListItem(BaseModel):
    name: str
    quantity: str
    estimated_cost_inr: float = 0
    category: str = "general"


class WasteOptimization(BaseModel):
    expiring_items_used: List[str] = []
    waste_prevented_grams: int = 0
    fridge_utilization_percent: float = 0


class MealPlanResponse(BaseModel):
    plan_id: str
    status: str  # generating | ready | failed
    progress_percent: int = 0
    message: str = ""
    duration_days: int = 0
    daily_calorie_target: int = 0
    days: List[DayPlan] = []
    shopping_list: List[ShoppingListItem] = []
    waste_optimization: WasteOptimization = WasteOptimization()
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
