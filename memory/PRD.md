# AI Recipe Generator - Product Requirements Document

## Overview
AI-powered recipe generator mobile app that turns available ingredients into delicious meals using Gemini AI.

## Tech Stack
- **Frontend**: React Native (Expo SDK 54) with expo-router
- **Backend**: FastAPI (Python) with async/await
- **Database**: MongoDB (via Motor async driver)
- **AI**: Gemini 2.5 Flash via emergentintegrations library (Emergent LLM Key)
- **Auth**: JWT-based (bcrypt + PyJWT)

## Architecture
- 2-stage AI pipeline: Gemini refines ingredients → Generates structured recipe JSON
- Custom model slot available for future recipe prediction model swap
- Bearer token auth stored in AsyncStorage on mobile

## Core Features (MVP)
1. **Authentication**: JWT register/login, profile management (allergies, dietary prefs)
2. **Fridge Management**: Add/edit/delete ingredients with expiry tracking (fresh/warning/critical/expired)
3. **AI Recipe Generation**: Gemini-powered with cuisine, diet, spice, servings preferences
4. **Recipe Detail**: Full recipe view with ingredients, steps, nutrition, tips
5. **Cooking Mode**: Dark immersive UI, step-by-step cards, per-step timers, keep-awake
6. **Favorites**: Save/unsave recipes

## Navigation
- Tab bar: Home | Fridge | Generate | Favorites | Profile
- Stack screens: Recipe Detail, Cooking Mode
- Auth screens: Login, Register
- Onboarding: Landing page

## Design System
- Theme: Organic & Earthy (light, warm)
- Colors: Orange CTAs (#EA580C), Green fresh (#16A34A), Amber warning (#D97706), Red critical (#DC2626)
- Typography: Black (900) for headings, medium for body
- Radius: Cards rounded-3xl, Buttons rounded-full

## API Endpoints
### Auth: /api/auth/register, /api/auth/login, /api/auth/me, /api/auth/profile, /api/auth/refresh
### Fridge: /api/fridge, /api/fridge/manual, /api/fridge/{item_id}
### Recipes: /api/recipes/generate, /api/recipes/my, /api/recipes/{recipe_id}, /api/recipes/{recipe_id}/cook, /api/recipes/{recipe_id}/favorite, /api/recipes/favorites

## Future Enhancements (from Master Prompt)
- Camera ingredient scanning (CNN/YOLOv8)
- Allergy Guardian middleware
- Smart Meal Planner (weekly AI-generated plans)
- Food Waste Tracker with gamification
- Social features (community feed, likes, trends)
- WebSocket real-time trending recipes
- Voice input (Whisper STT)
- Multi-language support
