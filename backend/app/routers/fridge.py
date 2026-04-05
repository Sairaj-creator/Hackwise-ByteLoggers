"""
Fridge Router
==============
Endpoints: list fridge, scan image, manual add, cart import, update, delete.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from typing import List

from app.dependencies import get_current_user
from app.database.mongodb import get_database
from app.services.waste_tracker_service import (
    get_default_expiry,
    calculate_expiry_status,
    calculate_days_until_expiry,
)
from app.models.fridge import (
    FridgeManualAddRequest,
    FridgeCartImportRequest,
    FridgeItemUpdateRequest,
    FridgeItemResponse,
    FridgeResponse,
    FridgeAddResponse,
    FridgeScanResponse,
)

router = APIRouter(prefix="/api/v1/fridge", tags=["Fridge"])


# ─── Helper ───

def _item_to_response(item: dict) -> FridgeItemResponse:
    expiry = item.get("expiry_date")
    return FridgeItemResponse(
        item_id=str(item["_id"]),
        name=item.get("ingredient_name", ""),
        category=item.get("category", "general"),
        quantity=item.get("quantity", 1),
        unit=item.get("unit", "pieces"),
        added_date=item.get("added_date"),
        expiry_date=expiry,
        days_until_expiry=calculate_days_until_expiry(expiry),
        expiry_status=calculate_expiry_status(expiry),
    )


# ─── Get Fridge ───

@router.get("")
async def get_fridge(user: dict = Depends(get_current_user)):
    db = get_database()
    items = await db.fridge_items.find(
        {"user_id": user["_id"], "is_used": False}
    ).to_list(length=500)

    responses = [_item_to_response(item) for item in items]
    expiring_soon = sum(
        1 for r in responses if r.expiry_status in ("warning", "critical")
    )

    return FridgeResponse(
        ingredients=responses,
        total=len(responses),
        expiring_soon_count=expiring_soon,
    )


# ─── Scan Image ───

@router.post("/scan")
async def scan_ingredients(
    image: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPEG, PNG or WebP images are accepted")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(400, "Image too large. Max 10MB.")

    try:
        from app.services.cnn_service import detect_ingredients_from_image
        result = await detect_ingredients_from_image(image_bytes)
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").error(f"CNN scan failed: {e}", exc_info=True)
        return FridgeScanResponse(
            detected_ingredients=[],
            processing_time_ms=0,
            error="Could not detect ingredients. Please add manually.",
        )

    return FridgeScanResponse(
        detected_ingredients=[
            {"name": ing.name, "confidence": ing.confidence}
            for ing in result.detected_ingredients
        ],
        processing_time_ms=result.processing_time_ms,
    )


# ─── Manual Add ───

@router.post("/manual")
async def add_ingredients_manual(
    request: FridgeManualAddRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    now = datetime.now(timezone.utc)
    docs = []

    for ing in request.ingredients:
        # Parse expiry date if provided, else auto-assign
        if ing.expiry_date:
            try:
                expiry = datetime.fromisoformat(ing.expiry_date.replace("Z", "+00:00"))
            except ValueError:
                expiry = now + timedelta(days=get_default_expiry(ing.name))
        else:
            expiry = now + timedelta(days=get_default_expiry(ing.name))

        docs.append({
            "user_id": user["_id"],
            "ingredient_name": ing.name,
            "category": ing.category or "general",
            "quantity": ing.quantity or 1,
            "unit": ing.unit or "pieces",
            "added_date": now,
            "expiry_date": expiry,
            "expiry_status": calculate_expiry_status(expiry),
            "source": "manual",
            "is_used": False,
            "used_in_recipe_id": None,
            "used_at": None,
        })

    if docs:
        await db.fridge_items.insert_many(docs)

    total = await db.fridge_items.count_documents(
        {"user_id": user["_id"], "is_used": False}
    )

    return FridgeAddResponse(added=len(docs), fridge_total=total)


# ─── Cart Import ───

@router.post("/cart-import")
async def cart_import(
    request: FridgeCartImportRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    now = datetime.now(timezone.utc)
    parsed = []

    for raw in request.cart_items:
        # Simple parsing: "Tomato x3" → name="Tomato", qty=3
        parts = raw.strip().rsplit("x", 1)
        name = parts[0].strip().rsplit(" ", 1)
        if len(parts) == 2:
            try:
                qty = float(parts[1].strip())
            except ValueError:
                qty = 1
            ing_name = parts[0].strip()
        else:
            qty = 1
            ing_name = raw.strip()

        expiry = now + timedelta(days=get_default_expiry(ing_name))

        parsed.append({
            "user_id": user["_id"],
            "ingredient_name": ing_name,
            "category": "general",
            "quantity": qty,
            "unit": "pieces",
            "added_date": now,
            "expiry_date": expiry,
            "expiry_status": "fresh",
            "source": request.source,
            "is_used": False,
            "used_in_recipe_id": None,
            "used_at": None,
        })

    if parsed:
        await db.fridge_items.insert_many(parsed)

    return {
        "parsed_items": [{"name": p["ingredient_name"], "quantity": p["quantity"]} for p in parsed],
        "added": len(parsed),
    }


# ─── Update Fridge Item ───

@router.put("/{ingredient_id}")
async def update_fridge_item(
    ingredient_id: str,
    request: FridgeItemUpdateRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    update_fields: dict = {}

    if request.quantity is not None:
        update_fields["quantity"] = request.quantity
    if request.expiry_date is not None:
        try:
            expiry = datetime.fromisoformat(request.expiry_date.replace("Z", "+00:00"))
            update_fields["expiry_date"] = expiry
            update_fields["expiry_status"] = calculate_expiry_status(expiry)
        except ValueError:
            raise HTTPException(400, "Invalid expiry date format")

    if not update_fields:
        raise HTTPException(400, "No fields to update")

    result = await db.fridge_items.update_one(
        {"_id": ObjectId(ingredient_id), "user_id": user["_id"]},
        {"$set": update_fields},
    )

    if result.matched_count == 0:
        raise HTTPException(404, "Item not found")

    return {"updated": True}


# ─── Delete Fridge Item ───

@router.delete("/{ingredient_id}")
async def delete_fridge_item(
    ingredient_id: str,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    result = await db.fridge_items.delete_one(
        {"_id": ObjectId(ingredient_id), "user_id": user["_id"]},
    )

    if result.deleted_count == 0:
        raise HTTPException(404, "Item not found")

    return {"deleted": True}
