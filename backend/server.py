from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import re
import json
import uuid
import bcrypt
import jwt as pyjwt
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from bson import ObjectId
from emergentintegrations.llm.chat import LlmChat, UserMessage

# ─── Config ──────────────────────────────────────────────────────────
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
EMERGENT_LLM_KEY = os.environ["EMERGENT_LLM_KEY"]

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Recipe Generator")

# ─── Pydantic Models ─────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    allergies: Optional[List[str]] = None
    dietary_preferences: Optional[List[str]] = None
    cuisine_preferences: Optional[List[str]] = None

class FridgeItemCreate(BaseModel):
    name: str
    category: str = "Other"
    quantity: float = 1.0
    unit: str = "pieces"
    expiry_date: Optional[str] = None

class FridgeItemBulkCreate(BaseModel):
    ingredients: List[FridgeItemCreate]

class FridgeItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    expiry_date: Optional[str] = None

class RecipeGenerateRequest(BaseModel):
    ingredients: List[str]
    servings: int = 2
    cuisine: Optional[str] = None
    diet: Optional[str] = None
    cook_time_max: Optional[int] = None
    spice_level: str = "Medium"

# ─── Auth Helpers ────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=60), "type": "access"}
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_expiry_status(expiry_date_str: Optional[str]) -> str:
    if not expiry_date_str:
        return "fresh"
    try:
        expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        days_left = (expiry - now).days
        if days_left < 0:
            return "expired"
        if days_left <= 1:
            return "critical"
        if days_left <= 3:
            return "warning"
        return "fresh"
    except ValueError:
        return "fresh"

# ─── Recipe JSON Parser ─────────────────────────────────────────────
def parse_recipe_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError("Could not parse recipe JSON from AI response")

# ─── Routers ─────────────────────────────────────────────────────────
auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
fridge_router = APIRouter(prefix="/api/fridge", tags=["fridge"])
recipe_router = APIRouter(prefix="/api/recipes", tags=["recipes"])

