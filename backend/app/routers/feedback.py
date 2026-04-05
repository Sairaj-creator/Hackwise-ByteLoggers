"""
Feedback Router
================
Endpoints to submit and retrieve user feedback.
Stored in MongoDB `feedback` collection.
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, List
from bson import ObjectId

from app.database.mongodb import get_database
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/feedback", tags=["Feedback"])


# ─── Schemas ───

class FeedbackSubmitRequest(BaseModel):
    type: str = Field(..., description="bug | feature | recipe | other")
    message: str = Field(..., min_length=10, max_length=500)

class FeedbackResponse(BaseModel):
    id: str
    user_name: str
    user_email: str
    type: str
    message: str
    submitted_at: datetime


# ─── Submit Feedback ───

@router.post("", status_code=201)
async def submit_feedback(
    request: FeedbackSubmitRequest,
    user: dict = Depends(get_current_user),
):
    """Submit feedback. Saved to MongoDB with user info and timestamp."""
    allowed_types = {"bug", "feature", "recipe", "other"}
    if request.type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"type must be one of: {allowed_types}")

    db = get_database()
    doc = {
        "user_id": str(user["_id"]),
        "user_name": user.get("name", "Unknown"),
        "user_email": user.get("email", ""),
        "type": request.type,
        "message": request.message.strip(),
        "submitted_at": datetime.now(timezone.utc),
    }
    result = await db.feedback.insert_one(doc)
    return {"id": str(result.inserted_id), "message": "Feedback submitted successfully"}


# ─── List All Feedback (Admin Only) ───

@router.get("", response_model=List[FeedbackResponse])
async def list_feedback(
    user: dict = Depends(get_current_user),
):
    """
    Returns all feedback submissions (newest first).
    Restricted to the configured ADMIN_EMAIL only.
    """
    from app.config import get_settings
    settings = get_settings()
    admin_email = settings.ADMIN_EMAIL.strip().lower()
    if not admin_email or user.get("email", "").strip().lower() != admin_email:
        raise HTTPException(status_code=403, detail="Access restricted to admins only.")

    db = get_database()
    cursor = db.feedback.find().sort("submitted_at", -1).limit(100)
    results = []
    async for doc in cursor:
        results.append(FeedbackResponse(
            id=str(doc["_id"]),
            user_name=doc.get("user_name", "Unknown"),
            user_email=doc.get("user_email", ""),
            type=doc.get("type", "other"),
            message=doc.get("message", ""),
            submitted_at=doc.get("submitted_at", datetime.now(timezone.utc)),
        ))
    return results
