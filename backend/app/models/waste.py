"""
Waste Tracker Models
======================
Pydantic models for food waste tracking, dashboard, achievements, and suggestions.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# ─── Request Models ───

class WasteLogRequest(BaseModel):
    ingredient_id: str
    action: str  # used_in_recipe | wasted | donated | composted
    recipe_id: Optional[str] = None
    quantity_used_grams: float = 0


# ─── Response / Sub-Models ───

class ExpiringItemResponse(BaseModel):
    id: str
    name: str
    quantity: str = ""
    expiry_date: Optional[str] = None
    days_remaining: int = 0
    status: str = "fresh"  # fresh | warning | critical | expired
    suggested_recipes: List[Dict] = []


class AchievementBadge(BaseModel):
    badge: str
    title: str
    description: str
    earned: bool = False
    earned_date: Optional[str] = None
    progress: Optional[str] = None


class WasteSummary(BaseModel):
    total_items_in_fridge: int = 0
    expiring_within_24h: int = 0
    expiring_within_3_days: int = 0
    expired: int = 0
    waste_prevented_this_week_grams: float = 0
    waste_prevented_this_month_grams: float = 0
    money_saved_inr: float = 0
    co2_prevented_kg: float = 0
    waste_reduction_streak_days: int = 0


class WasteDashboardResponse(BaseModel):
    summary: WasteSummary
    expiring_items: List[ExpiringItemResponse] = []
    achievements: List[AchievementBadge] = []


class WasteLogResponse(BaseModel):
    logged: bool = True
    waste_prevented_grams: float = 0
    streak_broken: bool = False
    new_streak_days: int = 0
    new_badges_earned: List[str] = []
    message: str = ""


class WasteHistoryResponse(BaseModel):
    period: str
    total_items_tracked: int = 0
    used_before_expiry: int = 0
    wasted: int = 0
    donated: int = 0
    composted: int = 0
    waste_rate_percent: float = 0
    money_saved_inr: float = 0
    co2_prevented_kg: float = 0
    weekly_breakdown: List[Dict] = []


class UrgentCookSuggestion(BaseModel):
    ingredients: List[str]
    recipe: Dict
    reason: str


class FreezeSuggestion(BaseModel):
    ingredient: str
    current_expiry: str = ""
    message: str
    freeze_instructions: str = ""


class UseThisWeekSuggestion(BaseModel):
    ingredient: str
    days_remaining: int = 0
    quantity: str = ""
    recipe_ideas: List[str] = []


class SmartSuggestionsResponse(BaseModel):
    urgent_cook_now: List[UrgentCookSuggestion] = []
    freeze_suggestions: List[FreezeSuggestion] = []
    use_this_week: List[UseThisWeekSuggestion] = []