# ─── Auth Endpoints ──────────────────────────────────────────────────
@auth_router.post("/register")
async def register(req: RegisterRequest):
    email = req.email.lower().strip()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user_doc = {
        "name": req.name.strip(),
        "email": email,
        "password_hash": hash_password(req.password),
        "allergies": [],
        "dietary_preferences": [],
        "cuisine_preferences": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    return {
        "user": {"id": user_id, "name": user_doc["name"], "email": email, "allergies": [], "dietary_preferences": [], "cuisine_preferences": []},
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@auth_router.post("/login")
async def login(req: LoginRequest):
    email = req.email.lower().strip()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    return {
        "user": {
            "id": user_id, "name": user["name"], "email": user["email"],
            "allergies": user.get("allergies", []),
            "dietary_preferences": user.get("dietary_preferences", []),
            "cuisine_preferences": user.get("cuisine_preferences", []),
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

@auth_router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["_id"], "name": user["name"], "email": user["email"],
        "allergies": user.get("allergies", []),
        "dietary_preferences": user.get("dietary_preferences", []),
        "cuisine_preferences": user.get("cuisine_preferences", []),
    }

@auth_router.put("/profile")
async def update_profile(req: ProfileUpdate, user: dict = Depends(get_current_user)):
    update_fields = {}
    if req.name is not None:
        update_fields["name"] = req.name.strip()
    if req.allergies is not None:
        update_fields["allergies"] = req.allergies
    if req.dietary_preferences is not None:
        update_fields["dietary_preferences"] = req.dietary_preferences
    if req.cuisine_preferences is not None:
        update_fields["cuisine_preferences"] = req.cuisine_preferences
    if update_fields:
        await db.users.update_one({"_id": ObjectId(user["_id"])}, {"$set": update_fields})
    return {"updated": True}

@auth_router.post("/refresh")
async def refresh_token(request: Request):
    body = await request.json()
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    try:
        payload = pyjwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        new_access = create_access_token(str(user["_id"]), user["email"])
        return {"access_token": new_access}
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ─── Fridge Endpoints ────────────────────────────────────────────────
@fridge_router.get("")
async def get_fridge(user: dict = Depends(get_current_user)):
    items = await db.fridge_items.find({"user_id": user["_id"]}, {"_id": 0}).to_list(500)
    expiring_soon = 0
    for item in items:
        item["expiry_status"] = get_expiry_status(item.get("expiry_date"))
        if item["expiry_status"] in ("warning", "critical"):
            expiring_soon += 1
    return {"ingredients": items, "total": len(items), "expiring_soon_count": expiring_soon}

@fridge_router.post("/manual")
async def add_manual(req: FridgeItemBulkCreate, user: dict = Depends(get_current_user)):
    added = 0
    for item in req.ingredients:
        doc = {
            "item_id": str(uuid.uuid4()),
            "user_id": user["_id"],
            "name": item.name.strip(),
            "category": item.category,
            "quantity": item.quantity,
            "unit": item.unit,
            "expiry_date": item.expiry_date,
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.fridge_items.insert_one(doc)
        added += 1
    total = await db.fridge_items.count_documents({"user_id": user["_id"]})
    return {"added": added, "fridge_total": total}

@fridge_router.put("/{item_id}")
async def update_fridge_item(item_id: str, req: FridgeItemUpdate, user: dict = Depends(get_current_user)):
    update_fields = {}
    if req.name is not None:
        update_fields["name"] = req.name.strip()
    if req.category is not None:
        update_fields["category"] = req.category
    if req.quantity is not None:
        update_fields["quantity"] = req.quantity
    if req.unit is not None:
        update_fields["unit"] = req.unit
    if req.expiry_date is not None:
        update_fields["expiry_date"] = req.expiry_date
    if not update_fields:
        return {"updated": False}
    result = await db.fridge_items.update_one(
        {"item_id": item_id, "user_id": user["_id"]}, {"$set": update_fields}
    )
    return {"updated": result.modified_count > 0}

@fridge_router.delete("/{item_id}")
async def delete_fridge_item(item_id: str, user: dict = Depends(get_current_user)):
    result = await db.fridge_items.delete_one({"item_id": item_id, "user_id": user["_id"]})
    return {"deleted": result.deleted_count > 0}

# ─── Recipe Endpoints ────────────────────────────────────────────────
@recipe_router.post("/generate")
async def generate_recipe(req: RecipeGenerateRequest, user: dict = Depends(get_current_user)):
    allergies = user.get("allergies", [])
    allergy_text = ", ".join(allergies) if allergies else "None"
    ingredients_text = ", ".join(req.ingredients)
    cuisine_text = req.cuisine or "Any"
    diet_text = req.diet or "None"
    time_text = f"{req.cook_time_max} minutes" if req.cook_time_max else "No limit"

    prompt = f"""Generate a recipe with these details:

Available ingredients: {ingredients_text}
Number of servings: {req.servings}
Cuisine preference: {cuisine_text}
Dietary restriction: {diet_text}
Maximum cook time: {time_text}
Spice level: {req.spice_level}
Allergies to avoid: {allergy_text}

Respond with ONLY valid JSON (no markdown, no code blocks) in this exact structure:
{{
  "title": "Recipe Name",
  "description": "A brief 1-2 sentence description",
  "cuisine": "Italian/Indian/Chinese/etc",
  "difficulty": "Easy/Medium/Hard",
  "prep_time_minutes": 15,
  "cook_time_minutes": 30,
  "total_time_minutes": 45,
  "servings": {req.servings},
  "ingredients": [
    {{"name": "ingredient name", "quantity": "2", "unit": "cups", "from_fridge": true}}
  ],
  "steps": [
    {{"step_number": 1, "instruction": "Detailed instruction", "timer_seconds": null}}
  ],
  "nutrition_per_serving": {{
    "calories": 350,
    "protein_g": 25,
    "carbs_g": 40,
    "fat_g": 12,
    "fiber_g": 5
  }},
  "tags": ["quick", "healthy"],
  "tips": ["Helpful cooking tip"]
}}

Rules:
- Use primarily the available ingredients, mark them with "from_fridge": true
- Additional ingredients needed should have "from_fridge": false
- Each step should be clear and actionable
- Include timer_seconds only for steps that need timing (baking, boiling, etc.), otherwise null
- Nutrition values should be realistic estimates per serving
- Make the recipe practical and delicious"""

    try:
        session_id = f"recipe-{user['_id']}-{uuid.uuid4()}"
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="You are a professional chef and certified nutritionist. Generate detailed, practical recipes. Always respond with valid JSON only - no markdown, no code blocks, no extra text."
        ).with_model("gemini", "gemini-2.5-flash")

        response = await chat.send_message(UserMessage(text=prompt))
        recipe_data = parse_recipe_json(response)

        # Store recipe in DB
        recipe_id = str(uuid.uuid4())
        recipe_doc = {
            "recipe_id": recipe_id,
            "user_id": user["_id"],
            **recipe_data,
            "is_generated": True,
            "favorited_by": [],
            "times_cooked": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.recipes.insert_one(recipe_doc)
        recipe_doc.pop("_id", None)
        return recipe_doc

    except ValueError as e:
        logger.error(f"Recipe parse error: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse AI recipe. Please try again.")
    except Exception as e:
        logger.error(f"Recipe generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Recipe generation failed: {str(e)}")

@recipe_router.get("/my")
async def get_my_recipes(user: dict = Depends(get_current_user)):
    recipes = await db.recipes.find(
        {"user_id": user["_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"recipes": recipes}

@recipe_router.get("/favorites")
async def get_favorites(user: dict = Depends(get_current_user)):
    recipes = await db.recipes.find(
        {"favorited_by": user["_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"recipes": recipes}

@recipe_router.get("/{recipe_id}")
async def get_recipe(recipe_id: str, user: dict = Depends(get_current_user)):
    recipe = await db.recipes.find_one({"recipe_id": recipe_id}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe["is_favorited"] = user["_id"] in recipe.get("favorited_by", [])
    return recipe

@recipe_router.get("/{recipe_id}/cook")
async def get_cooking_data(recipe_id: str, user: dict = Depends(get_current_user)):
    recipe = await db.recipes.find_one({"recipe_id": recipe_id}, {"_id": 0})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {
        "recipe_id": recipe["recipe_id"],
        "title": recipe.get("title", ""),
        "steps": recipe.get("steps", []),
        "total_time_minutes": recipe.get("total_time_minutes", 0),
    }

@recipe_router.post("/{recipe_id}/favorite")
async def toggle_favorite(recipe_id: str, user: dict = Depends(get_current_user)):
    recipe = await db.recipes.find_one({"recipe_id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    favorited_by = recipe.get("favorited_by", [])
    if user["_id"] in favorited_by:
        await db.recipes.update_one({"recipe_id": recipe_id}, {"$pull": {"favorited_by": user["_id"]}})
        return {"favorited": False, "total_favorites": len(favorited_by) - 1}
    else:
        await db.recipes.update_one({"recipe_id": recipe_id}, {"$addToSet": {"favorited_by": user["_id"]}})
        return {"favorited": True, "total_favorites": len(favorited_by) + 1}

@recipe_router.post("/{recipe_id}/done-cooking")
async def done_cooking(recipe_id: str, user: dict = Depends(get_current_user)):
    await db.recipes.update_one({"recipe_id": recipe_id}, {"$inc": {"times_cooked": 1}})
    return {"success": True}

# ─── Health Check ────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

# ─── Include Routers ─────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(fridge_router)
app.include_router(recipe_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Startup ─────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.fridge_items.create_index([("user_id", 1), ("item_id", 1)])
    await db.recipes.create_index([("user_id", 1), ("created_at", -1)])
    await db.recipes.create_index("recipe_id", unique=True)
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "name": "Admin",
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "allergies": [],
            "dietary_preferences": [],
            "cuisine_preferences": [],
            "role": "admin",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        logger.info(f"Admin user seeded: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
        logger.info("Admin password updated")

@app.on_event("shutdown")
async def shutdown():
    client.close()
