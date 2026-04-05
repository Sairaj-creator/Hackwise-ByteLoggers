<h1 align="center">
  <img src="https://img.icons8.com/color/96/000000/ingredients.png" alt="Recipe App Logo" width="80" />
  <br/>
  🍽️ AI Recipe Generator
</h1>

<p align="center">
  <b>Tell us what's in your fridge — we'll tell you what to cook.</b><br/>
  A full-stack mobile app powered by <b>Google Gemini AI</b> and <b>YOLOv8 Computer Vision</b> that generates personalized recipes from your available ingredients, tracks food waste, guards against allergens, and plans your meals for the week.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" />
  <img src="https://img.shields.io/badge/React_Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Expo_54-000020?style=for-the-badge&logo=expo&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB_Atlas-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_2.0_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/YOLOv8-FF6F00?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

---

## 🌟 What is this?

**AI Recipe Generator** (by **ByteLoggers**) is a smart kitchen assistant mobile app that answers one question: *"What can I make with what I have?"*

You add the ingredients sitting in your fridge — either by typing them manually, importing a grocery cart, or **scanning them with your phone camera** using our built-in YOLOv8 ingredient detector. The app sends the structured data through a **2-stage AI pipeline**: first, Google Gemini normalizes and refines the input, then generates a fully structured, personalized recipe complete with step-by-step instructions, cooking timers, difficulty level, nutritional estimates, and YouTube search links — all tailored to your dietary preferences and allergen restrictions.

No more wasted groceries. No more "what's for dinner?" panic.

---

## ✨ Core Features

### 🤖 2-Stage AI Recipe Pipeline
The heart of the app. A two-stage AI pipeline powers recipe generation:
1. **Stage 1 — Gemini Refinement**: Raw user input is normalized, typos are fixed, quantities estimated, and cuisine is auto-detected using Google Gemini 2.0 Flash.
2. **Stage 2 — Gemini Recipe Generation**: A full recipe is generated with structured JSON output — title, cuisine, difficulty, ingredients with quantities, step-by-step instructions with time estimates, and YouTube search queries.

A local **TF-IDF cosine similarity model** (trained on a recipe dataset via `recipe_model.joblib`) is available as an alternative fast-match engine, and all services include robust fallbacks ensuring the app works even when the Gemini API is unavailable.

### 📷 AI Ingredient Scanner (YOLOv8)
Point your phone camera at your ingredients. The built-in **YOLOv8n** computer vision model detects food items in real-time, identifies them with confidence scores and bounding boxes, and adds them directly to your fridge inventory. Currently detects 10 food classes including banana, apple, orange, broccoli, carrot, pizza, and more.

### 🛡️ Allergy Guardian
The backend actively cross-references **every** generated recipe against your saved allergen profile across **12 allergen categories** (Peanuts, Tree Nuts, Shellfish, Fish, Lactose, Gluten, Eggs, Soy, Sesame, Mustard, Celery, Sulfites). Hidden hazards, alias names (e.g. "ghee" → lactose), and cross-reactive ingredients are flagged before they ever reach your screen. Safe substitution suggestions are provided, and **severe allergens trigger automatic recipe regeneration** — the pipeline re-generates excluding dangerous ingredients without user intervention.

### 🗑️ Food Waste Tracker
A gamified waste reduction system that goes beyond simple tracking:
- **Expiry monitoring**: Items are classified as `fresh → warning → critical → expired` in real-time
- **Smart suggestions**: Three tiers — "Urgent Cook Now" (recipes for critical items), "Freeze Now" (freezing instructions for 10+ ingredients), and "Use This Week" (warning-level items)
- **Waste statistics**: Track grams saved, money saved (₹ INR), and CO₂ prevented (2.5 kg CO₂/kg food)
- **Streak system**: Consecutive zero-waste days tracked with best-streak records
- **Badge achievements**: 6 earnable badges — Waste Warrior (1kg saved), Super Saver (5kg), Week Streak, Month Master, Eco Hero (5kg CO₂), Zero Waste Week

### 🍎 AI Nutrition Estimator
Each recipe includes an estimated nutritional breakdown (calories, protein, carbs, fat, fiber) per serving — computed on-demand by the Gemini pipeline from the actual ingredient list. Results are cached in Redis for 7 days to avoid redundant API calls.

