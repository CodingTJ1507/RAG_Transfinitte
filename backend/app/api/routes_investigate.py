from fastapi import APIRouter, HTTPException

from app.api.errors import QUOTA_MESSAGE, is_quota_error
from app.config import settings
from app.models.schemas import InvestigationReport, InvestigationRequest
from app.reasoning.investigator import investigate_query
from app.reasoning.query_transform import decompose_query
from app.retrieval.hybrid_search import perform_hybrid_search
from app.retrieval.hybrid_search import reciprocal_rank_fusion

router = APIRouter()


@router.post("/", response_model=InvestigationReport)
def investigate_incident(req: InvestigationRequest) -> InvestigationReport:
    filters = {
        "incident_id": req.incident_id,
        "owner": req.owner,
        "source_types": [source_type.value for source_type in req.source_types] if req.source_types else None,
        "time_range_start": req.time_range_start,
        "time_range_end": req.time_range_end,
        "version": req.version,
    }
    filters = {key: value for key, value in filters.items() if value is not None}
    try:
        query_variants = decompose_query(req.query)
        ranked_evidence = []
        search_diagnostics = []
        for query_variant in query_variants:
            evidence, diagnostics = perform_hybrid_search(
                query_variant,
                top_k=settings.FINAL_EVIDENCE_LIMIT,
                filters=filters,
                include_diagnostics=True,
            )
            ranked_evidence.append(evidence)
            search_diagnostics.append(diagnostics)
        evidence = (
            ranked_evidence[0]
            if len(ranked_evidence) == 1
            else reciprocal_rank_fusion(
                ranked_evidence,
                settings.FINAL_EVIDENCE_LIMIT,
                method_names=[
                    "primary_query",
                    *(f"subquery_{index}" for index in range(1, len(ranked_evidence))),
                ],
            )
        )
        diagnostics = {
            "query_variants": query_variants,
            "searches": search_diagnostics,
            "unique_candidates": len({
                citation.chunk_id
                for result_set in ranked_evidence
                for citation in result_set
                if citation.chunk_id
            }),
            "final_result_count": len(evidence),
            "filters": filters,
        }
        return investigate_query(req.query, evidence, diagnostics)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        if is_quota_error(exc):
            raise HTTPException(status_code=429, detail=QUOTA_MESSAGE) from exc
        raise HTTPException(status_code=503, detail=str(exc)) from exc
