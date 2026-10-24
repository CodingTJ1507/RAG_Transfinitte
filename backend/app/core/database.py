import logging
from typing import Any

from pymongo import ASCENDING, MongoClient, TEXT
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
    sources.create_index([("source_id", ASCENDING)], unique=True)
    sources.create_index([("incident_id", ASCENDING), ("source_type", ASCENDING)])
    chunks.create_index([("chunk_id", ASCENDING)], unique=True)
    chunks.create_index([("source_id", ASCENDING), ("source_hash", ASCENDING)])
    chunks.create_index([
        ("incident_id", ASCENDING),
        ("source_type", ASCENDING),
        ("version", ASCENDING),
        ("timestamp", ASCENDING),
    ])
    for identifier_field in (
        "error_code", "request_id", "trace_id", "log_id", "event_id",
        "record_id", "dependency_id", "pipeline_run", "service",
        "http_status", "order_id",
    ):
        chunks.create_index(
            [(f"identifiers.{identifier_field}", ASCENDING)],
            name=f"identifier_{identifier_field}",
        )
    chunks.create_index([("text", TEXT), ("title", TEXT)], name="traceiq_lexical_text")


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
