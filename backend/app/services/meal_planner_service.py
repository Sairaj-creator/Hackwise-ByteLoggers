"""
Meal Planner Service
=====================
Orchestrates meal plan generation by batching calls to the recipe pipeline.
Handles allergy checking per-meal, shopping list generation, and waste optimization.
"""

from typing import List, Dict
from datetime import datetime, timedelta

from app.services.recipe_pipeline_service import generate_recipe_pipeline
from app.services.allergy_guardian import allergy_check
from app.services.recipe_model_service import (
    predict_recipe,
    ModelPredictionRequest,
    RecipeIngredient,
    RecipeStep,
)


async def build_meal_plan(
    fridge_items: List[str],
    expiring_items: List[str],
    user_allergies: list,
    preferences: dict,
    duration_days: int = 7,
    meals_per_day: int = 3,
    calorie_target: int = 1800,
    dietary_goal: str = "balanced",
) -> dict:
    """
    Generates a multi-day meal plan. Called from the Celery background task.

    Returns: dict matching MealPlanResponse schema.
    """
    meal_types = ["breakfast", "lunch", "dinner"][:meals_per_day]
    days = []

    for day_num in range(1, duration_days + 1):
        day_meals: Dict[str, dict] = {}
        day_total_cal = 0

        for meal_type in meal_types:
            # Build per-meal request
            result = await generate_recipe_pipeline(
                ingredients=fridge_items[:5],  # use a subset
                preferences={
                    "cuisine": preferences.get("cuisine", ""),
                    "dietary": dietary_goal,
                    "spice_level": "medium",
                    "max_time_minutes": "30",
                },
                user_allergies=user_allergies,
                expiring_items=expiring_items if day_num <= 3 else [],
                servings=2,
            )

            recipe = result.get("recipe")
            if recipe:
                cal_est = 400  # stub estimate
                day_meals[meal_type] = {
                    "recipe_id": "",
                    "title": recipe.get("title", "Untitled"),
                    "calories": cal_est,
                    "prep_time_minutes": recipe.get("estimated_time_minutes", 20),
                    "uses_fridge_items": [
                        ing["name"] for ing in recipe.get("ingredients", [])
                        if ing["name"].lower() in [f.lower() for f in fridge_items]
                    ],
                    "allergy_safe": result.get("allergy_check", {}).get("safe", True),
                    "ingredients": recipe.get("ingredients", []),
                    "preparation_steps": recipe.get("preparation_steps", []),
                    "tags": recipe.get("tags", []),
                }
                day_total_cal += cal_est
            else:
                day_meals[meal_type] = {
                    "recipe_id": "",
                    "title": f"Placeholder {meal_type.title()}",
                    "calories": 350,
                    "prep_time_minutes": 15,
                    "uses_fridge_items": [],
                    "allergy_safe": True,
                    "ingredients": [],
                    "preparation_steps": [],
                    "tags": [],
                }
                day_total_cal += 350

        snack_gap = max(0, calorie_target - day_total_cal)
        snack_suggestion = (
            f"Light snack (~{snack_gap} cal) to reach daily target"
            if snack_gap > 0
            else "You're on track!"
        )

        days.append({
            "day": day_num,
            "date": (datetime.utcnow() + timedelta(days=day_num - 1)).strftime("%Y-%m-%d"),
            "meals": day_meals,
            "snack_suggestion": snack_suggestion,
            "total_calories": day_total_cal,
        })

    # ─── Shopping list: plan ingredients minus fridge items ───
    fridge_set = set(f.lower() for f in fridge_items)
    shopping_dict: Dict[str, str] = {}

    for day in days:
        for meal_type, meal in day["meals"].items():
            for ing in meal.get("ingredients", []):
                name = ing.get("name", "") if isinstance(ing, dict) else getattr(ing, "name", "")
                qty = ing.get("quantity", "") if isinstance(ing, dict) else getattr(ing, "quantity", "")
                if name.lower() not in fridge_set and name not in shopping_dict:
                    shopping_dict[name] = qty

    shopping_list = [{"name": k, "quantity": v} for k, v in shopping_dict.items()]

    # ─── Waste optimization stats ───
    expiring_used = [
        item for item in expiring_items
        if any(
            item.lower() in str(day["meals"]).lower()
            for day in days
        )
    ]

    waste_optimization = {
        "expiring_items_used": expiring_used,
        "waste_prevented_grams": len(expiring_used) * 200,
        "fridge_utilization_percent": round(
            len([
                fi for fi in fridge_items
                if fi.lower() in str(days).lower()
            ]) / max(len(fridge_items), 1) * 100
        ),
    }

    return {
        "days": days,
        "shopping_list": shopping_list,
        "waste_optimization": waste_optimization,
    }
