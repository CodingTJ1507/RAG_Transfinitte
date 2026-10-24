import logging
from collections.abc import Sequence

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your-openai-api-key-here":
        raise RuntimeError("OPENAI_API_KEY is not configured")
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=settings.REQUEST_TIMEOUT_SECONDS)
    return _client


def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    clean_texts = [text.strip() for text in texts]
    if not clean_texts or any(not text for text in clean_texts):
        raise ValueError("Embedding inputs must be a non-empty sequence of non-empty strings")
    client = _get_client()
    vectors: list[list[float]] = []
    for start in range(0, len(clean_texts), settings.EMBEDDING_BATCH_SIZE):
        batch = clean_texts[start:start + settings.EMBEDDING_BATCH_SIZE]
        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
                dimensions=settings.EMBEDDING_DIMENSIONS,
            )
        except Exception as exc:
            logger.exception("Embedding provider request failed")
            raise RuntimeError("Embedding provider request failed; check provider configuration and retry") from exc
        for item in sorted(response.data, key=lambda result: result.index):
            vector = item.embedding
            if len(vector) != settings.EMBEDDING_DIMENSIONS:
                raise RuntimeError(
                    f"Embedding dimension mismatch: expected {settings.EMBEDDING_DIMENSIONS}, received {len(vector)}"
                )
            vectors.append(vector)
    return vectors


def embed_query(query: str) -> list[float]:
    if not query.strip():
        raise ValueError("Query must not be empty")
    return embed_texts([query])[0]
