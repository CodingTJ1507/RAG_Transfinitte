import logging
from collections.abc import Sequence

from google.genai import types

from app.config import settings
from app.services.gemini import get_gemini_client

logger = logging.getLogger(__name__)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    clean_texts = [text.strip() for text in texts]
    if any(not text for text in clean_texts):
        raise ValueError("Embedding inputs must be a non-empty sequence of non-empty strings")
    if not clean_texts:
        return []

    client = get_gemini_client()
    vectors: list[list[float]] = []
    max_retries = 5
    for start in range(0, len(clean_texts), settings.EMBEDDING_BATCH_SIZE):
        batch = clean_texts[start:start + settings.EMBEDDING_BATCH_SIZE]
        response = None
        for attempt in range(max_retries):
            try:
                response = client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=settings.EMBEDDING_DIMENSIONS,
                    ),
                )
                break
            except Exception as exc:
                err_msg = str(exc)
                if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper() or "quota" in err_msg.lower()) and attempt < max_retries - 1:
                    import re
                    import time
                    match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+)", err_msg)
                    delay = int(match.group(1)) + 2 if match else min(10 * (attempt + 1), 45)
                    logger.warning("Gemini rate limit reached; waiting %ds before retry %d/%d...", delay, attempt + 1, max_retries)
                    time.sleep(delay)
                    continue
                logger.exception("Gemini embedding request failed")
                raise RuntimeError("Gemini embedding request failed; check Gemini API configuration and retry") from exc

        if response is None or not response.embeddings or len(response.embeddings) != len(batch):
            raise RuntimeError("Gemini returned an incomplete embedding batch")
        for item in response.embeddings:
            vector = item.values or []
            if len(vector) != settings.EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSIONS}, received {len(vector)}"
                )
            vectors.append(vector)
    return vectors


def embed_query(query: str) -> list[float]:
    if not query.strip():
        raise ValueError("Query must not be empty")
    max_retries = 5
    response = None
    client = get_gemini_client()
    for attempt in range(max_retries):
        try:
            response = client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=query.strip(),
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=settings.EMBEDDING_DIMENSIONS,
                ),
            )
            break
        except Exception as exc:
            err_msg = str(exc)
            if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg.upper() or "quota" in err_msg.lower()) and attempt < max_retries - 1:
                import re
                import time
                match = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+)", err_msg)
                delay = int(match.group(1)) + 2 if match else min(5 * (attempt + 1), 25)
                logger.warning("Gemini query embedding rate limited; waiting %ds before retry %d/%d...", delay, attempt + 1, max_retries)
                time.sleep(delay)
                continue
            logger.exception("Gemini query embedding failed")
            raise RuntimeError("Gemini query embedding failed; check Gemini API configuration and retry") from exc

    if response is None or not response.embeddings or not response.embeddings[0].values:
        raise RuntimeError("Gemini returned no query embedding")
    vector = response.embeddings[0].values
    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSIONS}, received {len(vector)}"
        )
    return vector
