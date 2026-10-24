import logging
import re
from typing import Any

from app.config import settings
from app.core.database import get_chunks_collection
from app.models.schemas import Citation
from app.retrieval.vector_search import build_vector_filter, citation_from_document, perform_vector_search

logger = logging.getLogger(__name__)
RRF_K = 60


def _lexical_filter(query: str, filters: dict[str, Any] | None) -> dict[str, Any]:
    clauses: list[dict[str, Any]] = []
    metadata_filter = build_vector_filter(filters)
    if metadata_filter:
        clauses.append(metadata_filter)

    identifiers = re.findall(
        r"\b(?:[A-Z]{2,}(?:-[A-Z0-9]+)+|(?:trc|req|PIPE)-[A-Za-z0-9-]+|"
        r"\d+\.\d+(?:\.\d+)?|HTTP\s+\d{3})\b",
        query,
        flags=re.IGNORECASE,
    )
    if identifiers:
        exact_terms = []
        for identifier in identifiers:
            normalized = identifier.casefold()
            fields = [
                "error_code", "request_id", "trace_id", "log_id", "event_id",
                "record_id", "dependency_id", "pipeline_run", "service",
                "service_name", "version", "old_version", "new_version",
                "payment_service_version", "http_status", "order_id",
            ]
            value = normalized.split()[-1] if normalized.startswith("http ") else normalized
            exact_terms.extend(
                {f"identifiers.{field}": value}
                for field in fields
            )
            exact_terms.append({"text": {"$regex": re.escape(identifier), "$options": "i"}})
            exact_terms.append({"title": {"$regex": re.escape(identifier), "$options": "i"}})
        clauses.append({"$or": exact_terms})
    else:
        # MongoDB text search is token-based; exact identifiers are handled above.
        terms = [term for term in re.findall(r"[A-Za-z0-9_]+", query) if len(term) > 2]
        if terms:
            clauses.append({"$text": {"$search": " ".join(terms)}})
    if not clauses:
        return {}
    return {"$and": clauses} if len(clauses) > 1 else clauses[0]


def perform_lexical_search(
    query: str,
    top_k: int,
    filters: dict[str, Any] | None = None,
) -> list[Citation]:
    query_filter = _lexical_filter(query, filters)
    if not query_filter:
        return []
    projection = {"_id": 0}
    if "$text" in str(query_filter):
        projection["lexical_score"] = {"$meta": "textScore"}
    try:
        cursor = (
            get_chunks_collection()
            .find(query_filter, projection)
            .limit(top_k)
        )
        if "$text" in str(query_filter):
            cursor = cursor.sort([("lexical_score", {"$meta": "textScore"})])
        results = list(cursor)
    except Exception as exc:
        logger.exception("MongoDB lexical retrieval failed")
        raise RuntimeError("MongoDB lexical retrieval failed; verify indexes and database readiness") from exc
    return [
        citation_from_document(document, float(document.get("lexical_score", 0.0)))
        for document in results
    ]


def reciprocal_rank_fusion(
    ranked_lists: list[list[Citation]],
    top_k: int,
    rrf_k: int = RRF_K,
) -> list[Citation]:
    if top_k < 1 or rrf_k < 1:
        raise ValueError("top_k and rrf_k must be positive")
    scores: dict[str, float] = {}
    examples: dict[str, Citation] = {}
    methods: dict[str, set[str]] = {}
    for method_index, citations in enumerate(ranked_lists):
        method = "vector" if method_index == 0 else "lexical"
        for rank, citation in enumerate(citations, start=1):
            key = citation.chunk_id or f"{citation.source_id}:{citation.location}:{citation.snippet}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + rank)
            examples.setdefault(key, citation)
            methods.setdefault(key, set()).add(method)
    ordered = sorted(scores, key=lambda key: (-scores[key], key))
    fused: list[Citation] = []
    for key in ordered[:top_k]:
        citation = examples[key].model_copy(deep=True)
        citation.metadata["retrieval_methods"] = sorted(methods[key])
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
    fused = reciprocal_rank_fusion([vector_results, lexical_results], top_k)
    diagnostics = {
        "vector_candidates": len(vector_results),
        "lexical_candidates": len(lexical_results),
        "unique_candidates": len({
            citation.chunk_id or f"{citation.source_id}:{citation.location}:{citation.snippet}"
            for citation in [*vector_results, *lexical_results]
        }),
        "final_result_count": len(fused),
        "filters": filters or {},
    }
    return (fused, diagnostics) if include_diagnostics else fused
