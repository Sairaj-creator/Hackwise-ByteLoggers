"""
Meal Plan Generator — Celery Task
====================================
Async background task for generating multi-day meal plans.
"""

import os
import asyncio
from datetime import datetime, timezone

from app.tasks.celery_app import celery


def _get_sync_db():
    from pymongo import MongoClient
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/recipe_db")
    client = MongoClient(uri)
    db_name = uri.rsplit("/", 1)[-1].split("?")[0] if "/" in uri else "recipe_db"
    return client[db_name]


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery.task(bind=True, name="app.tasks.meal_plan_generator.generate_meal_plan_task", max_retries=1)
def generate_meal_plan_task(self, user_id: str, plan_id: str, plan_request: dict):
    """
    Background task: generates a full meal plan (7 days × 3 meals).
    Updates MongoDB with progress and sends notification when done.
    """
    from bson import ObjectId

    db = _get_sync_db()

    try:
        # 1. Update status
        db.meal_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {"$set": {"status": "generating", "progress_percent": 10}},
        )

        # 2. Fetch user data
        user = db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError(f"User {user_id} not found")

        fridge_items = list(db.fridge_items.find({
            "user_id": ObjectId(user_id),
            "is_used": False,
        }))

        # 3. Identify expiring items
        expiring = [
            item["ingredient_name"]
            for item in fridge_items
            if item.get("expiry_status") in ("warning", "critical")
        ]
        fridge_names = [item["ingredient_name"] for item in fridge_items]

        db.meal_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {"$set": {"progress_percent": 30}},
        )

        # 4. Generate plan via meal planner service
        from app.services.meal_planner_service import build_meal_plan

        plan_result = _run_async(build_meal_plan(
            fridge_items=fridge_names,
            expiring_items=expiring,
            user_allergies=user.get("allergies", []),
            preferences={
                "cuisine": ",".join(plan_request.get("cuisine_preferences", [])),
                "dietary": plan_request.get("dietary_goal", "balanced"),
            },
            duration_days=plan_request.get("duration_days", 7),
            meals_per_day=plan_request.get("meals_per_day", 3),
            calorie_target=plan_request.get("calorie_target_per_day", 1800),
            dietary_goal=plan_request.get("dietary_goal", "balanced"),
        ))

        db.meal_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {"$set": {"progress_percent": 80}},
        )

        # 5. Save completed plan
        db.meal_plans.update_one(
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

        return {"plan_id": plan_id, "status": "ready"}

    except Exception as exc:
        db.meal_plans.update_one(
            {"_id": ObjectId(plan_id)},
            {"$set": {"status": "failed", "error": str(exc)}},
        )
        raise self.retry(exc=exc, countdown=30)
