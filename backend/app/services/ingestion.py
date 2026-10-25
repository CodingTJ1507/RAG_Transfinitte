import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from bson import ObjectId
from bson.errors import InvalidId
from gridfs.errors import NoFile
from pymongo import UpdateOne
from pymongo.errors import DuplicateKeyError

from app.config import BACKEND_ROOT, settings
from app.core.database import (
    ensure_indexes,
    ensure_retrieval_indexes,
    get_collection,
    get_chunks_collection,
    get_originals_bucket,
    get_sources_collection,
    initialize_indexes,
)
from app.ingestion.chunking import chunk_evidence_units
from app.ingestion.parsers import (
    _safe_source_path,
    _source_hash,
    load_manifest,
    parse_source,
)
from app.models.schemas import IngestionReport, SourceType
from app.services.embeddings import embed_texts

logger = logging.getLogger(__name__)
UPLOAD_ROOT = BACKEND_ROOT / "uploads"
SUPPORTED_UPLOADS = {
    ".pdf": SourceType.DOCUMENT,
    ".docx": SourceType.DOCUMENT,
    ".md": SourceType.DOCUMENT,
    ".html": SourceType.WEBPAGE,
    ".htm": SourceType.WEBPAGE,
    ".vtt": SourceType.TRANSCRIPT,
    ".txt": SourceType.TRANSCRIPT,
    ".json": SourceType.STRUCTURED_RECORD,
    ".csv": SourceType.STRUCTURED_RECORD,
    ".png": SourceType.IMAGE,
    ".jpg": SourceType.IMAGE,
    ".jpeg": SourceType.IMAGE,
    ".webp": SourceType.IMAGE,
}


CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


def _store_original(path: Path, source_id: str, incident_id: str, source_hash: str) -> str:
    bucket = get_originals_bucket()
    existing = bucket.find_one({"metadata.sha256": source_hash})
    if existing:
        return str(existing._id)
    content_type = CONTENT_TYPES.get(path.suffix.lower(), "text/plain; charset=utf-8")
    file_id = bucket.put(
        path.read_bytes(),
        filename=path.name,
        metadata={
            "source_id": source_id,
            "incident_id": incident_id,
            "sha256": source_hash,
            "content_type": content_type,
        },
    )
    return str(file_id)


def _stored_source_type(source_type: str) -> str:
    return "structured_record" if source_type == "structured" else source_type


