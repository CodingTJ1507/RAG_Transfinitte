import logging
import re
from datetime import datetime
from typing import Any

from app.config import settings
from app.core.database import get_chunks_collection
from app.models.schemas import Citation
from app.retrieval.vector_search import (
    _date_value,
    build_vector_filter,
    citation_from_document,
    perform_vector_search,
)

logger = logging.getLogger(__name__)
RRF_K = 60
IDENTIFIER_PATTERN = re.compile(
    r"\b(?:[A-Z]{2,}(?:-[A-Z0-9]+)+|(?:trc|req|PIPE)-[A-Za-z0-9-]+|"
    r"\d+\.\d+(?:\.\d+)?|HTTP\s+\d{3})\b",
    flags=re.IGNORECASE,
)
IDENTIFIER_FIELDS = (
    "error_code", "request_id", "trace_id", "log_id", "event_id",
    "record_id", "dependency_id", "pipeline_run", "service",
    "service_name", "version", "old_version", "new_version",
    "payment_service_version", "http_status", "order_id",
)


def _atlas_search_filters(filters: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not filters:
        return []
    clauses: list[dict[str, Any]] = []
    for key in ("incident_id", "version", "owner"):
        if filters.get(key):
            clauses.append({"equals": {"path": key, "value": filters[key]}})
    source_types = filters.get("source_types") or filters.get("source_type")
    if source_types:
        if isinstance(source_types, str):
            source_types = [source_types]
        source_types = [getattr(item, "value", item) for item in source_types]
        clauses.append({"in": {"path": "source_type", "value": list(source_types)}})
    time_range: dict[str, datetime] = {}
    for name, operator in (("time_range_start", "gte"), ("time_range_end", "lte")):
        value = filters.get(name)
        if value:
            date_value = _date_value(value)
            if date_value:
                time_range[operator] = date_value
    if time_range:
        clauses.append({"range": {"path": "timestamp", **time_range}})
    return clauses


def perform_lexical_search(
    query: str,
    top_k: int,
    filters: dict[str, Any] | None = None,
) -> list[Citation]:
    if not query.strip():
        return []
    compound: dict[str, list[dict[str, Any]]] = {
        "must": [{
            "text": {
                "query": query,
                "path": ["text", "title", {"wildcard": "identifiers.*"}],
            }
        }]
    }
    search_filters = _atlas_search_filters(filters)
    if search_filters:
        compound["filter"] = search_filters
    pipeline = [
        {"$search": {
            "index": settings.MONGODB_SEARCH_INDEX,
            "compound": compound,
        }},
        {"$limit": top_k},
        {"$addFields": {"retrieval_score": {"$meta": "searchScore"}}},
    ]
    try:
        results = list(get_chunks_collection().aggregate(
            pipeline,
            maxTimeMS=int(settings.REQUEST_TIMEOUT_SECONDS * 1000),
        ))
    except Exception as exc:
        logger.exception("MongoDB Atlas Search BM25 retrieval failed")
        raise RuntimeError(
            "MongoDB Atlas Search retrieval failed; verify the configured search index"
        ) from exc
    return [
        citation_from_document(document, float(document.get("retrieval_score", 0.0)))
        for document in results
    ]


def perform_identifier_search(
    query: str,
    top_k: int,
    filters: dict[str, Any] | None = None,
) -> list[Citation]:
    identifiers = IDENTIFIER_PATTERN.findall(query)
    if not identifiers:
        return []
    exact_terms: list[dict[str, str]] = []
    for identifier in identifiers:
        value = identifier.casefold()
        if value.startswith("http "):
            value = value.split()[-1]
        exact_terms.extend(
            {f"identifiers.{field}": value}
            for field in IDENTIFIER_FIELDS
        )
    clauses: list[dict[str, Any]] = [{"$or": exact_terms}]
    metadata_filter = build_vector_filter(filters)
    if metadata_filter:
        clauses.append(metadata_filter)
    try:
        results = list(
            get_chunks_collection()
            .find({"$and": clauses}, {"_id": 0})
            .limit(top_k)
        )
    except Exception as exc:
        logger.exception("Exact identifier retrieval failed")
        raise RuntimeError(
            "Exact identifier retrieval failed; check MongoDB indexes and connectivity"
        ) from exc
    return [citation_from_document(document, 1.0) for document in results]


def reciprocal_rank_fusion(
    ranked_lists: list[list[Citation]],
    top_k: int,
    rrf_k: int = RRF_K,
    method_names: list[str] | None = None,
) -> list[Citation]:
    if top_k < 1 or rrf_k < 1:
        raise ValueError("top_k and rrf_k must be positive")
    scores: dict[str, float] = {}
    examples: dict[str, Citation] = {}
    methods: dict[str, set[str]] = {}
    names = method_names or ["vector", "lexical", "identifier"]
    for method_index, citations in enumerate(ranked_lists):
        method = names[method_index] if method_index < len(names) else f"query_{method_index}"
        for rank, citation in enumerate(citations, start=1):
            key = citation.chunk_id or f"{citation.source_id}:{citation.location}:{citation.snippet}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            examples.setdefault(key, citation)
            methods.setdefault(key, set()).add(method)
    ordered = sorted(scores, key=lambda key: (-scores[key], key))
    fused: list[Citation] = []
    for key in ordered[:top_k]:
        citation = examples[key].model_copy(deep=True)
        inherited_methods: set[str] = set()
        for ranked_list in ranked_lists:
            for item in ranked_list:
                identity = item.chunk_id or f"{item.source_id}:{item.location}:{item.snippet}"
                if identity == key:
                    inherited_methods.update(item.metadata.get("retrieval_methods", []))
        citation.metadata["retrieval_methods"] = sorted(methods[key] | inherited_methods)
        citation.retrieval_score = scores[key]
        fused.append(citation)
    return fused


def perform_hybrid_search(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    include_diagnostics: bool = False,
) -> list[Citation] | tuple[list[Citation], dict[str, Any]]:
    if not query.strip():
        raise ValueError("Query must not be empty")
    if top_k < 1 or top_k > 100:
        raise ValueError("top_k must be between 1 and 100")
    candidate_limit = min(max(top_k * 3, settings.RETRIEVAL_CANDIDATE_LIMIT), 100)
    vector_results = perform_vector_search(query, candidate_limit, filters)
    lexical_results = perform_lexical_search(query, candidate_limit, filters)
    identifier_results = perform_identifier_search(query, candidate_limit, filters)
    all_candidates = [*vector_results, *lexical_results, *identifier_results]
    fused = reciprocal_rank_fusion(
        [vector_results, lexical_results, identifier_results],
        top_k,
    )
    diagnostics = {
        "vector_candidates": len(vector_results),
        "lexical_candidates": len(lexical_results),
        "identifier_candidates": len(identifier_results),
        "unique_candidates": len({
            citation.chunk_id or f"{citation.source_id}:{citation.location}:{citation.snippet}"
            for citation in all_candidates
        }),
        "final_result_count": len(fused),
        "filters": filters or {},
    }
    return (fused, diagnostics) if include_diagnostics else fused
