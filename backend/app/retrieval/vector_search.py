import logging
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.core.database import get_chunks_collection, vector_index_status
from app.models.schemas import Citation, SourceType
from app.services.embeddings import embed_query

logger = logging.getLogger(__name__)


def _date_value(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value:
        iso_value = f"{value[:-1]}+00:00" if value.endswith("Z") else value
        try:
            parsed = datetime.fromisoformat(iso_value)
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_vector_filter(filters: dict[str, Any] | None) -> dict[str, Any] | None:
    if not filters:
        return None
    clauses: list[dict[str, Any]] = []
    for key in ("incident_id", "version", "owner"):
        if filters.get(key):
            clauses.append({key: {"$eq": filters[key]}})
    source_types = filters.get("source_types") or filters.get("source_type")
    if source_types:
        if isinstance(source_types, (str, SourceType)):
            source_types = [getattr(source_types, "value", source_types)]
        source_types = [getattr(value, "value", value) for value in source_types]
        clauses.append({"source_type": {"$in": list(source_types)}})
    timestamp_filter: dict[str, datetime] = {}
    if filters.get("time_range_start"):
        start = _date_value(filters["time_range_start"])
        if start:
            timestamp_filter["$gte"] = start
    if filters.get("time_range_end"):
        end = _date_value(filters["time_range_end"])
        if end:
            timestamp_filter["$lte"] = end
    if timestamp_filter:
        clauses.append({"timestamp": timestamp_filter})
    return {"$and": clauses} if len(clauses) > 1 else (clauses[0] if clauses else None)


def citation_from_document(document: dict[str, Any], score: float | None = None) -> Citation:
    source_type = document.get("source_type", "document")
    locator = document.get("locator") or {}
    location_parts = []
    for key, label in (
        ("page", "Page"),
        ("section", "Section"),
        ("cue_id", "Cue"),
        ("start", "Timestamp"),
        ("row_id", "Row"),
        ("event_id", "Event"),
        ("log_id", "Log"),
        ("record_id", "Record"),
        ("dependency_id", "Dependency"),
        ("image", "Image"),
    ):
        value = locator.get(key)
        if value not in (None, ""):
            location_parts.append(f"{label} {value}")
    if locator.get("analysis") == "metadata_only":
        location_parts.append("Image description only; visual content not analyzed")
    location = ", ".join(location_parts) or "Source-level evidence"
    raw_timestamp = document.get("timestamp") or locator.get("timestamp")
    parsed_timestamp = _date_value(raw_timestamp)
    citation_timestamp = (
        parsed_timestamp.isoformat().replace("+00:00", "Z")
        if parsed_timestamp
        else raw_timestamp
    )
    metadata = {
        "incident_id": document.get("incident_id"),
        "owner": document.get("owner"),
        "version": document.get("version"),
        "content_hash": document.get("content_hash"),
        "timestamp": citation_timestamp,
        "locator": locator,
        "services": document.get("metadata", {}).get("services", []),
        "analysis_status": document.get("analysis_status"),
        "retrieval_methods": document.get("retrieval_methods", []),
        "record": document.get("metadata", {}).get("record"),
    }
    return Citation(
        source_id=document["source_id"],
        chunk_id=document.get("chunk_id"),
        source_type=SourceType(source_type),
        title=document.get("title") or document["source_id"],
        location=location,
        snippet=document.get("text", ""),
        metadata=metadata,
        retrieval_score=score,
    )


def vector_search_stage(
    vector: list[float],
    top_k: int,
    filters: dict[str, Any] | None = None,
    num_candidates: int | None = None,
) -> dict[str, Any]:
    candidates = (
        num_candidates
        if num_candidates is not None
        else max(top_k * 15, settings.RETRIEVAL_CANDIDATE_LIMIT)
    )
    vector_filter = build_vector_filter(filters)
    stage: dict[str, Any] = {
        "index": settings.MONGODB_VECTOR_INDEX,
        "path": "embedding",
        "queryVector": vector,
        "numCandidates": candidates,
        "limit": top_k,
    }
    if vector_filter:
        stage["filter"] = vector_filter
    return {"$vectorSearch": stage}


def perform_vector_search(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
) -> list[Citation]:
    if not query.strip():
        raise ValueError("Query must not be empty")
    if top_k < 1 or top_k > 100:
        raise ValueError("top_k must be between 1 and 100")
    index_status = vector_index_status()
    if not index_status["ready"]:
        raise RuntimeError(
            f"MongoDB Atlas Vector Search index '{settings.MONGODB_VECTOR_INDEX}' is unavailable"
        )
    vector = embed_query(query)
    pipeline = [
        vector_search_stage(vector, top_k, filters),
        {"$addFields": {"retrieval_score": {"$meta": "vectorSearchScore"}}},
    ]
    try:
        results = list(get_chunks_collection().aggregate(pipeline, maxTimeMS=int(settings.REQUEST_TIMEOUT_SECONDS * 1000)))
    except Exception as exc:
        logger.exception("Atlas Vector Search failed")
        raise RuntimeError("MongoDB Atlas Vector Search failed; verify index definition and database readiness") from exc
    return [
        citation_from_document(document, float(document["retrieval_score"]))
        for document in results
    ]
