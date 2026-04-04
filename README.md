<h1 align="center">
  <img src="https://img.icons8.com/color/96/000000/ingredients.png" alt="Hackwise Logo" width="80" />
  <br>
  Hackwise (ByteLoggers)
</h1>

<p align="center">
  <b>An AI-Powered Smart Kitchen & Recipe Generator App</b><br>
  Designed to reduce food waste, ensure allergen safety, and deliver incredibly personalized recipes using Google Gemini AI.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=FastAPI&logoColor=white" />
  <img src="https://img.shields.io/badge/React_Native-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/Expo-000020?style=for-the-badge&logo=expo&logoColor=white" />
  <img src="https://img.shields.io/badge/MongoDB-4EA94B?style=for-the-badge&logo=mongodb&logoColor=white" />
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_AI-4285F4?style=for-the-badge&logo=google&logoColor=white" />
</p>

---

## 🌟 Overview

Hackwise is a full-stack smart kitchen assistant that helps users track their ingredients, get incredibly tailored recipes based on what they have, and drastically reduce food waste.

With built-in **Allergy Guardian** algorithms and **Google Gemini 2.0 AI** integrations, the app does heavy lifting behind the scenes to create safe, creative, and fast cooking instructions out of your leftover groceries.

## ✨ Core Features

### 🍳 Gemini-Powered Recipe Generation
Say goodbye to generic recipes! Select your ingredients, set a max cooking time, choose a cuisine or spice level, and Google's **Gemini AI** spins up a structured, customized recipe including cooking steps, required pantry staples, and difficulty—all within seconds.

### 🛡️ Allergy Guardian Framework
Safety comes first. The backend actively scans generated recipes against the user's saved allergen profile (e.g., Peanuts, Dairy, Gluten) to detect cross-reactivity and hidden hazards. It proactively suggests safe substitutions.

### 🍃 Food Waste Tracker
Log your groceries with expiry dates. The app alerts you when items are going bad and automatically tags them for "Urgent Cooks" or "Freeze Suggestions", giving you exact strategies to reduce your footprint and save money.

### 🍎 Nutrition Estimator
A built-in AI pipeline evaluates the recipe and estimates standard nutritional facts (calories, protein, carbs) per serving alongside curated health benefits.

### 📱 Beautiful Cross-Platform Mobile Experience
Built on React Native (Expo), delivering fluid animations, clean minimalist UI, modal bottom-sheets, and a unified experience across Android and iOS devices.

---

## 🏗️ Architecture Stack

### Backend (`/backend`)
- **Framework:** FastAPI (Python 3.11)
- **Database:** MongoDB Atlas (via `motor` async driver)
- **Caching & Brokers:** Redis & RabbitMQ
- **Background Tasks:** Celery (Worker & Beat)
- **AI Backend:** `google-genai` (Targeting `gemini-2.0-flash`)
- **Security:** JWT Auth & `bcrypt` password hashing

### Frontend (`/frontend`)
- **Framework:** Expo & React Native (managed workflow)
- **Routing:** Expo Router
- **State Management & Data:** Custom Hooks + REST API
- **UI:** Custom design system (`/constants/theme.ts`), `@expo/vector-icons`

---

## 🚀 Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/en/) & npm/yarn/pnpm
- [Docker](https://www.docker.com/) & Docker Compose
- [Expo Go App](https://expo.dev/client) installed on your mobile phone

### 1. Environment Setup

*Backend (`./backend/.env`):*
```env
MONGODB_URI=mongodb+srv://<USER>:<PASS>@<YOUR_CLUSTER>/Recipe
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672
JWT_SECRET=super_secret_key_change_me
GEMINI_API_KEY=your_gemini_api_key_here
```

*Frontend (`./frontend/.env`):*
```env
EXPO_PUBLIC_BACKEND_URL=http://<YOUR-LOCAL-IP>:8000/api/v1
```

### 2. Run the Backend (Docker)
We use `docker-compose` to seamlessly spin up FastAPI, Celery, MongoDB, Redis, and RabbitMQ.
```bash
cd backend
docker-compose up --build
```
> The API will be available at: http://localhost:8000/docs (Swagger UI)

### 3. Run the Frontend (Expo)
```bash
cd frontend
npm install
npx expo start --clear
```
> Scan the QR code using your **Expo Go** mobile app or press `a` to run it on an Android emulator.

---

## 📦 Project Structure

```
Hackwise/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── routers/          # API endpoint routes (auth, fridge, recipe)
│   │   ├── services/         # Core business logic (gemini, allergy, waste)
│   │   ├── models/           # Pydantic schemas and models
│   │   ├── database/         # MongoDB and Redis connection logic
│   │   ├── dependencies.py   # JWT verifiers & bcrypt hashing
│   │   ├── main.py           # Application Entry Point
│   ├── docker-compose.yml    # Orchestration configuration
...
├── frontend/                 # React Native / Expo Application
│   ├── app/                  # Screens & layouts utilizing Expo Route
│   │   ├── (tabs)/           # Bottom Tab Navigator Layout
│   │   │   ├── generate.tsx  # Recipe Generator Screen
│   │   │   ├── profile.tsx   # User Settings & Allergy Selection Screen
│   │   │   ├── fridge.tsx    # Ingredient Tracker Screen 
│   ├── services/
│   │   ├── api.ts            # Network abstraction connecting to the Backend
│   ├── constants/            # Theming styling and layout
```

---

## 💡 Troubleshooting
* **Error 422 on Recipe Generation:** Ensure you have updated the `preferences` structure correctly when making the call from `api.ts`.
* **Network Fetch Failed:** Double-check that your `EXPO_PUBLIC_BACKEND_URL` is pointing to the IPv4 address of your computer running the Docker containers, *not* `localhost`.
* **Redis Connection Errors:** The backend is configured to fail gracefully! If your Redis container crashes, caching steps are bypassed but functionality persists.

---
<p align="center">Built with 💻 and ☕ by <b>ByteLoggers</b>.</p>
