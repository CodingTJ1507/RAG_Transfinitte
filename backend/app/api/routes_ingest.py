from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import IngestionReport
from app.services.ingestion import get_ingestion_run, ingest_dataset, list_sources

router = APIRouter()


@router.post("/batch", response_model=IngestionReport)
def ingest_evidence_pack() -> IngestionReport:
    try:
        return ingest_dataset()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/sources")
def list_ingested_sources(incident_id: str | None = Query(default=None)) -> dict:
    try:
        sources = list_sources(incident_id)
        return {"count": len(sources), "sources": sources}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/runs/{run_id}")
def ingestion_status(run_id: str) -> dict:
    try:
        run = get_ingestion_run(run_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion run not found")
    return run
