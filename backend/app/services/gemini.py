import json
import logging
from typing import Any

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger(__name__)
_client: genai.Client | None = None
IMAGE_PROMPT = (
    "You are reading an image uploaded as incident evidence. Return JSON with "
    "description (3 to 6 sentences: every visible number, time, version, error "
    "code, label and trend; do not guess anything not visible) and visible_text "
    "(every readable line exactly as written, top to bottom)."
)


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
        logger.exception("Gemini JSON generation failed")
        raise RuntimeError("Gemini generation failed; check API configuration and retry") from exc


def describe_image(data: bytes, mime_type: str) -> dict[str, Any]:
    try:
        response = get_gemini_client().models.generate_content(
            model=settings.LLM_MODEL,
            contents=[
                types.Part.from_bytes(data=data, mime_type=mime_type),
                IMAGE_PROMPT,
            ],
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
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
