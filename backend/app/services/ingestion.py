import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pymongo import ReplaceOne

from app.config import settings
from app.core.database import get_collection, get_chunks_collection, get_sources_collection, initialize_indexes
from app.ingestion.chunking import chunk_evidence_units
from app.ingestion.parsers import load_manifest, parse_source
from app.models.schemas import IngestionReport
from app.services.embeddings import embed_texts

logger = logging.getLogger(__name__)


def _stored_source_type(source_type: str) -> str:
    return "structured_record" if source_type == "structured" else source_type


def ingest_dataset() -> IngestionReport:
    root, manifest = load_manifest()
    source_entries = manifest["sources"]
    run_id = str(uuid4())
    sources = get_sources_collection()
    chunks_collection = get_chunks_collection()
    runs_collection = get_collection("ingestion_runs")
    initialize_indexes()

    created = updated = skipped = processed = chunk_count = structured_count = 0
    failures: list[dict[str, str]] = []
    for entry in source_entries:
        source_id = str(entry.get("source_id", ""))
        try:
            parsed = parse_source(root, entry)
            source = parsed.source
            source["source_type"] = _stored_source_type(str(source["source_type"]))
            existing = sources.find_one({"source_id": source_id}, {"source_hash": 1})
            if existing and existing.get("source_hash") == parsed.source_hash:
                skipped += 1
                processed += 1
                continue

            prepared = chunk_evidence_units(parsed.units, source)
            if not prepared:
                raise ValueError("Source contains no indexable evidence")
            vectors = embed_texts([chunk["text"] for chunk in prepared])
            for chunk, vector in zip(prepared, vectors, strict=True):
                chunk["embedding"] = vector
                chunk["source_type"] = _stored_source_type(chunk["source_type"])
                chunk["updated_at"] = datetime.now(timezone.utc)
            chunks_collection.bulk_write([
                ReplaceOne({"chunk_id": chunk["chunk_id"]}, chunk, upsert=True)
                for chunk in prepared
            ], ordered=True)

            source["ingestion_status"] = "indexed"
            source["chunk_count"] = len(prepared)
            source["updated_at"] = datetime.now(timezone.utc)
            sources.replace_one({"source_id": source_id}, source, upsert=True)
            chunks_collection.delete_many({
                "source_id": source_id,
                "source_hash": {"$ne": parsed.source_hash},
            })
            processed += 1
            chunk_count += len(prepared)
            structured_count += len(prepared) if source["source_type"] == "structured_record" else 0
            if existing:
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
    runs_collection.insert_one({
        **report.model_dump(mode="json"),
        "created_at": datetime.now(timezone.utc),
    })
    return report


def list_sources(incident_id: str | None = None) -> list[dict[str, Any]]:
    query = {"incident_id": incident_id} if incident_id else {}
    records = get_sources_collection().find(query, {"_id": 0}).sort("source_id", 1)
    return list(records)


def get_ingestion_run(run_id: str) -> dict[str, Any] | None:
    record = get_collection("ingestion_runs").find_one({"run_id": run_id}, {"_id": 0})
    return record
