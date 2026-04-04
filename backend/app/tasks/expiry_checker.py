"""
Expiry Checker — Celery Tasks
==============================
Daily expiry check, default expiry assignment, and weekly waste report.
"""

import os
import asyncio
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery
from app.services.waste_tracker_service import (
    calculate_expiry_status,
    check_new_badges,
    CO2_FACTOR_PER_KG,
)

# ─── Sync MongoDB helper (Celery tasks are synchronous) ───

def _get_sync_db():
    """Get a synchronous pymongo database connection for Celery tasks."""
    from pymongo import MongoClient
    uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/recipe_db")
    client = MongoClient(uri)
    # Extract db name from URI or default
    db_name = uri.rsplit("/", 1)[-1].split("?")[0] if "/" in uri else "recipe_db"
    return client[db_name]


def _run_async(coro):
    """Run an async function synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@celery.task(name="app.tasks.expiry_checker.daily_expiry_check")
def daily_expiry_check():
    """
    Runs every day at 6 AM via Celery Beat.
    Checks ALL users' fridge items for approaching expiry.
    """
    db = _get_sync_db()
    now = datetime.now(timezone.utc)
    tomorrow = now + timedelta(days=1)
    three_days = now + timedelta(days=3)

    # Find all items expiring within 3 days
    expiring_items = list(db.fridge_items.find({
        "is_used": False,
        "expiry_date": {"$lte": three_days, "$gte": now},
    }))

    # Group by user
    user_items: dict = {}
    for item in expiring_items:
        uid = str(item["user_id"])
        if uid not in user_items:
            user_items[uid] = []
        user_items[uid].append(item)

    # Process each user
    for user_id, items in user_items.items():
        critical = [i for i in items if i["expiry_date"] <= tomorrow]
        warning = [i for i in items if i["expiry_date"] > tomorrow]

        for item in critical:
            db.fridge_items.update_one(
                {"_id": item["_id"]},
                {"$set": {"expiry_status": "critical"}},
            )
        for item in warning:
            db.fridge_items.update_one(
                {"_id": item["_id"]},
                {"$set": {"expiry_status": "warning"}},
            )

        # Generate quick recipe suggestions for critical items
        if critical:
            critical_names = [i["ingredient_name"] for i in critical]
            user = db.users.find_one({"_id": item["user_id"]})
            if user:
                allergies = [a.get("allergen", "") for a in user.get("allergies", [])]
                try:
                    from app.services.recipe_model_service import predict_quick_recipe
                    recipe = _run_async(predict_quick_recipe(critical_names, allergies))
                    db.waste_suggestions.update_one(
                        {"user_id": item["user_id"]},
                        {"$set": {
                            "urgent_cook_now": [{
                                "ingredients": critical_names,
                                "recipe": recipe.model_dump(),
                                "reason": f"{critical_names[0]} expires tomorrow!",
                            }],
                            "updated_at": now,
                        }},
                        upsert=True,
                    )
                except Exception:
                    pass

    # Mark actually expired items
    expired = db.fridge_items.update_many(
        {"is_used": False, "expiry_date": {"$lt": now}},
        {"$set": {"expiry_status": "expired"}},
    )

    return {
        "processed_users": len(user_items),
        "expired_marked": expired.modified_count,
    }


@celery.task(name="app.tasks.expiry_checker.assign_default_expiry_dates")
def assign_default_expiry_dates():
    """
    For items added without an expiry date, auto-assign based on ingredient type.
    """
    from app.services.waste_tracker_service import get_default_expiry

    db = _get_sync_db()
    items = list(db.fridge_items.find({
        "expiry_date": None,
        "is_used": False,
    }))

    for item in items:
        default_days = get_default_expiry(item["ingredient_name"])
        expiry_date = item["added_date"] + timedelta(days=default_days)
        db.fridge_items.update_one(
            {"_id": item["_id"]},
            {"$set": {"expiry_date": expiry_date, "expiry_status": "fresh"}},
        )

    return {"updated": len(items)}


@celery.task(name="app.tasks.expiry_checker.weekly_waste_report")
def weekly_waste_report():
    """
    Runs every Sunday at 9 AM. Aggregates weekly waste stats per user.
    """
    db = _get_sync_db()
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    pipeline = [
        {"$match": {"logged_at": {"$gte": week_ago}}},
        {"$group": {
            "_id": "$user_id",
            "total_saved": {
                "$sum": {"$cond": [{"$ne": ["$action", "wasted"]}, "$quantity_grams", 0]},
            },
            "total_wasted": {
                "$sum": {"$cond": [{"$eq": ["$action", "wasted"]}, "$quantity_grams", 0]},
            },
            "items_count": {"$sum": 1},
        }},
    ]

    results = list(db.waste_logs.aggregate(pipeline))

    for result in results:
        user_id = result["_id"]
        saved_grams = result["total_saved"]
        money_saved = round(saved_grams / 1000 * 150, 0)

        db.users.update_one(
            {"_id": user_id},
            {"$inc": {
                "waste_stats.total_saved_grams": saved_grams,
                "waste_stats.total_wasted_grams": result["total_wasted"],
                "waste_stats.money_saved_inr": money_saved,
            }},
        )

        # Check and award badges
        user = db.users.find_one({"_id": user_id})
        if user:
            ws = user.get("waste_stats", {})
            new_badges = check_new_badges(ws)
            if new_badges:
                db.users.update_one(
                    {"_id": user_id},
                    {"$addToSet": {"waste_stats.badges_earned": {"$each": new_badges}}},
                )

    return {"users_processed": len(results)}
