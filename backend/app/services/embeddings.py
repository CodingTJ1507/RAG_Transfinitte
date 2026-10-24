import logging
from collections.abc import Sequence

from google.genai import types

from app.config import settings
from app.services.gemini import call_with_retries, get_gemini_client

logger = logging.getLogger(__name__)


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    clean_texts = [text.strip() for text in texts]
    if any(not text for text in clean_texts):
        raise ValueError("Embedding inputs must be a non-empty sequence of non-empty strings")
    if not clean_texts:
        return []

    client = get_gemini_client()
    vectors: list[list[float]] = []
    for start in range(0, len(clean_texts), settings.EMBEDDING_BATCH_SIZE):
        batch = clean_texts[start:start + settings.EMBEDDING_BATCH_SIZE]
        try:
            response = call_with_retries(
                lambda: client.models.embed_content(
                    model=settings.EMBEDDING_MODEL,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=settings.EMBEDDING_DIMENSIONS,
                    ),
                )
            )
        except Exception as exc:
            logger.exception("Gemini embedding request failed")
            raise RuntimeError("Gemini embedding request failed; check Gemini API configuration and retry") from exc

        if not response.embeddings or len(response.embeddings) != len(batch):
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
    client = get_gemini_client()
    try:
        response = call_with_retries(
            lambda: client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=query.strip(),
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=settings.EMBEDDING_DIMENSIONS,
                ),
            )
        )
    except Exception as exc:
        logger.exception("Gemini query embedding failed")
        raise RuntimeError("Gemini query embedding failed; check Gemini API configuration and retry") from exc

    if not response.embeddings or not response.embeddings[0].values:
        raise RuntimeError("Gemini returned no query embedding")
    vector = response.embeddings[0].values
    if len(vector) != settings.EMBEDDING_DIMENSIONS:
        raise RuntimeError(
            f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSIONS}, received {len(vector)}"
        )
    return vector