def _index_source(root: Path, entry: dict[str, Any]) -> tuple[str, int, int]:
    source_id = str(entry.get("source_id", ""))
    path = _safe_source_path(root, entry["file_path"])
    source_hash = _source_hash(path, entry.get("sha256"))
    incident_id = str(entry.get("incident_id") or "")

    file_id = _store_original(path, source_id, incident_id, source_hash)

    existing = get_sources_collection().find_one(
        {"source_id": source_id},
        {"_id": 0, "source_hash": 1, "ingestion_status": 1, "chunk_count": 1, "file_id": 1},
    )
    if (
        existing
        and existing.get("source_hash") == source_hash
        and existing.get("ingestion_status") == "indexed"
        and existing.get("chunk_count", 0) > 0
    ):
        if not existing.get("file_id"):
            get_sources_collection().update_one(
                {"source_id": source_id},
                {"$set": {"file_id": file_id}},
            )
        return "skipped", 0, 0

    parsed = parse_source(root, entry)
    source = parsed.source
    source["source_type"] = _stored_source_type(str(source["source_type"]))
    sources = get_sources_collection()
    chunks_collection = get_chunks_collection()

    prepared = chunk_evidence_units(parsed.units, source)
    if not prepared:
        raise ValueError("Source contains no indexable evidence")
    chunk_ids = [chunk["chunk_id"] for chunk in prepared]
    existing_chunks = list(chunks_collection.find(
        {"source_id": source_id, "chunk_id": {"$in": chunk_ids}},
        {"_id": 0, "chunk_id": 1, "source_hash": 1},
    ))
    indexed_by_id = {chunk["chunk_id"]: chunk for chunk in existing_chunks}
    if all(
        indexed_by_id.get(chunk_id, {}).get("source_hash") == parsed.source_hash
        for chunk_id in chunk_ids
    ):
        sources.update_one(
            {"source_id": source_id},
            {"$set": {
                **source,
                "file_id": file_id,
                "ingestion_status": "indexed",
                "chunk_count": len(prepared),
            }},
            upsert=True,
        )
        return "skipped", 0, 0

    missing_chunks = [
        chunk for chunk in prepared
        if indexed_by_id.get(chunk["chunk_id"], {}).get("source_hash") != parsed.source_hash
    ]
    vectors = embed_texts([
        f"title: {chunk['title']} | text: {chunk['text']}"
        for chunk in missing_chunks
    ])
    updated_at = datetime.now(timezone.utc)
    for chunk, vector in zip(missing_chunks, vectors, strict=True):
        chunk["embedding"] = vector
        chunk["source_type"] = _stored_source_type(chunk["source_type"])
        chunk["updated_at"] = updated_at
    operations = [
        UpdateOne(
            {"source_id": chunk["source_id"], "chunk_id": chunk["chunk_id"]},
            {
                "$set": chunk,
                "$setOnInsert": {"created_at": updated_at},
            },
            upsert=True,
        )
        for chunk in missing_chunks
    ]
    try:
        if operations:
            chunks_collection.bulk_write(operations, ordered=True)
    except DuplicateKeyError:
        logger.info("Concurrent ingestion created chunks for source %s; retrying upserts", source_id)
        chunks_collection.bulk_write([
            UpdateOne(
                {"source_id": chunk["source_id"], "chunk_id": chunk["chunk_id"]},
                {"$set": chunk},
                upsert=False,
            )
            for chunk in missing_chunks
        ], ordered=True)

    source["ingestion_status"] = "indexed"
    source["chunk_count"] = len(prepared)
    source["updated_at"] = updated_at
    source["file_id"] = file_id
    sources.replace_one({"source_id": source_id}, source, upsert=True)
    chunks_collection.delete_many({
        "source_id": source_id,
        "chunk_id": {"$nin": chunk_ids},
    })
    return (
        "updated" if indexed_by_id else "created",
        len(missing_chunks),
        len(missing_chunks) if source["source_type"] == "structured_record" else 0,
    )


def _record_run(report: IngestionReport) -> None:
    get_collection("ingestion_runs").insert_one({
        **report.model_dump(mode="json"),
        "created_at": datetime.now(timezone.utc),
    })


def ingest_dataset(incident_id: str | None = None) -> IngestionReport:
    root, manifest = load_manifest()
    source_entries = [
        entry for entry in manifest["sources"]
        if incident_id is None or entry.get("incident_id", manifest.get("incident_id")) == incident_id
    ]
    if incident_id and not source_entries:
        raise ValueError(f"No dataset sources found for incident '{incident_id}'")
    run_id = str(uuid4())
    initialize_indexes()
    ensure_retrieval_indexes()

    created = updated = skipped = processed = chunk_count = structured_count = 0
    failures: list[dict[str, str]] = []
    for entry in source_entries:
        source_id = str(entry.get("source_id", ""))
        try:
            source_status, source_chunks, source_structured = _index_source(root, entry)
            if source_status == "skipped":
                skipped += 1
                processed += 1
                continue
            processed += 1
            chunk_count += source_chunks
            structured_count += source_structured
            if source_status == "updated":
                updated += 1
            else:
                created += 1
        except Exception as exc:
            logger.exception("Dataset source ingestion failed for %s", source_id or "unknown")
            failures.append({"source_id": source_id or "unknown", "error": str(exc)})

    status = "failed" if failures and processed == 0 else ("partial" if failures else "completed")
    report = IngestionReport(
        run_id=run_id,
        status=status,
        discovered_sources=len(source_entries),
        processed_sources=processed,
        created_sources=created,
        updated_sources=updated,
        skipped_sources=skipped,
        failed_sources=failures,
        chunks_created=chunk_count,
        structured_records_processed=structured_count,
    )
    _record_run(report)
    return report


