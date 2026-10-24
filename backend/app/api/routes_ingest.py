from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.config import settings
from app.models.schemas import IngestionReport, SourceType
from app.services.ingestion import (
    get_ingestion_run,
    ingest_dataset,
    ingest_uploaded_file,
    list_sources,
)

router = APIRouter()


@router.post("/batch", response_model=IngestionReport)
def ingest_evidence_pack(incident_id: str | None = Query(default=None)) -> IngestionReport:
    try:
        return ingest_dataset(incident_id=incident_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/upload")
async def upload_evidence_file(
    file: UploadFile = File(...),
    source_type: SourceType = Form(...),
    incident_id: str | None = Form(default=None),
    owner: str | None = Form(default=None),
) -> dict:
    filename = file.filename or ""
    try:
        content = await file.read(settings.MAX_SOURCE_FILE_BYTES + 1)
        report, source = ingest_uploaded_file(
            filename=filename,
            content=content,
            source_type=source_type,
            incident_id=incident_id,
            owner=owner,
        )
        return {
            "report": report,
            "source": {
                "source_id": source.get("source_id"),
                "title": source.get("title"),
                "source_type": source.get("source_type"),
                "chunk_count": source.get("chunk_count", 0),
                "size_bytes": source.get("size_bytes", len(content)),
                "created_at": source.get("updated_at"),
                "ingestion_status": source.get("ingestion_status"),
            },
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        await file.close()


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
