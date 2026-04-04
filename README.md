<h1 align="center">
  <img src="https://img.icons8.com/color/96/000000/ingredients.png" alt="Recipe App Logo" width="80" />
  <br/>
  🍽️ AI Recipe Generator
</h1>

<p align="center">
  <b>Tell us what's in your fridge — we'll tell you what to cook.</b><br/>
  A full-stack mobile app powered by <b>Google Gemini AI</b> that generates personalized recipes from your available ingredients, tracks food waste, and keeps you safe from allergens.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" />
  <img src="https://img.shields.io/badge/React_Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Expo-000020?style=for-the-badge&logo=expo&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

---

## 🌟 What is this?

**AI Recipe Generator** (by **ByteLoggers**) is a smart kitchen assistant mobile app that answers one question: *"What can I make with what I have?"*

You add the ingredients sitting in your fridge. The app sends them to **Google Gemini 2.0 Flash**, our LLM backbone, which returns a fully structured, personalized recipe complete with step-by-step instructions, cooking time, difficulty level, nutritional estimates, and required pantry staples — all tailored to your dietary preferences and allergen restrictions.

No more wasted groceries. No more "what's for dinner?" panic.

---

## ✨ Core Features

### 🤖 LLM-Powered Recipe Generation
The heart of the app. Select your available ingredients, set preferences (cuisine, spice level, max cook time), and hit generate. Google Gemini crafts a complete, structured recipe in seconds — not a template, but a real, context-aware cooking guide built specifically from *your* fridge.

### 🛡️ Allergy Guardian
The backend actively cross-references every generated recipe against your saved allergen profile (Peanuts, Dairy, Gluten, Shellfish, etc.). Hidden hazards and cross-reactive ingredients are flagged before they ever reach your screen, with safe substitution suggestions provided.

### 🗑️ Food Waste Tracker
Log groceries with expiry dates. The app monitors your stock, alerts you when items are nearing expiry, and smart-tags them as **"Urgent Cook"** or **"Freeze Now"** so you can use them before they go bad. Save money, reduce waste.

### 🍎 AI Nutrition Estimator
Each generated recipe includes an estimated nutritional breakdown (calories, protein, carbohydrates, fat) per serving — computed by the Gemini pipeline from the ingredient list, not a lookup table.

### 🗓️ Meal Planner
Plan your meals across the week. The planner syncs with your fridge inventory to suggest realistic options using what you already own.

### 🤝 Social — Share Recipes
Found a winner? Share your AI-generated recipes with others directly through the app's social layer.

### 📱 Smooth Cross-Platform Mobile UI
React Native + Expo means a polished, native-feeling experience on both **Android** and **iOS** with fluid transitions, bottom-sheet modals, and a clean minimalist design.

---

## 🏗️ Architecture

```
AI Recipe Generator
├── Backend  (FastAPI + Python 3.11)
│   ├── REST API       → FastAPI, Pydantic v2, Uvicorn
│   ├── AI Engine      → Google Gemini 2.0 Flash (google-genai)
│   ├── Database       → MongoDB Atlas (motor async driver)
│   ├── Cache/Broker   → Redis + RabbitMQ
│   ├── Background     → Celery Worker & Beat
│   ├── Auth           → JWT (python-jose) + bcrypt
│   └── Rate Limiting  → slowapi
│
└── Frontend (React Native + Expo)
    ├── Routing        → Expo Router (file-based)
    ├── State          → Custom Hooks + REST API
    └── UI             → Custom design system + @expo/vector-icons
```

### Backend API Modules

| Router | Responsibility |
|---|---|
| `auth.py` | Register, Login, JWT refresh, password management |
| `recipes.py` | Gemini recipe generation, history, save/unsave |
| `fridge.py` | Ingredient CRUD, expiry tracking |
| `waste_tracker.py` | Waste alerts, urgent cook tagging, freeze suggestions |
| `meal_planner.py` | Weekly meal schedule, fridge-aware suggestions |
| `social.py` | Share, discover, and interact with community recipes |
| `websocket.py` | Real-time notifications (expiry alerts, task updates) |

---

## 🚀 Getting Started

### Prerequisites

