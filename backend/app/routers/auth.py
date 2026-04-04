"""
Auth Router
============
Endpoints: register, login, refresh, profile GET/PUT, allergy profile.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from datetime import datetime, timezone
from bson import ObjectId

from app.dependencies import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.database.mongodb import get_database
from app.models.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    UserProfileUpdateRequest,
    AllergyProfileUpdateRequest,
    UserResponse,
    AuthTokenResponse,
    TokenRefreshResponse,
    WasteStats,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ─── Helper ───

def _user_to_response(user: dict) -> UserResponse:
    """Convert a MongoDB user document to a UserResponse."""
    return UserResponse(
        id=str(user["_id"]),
        name=user.get("name", ""),
        email=user.get("email", ""),
        allergies=user.get("allergies", []),
        dietary_preferences=user.get("dietary_preferences", []),
        cuisine_preferences=user.get("cuisine_preferences", []),
        calorie_target=user.get("calorie_target", 1800),
        dietary_goal=user.get("dietary_goal", "balanced"),
        waste_stats=WasteStats(**user.get("waste_stats", {})),
        created_at=user.get("created_at"),
    )


# ─── Register ───

@router.post("/register")
async def register(request: UserRegisterRequest):
    db = get_database()
    email_lower = request.email.lower().strip()

    # Check for duplicate
    existing = await db.users.find_one({"email": email_lower})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate password length
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Create user
    user_doc = {
        "name": request.name.strip(),
        "email": email_lower,
        "password_hash": hash_password(request.password),
        "allergies": [],
        "dietary_preferences": [],
        "cuisine_preferences": [],
        "calorie_target": 1800,
        "dietary_goal": "balanced",
        "favorite_recipe_ids": [],
        "waste_stats": {
            "total_saved_grams": 0,
            "total_wasted_grams": 0,
            "money_saved_inr": 0,
            "co2_prevented_kg": 0,
            "current_streak_days": 0,
            "best_streak_days": 0,
            "badges_earned": [],
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    access_token = create_access_token({"sub": str(result.inserted_id)})
    refresh_token = create_refresh_token({"sub": str(result.inserted_id)})

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user_doc),
    )


# ─── Login ───

@router.post("/login")
async def login(request: UserLoginRequest):
    db = get_database()
    email_lower = request.email.lower().strip()

    user = await db.users.find_one({"email": email_lower})
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token({"sub": str(user["_id"])})
    refresh_token = create_refresh_token({"sub": str(user["_id"])})

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=_user_to_response(user),
    )


# ─── Token Refresh ───

@router.post("/refresh")
async def refresh_token(request: TokenRefreshRequest):
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")

    new_access = create_access_token({"sub": payload["sub"]})
    return TokenRefreshResponse(access_token=new_access)


# ─── Get Profile (/me) ───

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return _user_to_response(user)


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return _user_to_response(user)


# ─── Update Profile ───

@router.put("/profile")
async def update_profile(
    request: UserProfileUpdateRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    update_fields: dict = {"updated_at": datetime.now(timezone.utc)}

    if request.name is not None:
        update_fields["name"] = request.name
    if request.allergies is not None:
        update_fields["allergies"] = [a.model_dump() for a in request.allergies]
    if request.dietary_preferences is not None:
        update_fields["dietary_preferences"] = request.dietary_preferences
    if request.cuisine_preferences is not None:
        update_fields["cuisine_preferences"] = request.cuisine_preferences
    if request.calorie_target is not None:
        update_fields["calorie_target"] = request.calorie_target
    if request.dietary_goal is not None:
        update_fields["dietary_goal"] = request.dietary_goal

    await db.users.update_one({"_id": user["_id"]}, {"$set": update_fields})
    return {"updated": True}


# ─── Update Allergy Profile (separate endpoint per spec) ───

@router.put("/profile/allergies")
async def update_allergy_profile(
    request: AllergyProfileUpdateRequest,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    allergies = [a.model_dump() for a in request.allergies]
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "allergies": allergies,
            "updated_at": datetime.now(timezone.utc),
        }},
    )
    return {"updated": True, "allergy_count": len(allergies)}
