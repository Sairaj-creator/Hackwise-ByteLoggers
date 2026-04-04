"""
CNN SERVICE — INGREDIENT DETECTION FROM IMAGES
===============================================
Owner: [Teammate Name]
Status: STUB — returns mock data until real model is integrated

CONTRACT:
  Input:  Raw image bytes (JPEG/PNG, max 10MB, ideally 640x640)
  Output: List of detected ingredients with confidence scores

INTEGRATION POINT:
  Called by: POST /api/v1/fridge/scan endpoint (routers/fridge.py)

REQUIREMENTS FOR REAL IMPLEMENTATION:
  - Model: YOLOv8 fine-tuned on food dataset OR EfficientNet classifier
  - Input preprocessing: Resize to 640x640, normalize RGB
  - Output: Array of { name, confidence, bounding_box }
  - Confidence threshold: Only return items with confidence >= 0.75
  - Latency target: < 3 seconds per image
"""

from typing import List, Optional
from pydantic import BaseModel


# ============ INPUT/OUTPUT CONTRACTS ============

class DetectedIngredient(BaseModel):
    name: str
    confidence: float
    bounding_box: Optional[dict] = None


class CNNScanResponse(BaseModel):
    detected_ingredients: List[DetectedIngredient]
    processing_time_ms: int
    model_version: str


# ============ STUB IMPLEMENTATION ============

async def detect_ingredients_from_image(image_bytes: bytes) -> CNNScanResponse:
    """
    TODO: [TEAMMATE] — Replace this mock with real CNN inference.
    MOCK BEHAVIOR: Returns hardcoded ingredients regardless of image content.
    """
    mock_ingredients = [
        DetectedIngredient(name="Paneer", confidence=0.94),
        DetectedIngredient(name="Bell Pepper", confidence=0.89),
        DetectedIngredient(name="Onion", confidence=0.92),
        DetectedIngredient(name="Tomato", confidence=0.87),
    ]

    return CNNScanResponse(
        detected_ingredients=mock_ingredients,
        processing_time_ms=450,
        model_version="stub-v0.0.1",
    )


# ============ NOTES FOR TEAMMATE ============
#
# 1. The FastAPI endpoint at /fridge/scan will call:
#       result = await detect_ingredients_from_image(image_bytes)
#
# 2. If your model runs on a separate GPU server, change this to an HTTP call:
#       response = await httpx.post("http://cnn-gpu:8001/predict", content=image_bytes)
#
# 3. Error handling: If model fails, raise an exception.
#    The endpoint will catch it and return a fallback message.
