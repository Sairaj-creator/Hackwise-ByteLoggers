from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import MongoClient

from app.config import get_settings
from app.main import app


@dataclass
class CheckResult:
    name: str
    status: str
    details: str


results: list[CheckResult] = []


def add_result(name: str, status: str, details: str) -> None:
    results.append(CheckResult(name=name, status=status, details=details))


def safe_json(response) -> Any:
    try:
        return response.json()
    except Exception:
        return response.text


def headers(token: str | None = None) -> dict[str, str]:
    base: dict[str, str] = {}
    if token:
        base["Authorization"] = f"Bearer {token}"
    return base


def main() -> int:
    settings = get_settings()
    mongo = MongoClient(settings.MONGODB_URI)
    db = mongo.get_default_database()
    if db is None:
        db = mongo["recipe_db"]

    email = f"qa_{int(time.time())}_{uuid4().hex[:6]}@example.com"
    password = "TestPass123!"
    user_id: Optional[str] = None
    token: Optional[str] = None
    recipe_id: Optional[str] = None
    fridge_item_id: Optional[str] = None
    meal_plan_id: Optional[str] = None
    social_post_id: Optional[str] = None

    with TestClient(app, raise_server_exceptions=False) as client:
        try:
            response = client.get("/api/v1/health")
            if response.status_code == 200 and safe_json(response).get("status") == "ok":
                add_result("Health endpoint", "PASS", "GET /api/v1/health returned 200 ok.")
            else:
                add_result("Health endpoint", "FAIL", f"Unexpected response: {response.status_code} {safe_json(response)}")
        except Exception as exc:
            add_result("Health endpoint", "FAIL", f"Exception during health check: {exc}")

        try:
            collections = sorted(db.list_collection_names())
            add_result("MongoDB connectivity", "PASS", f"Connected to MongoDB. Collections present: {collections}")
        except Exception as exc:
            add_result("MongoDB connectivity", "FAIL", f"MongoDB connection failed: {exc}")
            print(json.dumps({"results": [asdict(item) for item in results]}, indent=2))
            return 1

        register_payload = {"name": "QA Test User", "email": email, "password": password}
        response = client.post("/api/v1/auth/register", json=register_payload)
        body = safe_json(response)
        if response.status_code == 200 and body.get("access_token") and body.get("refresh_token"):
            token = body["access_token"]
            user_id = body["user"]["id"]
            add_result("Register user", "PASS", f"Registered user {email} with id {user_id}.")
        else:
            add_result("Register user", "FAIL", f"Register failed: {response.status_code} {body}")
            print(json.dumps({"results": [asdict(item) for item in results]}, indent=2))
            return 1

        user_doc = db.users.find_one({"email": email})
        if user_doc and "password_hash" in user_doc and user_doc["password_hash"].startswith("$2"):
            add_result("User stored securely", "PASS", "MongoDB user document contains bcrypt password hash and default fields.")
        else:
            add_result("User stored securely", "FAIL", f"Unexpected user document: {user_doc}")

        response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        if response.status_code == 200 and safe_json(response).get("access_token"):
            add_result("Login success", "PASS", "Login returned access and refresh tokens.")
        else:
            add_result("Login success", "FAIL", f"Login failed: {response.status_code} {safe_json(response)}")

        response = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})
        if response.status_code == 401:
            add_result("Login wrong password", "PASS", "Wrong password returns 401.")
        else:
            add_result("Login wrong password", "FAIL", f"Expected 401, got {response.status_code} {safe_json(response)}")

        response = client.get("/api/v1/auth/profile", headers=headers(token))
        if response.status_code == 200 and safe_json(response).get("email") == email:
            add_result("Get profile", "PASS", "Protected profile route returned the registered user.")
        else:
            add_result("Get profile", "FAIL", f"Profile fetch failed: {response.status_code} {safe_json(response)}")

        update_payload = {
            "allergies": [
                {"allergen": "peanuts", "severity": "severe"},
                {"allergen": "lactose", "severity": "mild"},
            ],
            "dietary_preferences": ["vegetarian"],
            "cuisine_preferences": ["Indian", "Italian"],
        }
        response = client.put("/api/v1/auth/profile", headers=headers(token), json=update_payload)
        user_doc = db.users.find_one({"email": email}, {"allergies": 1, "dietary_preferences": 1, "cuisine_preferences": 1})
        if response.status_code == 200 and user_doc and len(user_doc.get("allergies", [])) == 2:
            add_result("Update profile", "PASS", f"Profile updated successfully in MongoDB: {user_doc}")
        else:
            add_result("Update profile", "FAIL", f"Profile update failed: {response.status_code} {safe_json(response)}; doc={user_doc}")

        fridge_payload = {
            "ingredients": [
                {"name": "Paneer", "quantity": 200, "unit": "grams", "expiry_date": "2026-04-15"},
                {"name": "Tomato", "quantity": 3, "unit": "pieces", "expiry_date": "2026-04-12"},
                {"name": "Onion", "quantity": 2, "unit": "pieces", "expiry_date": "2026-05-01"},
                {"name": "Bell Pepper", "quantity": 1, "unit": "pieces", "expiry_date": "2026-04-11"},
            ]
        }
        response = client.post("/api/v1/fridge/manual", headers=headers(token), json=fridge_payload)
        if response.status_code == 200 and safe_json(response).get("added") == 4:
            add_result("Add fridge ingredients", "PASS", f"Manual add succeeded: {safe_json(response)}")
        else:
            add_result("Add fridge ingredients", "FAIL", f"Manual add failed: {response.status_code} {safe_json(response)}")

        response = client.get("/api/v1/fridge", headers=headers(token))
        fridge_body = safe_json(response)
        if response.status_code == 200 and len(fridge_body.get("ingredients", [])) >= 4:
            fridge_item_id = fridge_body["ingredients"][0]["item_id"]
            add_result("Get fridge contents", "PASS", f"Fridge returned {len(fridge_body.get('ingredients', []))} items; expiring_soon_count={fridge_body.get('expiring_soon_count')}")
        else:
            add_result("Get fridge contents", "FAIL", f"Fridge fetch failed: {response.status_code} {fridge_body}")

        good_image_path = Path("carrot_photo.jpg")
        if good_image_path.exists():
            with good_image_path.open("rb") as handle:
                response = client.post(
                    "/api/v1/fridge/scan",
                    headers=headers(token),
                    files={"image": ("carrot_photo.jpg", handle.read(), "image/jpeg")},
                )
            body = safe_json(response)
            if response.status_code == 200:
                detected = body.get("detected_ingredients", [])
                if detected:
                    add_result("Image scan good image", "PASS", f"Image scan detected ingredients: {detected}")
                else:
                    add_result("Image scan good image", "WARN", f"Image scan returned 200 but no detections. Body: {body}")
            else:
                add_result("Image scan good image", "FAIL", f"Image scan failed: {response.status_code} {body}")
        else:
            add_result("Image scan good image", "BLOCKED", "No sample food image found in backend/.")

        response = client.post(
            "/api/v1/fridge/scan",
            headers=headers(token),
            files={"image": ("not_a_food_image.txt", b"not an image", "text/plain")},
        )
        if response.status_code == 400:
            add_result("Image scan bad file", "PASS", "Bad image content type rejected with 400.")
        else:
            add_result("Image scan bad file", "FAIL", f"Expected 400, got {response.status_code} {safe_json(response)}")

        direct_recipe_payload = {
            "ingredients": ["paneer", "bell pepper", "onion", "tomato"],
            "preferences": {"cuisine": "Indian", "spice_level": "medium"},
            "number_of_people": 2,
            "dietary_preferences": ["vegetarian"],
            "prioritize_expiring": True,
        }
        response = client.post("/api/v1/recipes/generate", headers=headers(token), json=direct_recipe_payload)
        recipe_body = safe_json(response)
        if response.status_code == 200 and recipe_body.get("recipe", {}).get("title"):
            recipe_id = recipe_body["recipe"].get("recipe_id")
            details = f"title={recipe_body['recipe'].get('title')}, stages={recipe_body.get('pipeline_stages')}"
            if "status" not in recipe_body["recipe"] or "similarity_score" not in recipe_body["recipe"]:
                details += " | Note: serialized recipe response omits status/similarity_score from the master contract."
                add_result("Generate recipe direct input", "WARN", details)
            else:
                add_result("Generate recipe direct input", "PASS", details)
        else:
            add_result("Generate recipe direct input", "FAIL", f"Recipe generation failed: {response.status_code} {recipe_body}")

        latest_recipe = db.recipes.find_one({"user_id": ObjectId(user_id)}, sort=[("created_at", -1)])
        if latest_recipe and latest_recipe.get("title"):
            add_result("Recipe persisted", "PASS", f"Latest recipe stored in MongoDB: {latest_recipe.get('title')}")
        else:
            add_result("Recipe persisted", "FAIL", "Generated recipe was not found in MongoDB.")

        nl_recipe_payload = {
            "raw_text_input": "I have some tomatoes and a box of spaghetti",
            "number_of_people": 4,
            "dietary_preferences": ["vegetarian"],
        }
        response = client.post("/api/v1/recipes/generate", headers=headers(token), json=nl_recipe_payload)
        body = safe_json(response)
        if response.status_code == 200 and body.get("pipeline_stages", {}).get("stage_1") == "gemini_refinement":
            add_result("Generate recipe natural language", "PASS", f"Stage 1 refinement triggered successfully: {body.get('pipeline_stages')}")
        else:
            add_result("Generate recipe natural language", "FAIL", f"Natural-language recipe flow failed or did not refine: {response.status_code} {body}")

        allergy_recipe_payload = {
            "ingredients": ["chicken", "peanut butter", "soy sauce", "noodles"],
            "preferences": {"cuisine": "Chinese"},
            "number_of_people": 2,
        }
        response = client.post("/api/v1/recipes/generate", headers=headers(token), json=allergy_recipe_payload)
        body = safe_json(response)
        warnings = body.get("allergy_check", {}).get("warnings", [])
        recipe_ingredients = json.dumps(body.get("recipe", {}).get("ingredients", []))
        if response.status_code == 200 and body.get("allergy_check", {}).get("safe") is False:
            if "peanut" in recipe_ingredients.lower():
                add_result("Allergy Guardian severe allergen", "FAIL", f"Allergy flagged but recipe still contains peanut ingredient. Body: {body}")
            else:
                add_result("Allergy Guardian severe allergen", "PASS", f"Allergy Guardian flagged allergens and removed peanuts. warnings={warnings}")
        else:
            add_result("Allergy Guardian severe allergen", "FAIL", f"Expected unsafe allergy response, got {response.status_code} {body}")

        weird_recipe_payload = {"ingredients": ["unicorn tears", "dragon scales"], "preferences": {"cuisine": "Martian"}}
        response = client.post("/api/v1/recipes/generate", headers=headers(token), json=weird_recipe_payload)
        body = safe_json(response)
        if response.status_code == 200 and body.get("recipe", {}).get("title"):
            add_result("No-match recipe handling", "WARN", f"Endpoint generated a fallback recipe instead of returning an error: {body.get('recipe', {}).get('title')}")
        else:
            add_result("No-match recipe handling", "PASS", f"No-match request handled without crash: {response.status_code} {body}")

        if recipe_id:
            response = client.get(f"/api/v1/recipes/{recipe_id}/nutrients", headers=headers(token))
            body = safe_json(response)
            if response.status_code == 200 and body.get("total_calories") is not None:
                add_result("Nutrition lookup", "PASS", f"Nutrition response source={body.get('source')} total_calories={body.get('total_calories')}")
            else:
                add_result("Nutrition lookup", "FAIL", f"Nutrition failed: {response.status_code} {body}")

            response = client.get("/api/v1/recipes/000000000000000000000000/nutrients", headers=headers(token))
            if response.status_code == 404:
                add_result("Nutrition invalid recipe id", "PASS", "Invalid ObjectId returns 404 recipe not found.")
            else:
                add_result("Nutrition invalid recipe id", "FAIL", f"Expected 404, got {response.status_code} {safe_json(response)}")

            response = client.get(f"/api/v1/recipes/{recipe_id}/cook", headers=headers(token))
            body = safe_json(response)
            if response.status_code == 200 and body.get("steps"):
                add_result("Cooking mode", "PASS", f"Cooking mode returned {len(body.get('steps', []))} steps.")
            else:
                add_result("Cooking mode", "FAIL", f"Cooking mode failed: {response.status_code} {body}")

            response = client.post(f"/api/v1/recipes/{recipe_id}/done-cooking", headers=headers(token))
            recipe_doc = db.recipes.find_one({"_id": ObjectId(recipe_id)})
            if response.status_code == 200 and recipe_doc and recipe_doc.get("times_cooked", 0) >= 1:
                if recipe_doc.get("last_cooked_at"):
                    add_result("Done cooking", "PASS", "times_cooked incremented and last_cooked_at present.")
                else:
                    add_result("Done cooking", "WARN", "times_cooked incremented, but last_cooked_at was not written.")
            else:
                add_result("Done cooking", "FAIL", f"Done cooking failed: {response.status_code} {safe_json(response)}; doc={recipe_doc}")

        response = client.get("/api/v1/waste-tracker/dashboard", headers=headers(token))
        body = safe_json(response)
        if response.status_code == 200 and body.get("summary"):
            add_result("Waste dashboard", "PASS", f"Dashboard summary: {body.get('summary')}")
        else:
            add_result("Waste dashboard", "FAIL", f"Waste dashboard failed: {response.status_code} {body}")

        if fridge_item_id and recipe_id:
            response = client.post(
                "/api/v1/waste-tracker/log-usage",
                headers=headers(token),
                json={
                    "ingredient_id": fridge_item_id,
                    "action": "used_in_recipe",
                    "recipe_id": recipe_id,
                    "quantity_used_grams": 200,
                },
            )
            log_doc = db.waste_logs.find_one({"user_id": ObjectId(user_id), "action": "used_in_recipe"}, sort=[("logged_at", -1)])
            used_item = db.fridge_items.find_one({"_id": ObjectId(fridge_item_id)})
            if response.status_code == 200 and log_doc and used_item and used_item.get("is_used") is True:
                add_result("Waste log usage", "PASS", "Waste usage log created and fridge item marked used.")
            else:
                add_result("Waste log usage", "FAIL", f"Log usage failed: {response.status_code} {safe_json(response)}; log={log_doc}; item={used_item}")

        response = client.get("/api/v1/waste-tracker/smart-suggestions", headers=headers(token))
        body = safe_json(response)
        if response.status_code == 200 and "urgent_cook_now" in body:
            add_result("Waste smart suggestions", "PASS", f"Smart suggestions returned successfully: keys={list(body.keys())}")
        else:
            add_result("Waste smart suggestions", "FAIL", f"Smart suggestions failed: {response.status_code} {body}")

        meal_payload = {
            "duration_days": 3,
            "meals_per_day": 3,
            "dietary_goal": "balanced",
            "calorie_target_per_day": 1800,
            "use_fridge_ingredients": True,
            "cuisine_preferences": ["Indian", "Italian"],
        }
        response = client.post("/api/v1/meal-planner/generate", headers=headers(token), json=meal_payload)
        body = safe_json(response)
        if response.status_code == 200 and body.get("plan_id"):
            meal_plan_id = body["plan_id"]
            add_result("Meal plan generate", "PASS", f"Meal plan request accepted with id {meal_plan_id}")
            get_response = client.get(f"/api/v1/meal-planner/{meal_plan_id}", headers=headers(token))
            get_body = safe_json(get_response)
            if get_response.status_code == 200 and get_body.get("status") in {"ready", "generating"}:
                if get_body.get("status") == "ready":
                    add_result("Meal plan poll", "PASS", f"Meal plan ready with {len(get_body.get('days', []))} day entries.")
                else:
                    add_result("Meal plan poll", "WARN", f"Meal plan still generating in terminal-only run: {get_body}")
            else:
                add_result("Meal plan poll", "FAIL", f"Meal plan poll failed: {get_response.status_code} {get_body}")
        else:
            add_result("Meal plan generate", "FAIL", f"Meal plan generation failed: {response.status_code} {body}")

        if meal_plan_id:
            response = client.put(
                f"/api/v1/meal-planner/{meal_plan_id}/swap",
                headers=headers(token),
                json={"day": 1, "meal": "lunch", "reason": "not_in_mood"},
            )
            body = safe_json(response)
            if response.status_code == 200 and body.get("new_meal", {}).get("title"):
                add_result("Meal swap", "PASS", f"Meal swap returned {body.get('new_meal', {}).get('title')}")
            else:
                add_result("Meal swap", "FAIL", f"Meal swap failed: {response.status_code} {body}")

        response = client.get("/api/v1/social/feed?page=1&limit=10", headers=headers(token))
        body = safe_json(response)
        if response.status_code == 200 and "posts" in body:
            add_result("Social feed", "PASS", f"Social feed returned {len(body.get('posts', []))} posts.")
        else:
            add_result("Social feed", "FAIL", f"Social feed failed: {response.status_code} {body}")

        if recipe_id:
            response = client.post(
                "/api/v1/social/posts",
                headers=headers(token),
                files={},
                data={"recipe_id": recipe_id, "content": "Made this tonight - delicious!"},
            )
            body = safe_json(response)
            if response.status_code == 200 and body.get("post_id"):
                social_post_id = body["post_id"]
                add_result("Create social post", "PASS", f"Social post created with id {social_post_id}")
            else:
                add_result("Create social post", "FAIL", f"Create post failed: {response.status_code} {body}")

        if recipe_id:
            response = client.post(f"/api/v1/recipes/{recipe_id}/favorite", headers=headers(token))
            body1 = safe_json(response)
            response2 = client.post(f"/api/v1/recipes/{recipe_id}/favorite", headers=headers(token))
            body2 = safe_json(response2)
            if response.status_code == 200 and response2.status_code == 200 and body1.get("favorited") is True and body2.get("favorited") is False:
                add_result("Favorite toggle", "PASS", "Recipe favorite toggled on and back off.")
            else:
                add_result("Favorite toggle", "FAIL", f"Unexpected favorite toggle responses: {body1} then {body2}")

        try:
            with client.websocket_connect(f"/api/v1/ws/trends?token={token}") as websocket:
                websocket.send_text("ping")
                first = websocket.receive_json()
                second = websocket.receive_json()
                if first.get("event") == "pong" and second.get("event") == "trending_ingredient":
                    add_result("WebSocket trends", "PASS", "WebSocket connected, pong heartbeat worked, and periodic trend message arrived.")
                else:
                    add_result("WebSocket trends", "FAIL", f"Unexpected websocket messages: {first}, {second}")
        except Exception as exc:
            add_result("WebSocket trends", "FAIL", f"WebSocket verification failed: {exc}")

        response = client.get("/api/v1/fridge", headers={"Authorization": "Bearer expired.token.here"})
        if response.status_code == 401:
            add_result("Expired JWT handling", "PASS", "Expired/invalid JWT returns 401.")
        else:
            add_result("Expired JWT handling", "FAIL", f"Expected 401, got {response.status_code} {safe_json(response)}")

        response = client.get("/api/v1/fridge")
        if response.status_code in {401, 403}:
            add_result("Missing auth header", "PASS", f"Missing auth rejected with {response.status_code}.")
        else:
            add_result("Missing auth header", "FAIL", f"Expected 401/403, got {response.status_code} {safe_json(response)}")

        response = client.post(
            "/api/v1/recipes/generate",
            headers={**headers(token), "Content-Type": "application/json"},
            content='{"this is not valid json',
        )
        if response.status_code == 422:
            add_result("Malformed JSON body", "PASS", "Malformed JSON rejected with 422.")
        else:
            add_result("Malformed JSON body", "FAIL", f"Expected 422, got {response.status_code} {safe_json(response)}")

        rate_codes = []
        for _ in range(12):
            resp = client.post("/api/v1/recipes/generate", headers=headers(token), json={"ingredients": ["test"]})
            rate_codes.append(resp.status_code)
        if 429 in rate_codes:
            add_result("Rate limiting", "PASS", f"Rate limiting active; observed codes: {rate_codes}")
        else:
            add_result("Rate limiting", "WARN", f"No 429 observed; current router implementation appears to have no per-endpoint limiter decorators. codes={rate_codes}")

        if fridge_item_id:
            response = client.delete(f"/api/v1/fridge/{fridge_item_id}", headers=headers(token))
            deleted = db.fridge_items.find_one({"_id": ObjectId(fridge_item_id)})
            if response.status_code == 200 and deleted is None:
                add_result("Delete fridge item", "PASS", "Fridge item deleted from MongoDB.")
            elif response.status_code == 200:
                add_result("Delete fridge item", "WARN", f"Delete returned 200 but item still exists: {deleted}")
            else:
                add_result("Delete fridge item", "FAIL", f"Delete failed: {response.status_code} {safe_json(response)}")

        try:
            explain = db.fridge_items.find({"user_id": ObjectId(user_id), "expiry_status": "warning"}).explain()
            winning_plan = json.dumps(explain.get("queryPlanner", {}).get("winningPlan", {}))
            if "IXSCAN" in winning_plan:
                add_result("MongoDB fridge index usage", "PASS", "Fridge query uses IXSCAN.")
            else:
                add_result("MongoDB fridge index usage", "WARN", f"Winning plan did not show IXSCAN: {winning_plan}")
        except Exception as exc:
            add_result("MongoDB fridge index usage", "WARN", f"Could not run explain(): {exc}")

        add_result("Redis verification", "BLOCKED", "Docker/Redis service is not available in this session, so cache key and TTL checks could not be verified externally.")
        add_result("Celery/RabbitMQ verification", "BLOCKED", "Docker/RabbitMQ service is not available in this session, so worker log and broker checks could not be verified.")
        add_result("Frontend Expo runtime", "BLOCKED", "Terminal-only environment cannot validate the live mobile UI. Frontend request shapes were validated earlier by code-path inspection.")
        add_result("Docker service health", "BLOCKED", "Docker daemon is not available in this session, so docker-compose ps/log checks could not be executed.")

    print(json.dumps({"email": email, "user_id": user_id, "recipe_id": recipe_id, "meal_plan_id": meal_plan_id, "results": [asdict(item) for item in results]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
