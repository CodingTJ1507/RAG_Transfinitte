import re

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.api.errors import QUOTA_MESSAGE, is_quota_error
from app.config import settings
from app.core.database import SearchIndexNotReadyError
from app.models.schemas import IngestionReport, SourceType
from app.services.ingestion import (
    get_ingestion_run,
    get_source_original,
    ingest_dataset,
    ingest_uploaded_file,
    list_sources,
)

router = APIRouter()
INDEXES_BUILDING = "Search indexes are still building. Try again in a minute."
DEPENDENCY_TIMEOUT = "A database or AI request timed out. Try again."


def _timeout_error(exc: TimeoutError) -> HTTPException:
    detail = INDEXES_BUILDING if isinstance(exc, SearchIndexNotReadyError) else DEPENDENCY_TIMEOUT
    return HTTPException(status_code=503, detail=detail)


@router.post("/batch", response_model=IngestionReport)
def ingest_evidence_pack(incident_id: str | None = Query(default=None)) -> IngestionReport:
    try:
        return ingest_dataset(incident_id=incident_id)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise _timeout_error(exc) from exc
    except RuntimeError as exc:
        if is_quota_error(exc):
            raise HTTPException(status_code=429, detail=QUOTA_MESSAGE) from exc
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
        # Parsing, embedding and index waits block; keep them off the event loop.
        report, source = await run_in_threadpool(
            ingest_uploaded_file,
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
    except TimeoutError as exc:
        raise _timeout_error(exc) from exc
    except RuntimeError as exc:
        if is_quota_error(exc):
            raise HTTPException(status_code=429, detail=QUOTA_MESSAGE) from exc
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


@router.get("/sources/{source_id}/original")
def download_original_source(source_id: str) -> Response:
    try:
        result = get_source_original(source_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Original file not found")
        data, content_type, filename = result
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename) or "original"
        return Response(
            content=data,
            media_type=content_type,
            headers={
                "X-Content-Type-Options": "nosniff",
                "Content-Disposition": f'inline; filename="{safe_name}"',
            },
        )
    except HTTPException:
        raise
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
