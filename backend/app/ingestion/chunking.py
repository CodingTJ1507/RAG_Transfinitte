import hashlib
import json
import re
from datetime import timedelta
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.retrieval.vector_search import _date_value


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


def _chunk_owner(record: Any, source_owner: str | None, service_owners: dict[str, str]) -> str | None:
    """A record belongs to its own service's team; any other unit to the source owner."""
    service = (record.get("service") or record.get("client_service")) if isinstance(record, dict) else None
    if not service:
        return source_owner
    return service_owners.get(service, "Unassigned") if isinstance(service, str) else "Unassigned"


def _cue_offset(start: str) -> timedelta | None:
    """WebVTT cue start, 'hh:mm:ss.ttt' or 'mm:ss.ttt', as an offset from the recording start."""
    parts = start.replace(",", ".").split(":")
    if not 2 <= len(parts) <= 3:
        return None
    hours, minutes, seconds = ["0"] * (3 - len(parts)) + parts
    try:
        return timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))
    except ValueError:
        return None


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
        owner = _chunk_owner(record, source.get("owner"), service_owners)
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
            timestamp = _date_value(locator.get("timestamp")) or _date_value(source.get("created_at"))
            if source.get("source_type") == "transcript" and locator.get("start"):
                recording_start = _date_value(source.get("recording_start"))
                offset = _cue_offset(str(locator["start"]))
                if recording_start and offset is not None:
                    timestamp = recording_start + offset
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
