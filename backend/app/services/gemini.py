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
IMAGE_PROMPT = (
    "You are reading an image uploaded as incident evidence. Return JSON with "
    "description (3 to 6 sentences: every visible number, time, version, error "
    "code, label and trend; do not guess anything not visible) and visible_text "
    "(every readable line exactly as written, top to bottom)."
)
# Without a schema the model may return visible_text as one string instead of a list of lines.
IMAGE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "description": types.Schema(type=types.Type.STRING),
        "visible_text": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
    },
    required=["description", "visible_text"],
)

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
            retryable = code in (429, 500, 503, 504) or isinstance(exc, httpx.TimeoutException)
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


def describe_image(data: bytes, mime_type: str) -> dict[str, Any]:
    try:
        response = call_with_retries(lambda: get_gemini_client().models.generate_content(
            model=settings.LLM_MODEL,
            contents=[
                types.Part.from_bytes(data=data, mime_type=mime_type),
                IMAGE_PROMPT,
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                response_schema=IMAGE_SCHEMA,
            ),
        ))
        if not response.text:
            raise ValueError("Gemini returned an empty image description")
        result = json.loads(response.text)
        if not isinstance(result, dict):
            raise ValueError("Gemini image response must be a JSON object")
        description = result.get("description", "")
        visible_text = result.get("visible_text", [])
        if not isinstance(description, str) or not isinstance(visible_text, list) or any(
            not isinstance(line, str) for line in visible_text
        ):
            raise ValueError("Gemini image response has invalid field types")
        return {"description": description, "visible_text": visible_text}
    except Exception as exc:
        logger.exception("Gemini image reading failed")
        raise RuntimeError("Gemini image reading failed") from exc