| Tool | Purpose |
|---|---|
| [Docker + Docker Compose](https://www.docker.com/) | Runs the full backend stack |
| [Node.js + npm](https://nodejs.org/) | Runs the Expo frontend |
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

Create `backend/.env` with the following:

```env
# Database
MONGODB_URI=mongodb+srv://<USER>:<PASS>@<YOUR_CLUSTER>/Recipe

# Cache & Message Broker
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672

# Authentication
JWT_SECRET=your_super_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI — The core ingredient!
GEMINI_API_KEY=your_gemini_api_key_here

# Rate Limits
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_RECIPE_GENERATE=20/hour
RATE_LIMIT_IMAGE_SCAN=10/hour
RATE_LIMIT_MEAL_PLAN=3/hour
```

> ⚠️ **Never commit your real `.env` file.** It's already in `.gitignore`.

---

### Step 3 — Start the Backend (Docker)

```bash
cd backend
docker-compose up --build
```

This single command spins up:
- ✅ **FastAPI** server on `http://localhost:8000`
- ✅ **MongoDB** (or connects to Atlas)
- ✅ **Redis** cache
- ✅ **RabbitMQ** message broker
- ✅ **Celery** background workers

> 📖 **Swagger API Docs** available at: `http://localhost:8000/docs`

---

### Step 4 — Configure the Frontend

Create `frontend/.env`:

```env
# Replace with your machine's local IPv4 address (not localhost!)
EXPO_PUBLIC_BACKEND_URL=http://192.168.x.x:8000/api/v1
```

> 💡 Find your IPv4: run `ipconfig` (Windows) or `ifconfig` (macOS/Linux).

---

### Step 5 — Start the Frontend (Expo)

```bash
cd frontend
npm install
npx expo start --clear
```

Then:
- 📷 **Scan the QR code** with the **Expo Go** app on your phone, or
- 🤖 Press `a` to open on a **connected Android emulator**

---

## 📁 Project Structure

```
Hackwise-ByteLoggers/
│
├── backend/                        # FastAPI Python Backend
│   ├── app/
│   │   ├── routers/                # API route handlers
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── recipes.py          # 🤖 AI recipe generation
│   │   │   ├── fridge.py           # Ingredient management
│   │   │   ├── waste_tracker.py    # Food waste monitoring
│   │   │   ├── meal_planner.py     # Weekly meal scheduling
│   │   │   ├── social.py           # Community recipe sharing
│   │   │   └── websocket.py        # Real-time notifications
│   │   ├── services/               # Core business logic
│   │   ├── models/                 # Pydantic schemas & DB models
│   │   ├── database/               # MongoDB & Redis connections
│   │   ├── tasks/                  # Celery async task definitions
│   │   ├── dependencies.py         # JWT auth & hashing utilities
│   │   ├── config.py               # App configuration (env vars)
│   │   └── main.py                 # Application entry point
│   ├── docker-compose.yml          # Full stack orchestration
│   ├── Dockerfile                  # Backend container image
│   └── requirements.txt            # Python dependencies
│
└── frontend/                       # React Native + Expo App
    ├── app/
    │   ├── (auth)/                 # Login & registration screens
    │   ├── (tabs)/                 # Bottom tab navigator
    │   │   ├── generate.tsx        # 🌟 Recipe generator screen
    │   │   ├── fridge.tsx          # Ingredient tracker screen
    │   │   └── profile.tsx         # User profile & allergy settings
    │   ├── recipe/                 # Recipe detail screens
    │   └── cooking/                # Step-by-step cooking mode
    ├── services/
    │   └── api.ts                  # Backend API client
    ├── constants/                  # Theming & design tokens
    └── context/                    # Global state providers
```

---

## 🔌 Key API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create a new user account |
| `POST` | `/api/v1/auth/login` | Login and receive JWT tokens |
| `POST` | `/api/v1/recipes/generate` | 🤖 Generate recipe from ingredients via Gemini |
| `GET` | `/api/v1/recipes/history` | Get previously generated recipes |
| `GET` | `/api/v1/fridge/` | List all tracked ingredients |
| `POST` | `/api/v1/fridge/` | Add ingredient to fridge |
| `GET` | `/api/v1/waste-tracker/alerts` | Get expiry & waste alerts |
| `GET` | `/api/v1/meal-planner/` | Fetch weekly meal plan |

> Full interactive docs at `http://localhost:8000/docs` (Swagger UI)

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| **Error 422 on recipe generation** | Check that the request payload matches the expected Pydantic schema for `preferences`. See `backend/app/models/`. |
| **"Network request failed" on mobile** | Your `EXPO_PUBLIC_BACKEND_URL` must point to your machine's **LAN IPv4** (e.g. `192.168.x.x`), NOT `localhost`. |
| **Redis connection errors** | The backend handles Redis failures gracefully — caching is bypassed but the app stays functional. Check Docker containers are running. |
| **Gemini API errors** | Verify `GEMINI_API_KEY` is set correctly in `backend/.env`. Get a key at [aistudio.google.com](https://aistudio.google.com/app/apikey). |
| **Celery tasks not running** | Ensure RabbitMQ container is healthy: `docker-compose ps`. |

---

## 🧰 Tech Stack Summary

| Layer | Technology |
|---|---|
| **AI / LLM** | Google Gemini 2.0 Flash (`google-genai`) |
| **Backend Framework** | FastAPI 0.115 (Python 3.11) |
| **Database** | MongoDB Atlas (`motor` async driver) |
| **Cache** | Redis 5 |
| **Message Broker** | RabbitMQ |
| **Background Tasks** | Celery 5.4 |
| **Auth** | JWT (`python-jose`) + bcrypt |
| **Rate Limiting** | slowapi |
| **Containerization** | Docker + Docker Compose |
| **Mobile Framework** | React Native + Expo (managed) |
| **Navigation** | Expo Router (file-based) |
| **Language** | Python 3.11 (backend), TypeScript (frontend) |

---

<p align="center">
  Built with 💻 ☕ and a fridge full of random ingredients by <b>ByteLoggers</b>
</p>
