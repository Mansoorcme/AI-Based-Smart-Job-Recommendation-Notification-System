"""
gemini_client.py — Google Gemini SDK wrapper with model fallback + retry.
"""

import re
import time
from typing import Optional

from google import genai

from config import GEMINI_API_KEY, GEMINI_MODELS   # direct import — no dot prefix

_client: Optional[genai.Client] = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is missing. Add it to backend/.env")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def get_candidate_models() -> list:
    models = list(GEMINI_MODELS)
    try:
        client = _get_client()
        for m in client.models.list():
            name = getattr(m, "name", "") or ""
            if "gemini" not in name.lower():
                continue
            clean = name.split("/", 1)[1] if name.startswith("models/") else name
            if clean and clean not in models:
                models.append(clean)
    except Exception:
        pass
    return [m for m in models if m]


def gemini_generate(prompt: str, max_retries: int = 3) -> str:
    """
    Generate text from Gemini. Tries each model in priority order.
    Handles 429 rate limits with back-off. Raises RuntimeError if all fail.
    """
    client = _get_client()
    candidates = get_candidate_models()
    if not candidates:
        raise RuntimeError("No Gemini models available.")

    last_err = None
    for model_name in candidates:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(model=model_name, contents=prompt)
                return response.text
            except Exception as exc:
                err_str = str(exc)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    delay = 30 * (attempt + 1)
                    hint = re.search(r"retryDelay.*?(\d+)s", err_str)
                    if hint:
                        delay = int(hint.group(1)) + 2
                    time.sleep(delay)
                    last_err = exc
                else:
                    last_err = exc
                    break
    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")
