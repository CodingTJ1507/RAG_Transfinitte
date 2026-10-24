import logging
import json
import time
from typing import Any
from pathlib import Path

from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import settings

logger = logging.getLogger(__name__)
_client: MongoClient[dict[str, Any]] | None = None
_database: Database[dict[str, Any]] | None = None


def get_db() -> Database[dict[str, Any]]:
    global _client, _database
    if _database is None:
        if not settings.MONGODB_URI:
            raise RuntimeError("MONGODB_URI is not configured")
        try:
            _client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=int(settings.REQUEST_TIMEOUT_SECONDS * 1000),
                connectTimeoutMS=int(settings.REQUEST_TIMEOUT_SECONDS * 1000),
                appname="TraceIQ",
            )
            _client.admin.command("ping")
            _database = _client[settings.MONGODB_DATABASE]
            logger.info("Connected to MongoDB database %s", settings.MONGODB_DATABASE)
        except Exception as exc:
            close_database()
            logger.exception("MongoDB connection check failed")
            raise RuntimeError("MongoDB is unavailable; verify MONGODB_URI and network access") from exc
    return _database


def get_collection(name: str) -> Collection[dict[str, Any]]:
    if not name or name.startswith("$"):
        raise ValueError("A valid collection name is required")
    return get_db()[name]


def get_sources_collection() -> Collection[dict[str, Any]]:
    return get_collection(settings.MONGODB_SOURCE_COLLECTION)


def get_chunks_collection() -> Collection[dict[str, Any]]:
    return get_collection(settings.MONGODB_CHUNK_COLLECTION)


def initialize_indexes() -> None:
    sources = get_sources_collection()
    chunks = get_chunks_collection()
    runs = get_collection("ingestion_runs")
    sources.create_index([("source_id", ASCENDING)], unique=True)
    sources.create_index([("incident_id", ASCENDING), ("source_type", ASCENDING)])
    chunks.create_index([("chunk_id", ASCENDING)], unique=True)
    chunks.create_index([("source_id", ASCENDING), ("source_hash", ASCENDING)])
    chunks.create_index([
        ("incident_id", ASCENDING),
        ("source_type", ASCENDING),
        ("version", ASCENDING),
        ("timestamp", ASCENDING),
        ("owner", ASCENDING),
    ])
    for identifier_field in (
        "error_code", "request_id", "trace_id", "log_id", "event_id",
        "record_id", "dependency_id", "pipeline_run", "service",
        "service_name", "version", "old_version", "new_version",
        "payment_service_version", "http_status", "order_id",
    ):
        chunks.create_index(
            [(f"identifiers.{identifier_field}", ASCENDING)],
            name=f"identifier_{identifier_field}",
        )
    runs.create_index([("run_id", ASCENDING)], unique=True)


def search_index_status() -> dict[str, Any]:
    collection = get_chunks_collection()
    try:
        indexes = list(collection.list_search_indexes())
    except Exception as exc:
        logger.exception("Unable to inspect Atlas Search indexes")
        return {"ready": False, "error": "Could not inspect Atlas Search indexes"}
    configured = next((index for index in indexes if index.get("name") == settings.MONGODB_SEARCH_INDEX), None)
    ready = bool(configured) and (
        configured.get("queryable") is True
        or configured.get("status") in {"READY", "ACTIVE"}
    )
    return {
        "ready": ready,
        "configured_index": settings.MONGODB_SEARCH_INDEX,
        "available_indexes": sorted(
            name for name in (index.get("name") for index in indexes) if isinstance(name, str)
        ),
    }


def ensure_indexes(
    index_definitions: list[dict[str, Any]],
    timeout_seconds: float | None = None,
) -> dict[str, dict[str, Any]]:
    collection = get_chunks_collection()
    configured_names = [definition["name"] for definition in index_definitions]
    existing = {
        index.get("name"): index
        for index in collection.list_search_indexes()
        if index.get("name") in configured_names
    }
    pending = [
        definition for definition in index_definitions
        if definition["name"] not in existing
    ]
    if pending:
        for definition in pending:
            collection.create_search_index(definition)

    deadline = time.monotonic() + (
        settings.REQUEST_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    )
    while True:
        existing = {
            index.get("name"): index
            for index in collection.list_search_indexes()
            if index.get("name") in configured_names
        }
        if all(
            existing.get(name, {}).get("queryable") is True
            or existing.get(name, {}).get("status") in {"READY", "ACTIVE"}
            for name in configured_names
        ):
            return existing
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Atlas search indexes did not become ready: {configured_names}"
            )
        time.sleep(1)


def ensure_retrieval_indexes() -> dict[str, dict[str, Any]]:
    scripts_dir = Path(__file__).resolve().parents[2] / "scripts"
    vector_path = scripts_dir / "vector_search_index.json"
    search_path = scripts_dir / "atlas_search_index.json"
    vector_definition = json.loads(vector_path.read_text(encoding="utf-8"))
    search_definition = json.loads(search_path.read_text(encoding="utf-8"))
    vector_definition["name"] = settings.MONGODB_VECTOR_INDEX
    search_definition["name"] = settings.MONGODB_SEARCH_INDEX
    if (
        vector_definition["definition"]["fields"][0]["numDimensions"]
        != settings.EMBEDDING_DIMENSIONS
    ):
        raise ValueError(
            "Vector index definition dimensions do not match configured embedding dimensions"
        )
    indexes = ensure_indexes([vector_definition, search_definition])
    vector_index = indexes[settings.MONGODB_VECTOR_INDEX]
    definition = vector_index.get("latestDefinition") or vector_index.get("definition") or {}
    fields = definition.get("fields", [])
    vector_field = next(
        (
            field for field in fields
            if isinstance(field, dict) and field.get("path") == "embedding"
        ),
        None,
    ) if isinstance(fields, list) else None
    indexed_dimensions = vector_field.get("numDimensions") if vector_field else None
    if indexed_dimensions is not None and indexed_dimensions != settings.EMBEDDING_DIMENSIONS:
        raise ValueError(
            f"Atlas vector index '{settings.MONGODB_VECTOR_INDEX}' uses {indexed_dimensions} "
            f"dimensions, but Gemini is configured for {settings.EMBEDDING_DIMENSIONS}; "
            "recreate the index and re-embed all chunks."
        )
    return indexes


def vector_index_status() -> dict[str, Any]:
    collection = get_chunks_collection()
    try:
        indexes = list(collection.list_search_indexes())
    except Exception as exc:
        logger.exception("Unable to inspect Atlas Search indexes")
        return {"ready": False, "error": "Could not inspect Atlas Vector Search indexes"}
    configured = next((index for index in indexes if index.get("name") == settings.MONGODB_VECTOR_INDEX), None)
    ready = bool(configured) and (
        configured.get("queryable") is True
        or configured.get("status") in {"READY", "ACTIVE"}
    )
    return {
        "ready": ready,
        "configured_index": settings.MONGODB_VECTOR_INDEX,
        "available_indexes": sorted(
            name for name in (index.get("name") for index in indexes) if isinstance(name, str)
        ),
    }


def close_database() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None
