"""
Meal Planner Router
====================
Endpoints: generate plan (async), get plan, swap meal, shopping list.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from bson import ObjectId
import uuid

from app.dependencies import get_current_user
from app.database.mongodb import get_database
from app.models.meal_plan import (
    MealPlanGenerateRequest,
    MealSwapRequest,
    MealPlanResponse,
)

router = APIRouter(prefix="/api/v1/meal-planner", tags=["Meal Planner"])


# ─── Generate Meal Plan (async via Celery) ───

@router.post("/generate")
async def generate_meal_plan(
    request: MealPlanGenerateRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    plan_id = str(ObjectId())

    # Create plan stub in MongoDB (status: generating)
    plan_doc = {
        "_id": ObjectId(plan_id),
        "user_id": user["_id"],
        "duration_days": request.duration_days,
        "meals_per_day": request.meals_per_day,
        "calorie_target": request.calorie_target_per_day,
        "dietary_goal": request.dietary_goal,
        "cuisine_preferences": request.cuisine_preferences,
        "status": "generating",
        "progress_percent": 0,
        "days": [],
        "shopping_list": [],
        "waste_optimization": {},
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    await db.meal_plans.insert_one(plan_doc)

    # Dispatch Celery task
    try:
        from app.tasks.meal_plan_generator import generate_meal_plan_task
        generate_meal_plan_task.delay(
            str(user["_id"]),
            plan_id,
            request.model_dump(),
        )
    except Exception:
        # Celery not available — generate synchronously as fallback
        from app.services.meal_planner_service import build_meal_plan

        fridge_items_cursor = await db.fridge_items.find(
            {"user_id": user["_id"], "is_used": False}
        ).to_list(length=500)
        fridge_names = [i["ingredient_name"] for i in fridge_items_cursor]
        expiring = [
            i["ingredient_name"] for i in fridge_items_cursor
            if i.get("expiry_status") in ("warning", "critical")
        ]

        plan_result = await build_meal_plan(
            fridge_items=fridge_names,
            expiring_items=expiring,
            user_allergies=user.get("allergies", []),
            preferences={"cuisine": ",".join(request.cuisine_preferences)},
            duration_days=request.duration_days,
            meals_per_day=request.meals_per_day,
            calorie_target=request.calorie_target_per_day,
            dietary_goal=request.dietary_goal,
        )

        await db.meal_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {"$set": {
                "status": "ready",
                "progress_percent": 100,
                "days": plan_result["days"],
                "shopping_list": plan_result["shopping_list"],
                "waste_optimization": plan_result["waste_optimization"],
                "completed_at": datetime.now(timezone.utc),
            }},
        )

    return {
        "plan_id": plan_id,
        "status": "generating",
        "message": "Your meal plan is being created. We'll notify you when it's ready.",
    }


# ─── Get Meal Plan ───

@router.get("/{plan_id}")
async def get_meal_plan(plan_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    plan = await db.meal_plans.find_one(
        {"_id": ObjectId(plan_id), "user_id": user["_id"]}
    )
    if not plan:
        raise HTTPException(404, "Meal plan not found")

    return {
        "plan_id": str(plan["_id"]),
        "status": plan.get("status", "generating"),
        "progress_percent": plan.get("progress_percent", 0),
        "duration_days": plan.get("duration_days", 0),
        "daily_calorie_target": plan.get("calorie_target", 0),
        "days": plan.get("days", []),
        "shopping_list": plan.get("shopping_list", []),
        "waste_optimization": plan.get("waste_optimization", {}),
        "created_at": str(plan.get("created_at", "")),
        "completed_at": str(plan.get("completed_at", "")) if plan.get("completed_at") else None,
    }


# ─── Swap Meal ───

@router.put("/{plan_id}/swap")
async def swap_meal(
    plan_id: str,
    request: MealSwapRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    plan = await db.meal_plans.find_one(
        {"_id": ObjectId(plan_id), "user_id": user["_id"]}
    )
    if not plan:
        raise HTTPException(404, "Meal plan not found")
    if plan.get("status") != "ready":
        raise HTTPException(400, "Plan is not ready yet")

    from app.services.recipe_pipeline_service import generate_recipe_pipeline

    fridge_items = await db.fridge_items.find(
        {"user_id": user["_id"], "is_used": False}
    ).to_list(length=500)
    fridge_names = [i["ingredient_name"] for i in fridge_items]

    result = await generate_recipe_pipeline(
        ingredients=fridge_names[:5],
        preferences={"dietary": plan.get("dietary_goal", "balanced")},
        user_allergies=user.get("allergies", []),
        servings=2,
    )

    recipe = result.get("recipe", {})
    new_meal = {
        "recipe_id": "",
        "title": recipe.get("title", "New Recipe"),
        "calories": 400,
        "prep_time_minutes": recipe.get("estimated_time_minutes", 20),
        "uses_fridge_items": [],
        "allergy_safe": result.get("allergy_check", {}).get("safe", True),
    }

    # Update the specific day/meal in the plan
    days = plan.get("days", [])
    for day in days:
        if day.get("day") == request.day:
            day["meals"][request.meal] = new_meal
            break

    await db.meal_plans.update_one(
        {"_id": ObjectId(plan_id)},
        {"$set": {"days": days}},
    )

    return {"new_meal": new_meal}


# ─── Shopping List ───

@router.get("/{plan_id}/shopping-list")
async def get_shopping_list(plan_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    plan = await db.meal_plans.find_one(
        {"_id": ObjectId(plan_id), "user_id": user["_id"]}
    )
    if not plan:
        raise HTTPException(404, "Meal plan not found")

    shopping = plan.get("shopping_list", [])

    # Categorize items
    categories: dict = {}
    for item in shopping:
        cat = item.get("category", "general")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({"name": item["name"], "quantity": item.get("quantity", "")})

    return {
        "categorized": categories,
        "total_estimated_cost_inr": sum(
            item.get("estimated_cost_inr", 0) for item in shopping
        ),
    }