### 🗓️ Smart Meal Planner
Generate multi-day meal plans (up to 7 days × 5 meals/day) that sync with your fridge inventory:
- Prioritizes expiring ingredients in the first 3 days
- Auto-generates a categorized **shopping list** for items you don't have
- Supports meal swapping (regenerate a specific meal slot)
- Includes waste optimization stats — tracks how many fridge items and expiring items are utilized
- Configurable: dietary goal (balanced/weight loss/muscle gain/diabetic-friendly), calorie target, cuisine preferences, budget level
- Background generation via **Celery** with progress polling, with synchronous fallback when Celery is unavailable

### 🤝 Social Feed
Share your AI-generated recipes with the community:
- Create posts with recipe links and images
- Like and comment on posts
- Paginated feed with user info and recipe metadata

### 📡 Real-Time WebSocket
Live trending ingredient broadcasts and community recipe notifications via WebSocket (`/api/v1/ws/trends`) with ping/pong heartbeat support and JWT-authenticated connections.

### 👨‍🍳 Cooking Mode
Step-by-step cooking interface with:
- Individual step timers (auto-calculated from recipe data)
- Total cooking time display
- YouTube recipe video link
- "Done Cooking" tracking (counts how many times a recipe has been cooked)

### 📱 Smooth Cross-Platform Mobile UI
React Native + Expo 54 delivers a polished, native-feeling experience on both **Android** and **iOS** with:
- File-based routing via Expo Router
- Bottom tab navigation (Home, Generate, Fridge, Feed, Profile)
- Token-based authentication with automatic refresh
- Image picker for ingredient scanning
- Haptic feedback and blur effects

---

## 🏗️ Architecture

```
Hackwise — AI Recipe Generator
│
├── Backend (FastAPI + Python 3.12)
│   ├── REST API          → FastAPI 0.115, Pydantic v2, Uvicorn
│   ├── AI Pipeline
│   │   ├── Stage 1       → Gemini 2.0 Flash (input refinement)
│   │   ├── Stage 2       → Gemini 2.0 Flash (recipe generation)
│   │   ├── CNN Scanner   → YOLOv8n (ingredient detection from images)
│   │   ├── TF-IDF Model  → scikit-learn cosine similarity (recipe matching)
│   │   └── Nutrition     → Gemini 2.0 Flash (on-demand estimation)
│   ├── Safety            → Allergy Guardian (12 allergen categories)
│   ├── Database          → MongoDB Atlas (motor async driver)
│   ├── Cache             → Redis (recipe + nutrition caching)
│   ├── Message Broker    → RabbitMQ
│   ├── Background Tasks  → Celery Worker & Beat
│   ├── Auth              → JWT (PyJWT) + bcrypt
│   └── Rate Limiting     → slowapi
│
└── Frontend (React Native + Expo 54)
    ├── Routing            → Expo Router (file-based)
    ├── State              → AuthContext + AsyncStorage
    ├── API Client         → Centralized fetch with auto token refresh
    ├── Camera             → expo-image-picker (ingredient scanning)
    └── UI                 → Custom theme + @expo/vector-icons
```

### Backend API Modules

| Router | Prefix | Endpoints | Responsibility |
|---|---|---|---|
| `auth.py` | `/api/v1/auth` | 7 | Register, Login, JWT refresh, profile CRUD, allergy profile |
| `recipes.py` | `/api/v1/recipes` | 8 | AI recipe generation, favorites, cooking mode, nutrients |
| `fridge.py` | `/api/v1/fridge` | 6 | Ingredient CRUD, image scan, cart import, expiry tracking |
| `waste_tracker.py` | `/api/v1/waste-tracker` | 4 | Dashboard, log usage, history, smart suggestions |
| `meal_planner.py` | `/api/v1/meal-planner` | 4 | Generate plan, get plan, swap meal, shopping list |
| `social.py` | `/api/v1/social` | 4 | Feed, create post, like, comment |
| `websocket.py` | `/api/v1/ws` | 1 | Real-time trending ingredients |
| **Root** | `/` | **2** | Health check (`/api/health`) + root |
| | | **36+** | **Total unique endpoints** |

