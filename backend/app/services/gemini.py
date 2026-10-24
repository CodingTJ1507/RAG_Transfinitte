import json
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

import httpx
from google import genai
from google.genai import errors, types

from app.config import settings

logger = logging.getLogger(__name__)
_client: genai.Client | None = None

T = TypeVar("T")


def get_gemini_client() -> genai.Client:
    global _client
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
        raise RuntimeError("GEMINI_API_KEY is not configured")
    if _client is None:
        _client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=int(settings.GEMINI_TIMEOUT_SECONDS * 1000),
            ),
        )
    return _client


def call_with_retries(call: Callable[[], T]) -> T:
    deadline = time.monotonic() + settings.GEMINI_RETRY_BUDGET_SECONDS
    for attempt in range(settings.GEMINI_MAX_RETRIES + 1):
        try:
            return call()
        except (errors.APIError, httpx.TimeoutException) as exc:
            code = getattr(exc, "code", None)
            retryable = code in (429, 500, 503) or isinstance(exc, httpx.TimeoutException)
            delay = min(float(2 ** attempt), settings.GEMINI_MAX_BACKOFF_SECONDS)
            if not retryable or attempt == settings.GEMINI_MAX_RETRIES or time.monotonic() + delay > deadline:
                raise
            logger.warning(
                "Gemini request retryable error (attempt %d/%d, code=%s): %s; retrying in %.1fs...",
                attempt + 1,
                settings.GEMINI_MAX_RETRIES,
                code,
                exc,
                delay,
            )
            time.sleep(delay)


def generate_json(system_instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
    def _invoke() -> dict[str, Any]:
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

    try:
        return call_with_retries(_invoke)
    except Exception as exc:
        logger.exception("Gemini JSON generation failed")
        raise RuntimeError("Gemini generation failed; check API configuration and retry") from exc
