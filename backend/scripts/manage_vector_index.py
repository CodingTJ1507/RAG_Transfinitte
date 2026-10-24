import argparse
import json
import logging
import sys
import time

from app.config import settings
from app.core.database import get_chunks_collection

logger = logging.getLogger(__name__)


def _wait_for_index(collection, name: str) -> dict | None:
    deadline = time.monotonic() + settings.SEARCH_INDEX_TIMEOUT_SECONDS
    current = None
    while time.monotonic() < deadline:
        indexes = list(collection.list_search_indexes())
        current = next((item for item in indexes if item.get("name") == name), None)
        if current and (current.get("queryable") or current.get("status") == "READY"):
            return current
        time.sleep(1)
    return current


def _ensure_index(collection, name: str, index_type: str, definition: dict, create: bool) -> dict | None:
    indexes = list(collection.list_search_indexes())
    current = next((item for item in indexes if item.get("name") == name), None)
    if current is None and create:
        collection.create_search_index({
            "name": name,
            "type": index_type,
            "definition": definition,
        })
        current = _wait_for_index(collection, name)
    return current


def _vector_dimensions(index: dict) -> int | None:
    definition = index.get("latestDefinition") or index.get("definition") or {}
    fields = definition.get("fields", [])
    if not isinstance(fields, list):
        return None
    vector = next(
        (
            field for field in fields
            if isinstance(field, dict) and field.get("path") == "embedding"
        ),
        None,
    )
    return vector.get("numDimensions") if isinstance(vector, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create or verify TraceIQ's Atlas Vector Search and BM25 indexes."
    )
    parser.add_argument("--create", action="store_true", help="Create either Atlas index if it is missing.")
    args = parser.parse_args()

    collection = get_chunks_collection()
    vector_definition = {
        "fields": [
            {
                "type": "vector",
                "path": "embedding",
                "numDimensions": settings.EMBEDDING_DIMENSIONS,
                "similarity": "cosine",
            },
            *[
                {"type": "filter", "path": field}
                for field in ("incident_id", "source_type", "version", "timestamp", "owner")
            ],
        ]
    }
    search_definition = {
        "mappings": {
            "dynamic": False,
            "fields": {
                "text": {"type": "string", "analyzer": "lucene.standard"},
                "title": {"type": "string", "analyzer": "lucene.standard"},
                "incident_id": {"type": "token"},
                "source_type": {"type": "token"},
                "version": {"type": "token"},
                "owner": {"type": "token"},
                "timestamp": {"type": "string"},
                "identifiers": {"type": "document", "dynamic": True},
            },
        }
    }
    try:
        vector = _ensure_index(
            collection,
            settings.MONGODB_VECTOR_INDEX,
            "vectorSearch",
            vector_definition,
            args.create,
        )
        search = _ensure_index(
            collection,
            settings.MONGODB_SEARCH_INDEX,
            "search",
            search_definition,
            args.create,
        )
    except Exception:
        logger.exception("Atlas search index management failed")
        print("Failed to inspect or create Atlas indexes. Verify cluster permissions and connectivity.")
        return 1

    missing = [
        name for name, item in (
            (settings.MONGODB_VECTOR_INDEX, vector),
            (settings.MONGODB_SEARCH_INDEX, search),
        )
        if item is None or not item.get("queryable")
    ]
    if missing:
        print(f"Indexes missing or not queryable: {', '.join(missing)}. Run with --create on Atlas.")
        return 1
    actual_dimensions = _vector_dimensions(vector)
    if actual_dimensions != settings.EMBEDDING_DIMENSIONS:
        print(
            f"Vector index dimension is {actual_dimensions}; configured Gemini embeddings use "
            f"{settings.EMBEDDING_DIMENSIONS}. Recreate the index and re-embed all chunks."
        )
        return 1
    print(json.dumps({
        "vector_index": {
            "name": vector.get("name"),
            "type": vector.get("type"),
            "status": vector.get("status"),
            "queryable": vector.get("queryable"),
        },
        "search_index": {
            "name": search.get("name"),
            "type": search.get("type"),
            "status": search.get("status"),
            "queryable": search.get("queryable"),
        },
        "embedding_dimensions_expected": settings.EMBEDDING_DIMENSIONS,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