### AI Service Architecture

| Service | File | Purpose |
|---|---|---|
| `gemini_refine_service.py` | Stage 1 | Normalize ingredients, detect cuisine/dietary, estimate quantities |
| `recipe_model_service.py` | Stage 2 | Generate full structured recipes via Gemini |
| `recipe_pipeline_service.py` | Orchestrator | Chains Stage 1 → Stage 2 → Allergy Check → Cache |
| `allergy_guardian.py` | Safety | 12-category allergen detection with cross-reactivity |
| `cnn_service.py` | Vision | YOLOv8n ingredient detection from camera images |
| `gemini_nutrition_service.py` | Nutrition | On-demand nutritional estimation per recipe |
| `llm_services.py` | Legacy | TF-IDF model + Gemini fallback (alternative pipeline) |
| `meal_planner_service.py` | Planning | Multi-day meal plan generation with waste optimization |
| `waste_tracker_service.py` | Tracking | Expiry calc, badges, freeze suggestions, CO₂ estimates |
| `cache_service.py` | Caching | Redis get/set/invalidate with TTL and key hashing |

### Background Tasks (Celery)

| Task | Schedule | Purpose |
|---|---|---|
| `daily_expiry_check` | Daily 6:00 AM | Mark items as critical/warning/expired, generate urgent recipes |
| `assign_default_expiry_dates` | Daily 6:30 AM | Auto-assign shelf life to undated fridge items |
| `weekly_waste_report` | Sunday 9:00 AM | Aggregate weekly waste stats, award badges |
| `generate_meal_plan_task` | On demand | Async multi-day meal plan generation |

---

## 🚀 Getting Started

### Prerequisites

