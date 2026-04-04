"""
Fridge Models
=============
Pydantic models for fridge ingredient management and scanning.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Request Models ───

class FridgeIngredientInput(BaseModel):
    name: str
    category: Optional[str] = "general"
    quantity: Optional[float] = 1
    unit: Optional[str] = "pieces"
    expiry_date: Optional[str] = None  # ISO date string, e.g. "2026-04-10"


class FridgeManualAddRequest(BaseModel):
    ingredients: List[FridgeIngredientInput]


class FridgeCartImportRequest(BaseModel):
    cart_items: List[str]
    source: str = "manual"


class FridgeItemUpdateRequest(BaseModel):
    quantity: Optional[float] = None
    expiry_date: Optional[str] = None


# ─── Response Models ───

class FridgeItemResponse(BaseModel):
    item_id: str
    name: str
    category: str = "general"
    quantity: float = 1
    unit: str = "pieces"
    added_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    days_until_expiry: Optional[int] = None
    expiry_status: str = "fresh"  # fresh | warning | critical | expired


class FridgeResponse(BaseModel):
    ingredients: List[FridgeItemResponse]
    total: int
    expiring_soon_count: int = 0


class FridgeAddResponse(BaseModel):
    added: int
    fridge_total: int


class FridgeScanResponse(BaseModel):
    detected_ingredients: List[dict]
    processing_time_ms: int = 0
    error: Optional[str] = None
