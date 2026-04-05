# AI Recipe Generator — Engineering Docs

This document serves as an overview of the backend system architecture, the integration between our AI pipelines, and a detailed log of the critical backend problems solved during the system debugging phase.

---

## Part 1: Project Content & AI Architecture

The Hackwise Backend is a FastAPI-driven services cluster that interfaces with multiple AI models, standard databases, and background task runners to power the React Native frontend.

### 1. The Core AI Pipeline

When a user requests a recipe, the data flows through a **Two-Stage AI Pipeline**:

*   **Stage 1: Input Refinement (`gemini_refine_service.py`)**
    *   Takes messy user input (e.g., typos, vague quantities).
    *   Calls Google Gemini 2.0 Flash to normalize the ingredient list.
    *   Auto-detects the implied cuisine and dietary category from the raw ingredients.
*   **Stage 2: Recipe Generation (`recipe_model_service.py`)**
    *   Takes the perfectly normalized list and passes it back to Gemini with strict JSON schema enforcing.
    *   Generates step-by-step instructions, specific cooking timers per step, difficulty, and YouTube search queries.

### 2. The Ingredient Scanner (`cnn_service.py`)

*   **The Model:** We use **YOLOv8-nano** (`yolov8n.pt`) because of its insanely small size (6.2 MB) and fast inference times.
*   **The Flow:** The React Native frontend uploads an image via `multipart/form-data`. The FastAPI backend writes this locally to a temp folder, runs the YOLO bounding box detection, filters down to COCO food classes (apples, carrots, broccoli, pizza, etc.), and returns the highest-confidence detections.

### 3. The Allergy Guardian (`allergy_guardian.py`)

*   Before ANY recipe is sent to the user, the backend runs the generated ingredient list through a safety checker.
*   **Cross-reactivity logic:** If a user is allergic to "Lactose", the system knows to flag "Butter", "Ghee", and "Cheese".
*   **Auto-Regeneration:** If a severe allergen is detected in a Gemini-generated recipe, the backend automatically throws the recipe away, informs Gemini of the danger, and regenerates a safe alternative behind the scenes.

### 4. Background Waste Tracking & Meal Planning (`celery_app.py`)

*   **Waste Tracking:** Gamified engine tracking expiry dates (`fresh` → `warning` → `critical`). Nightly Celery tasks evaluate expiring items to trigger badges (e.g., *Eco Hero*, *Waste Warrior*) and automatically generate "Urgent Cook" suggestions.
*   **Meal Planner:** Generates multi-day meal schedules optimizing for expiring fridge items.

---

## Part 2: Troubleshooting Log & Solved Problems

During integration testing, several critical blockers took down the application. Below is the post-mortem of what went wrong and how it was fixed.

### 🔴 Problem 1: Cascading Failure via Environment Configuration

**The Symptoms:**
The API wouldn't start properly, MongoDB connection failed, and all AI services returned immediate `500 Server Errors`.

**The Root Cause:**
In Pydantic v2, data-classes configured to parse environment variables default to strict mode (`extra='forbid'`).
Our `.env` file contained `GEMINI_API_KEY=AIza...`, but our `config.py` `Settings` class only had a slot for `GOOGLE_API_KEY`. When Pydantic saw `GEMINI_API_KEY`, it rejected the entire environment file, killing all downstream configuration (including the MongoDB URIs).

**The Fix:**
Added `GEMINI_API_KEY` to the `Settings` class definition in `app/config.py`.

---

### 🔴 Problem 2: NumPy / OpenCV Integration Crash

**The Symptoms:**
`POST /api/v1/fridge/scan` requests crashed the API server immediately with an `AttributeError: _ARRAY_API not found`.

**The Root Cause:**
The Ultralytics (YOLO) library relies on OpenCV (`cv2`). The container was running Python 3.11 with the brand new `NumPy 2.x`, but the OpenCV binaries distributed via pip were compiled against `NumPy 1.x`. This caused memory mapping violations between the two C-extensions.

**The Fix:**
Downgraded the numerical backend by enforcing `pip install "numpy<2"` in the host environment.

---

### 🟡 Problem 3: Carrot Image Scan Returning Empty

**The Symptoms:**
Scanning a clear picture of a carrot via the frontend camera interface returned "no ingredient found".

**The Root Cause:**
Because we are utilizing the `yolov8n` (nano) architecture to save server costs, the model trades high-accuracy for extreme speed. Carrots in unusual lighting or angles were hitting a confidence score of `0.25` or `0.30`. Our backend was strictly filtering out any detection with a confidence score below `0.40`.

**The Fix:**
Edited `app/services/cnn_service.py` and lowered the `CONFIDENCE_THRESHOLD` variable from `0.40` down to `0.15`. This allows the nano model to aggressively predict ingredients, catching the carrot successfully.

---

### 🟡 Problem 4: Legacy Code Variable Mismatch

**The Symptoms:**
`llm_services.py` (which houses the old TF-IDF matching engine) was failing to authenticate.

**The Root Cause:**
The original legacy code utilized `os.getenv("GOOGLE_API_KEY")` directly, bypassing the Pydantic settings. However, the development `.env` only contained `GEMINI_API_KEY`.

**The Recommendation:**
Dual-declare your API keys in the environment:
```env
GEMINI_API_KEY=AIzaSy...
GOOGLE_API_KEY=AIzaSy...
```
*(This ensures both modern and legacy code paths can authenticate without refactoring old models).*

---

### 🟡 Problem 5: Gemini "RESOURCE_EXHAUSTED"

**The Symptoms:**
Recipe generation occasionally returning a 429 error and serving fallback template recipes instead of AI recipes.

**The Root Cause:**
Google's Gemini 2.0 Flash free tier has strict RPM (Requests Per Minute) limits. The dual-pipeline nature of our app (Input Refine + Recipe Gen + Nutrition Estimate) burns through tokens and request limits very quickly.

**The Fix:**
No code required. The system is designed with a fallback mechanism that automatically intercepts 429 errors and serves hard-coded, safe recipe backups to ensure the user never experiences an app crash. Scaling to production simply requires swapping the free-tier API key for a paid Google Cloud key.
