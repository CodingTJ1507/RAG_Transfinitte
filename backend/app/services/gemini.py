import json
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)
_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
        raise RuntimeError("GEMINI_API_KEY is not configured")
    if _client is None:
        _client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=int(settings.REQUEST_TIMEOUT_SECONDS * 1000),
            ),
        )
    return _client


def generate_json(system_instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
    import time
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = get_gemini_client().models.generate_content(
                model=settings.LLM_MODEL,
                contents=json.dumps(payload, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
            if not response.text:
                raise ValueError("Gemini returned an empty response")
            result = json.loads(response.text)
            if not isinstance(result, dict):
                raise ValueError("Gemini response must be a JSON object")
            return result
        except Exception as exc:
            err_msg = str(exc)
            if attempt < max_retries - 1 and (
                "timed out" in err_msg.lower()
                or "429" in err_msg
                or "503" in err_msg
                or "unavailable" in err_msg.lower()
                or "high demand" in err_msg.lower()
                or "resource_exhausted" in err_msg.lower()
            ):
                delay = 3 * (attempt + 1)
                logger.warning("Gemini generation transient error (%s); waiting %ds before retry %d/%d...", err_msg[:80], delay, attempt + 1, max_retries)
                time.sleep(delay)
                continue
            logger.exception("Gemini JSON generation failed")
            raise RuntimeError("Gemini generation failed; check API configuration and retry") from exc
