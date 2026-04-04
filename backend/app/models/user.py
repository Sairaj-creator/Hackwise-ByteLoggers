"""
User Models
============
Pydantic models for user registration, login, profile, and allergy data.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ─── Request Models ───

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AllergyEntry(BaseModel):
    allergen: str
    severity: str = Field(default="moderate", pattern="^(mild|moderate|severe)$")


class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    allergies: Optional[List[AllergyEntry]] = None
    dietary_preferences: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None
    calorie_target: Optional[int] = None
    dietary_goal: Optional[str] = None


class AllergyProfileUpdateRequest(BaseModel):
    allergies: List[AllergyEntry]


# ─── Response Models ───

class WasteStats(BaseModel):
    total_saved_grams: int = 0
    total_wasted_grams: int = 0
    money_saved_inr: float = 0
    co2_prevented_kg: float = 0
    current_streak_days: int = 0
    best_streak_days: int = 0
    badges_earned: List[str] = []


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    allergies: List[AllergyEntry] = []
    dietary_preferences: List[str] = []
    cuisine_preferences: List[str] = []
    calorie_target: int = 1800
    dietary_goal: str = "balanced"
    waste_stats: WasteStats = WasteStats()
    created_at: Optional[datetime] = None


class AuthTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse


class TokenRefreshResponse(BaseModel):
    access_token: str
