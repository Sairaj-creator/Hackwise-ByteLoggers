"""
Waste Tracker Service
======================
Handles food waste tracking, expiry calculations, streak management,
badge awarding, and smart suggestion generation.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from bson import ObjectId


# ─── Default expiry days for common ingredients ───
DEFAULT_EXPIRY_DAYS = {
    "milk": 5, "yogurt": 7, "curd": 7, "paneer": 5, "cheese": 14,
    "chicken": 2, "fish": 1, "mutton": 2, "eggs": 21,
    "bread": 5, "rice": 180, "dal": 90, "atta": 60,
    "tomato": 7, "onion": 30, "potato": 21, "banana": 5,
    "apple": 14, "mango": 5, "leafy_greens": 3, "spinach": 3,
    "bell_pepper": 7, "bell pepper": 7, "carrot": 14, "cucumber": 5,
    "butter": 30, "ghee": 90, "oil": 180,
    "ginger": 21, "garlic": 30, "lemon": 14,
}

AVERAGE_PRICE_PER_KG_INR = {
    "paneer": 400, "chicken": 250, "fish": 350, "milk": 60,
    "tomato": 40, "onion": 35, "potato": 30, "banana": 50,
    "apple": 150, "mango": 100, "bell_pepper": 80, "bell pepper": 80,
    "yogurt": 80, "bread": 50, "eggs": 7,
}

CO2_FACTOR_PER_KG = 2.5  # kg CO2 per kg of food wasted


def get_default_expiry(ingredient_name: str) -> int:
    """Return the default expiry days for a given ingredient."""
    return DEFAULT_EXPIRY_DAYS.get(ingredient_name.lower().strip(), 7)


def calculate_expiry_status(expiry_date: Optional[datetime]) -> str:
    """Classify item by its proximity to expiry."""
    if not expiry_date:
        return "fresh"
    now = datetime.now(timezone.utc)
    # Normalize expiry_date to timezone-aware if it isn't
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    delta = (expiry_date - now).days
    if delta < 0:
        return "expired"
    elif delta <= 1:
        return "critical"
    elif delta <= 3:
        return "warning"
    return "fresh"


def calculate_days_until_expiry(expiry_date: Optional[datetime]) -> Optional[int]:
    """Return the number of days until expiry, or None."""
    if not expiry_date:
        return None
    now = datetime.now(timezone.utc)
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    return max(0, (expiry_date - now).days)


def estimate_money_saved(grams: float, ingredient_name: str = "") -> float:
    """Estimate INR saved based on weight and ingredient type."""
    price_per_kg = AVERAGE_PRICE_PER_KG_INR.get(ingredient_name.lower().strip(), 150)
    return round(grams / 1000 * price_per_kg, 2)


def estimate_co2_prevented(grams: float) -> float:
    """Estimate kg CO2 prevented."""
    return round(grams / 1000 * CO2_FACTOR_PER_KG, 2)


# ─── Badge System ───

BADGE_RULES = {
    "waste_warrior": {
        "title": "Waste Warrior",
        "description": "Prevented 1kg of food waste",
        "condition": lambda s: s.get("total_saved_grams", 0) >= 1000,
    },
    "super_saver": {
        "title": "Super Saver",
        "description": "Prevented 5kg of food waste",
        "condition": lambda s: s.get("total_saved_grams", 0) >= 5000,
    },
    "streak_7": {
        "title": "Week Streak",
        "description": "No expired items for 7 days",
        "condition": lambda s: s.get("current_streak_days", 0) >= 7,
    },
    "streak_30": {
        "title": "Month Master",
        "description": "No expired items for 30 days",
        "condition": lambda s: s.get("current_streak_days", 0) >= 30,
    },
    "eco_hero": {
        "title": "Eco Hero",
        "description": "Prevented 5kg CO₂ emissions",
        "condition": lambda s: (s.get("total_saved_grams", 0) / 1000 * CO2_FACTOR_PER_KG) >= 5.0,
    },
    "zero_waste_week": {
        "title": "Zero Waste Week",
        "description": "No wasted items for 7 consecutive days",
        "condition": lambda s: (
            s.get("current_streak_days", 0) >= 7 and s.get("total_wasted_grams", 0) == 0
        ),
    },
}


def check_new_badges(waste_stats: dict) -> List[str]:
    """Check which new badges the user has earned."""
    current_badges = set(waste_stats.get("badges_earned", []))
    new_badges = []

    for badge_id, rule in BADGE_RULES.items():
        if badge_id not in current_badges and rule["condition"](waste_stats):
            new_badges.append(badge_id)

    return new_badges


def get_all_achievements(waste_stats: dict) -> List[dict]:
    """Return the full achievement list with progress."""
    earned = set(waste_stats.get("badges_earned", []))
    achievements = []

    progress_map = {
        "waste_warrior": f"{waste_stats.get('total_saved_grams', 0)}/1000g",
        "super_saver": f"{waste_stats.get('total_saved_grams', 0)}/5000g",
        "streak_7": f"{waste_stats.get('current_streak_days', 0)}/7 days",
        "streak_30": f"{waste_stats.get('current_streak_days', 0)}/30 days",
        "eco_hero": f"{estimate_co2_prevented(waste_stats.get('total_saved_grams', 0))}/5.0 kg",
    }

    for badge_id, rule in BADGE_RULES.items():
        achievements.append({
            "badge": badge_id,
            "title": rule["title"],
            "description": rule["description"],
            "earned": badge_id in earned,
            "progress": None if badge_id in earned else progress_map.get(badge_id),
        })

    return achievements


# ─── Freeze-suggestion logic ───

FREEZABLE_ITEMS = {
    "chicken": "Portion into 250g bags, remove air, label with date. Extends shelf life by 3 months.",
    "fish": "Wrap tightly in cling film, then foil. Freeze for up to 2 months.",
    "paneer": "Cut into cubes, freeze in a single layer on a tray, then bag. Lasts 3 months.",
    "bread": "Slice before freezing. Remove slices as needed. Lasts 3 months.",
    "milk": "Pour into ice cube trays for cooking use. Lasts 3 months.",
    "butter": "Wrap tightly and freeze. Lasts 6 months.",
    "mutton": "Portion and vacuum seal if possible. Freeze for up to 4 months.",
    "mango": "Peel, cube, freeze in single layer, then bag. Lasts 6 months.",
    "banana": "Peel and freeze for smoothies. Lasts 3 months.",
    "bell pepper": "Slice, spread on tray, freeze, then bag. Lasts 6 months.",
}


def get_freeze_suggestion(ingredient_name: str, expiry_date: Optional[datetime]) -> Optional[dict]:
    """Return freeze instructions if the item is freezable and nearing expiry."""
    name_lower = ingredient_name.lower().strip()
    instructions = FREEZABLE_ITEMS.get(name_lower)
    if not instructions:
        return None

    days_left = calculate_days_until_expiry(expiry_date)
    if days_left is not None and days_left <= 3:
        return {
            "ingredient": ingredient_name,
            "current_expiry": expiry_date.strftime("%Y-%m-%d") if expiry_date else "",
            "message": f"{ingredient_name} expires in {days_left} day(s). Freeze now to extend shelf life.",
            "freeze_instructions": instructions,
        }
    return None
