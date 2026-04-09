"""
Shared Gemini helpers for backend AI services.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import warnings
from functools import lru_cache
from typing import Any

from app.config import get_settings

logger = logging.getLogger("uvicorn.error")

try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        import google.generativeai as genai
except Exception:  # pragma: no cover - handled at runtime
    genai = None


_CONFIGURED_API_KEY: str | None = None


def _clean_api_key(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned or cleaned.startswith("placeholder_"):
        return None
    return cleaned


def get_gemini_api_key() -> str | None:
    settings = get_settings()
    return (
        _clean_api_key(getattr(settings, "GEMINI_API_KEY", None))
        or _clean_api_key(getattr(settings, "GOOGLE_API_KEY", None))
        or _clean_api_key(os.getenv("GEMINI_API_KEY"))
        or _clean_api_key(os.getenv("GOOGLE_API_KEY"))
    )


def is_gemini_configured() -> bool:
    return bool(genai and get_gemini_api_key())


def configure_gemini() -> bool:
    global _CONFIGURED_API_KEY

    api_key = get_gemini_api_key()
    if not genai or not api_key:
        return False

    if _CONFIGURED_API_KEY != api_key:
        genai.configure(api_key=api_key)
        _CONFIGURED_API_KEY = api_key
    return True


@lru_cache(maxsize=8)
def get_model(model_name: str):
    if not configure_gemini():
        raise RuntimeError("Gemini API key is not configured")
    return genai.GenerativeModel(model_name)


async def generate_content_text(prompt: str, *, model_name: str = "gemini-2.5-flash", media: Any = None) -> str:
    model = get_model(model_name)
    parts = [prompt]
    if media is not None:
        parts.append(media)

    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, lambda: model.generate_content(parts if media is not None else prompt))
    return (getattr(response, "text", "") or "").strip()


def strip_code_fences(text: str) -> str:
    cleaned = (text or "").strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
    return cleaned


def extract_json_block(text: str, *, prefer_array: bool = False) -> str:
    cleaned = strip_code_fences(text)
    patterns = [r"\[[\s\S]*\]", r"\{[\s\S]*\}"] if prefer_array else [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]

    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return match.group(0)
    return cleaned


def parse_json_payload(text: str, *, prefer_array: bool = False) -> Any:
    payload = extract_json_block(text, prefer_array=prefer_array)
    return json.loads(payload)
