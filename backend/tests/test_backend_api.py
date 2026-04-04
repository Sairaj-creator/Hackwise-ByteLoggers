"""
Backend API Tests for AI Recipe Generator
Tests: Health, Auth (register, login, /me, profile), Fridge (CRUD), Recipes (generate, favorites)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://build-from-read.preview.emergentagent.com').rstrip('/')

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture
def test_user_token(api_client):
    """Create test user and return auth token"""
    import random
    email = f"TEST_user_{int(time.time())}_{random.randint(1000,9999)}@test.com"
    password = "testpass123"
    name = "Test User"
    
    response = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "name": name,
        "email": email,
        "password": password
    })
    assert response.status_code == 200, f"Registration failed: {response.json()}"
    data = response.json()
    # Backend normalizes email to lowercase
    return data["access_token"], email.lower(), password

class TestHealth:
    """Health check endpoint"""
    
    def test_health_check(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

class TestAuth:
    """Authentication endpoints"""
    
    def test_register_success(self, api_client):
        import random
        email = f"TEST_newuser_{int(time.time())}_{random.randint(1000,9999)}@test.com"
        response = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "name": "New User",
            "email": email,
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        # Backend normalizes email to lowercase
        assert data["user"]["email"] == email.lower()
        assert data["user"]["name"] == "New User"
        assert data["user"]["allergies"] == []
    
    def test_register_duplicate_email(self, api_client):
        import random
        email = f"TEST_duplicate_{int(time.time())}_{random.randint(1000,9999)}@test.com"
        api_client.post(f"{BASE_URL}/api/auth/register", json={
            "name": "User One",
            "email": email,
            "password": "pass123"
        })
        
        response = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "name": "User Two",
            "email": email,
            "password": "pass456"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_short_password(self, api_client):
        response = api_client.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test",
            "email": "test@short.com",
            "password": "12345"
        })
        assert response.status_code == 400
        assert "6 characters" in response.json()["detail"]
    
    def test_login_success(self, api_client):
        # Use admin credentials
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "admin@example.com"
    
    def test_login_invalid_credentials(self, api_client):
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_me_with_token(self, api_client, test_user_token):
        token, email, _ = test_user_token
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "id" in data
        assert "name" in data
    
    def test_get_me_without_token(self, api_client):
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
    
    def test_update_profile(self, api_client, test_user_token):
        token, email, _ = test_user_token
        
        # Update profile
        update_response = api_client.put(
            f"{BASE_URL}/api/auth/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "allergies": ["peanuts", "shellfish"],
                "dietary_preferences": ["vegetarian"],
                "cuisine_preferences": ["Italian", "Indian"]
            }
        )
        assert update_response.status_code == 200
        assert update_response.json()["updated"] == True
        
        # Verify changes persisted
        get_response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        user_data = get_response.json()
        assert "peanuts" in user_data["allergies"]
        assert "vegetarian" in user_data["dietary_preferences"]
        assert "Italian" in user_data["cuisine_preferences"]

class TestFridge:
    """Fridge management endpoints"""
    
    def test_get_empty_fridge(self, api_client, test_user_token):
        token, _, _ = test_user_token
        response = api_client.get(
            f"{BASE_URL}/api/fridge",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "ingredients" in data
        assert "total" in data
        assert data["total"] == 0
    
    def test_add_ingredients_manual(self, api_client, test_user_token):
        token, _, _ = test_user_token
        
        # Add ingredients
        add_response = api_client.post(
            f"{BASE_URL}/api/fridge/manual",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ingredients": [
                    {"name": "Tomatoes", "category": "Vegetables", "quantity": 5, "unit": "pieces"},
                    {"name": "Onion", "category": "Vegetables", "quantity": 2, "unit": "pieces"},
                    {"name": "Garlic", "category": "Vegetables", "quantity": 1, "unit": "bulb"}
                ]
            }
        )
        assert add_response.status_code == 200
        add_data = add_response.json()
        assert add_data["added"] == 3
        assert add_data["fridge_total"] == 3
        
        # Verify persistence
        get_response = api_client.get(
            f"{BASE_URL}/api/fridge",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        fridge_data = get_response.json()
        assert fridge_data["total"] == 3
        assert len(fridge_data["ingredients"]) == 3
        
        # Check ingredient details
        ingredient_names = [item["name"] for item in fridge_data["ingredients"]]
        assert "Tomatoes" in ingredient_names
        assert "Onion" in ingredient_names
    
    def test_delete_fridge_item(self, api_client, test_user_token):
        token, _, _ = test_user_token
        
        # Add item
        add_response = api_client.post(
            f"{BASE_URL}/api/fridge/manual",
            headers={"Authorization": f"Bearer {token}"},
            json={"ingredients": [{"name": "TEST_DeleteMe", "category": "Test"}]}
        )
        assert add_response.status_code == 200
        
        # Get item_id
        fridge_response = api_client.get(
            f"{BASE_URL}/api/fridge",
            headers={"Authorization": f"Bearer {token}"}
        )
        items = fridge_response.json()["ingredients"]
        test_item = next((item for item in items if item["name"] == "TEST_DeleteMe"), None)
        assert test_item is not None
        item_id = test_item["item_id"]
        
        # Delete item
        delete_response = api_client.delete(
            f"{BASE_URL}/api/fridge/{item_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == True
        
        # Verify deletion
        verify_response = api_client.get(
            f"{BASE_URL}/api/fridge",
            headers={"Authorization": f"Bearer {token}"}
        )
        remaining_items = verify_response.json()["ingredients"]
        remaining_names = [item["name"] for item in remaining_items]
        assert "TEST_DeleteMe" not in remaining_names

class TestRecipes:
    """Recipe generation and management endpoints"""
    
    def test_generate_recipe_with_ai(self, api_client, test_user_token):
        token, _, _ = test_user_token
        
        # Add ingredients first
        api_client.post(
            f"{BASE_URL}/api/fridge/manual",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ingredients": [
                    {"name": "Tomatoes", "category": "Vegetables", "quantity": 3, "unit": "pieces"},
                    {"name": "Onion", "category": "Vegetables", "quantity": 1, "unit": "pieces"},
                    {"name": "Garlic", "category": "Vegetables", "quantity": 2, "unit": "cloves"}
                ]
            }
        )
        
        # Generate recipe (this may take 10-20 seconds)
        response = api_client.post(
            f"{BASE_URL}/api/recipes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ingredients": ["tomatoes", "onion", "garlic"],
                "servings": 2,
                "cuisine": "Italian",
                "spice_level": "Medium"
            },
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate recipe structure
        assert "recipe_id" in data
        assert "title" in data
        assert "ingredients" in data
        assert "steps" in data
        assert len(data["steps"]) > 0
        assert "nutrition_per_serving" in data
        assert data["servings"] == 2
    
    def test_get_my_recipes(self, api_client, test_user_token):
        token, _, _ = test_user_token
        response = api_client.get(
            f"{BASE_URL}/api/recipes/my",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
    
    def test_get_recipe_detail(self, api_client, test_user_token):
        token, _, _ = test_user_token
        
        # First generate a recipe
        gen_response = api_client.post(
            f"{BASE_URL}/api/recipes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "ingredients": ["pasta", "tomato sauce"],
                "servings": 2
            },
            timeout=30
        )
        
        if gen_response.status_code == 200:
            recipe_id = gen_response.json()["recipe_id"]
            
            # Get recipe detail
            detail_response = api_client.get(
                f"{BASE_URL}/api/recipes/{recipe_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert detail_response.status_code == 200
            recipe = detail_response.json()
            assert recipe["recipe_id"] == recipe_id
            assert "is_favorited" in recipe
    
    def test_toggle_favorite(self, api_client, test_user_token):
        token, _, _ = test_user_token
        
        # Generate recipe first
        gen_response = api_client.post(
            f"{BASE_URL}/api/recipes/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"ingredients": ["chicken", "rice"], "servings": 2},
            timeout=30
        )
        
        if gen_response.status_code == 200:
            recipe_id = gen_response.json()["recipe_id"]
            
            # Favorite it
            fav_response = api_client.post(
                f"{BASE_URL}/api/recipes/{recipe_id}/favorite",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert fav_response.status_code == 200
            assert fav_response.json()["favorited"] == True
            
            # Unfavorite it
            unfav_response = api_client.post(
                f"{BASE_URL}/api/recipes/{recipe_id}/favorite",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert unfav_response.status_code == 200
            assert unfav_response.json()["favorited"] == False
    
    def test_get_favorites(self, api_client, test_user_token):
        token, _, _ = test_user_token
        response = api_client.get(
            f"{BASE_URL}/api/recipes/favorites",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert isinstance(data["recipes"], list)