def ingest_uploaded_file(
    filename: str,
    content: bytes,
    source_type: SourceType,
    incident_id: str | None = None,
    owner: str | None = None,
) -> tuple[IngestionReport, dict[str, Any]]:
    safe_name = Path(filename).name
    suffix = Path(safe_name).suffix.lower()
    if not safe_name or suffix not in SUPPORTED_UPLOADS:
        raise ValueError(f"Unsupported uploaded file format: {suffix or 'unknown'}")
    if not content:
        raise ValueError("Uploaded file is empty")
    if len(content) > settings.MAX_SOURCE_FILE_BYTES:
        raise ValueError("Uploaded file exceeds MAX_SOURCE_FILE_BYTES")
    if source_type != SUPPORTED_UPLOADS[suffix]:
        raise ValueError(f"File format {suffix} is not compatible with source type {source_type.value}")

    source_hash = hashlib.sha256(content).hexdigest()
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    stored_path = UPLOAD_ROOT / f"{source_hash}{suffix}"
    if not stored_path.exists():
        stored_path.write_bytes(content)
    source_identity = f"{incident_id or 'INC-USER-UPLOAD'}:{owner or ''}:{source_hash}"
    source_id = f"UPL-{hashlib.sha256(source_identity.encode('utf-8')).hexdigest()[:24]}"
    source_entry = {
        "source_id": source_id,
        "title": safe_name,
        "source_type": "structured" if source_type == SourceType.STRUCTURED_RECORD else source_type.value,
        "format": suffix.lstrip("."),
        "file_path": stored_path.name,
        "sha256": source_hash,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "incident_id": incident_id or "INC-USER-UPLOAD",
        "owner": owner,
        "services": [],
        "tags": ["user-upload"],
        "synthetic": False,
    }
    initialize_indexes()
    ensure_retrieval_indexes()
    run_id = str(uuid4())
    source_status, chunk_count, structured_count = _index_source(UPLOAD_ROOT, source_entry)
    report = IngestionReport(
        run_id=run_id,
        status="completed",
        discovered_sources=1,
        processed_sources=1,
        created_sources=int(source_status == "created"),
        updated_sources=int(source_status == "updated"),
        skipped_sources=int(source_status == "skipped"),
        chunks_created=chunk_count,
        structured_records_processed=structured_count,
    )
    _record_run(report)
    source_record = get_sources_collection().find_one({"source_id": source_id}, {"_id": 0}) or {}
    return report, source_record


def list_sources(incident_id: str | None = None) -> list[dict[str, Any]]:
    query = {"incident_id": incident_id} if incident_id else {}
    records = get_sources_collection().find(query, {"_id": 0}).sort("source_id", 1)
    return list(records)


def get_source_original(source_id: str) -> tuple[bytes, str, str] | None:
    source = get_sources_collection().find_one(
        {"source_id": source_id},
        {"_id": 0, "file_id": 1, "title": 1, "file_path": 1},
    )
    if not source or not source.get("file_id"):
        return None
    try:
        bucket = get_originals_bucket()
        grid_out = bucket.get(ObjectId(str(source["file_id"])))
        data = grid_out.read()
        metadata = getattr(grid_out, "metadata", {}) or {}
        content_type = metadata.get("content_type") or "application/octet-stream"
        filename = getattr(grid_out, "filename", None) or Path(source.get("file_path", "original")).name
        return data, content_type, filename
    except (InvalidId, NoFile):
        return None
    except Exception as exc:
        logger.exception("Failed to retrieve original file for source %s", source_id)
        raise RuntimeError(f"Failed to retrieve original file for source {source_id}") from exc


def get_ingestion_run(run_id: str) -> dict[str, Any] | None:
    record = get_collection("ingestion_runs").find_one({"run_id": run_id}, {"_id": 0})
    return record