| Tool | Purpose |
|---|---|
| [Python 3.11+](https://www.python.org/) | Backend runtime |
| [Node.js 18+ & npm](https://nodejs.org/) | Frontend runtime |
| [Docker + Docker Compose](https://www.docker.com/) | (Optional) Full backend stack |
| [Expo Go](https://expo.dev/client) | Preview the app on your phone |
| Google Gemini API Key | Powers the recipe AI — [Get one free](https://aistudio.google.com/app/apikey) |

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Sairaj-creator/Hackwise-ByteLoggers.git
cd Hackwise-ByteLoggers
```

---

### Step 2 — Configure the Backend

Create `backend/.env`:

```env
# ─── Database ───
MONGODB_URI=mongodb+srv://<USER>:<PASS>@<YOUR_CLUSTER>/Recipe

# ─── Cache & Message Broker ───
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672

# ─── Authentication ───
JWT_SECRET=your_super_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── AI — The core ingredient ───
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_gemini_api_key_here

# ─── Image Scanner ───
CNN_SERVICE_URL=http://localhost:8001

# ─── Rate Limits ───
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_RECIPE_GENERATE=20/hour
RATE_LIMIT_IMAGE_SCAN=10/hour
RATE_LIMIT_MEAL_PLAN=3/hour

# ─── External Services ───
CLOUDINARY_URL=cloudinary://<API_KEY>:<SECRET>@<CLOUD_NAME>
```

> ⚠️ **Never commit your real `.env` file.** It's already in `.gitignore`.

> 💡 Both `GEMINI_API_KEY` and `GOOGLE_API_KEY` should be set to the same value — different services reference different variable names.

---

### Step 3a — Start the Backend (Docker — Recommended)

```bash
cd backend
docker-compose up --build
```

This single command spins up:
- ✅ **FastAPI** server on `http://localhost:8000`
- ✅ **MongoDB** on port 27017
- ✅ **Redis** cache on port 6379
- ✅ **RabbitMQ** broker on port 5673 (management UI: port 15673)
- ✅ **Celery** worker + beat for background tasks

### Step 3b — Start the Backend (Local — Without Docker)

```bash
cd backend

# Create virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> 📖 **Swagger API Docs** available at: `http://localhost:8000/docs`

> ℹ️ When running locally without Docker, Redis and RabbitMQ are optional — the app gracefully falls back (caching is bypassed, background tasks run synchronously).

---

### Step 4 — Configure the Frontend

Create `frontend/.env`:

```env
# Replace with your machine's local IPv4 address (not localhost!)
EXPO_PUBLIC_BACKEND_URL=http://192.168.x.x:8000
```

> 💡 Find your IPv4: run `ipconfig` (Windows) or `ifconfig` (macOS/Linux).

> ⚠️ **Do NOT add `/api/v1` suffix** — the API client handles route prefixes internally.

---

### Step 5 — Start the Frontend (Expo)

```bash
cd frontend
npm install
npx expo start --clear
```

Then:
- 📷 **Scan the QR code** with the **Expo Go** app on your phone, or
- 🤖 Press `a` to open on a **connected Android emulator**, or
- 🍎 Press `i` for an **iOS simulator** (macOS only)

---

## 📁 Project Structure

```
Hackwise-ByteLoggers/
│
├── backend/                          # FastAPI Python Backend
│   ├── app/
│   │   ├── config.py                # Pydantic Settings (env parsing)
│   │   ├── main.py                  # Application entry point, CORS, lifespan
│   │   ├── dependencies.py          # JWT auth, bcrypt hashing, get_current_user
│   │   │
│   │   ├── routers/                 # API route handlers
│   │   │   ├── auth.py              # 7 endpoints: register, login, refresh, profile
│   │   │   ├── recipes.py           # 8 endpoints: generate, favorites, cook, nutrients
│   │   │   ├── fridge.py            # 6 endpoints: list, scan, manual add, cart import
│   │   │   ├── waste_tracker.py     # 4 endpoints: dashboard, log, history, suggestions
│   │   │   ├── meal_planner.py      # 4 endpoints: generate plan, get, swap, shopping
│   │   │   ├── social.py            # 4 endpoints: feed, post, like, comment
│   │   │   └── websocket.py         # 1 endpoint: real-time trends
│   │   │
│   │   ├── services/                # Core business logic & AI pipeline
│   │   │   ├── gemini_refine_service.py      # Stage 1: input normalization
│   │   │   ├── recipe_model_service.py       # Stage 2: recipe generation
│   │   │   ├── recipe_pipeline_service.py    # 2-stage orchestrator
│   │   │   ├── allergy_guardian.py           # 12-category allergen checker
│   │   │   ├── cnn_service.py                # YOLOv8n image detection
│   │   │   ├── gemini_nutrition_service.py   # Nutritional estimation
│   │   │   ├── llm_services.py               # TF-IDF model + legacy pipeline
│   │   │   ├── meal_planner_service.py       # Multi-day meal plan builder
│   │   │   ├── waste_tracker_service.py      # Expiry, badges, freeze logic
│   │   │   └── cache_service.py              # Redis caching wrapper
│   │   │
│   │   ├── models/                  # Pydantic request/response schemas
│   │   │   ├── user.py              # Auth, profile, allergy models
│   │   │   ├── recipe.py            # Recipe generation & detail models
│   │   │   ├── fridge.py            # Fridge CRUD & scan models
│   │   │   ├── meal_plan.py         # Meal plan, shopping list models
│   │   │   └── waste.py             # Waste dashboard, log, suggestion models
│   │   │
│   │   ├── database/                # Database connections
│   │   │   ├── mongodb.py           # Motor async client + index creation
│   │   │   └── redis.py             # Async Redis connection
│   │   │
│   │   └── tasks/                   # Celery background tasks
│   │       ├── celery_app.py        # Celery config + beat schedule
│   │       ├── expiry_checker.py    # Daily expiry check, weekly reports
│   │       └── meal_plan_generator.py # Async meal plan generation
│   │
│   ├── ai_models/                   # AI model files
│   │   ├── yolov8n.pt               # YOLOv8 nano model (6.2 MB)
│   │   └── recipe_model.joblib      # TF-IDF recipe matcher
│   │
│   ├── docker-compose.yml           # Full stack orchestration
│   ├── Dockerfile                   # Backend container (python:3.11-slim)
│   └── requirements.txt             # Python dependencies
│
└── frontend/                         # React Native + Expo 54 App
    ├── app/
    │   ├── _layout.tsx              # Root layout + AuthContext provider
    │   ├── index.tsx                # Entry redirect (auth check)
    │   ├── (auth)/                  # Auth group
    │   │   ├── login.tsx            # Login screen
    │   │   └── register.tsx         # Registration screen
    │   ├── (tabs)/                  # Main tab navigator
    │   │   ├── _layout.tsx          # Bottom tab bar configuration
    │   │   ├── home.tsx             # Dashboard / home screen
    │   │   ├── generate.tsx         # 🌟 Recipe generator screen
    │   │   ├── fridge.tsx           # Fridge inventory manager
    │   │   ├── feed.tsx             # Social recipe feed
    │   │   └── profile.tsx          # User profile & allergy settings
    │   ├── recipe/[id].tsx          # Recipe detail view
    │   ├── cooking/[id].tsx         # Step-by-step cooking mode
    │   └── ingredient-benefits.tsx  # Ingredient health info
    │
    ├── services/
    │   └── api.ts                   # Centralized API client (41 methods)
    ├── context/
    │   └── AuthContext.tsx           # Auth state management
    ├── constants/
    │   └── theme.ts                 # Design system tokens
    ├── assets/                      # Icons, splash, images
    ├── app.json                     # Expo configuration
    └── package.json                 # Node dependencies
```

---

## 🔌 Complete API Reference

### Authentication (`/api/v1/auth`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/register` | ✗ | Create account → returns JWT tokens + user |
| `POST` | `/login` | ✗ | Email/password login → returns JWT tokens |
| `POST` | `/refresh` | ✗ | Refresh an expired access token |
| `GET` | `/me` | ✓ | Get current authenticated user |
| `GET` | `/profile` | ✓ | Get user profile (alias for /me) |
| `PUT` | `/profile` | ✓ | Update name, allergies, preferences, calorie target |
| `PUT` | `/profile/allergies` | ✓ | Update allergy profile |

### Recipes (`/api/v1/recipes`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/generate` | ✓ | 🤖 Generate recipe from ingredients via AI pipeline |
| `GET` | `/my` | ✓ | List user's generated recipes |
| `GET` | `/favorites` | ✓ | List favorited recipes |
| `POST` | `/{id}/favorite` | ✓ | Toggle favorite on a recipe |
| `GET` | `/{id}` | ✓ | Get full recipe detail |
| `GET` | `/{id}/nutrients` | ✓ | Get AI-estimated nutritional data |
| `GET` | `/{id}/cook` | ✓ | Get cooking mode data (steps + timers) |
| `POST` | `/{id}/done-cooking` | ✓ | Mark recipe as cooked |

### Fridge (`/api/v1/fridge`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | ✓ | List all active fridge items |
| `POST` | `/scan` | ✓ | 📷 Upload image → YOLOv8 ingredient detection |
| `POST` | `/manual` | ✓ | Manually add ingredients |
| `POST` | `/cart-import` | ✓ | Import from cart text (e.g. "Tomato x3") |
| `PUT` | `/{id}` | ✓ | Update quantity/expiry |
| `DELETE` | `/{id}` | ✓ | Remove item from fridge |

### Waste Tracker (`/api/v1/waste-tracker`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/dashboard` | ✓ | Full dashboard: stats, expiring items, achievements |
| `POST` | `/log-usage` | ✓ | Log item as used/wasted/donated/composted |
| `GET` | `/history` | ✓ | Weekly or monthly waste history |
| `GET` | `/smart-suggestions` | ✓ | Urgent cook, freeze, use-this-week suggestions |

### Meal Planner (`/api/v1/meal-planner`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/generate` | ✓ | Generate multi-day meal plan (async) |
| `GET` | `/{id}` | ✓ | Get meal plan with progress polling |
| `PUT` | `/{id}/swap` | ✓ | Swap a specific meal in the plan |
| `GET` | `/{id}/shopping-list` | ✓ | Categorized shopping list with cost estimate |

### Social (`/api/v1/social`)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/feed` | ✓ | Paginated community feed |
| `POST` | `/posts` | ✓ | Create a new post (with optional image) |
| `POST` | `/posts/{id}/like` | ✓ | Toggle like on a post |
| `POST` | `/posts/{id}/comment` | ✓ | Comment on a post |

### WebSocket & Health

| Method | Endpoint | Description |
|---|---|---|
| `WS` | `/api/v1/ws/trends` | Real-time trending ingredients (JWT optional) |
| `GET` | `/api/health` | Health check |
| `GET` | `/` | Root info |

> 📖 Full interactive docs at `http://localhost:8000/docs` (Swagger UI)

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| **App won't start — "GEMINI_API_KEY extra inputs not permitted"** | Your `.env` has a variable not listed in `config.py`. Make sure `GEMINI_API_KEY` and `GOOGLE_API_KEY` are both defined in the Settings class. |
| **"Network request failed" on mobile** | Your `EXPO_PUBLIC_BACKEND_URL` must point to your machine's **LAN IPv4** (e.g. `192.168.x.x`), NOT `localhost`. |
| **Gemini returns 429 RESOURCE_EXHAUSTED** | Free-tier API quota exceeded. Wait for reset, switch to a paid plan, or rotate API key. All services fall back to local alternatives. |
| **NumPy error / "_ARRAY_API not found"** | Run `pip install "numpy<2"` — OpenCV/ultralytics needs NumPy 1.x. |
| **Redis connection errors** | Redis is optional. The backend gracefully bypasses caching when Redis is unavailable. |
| **Recipe generation returns fallback** | Check that `GEMINI_API_KEY` is valid and quota is not exhausted. The system will use template recipes as fallback. |
| **YOLOv8 model not found** | Ensure `backend/ai_models/yolov8n.pt` exists (6.2 MB). |
| **MongoDB index warning** | Non-blocking. May occur due to pymongo/motor version mismatch. Indexes likely already exist. |
| **Celery tasks not running** | Ensure RabbitMQ is running. Without it, meal plan generation falls back to synchronous mode. |

---

## 🧰 Tech Stack Summary

| Layer | Technology | Version |
|---|---|---|
| **AI / LLM** | Google Gemini 2.0 Flash | `google-genai ≥ 1.0` |
| **Computer Vision** | YOLOv8n (Ultralytics) | `ultralytics latest` |
| **ML Model** | TF-IDF Cosine Similarity | `scikit-learn + joblib` |
| **Backend Framework** | FastAPI | `0.115.0` |
| **Database** | MongoDB Atlas | `motor 3.3.2` |
| **Cache** | Redis | `redis 5.0.8` |
| **Message Broker** | RabbitMQ | `3.x` |
| **Background Tasks** | Celery | `5.4.0` |
| **Auth** | JWT + bcrypt | `PyJWT 2.8.0` |
| **Rate Limiting** | slowapi | `0.1.9` |
| **HTTP Client** | httpx | `0.27.2` |
| **Validation** | Pydantic v2 | `2.9.2` |
| **Containerization** | Docker + Docker Compose | `python:3.11-slim` |
| **Mobile Framework** | React Native + Expo | `RN 0.81.5, Expo 54` |
| **Navigation** | Expo Router | `6.0.22` |
| **Language** | Python 3.11+ (backend), TypeScript (frontend) | |

---

## 📊 Database Collections

| Collection | Purpose | Key Indexes |
|---|---|---|
| `users` | User accounts, allergies, preferences, waste stats | `email` (unique) |
| `recipes` | Generated recipes with allergy checks, nutrition | `tags`, `cuisine`, `favorites_count`, `ingredients.name` |
| `fridge_items` | Ingredient inventory per user with expiry tracking | `(user_id, expiry_status)`, `(user_id, is_used)`, `expiry_date` |
| `meal_plans` | Multi-day meal plans with shopping lists | `(user_id, status)` |
| `waste_logs` | Usage/waste logging per ingredient | `(user_id, logged_at)`, `(user_id, action)` |
| `waste_suggestions` | Cached smart suggestions per user | `user_id` (unique) |
| `social_posts` | Community recipe posts with likes/comments | `(created_at)`, `(user_id, created_at)` |

---

## 👥 Team

Built with 💻 ☕ and a fridge full of random ingredients by **ByteLoggers**

---

<p align="center">
  <i>"What can I make with what I have?" — Now you'll always know.</i>
</p>
