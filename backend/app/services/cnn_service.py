"""
CNN SERVICE — INGREDIENT DETECTION FROM IMAGES
===============================================
Status: LIVE — Uses YOLOv8n pretrained model

CONTRACT:
  Input:  Raw image bytes (JPEG/PNG, max 10MB)
  Output: List of detected ingredients with confidence scores

INTEGRATION POINT:
  Called by: POST /api/v1/fridge/scan endpoint (routers/fridge.py)
  Model location: backend/ai_models/yolov8n.pt
"""

from typing import List, Optional
from pydantic import BaseModel
from ultralytics import YOLO
import tempfile
import time
import os
import logging

logger = logging.getLogger(__name__)


# ============ INPUT/OUTPUT CONTRACTS (unchanged) ============

class DetectedIngredient(BaseModel):
    name: str
    confidence: float
    bounding_box: Optional[dict] = None


class CNNScanResponse(BaseModel):
    detected_ingredients: List[DetectedIngredient]
    processing_time_ms: int
    model_version: str


# ============ MODEL LOADING ============

# Path to your model — adjust if your directory is different
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),  # backend/app/services/
    "..", "..",                  # backend/
    "ai_models", "yolov8n.pt"   # backend/ai_models/yolov8n.pt
)
MODEL_PATH = os.path.abspath(MODEL_PATH)

# COCO food class IDs that YOLOv8n can detect
FOOD_CLASSES = {
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot dog",
    53: "pizza",
    54: "donut",
    55: "cake",
}
FOOD_CLASS_IDS = set(FOOD_CLASSES.keys())

# Confidence threshold — lowered to 0.15 to catch more items (nano model struggles sometimes)
CONFIDENCE_THRESHOLD = 0.15

# Load model once at module import
_model = None


def _get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. "
                f"Make sure yolov8n.pt is in backend/ai_models/"
            )
        logger.info(f"Loading YOLOv8 model from {MODEL_PATH}")
        _model = YOLO(MODEL_PATH)
        logger.info("Model loaded successfully")
    return _model


# ============ REAL IMPLEMENTATION ============

async def detect_ingredients_from_image(image_bytes: bytes) -> CNNScanResponse:
    """
    Detect food ingredients from image bytes using YOLOv8n.

    Called by: routers/fridge.py → POST /api/v1/fridge/scan
    Usage:     result = await detect_ingredients_from_image(image_bytes)
    """
    model = _get_model()

    # Write image bytes to a temp file (YOLO needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        # Run inference
        start = time.time()
        results = model(tmp_path, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]
        processing_time = int((time.time() - start) * 1000)

        # Extract food detections
        detected = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            # Only keep food items
            if cls_id not in FOOD_CLASS_IDS:
                continue

            name = FOOD_CLASSES[cls_id]
            coords = box.xyxy[0].tolist()

            detected.append(DetectedIngredient(
                name=name.title(),
                confidence=round(conf, 2),
                bounding_box={
                    "x1": round(coords[0], 1),
                    "y1": round(coords[1], 1),
                    "x2": round(coords[2], 1),
                    "y2": round(coords[3], 1),
                },
            ))

        # Deduplicate — keep highest confidence per ingredient name
        unique = {}
        for d in detected:
            if d.name not in unique or d.confidence > unique[d.name].confidence:
                unique[d.name] = d

        return CNNScanResponse(
            detected_ingredients=list(unique.values()),
            processing_time_ms=processing_time,
            model_version="yolov8n-coco-v1",
        )

    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise

    finally:
        os.unlink(tmp_path)