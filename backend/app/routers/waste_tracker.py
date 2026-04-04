"""
Waste Tracker Router
=====================
Endpoints: dashboard, log usage, history, smart suggestions.
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from app.dependencies import get_current_user
from app.database.mongodb import get_database
from app.services.waste_tracker_service import (
    calculate_expiry_status,
    calculate_days_until_expiry,
    estimate_money_saved,
    estimate_co2_prevented,
    check_new_badges,
    get_all_achievements,
    get_freeze_suggestion,
    CO2_FACTOR_PER_KG,
)
from app.models.waste import (
    WasteLogRequest,
    WasteDashboardResponse,
    WasteSummary,
    ExpiringItemResponse,
    WasteLogResponse,
    WasteHistoryResponse,
    SmartSuggestionsResponse,
)

router = APIRouter(prefix="/api/v1/waste-tracker", tags=["Waste Tracker"])


# ─── Dashboard ───

@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = user["_id"]
    now = datetime.now(timezone.utc)

    # Fetch all active fridge items
    items = await db.fridge_items.find(
        {"user_id": user_id, "is_used": False}
    ).to_list(length=500)

    total = len(items)
    within_24h = sum(1 for i in items if calculate_expiry_status(i.get("expiry_date")) == "critical")
    within_3d = sum(1 for i in items if calculate_expiry_status(i.get("expiry_date")) in ("critical", "warning"))
    expired = sum(1 for i in items if calculate_expiry_status(i.get("expiry_date")) == "expired")

    # Waste stats from user profile
    ws = user.get("waste_stats", {})

    # Build expiring items list with recipe suggestions
    expiring = []
    for item in items:
        status = calculate_expiry_status(item.get("expiry_date"))
        if status in ("critical", "warning"):
            expiring.append(ExpiringItemResponse(
                id=str(item["_id"]),
                name=item["ingredient_name"],
                quantity=f"{item.get('quantity', '')} {item.get('unit', '')}".strip(),
                expiry_date=item.get("expiry_date", now).strftime("%Y-%m-%d") if item.get("expiry_date") else None,
                days_remaining=calculate_days_until_expiry(item.get("expiry_date")) or 0,
                status=status,
                suggested_recipes=[],  # Populated by smart-suggestions
            ))

    summary = WasteSummary(
        total_items_in_fridge=total,
        expiring_within_24h=within_24h,
        expiring_within_3_days=within_3d,
        expired=expired,
        waste_prevented_this_week_grams=ws.get("total_saved_grams", 0),
        waste_prevented_this_month_grams=ws.get("total_saved_grams", 0),
        money_saved_inr=ws.get("money_saved_inr", 0),
        co2_prevented_kg=ws.get("co2_prevented_kg", 0),
        waste_reduction_streak_days=ws.get("current_streak_days", 0),
    )

    achievements = get_all_achievements(ws)

    return WasteDashboardResponse(
        summary=summary,
        expiring_items=expiring,
        achievements=achievements,
    )


# ─── Log Usage ───

@router.post("/log-usage")
async def log_usage(
    request: WasteLogRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    user_id = user["_id"]
    now = datetime.now(timezone.utc)
    ws = user.get("waste_stats", {})

    # Fetch the fridge item
    item = await db.fridge_items.find_one({"_id": ObjectId(request.ingredient_id), "user_id": user_id})
    if not item:
        raise HTTPException(404, "Fridge item not found")

    was_expiring = calculate_expiry_status(item.get("expiry_date")) in ("critical", "warning")

    # Log the waste entry
    log_doc = {
        "user_id": user_id,
        "ingredient_name": item["ingredient_name"],
        "fridge_item_id": item["_id"],
        "action": request.action,
        "recipe_id": ObjectId(request.recipe_id) if request.recipe_id else None,
        "quantity_grams": request.quantity_used_grams,
        "was_expiring": was_expiring,
        "days_before_expiry": calculate_days_until_expiry(item.get("expiry_date")),
        "logged_at": now,
    }
    await db.waste_logs.insert_one(log_doc)

    # Mark fridge item as used
    await db.fridge_items.update_one(
        {"_id": item["_id"]},
        {"$set": {
            "is_used": True,
            "used_in_recipe_id": ObjectId(request.recipe_id) if request.recipe_id else None,
            "used_at": now,
        }},
    )

    # Update user waste stats
    grams = request.quantity_used_grams
    streak_broken = False
    new_streak = ws.get("current_streak_days", 0)

    if request.action == "wasted":
        await db.users.update_one(
            {"_id": user_id},
            {"$inc": {"waste_stats.total_wasted_grams": grams},
             "$set": {"waste_stats.current_streak_days": 0}},
        )
        streak_broken = True
        new_streak = 0
    else:
        money = estimate_money_saved(grams, item["ingredient_name"])
        co2 = estimate_co2_prevented(grams)
        new_streak = ws.get("current_streak_days", 0) + 1
        best = max(ws.get("best_streak_days", 0), new_streak)

        await db.users.update_one(
            {"_id": user_id},
            {"$inc": {
                "waste_stats.total_saved_grams": grams,
                "waste_stats.money_saved_inr": money,
                "waste_stats.co2_prevented_kg": co2,
            },
             "$set": {
                "waste_stats.current_streak_days": new_streak,
                "waste_stats.best_streak_days": best,
            }},
        )

    # Check for new badges
    updated_user = await db.users.find_one({"_id": user_id})
    updated_ws = updated_user.get("waste_stats", {})
    new_badges = check_new_badges(updated_ws)

    if new_badges:
        await db.users.update_one(
            {"_id": user_id},
            {"$addToSet": {"waste_stats.badges_earned": {"$each": new_badges}}},
        )

    return WasteLogResponse(
        logged=True,
        waste_prevented_grams=grams if request.action != "wasted" else 0,
        streak_broken=streak_broken,
        new_streak_days=new_streak,
        new_badges_earned=new_badges,
        message="It happens! Tomorrow is a fresh start." if streak_broken else "",
    )


# ─── History ───

@router.get("/history")
async def get_history(
    period: str = "monthly",
    user: dict = Depends(get_current_user),
):
    db = get_database()
    user_id = user["_id"]
    now = datetime.now(timezone.utc)

    if period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now - timedelta(days=7)

    logs = await db.waste_logs.find(
        {"user_id": user_id, "logged_at": {"$gte": start}}
    ).to_list(length=1000)

    used = sum(1 for l in logs if l["action"] != "wasted")
    wasted = sum(1 for l in logs if l["action"] == "wasted")
    donated = sum(1 for l in logs if l["action"] == "donated")
    composted = sum(1 for l in logs if l["action"] == "composted")
    total = len(logs)

    saved_grams = sum(l["quantity_grams"] for l in logs if l["action"] != "wasted")
    wasted_grams = sum(l["quantity_grams"] for l in logs if l["action"] == "wasted")

    return WasteHistoryResponse(
        period=now.strftime("%Y-%m"),
        total_items_tracked=total,
        used_before_expiry=used,
        wasted=wasted,
        donated=donated,
        composted=composted,
        waste_rate_percent=round(wasted / max(total, 1) * 100, 1),
        money_saved_inr=round(saved_grams / 1000 * 150, 0),
        co2_prevented_kg=round(saved_grams / 1000 * CO2_FACTOR_PER_KG, 2),
    )


# ─── Smart Suggestions ───

@router.get("/smart-suggestions")
async def get_smart_suggestions(user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = user["_id"]

    # Get items expiring soon
    items = await db.fridge_items.find(
        {"user_id": user_id, "is_used": False}
    ).to_list(length=500)

    critical = [i for i in items if calculate_expiry_status(i.get("expiry_date")) == "critical"]
    warning = [i for i in items if calculate_expiry_status(i.get("expiry_date")) == "warning"]

    # Urgent cook suggestions
    urgent = []
    if critical:
        crit_names = [i["ingredient_name"] for i in critical]
        from app.services.recipe_pipeline_service import generate_quick_recipe_pipeline
        result = await generate_quick_recipe_pipeline(
            crit_names, user.get("allergies", [])
        )
        recipe = result.get("recipe", {})
        if recipe:
            urgent.append({
                "ingredients": crit_names,
                "recipe": {
                    "title": recipe.get("title", "Quick Recipe"),
                    "time_minutes": recipe.get("estimated_time_minutes", 10),
                },
                "reason": f"{crit_names[0]} expires tomorrow!",
            })

    # Freeze suggestions
    freeze = []
    for item in warning + critical:
        sug = get_freeze_suggestion(item["ingredient_name"], item.get("expiry_date"))
        if sug:
            freeze.append(sug)

    # Use this week
    use_week = []
    for item in warning:
        days_left = calculate_days_until_expiry(item.get("expiry_date"))
        use_week.append({
            "ingredient": item["ingredient_name"],
            "days_remaining": days_left or 0,
            "quantity": f"{item.get('quantity', '')} {item.get('unit', '')}".strip(),
            "recipe_ideas": [],
        })

    return SmartSuggestionsResponse(
        urgent_cook_now=urgent,
        freeze_suggestions=freeze,
        use_this_week=use_week,
    )
