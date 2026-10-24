from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import InvestigationReport, InvestigationRequest
from app.reasoning.investigator import investigate_query
from app.retrieval.hybrid_search import perform_hybrid_search

router = APIRouter()


@router.post("/", response_model=InvestigationReport)
def investigate_incident(req: InvestigationRequest) -> InvestigationReport:
    filters = {
        "incident_id": req.incident_id,
        "source_types": [source_type.value for source_type in req.source_types] if req.source_types else None,
        "time_range_start": req.time_range_start,
        "time_range_end": req.time_range_end,
        "version": req.version,
    }
    filters = {key: value for key, value in filters.items() if value is not None}
    try:
        evidence, diagnostics = perform_hybrid_search(
            req.query,
            top_k=settings.FINAL_EVIDENCE_LIMIT,
            filters=filters,
            include_diagnostics=True,
        )
        return investigate_query(req.query, evidence, diagnostics)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
