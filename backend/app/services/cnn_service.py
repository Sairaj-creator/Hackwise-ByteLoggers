"""
Ingredient detection service.

Primary path:
- Gemini 2.5 Flash multimodal ingredient detection

Fallback path:
- Local YOLOv8 COCO model for common produce classes
"""

from __future__ import annotations

import io
import logging
import os
import time
from functools import lru_cache
from typing import List

from pydantic import BaseModel, ConfigDict, Field

from app.services.gemini_common import generate_content_text, parse_json_payload

logger = logging.getLogger("uvicorn.error")

try:
    from PIL import Image
except Exception:  # pragma: no cover - handled at runtime
    Image = None

try:
    from ultralytics import YOLO
except Exception:  # pragma: no cover - handled at runtime
    YOLO = None


class DetectedIngredient(BaseModel):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)


class CNNScanResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    detected_ingredients: List[DetectedIngredient]
    processing_time_ms: int
    model_version: str


MODEL_PATHS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "ai_models", "yolov8n.pt")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "ai_models", "yolov8n.pt")),
]

YOLO_FOOD_CLASSES = {
    46: "banana",
    47: "apple",
    49: "orange",
    50: "broccoli",
    51: "carrot",
}

VISION_PROMPT = """
Identify all visible food ingredients in this image.
Return ONLY a valid JSON array like:
[{"name":"tomato","confidence":0.92}]

Rules:
- Use simple lowercase ingredient names.
- Include only edible ingredients or produce, not cookware or packaging.
- If an item is a prepared dish, name its main visible ingredient if clear; otherwise omit it.
- Confidence must be between 0.0 and 1.0.
- No markdown, no commentary.
""".strip()


def _normalize_name(name: str) -> str:
    cleaned = (name or "").strip().lower()
    replacements = {
        "bell peppers": "bell pepper",
        "capsicum": "bell pepper",
        "tomatoes": "tomato",
        "onions": "onion",
        "potatoes": "potato",
        "chilies": "chili",
        "chillies": "chili",
    }
    return replacements.get(cleaned, cleaned)


def _dedupe(ingredients: List[DetectedIngredient]) -> List[DetectedIngredient]:
    by_name: dict[str, DetectedIngredient] = {}
    for ingredient in ingredients:
        existing = by_name.get(ingredient.name)
        if existing is None or ingredient.confidence > existing.confidence:
            by_name[ingredient.name] = ingredient
    return sorted(by_name.values(), key=lambda item: item.confidence, reverse=True)


@lru_cache(maxsize=1)
def _get_yolo_model():
    if YOLO is None:
        return None

    for path in MODEL_PATHS:
        if os.path.exists(path):
            logger.info("Loading YOLO vision fallback from %s", path)
            return YOLO(path)
    return None


async def _detect_with_gemini(image_bytes: bytes) -> List[DetectedIngredient]:
    if Image is None:
        raise RuntimeError("Pillow is not installed")

    image = Image.open(io.BytesIO(image_bytes))
    raw_text = await generate_content_text(VISION_PROMPT, model_name="gemini-2.5-flash", media=image)
    items = parse_json_payload(raw_text, prefer_array=True)

    detected: List[DetectedIngredient] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or "name" not in item:
            continue
        name = _normalize_name(str(item.get("name", "")))
        if not name:
            continue
        try:
            confidence = float(item.get("confidence", 0.8))
        except (TypeError, ValueError):
            confidence = 0.8
        detected.append(
            DetectedIngredient(
                name=name,
                confidence=max(0.0, min(1.0, confidence)),
            )
        )
    return _dedupe(detected)


async def _detect_with_yolo(image_bytes: bytes) -> List[DetectedIngredient]:
    model = _get_yolo_model()
    if model is None:
        return []

    import tempfile

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            temp_path = tmp.name

        results = model(temp_path, conf=0.15, verbose=False)[0]
        detected: List[DetectedIngredient] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in YOLO_FOOD_CLASSES:
                continue
            detected.append(
                DetectedIngredient(
                    name=YOLO_FOOD_CLASSES[cls_id],
                    confidence=max(0.0, min(1.0, float(box.conf[0]))),
                )
            )
        return _dedupe(detected)
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                logger.debug("Failed to remove temp image %s", temp_path)


async def detect_ingredients_from_image(image_bytes: bytes) -> CNNScanResponse:
    start = time.perf_counter()

    try:
        detected = await _detect_with_gemini(image_bytes)
        if detected:
            return CNNScanResponse(
                detected_ingredients=detected,
                processing_time_ms=int((time.perf_counter() - start) * 1000),
                model_version="gemini-2.5-flash-vision-mvp",
            )
    except Exception as exc:
        logger.warning("Gemini vision ingredient detection failed: %s", exc)

    try:
        detected = await _detect_with_yolo(image_bytes)
        return CNNScanResponse(
            detected_ingredients=detected,
            processing_time_ms=int((time.perf_counter() - start) * 1000),
            model_version="yolov8n-coco-fallback",
        )
    except Exception as exc:
        logger.warning("YOLO fallback ingredient detection failed: %s", exc)
        return CNNScanResponse(
            detected_ingredients=[],
            processing_time_ms=int((time.perf_counter() - start) * 1000),
            model_version="ingredient-detection-empty-fallback",
        )
