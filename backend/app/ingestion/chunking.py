import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


def _to_utc_datetime(value: Any) -> datetime | None:
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


def _split_text(text: str, size: int, overlap: int) -> list[tuple[str, int]]:
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=size,
        chunk_overlap=overlap,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [
        (document.page_content, int(document.metadata["start_index"]))
        for document in splitter.create_documents([text])
    ]


def chunk_evidence_units(
    units: list[dict[str, Any]],
    source: dict[str, Any],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[dict[str, Any]]:
    size = chunk_size or settings.CHUNK_SIZE
    overlap_size = settings.CHUNK_OVERLAP if overlap is None else overlap
    if size <= 0 or overlap_size < 0 or overlap_size >= size:
        raise ValueError("Chunk size must be positive and overlap must be in [0, chunk_size)")

    results: list[dict[str, Any]] = []
    source_id = source["source_id"]
    service_owners = settings.service_owner_map
    for unit_index, unit in enumerate(units):
        text = re.sub(r"\s+", " ", str(unit.get("text", ""))).strip()
        if not text:
            continue
        unit_metadata = unit.get("metadata") or {}
        record = unit_metadata.get("record", {})
        owner = source.get("owner")
        if isinstance(record, dict):
            record_service = record.get("service") or record.get("client_service")
            if record_service:
                owner = (
                    service_owners.get(record_service, "Unassigned")
                    if isinstance(record_service, str)
                    else "Unassigned"
                )
        identifiers: dict[str, list[str]] = {}
        identifier_fields = {
            "error_code", "request_id", "trace_id", "log_id", "event_id",
            "record_id", "dependency_id", "pipeline_run", "service",
            "service_name", "version", "old_version", "new_version",
            "payment_service_version", "http_status", "order_id",
        }
        if isinstance(record, dict):
            for field in identifier_fields:
                value = record.get(field)
                if value is None:
                    continue
                values = value if isinstance(value, list) else [value]
                identifiers[field] = [str(item).casefold() for item in values if item is not None]
        identifiers.setdefault("version", []).append(str(source.get("version", "")).casefold())
        for service in source.get("services", []):
            identifiers.setdefault("service", []).append(str(service).casefold())
        pieces = _split_text(text, size, overlap_size)
        for piece_index, (piece, start_index) in enumerate(pieces):
            locator = dict(unit.get("locator") or {})
            content_hash = hashlib.sha256(piece.encode("utf-8")).hexdigest()
            chunk_identity = (
                f"{source_id}:{source.get('source_hash', '')}:"
                f"{json.dumps(locator, sort_keys=True, default=str)}:{piece_index}:{content_hash}"
            )
            chunk_id = str(uuid5(NAMESPACE_URL, chunk_identity))
            timestamp = locator.get("timestamp") or source.get("created_at")
            if source.get("source_type") == "transcript" and locator.get("start") and source.get("recording_start"):
                recording_start = _to_utc_datetime(source["recording_start"])
                cue_time = locator["start"].replace(",", ".")
                hours, minutes, seconds = cue_time.split(":")
                if recording_start:
                    timestamp = recording_start + timedelta(
                        hours=int(hours), minutes=int(minutes), seconds=float(seconds)
                    )
            timestamp = _to_utc_datetime(timestamp)
            results.append({
                "chunk_id": chunk_id,
                "source_id": source_id,
                "source_type": source["source_type"],
                "title": source.get("title", source_id),
                "text": piece,
                "content_hash": content_hash,
                "chunk_index": piece_index,
                "start_index": start_index,
                "locator": locator,
                "incident_id": source.get("incident_id"),
                "owner": owner,
                "version": source.get("version"),
                "timestamp": timestamp,
                "source_hash": source.get("source_hash"),
                "metadata": {
                    **unit_metadata,
                    "services": source.get("services", []),
                    "tags": source.get("tags", []),
                    "created_at": source.get("created_at"),
                    "recording_start": source.get("recording_start"),
                },
                "identifiers": identifiers,
                "embedding": None,
            })
    return results


def chunk_document_with_location(
    content: str,
    source_id: str,
    source_type: Any,
    chunk_size: int = 500,
    locator: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    value = getattr(source_type, "value", source_type)
    source = {
        "source_id": source_id,
        "source_type": value,
        "title": source_id,
        "source_hash": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
    return chunk_evidence_units(
        [{"text": content, "locator": locator or {}, "metadata": metadata or {}}],
        source,
        chunk_size=chunk_size,
        overlap=min(settings.CHUNK_OVERLAP, max(0, chunk_size - 1)),
    )
