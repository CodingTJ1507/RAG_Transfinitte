import argparse
import json
import sys
import time

from app.config import settings
from app.core.database import get_chunks_collection


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or verify TraceIQ's MongoDB Atlas Vector Search index.")
    parser.add_argument("--create", action="store_true", help="Create the vector index if it is missing.")
    args = parser.parse_args()

    collection = get_chunks_collection()
    expected_name = settings.MONGODB_VECTOR_INDEX
    indexes = list(collection.list_search_indexes())
    current = next((item for item in indexes if item.get("name") == expected_name), None)
    if current is None and args.create:
        definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": settings.EMBEDDING_DIMENSIONS,
                    "similarity": "cosine",
                },
                *[
                    {"type": "filter", "path": field}
                    for field in ("incident_id", "source_type", "version", "timestamp")
                ],
            ]
        }
        model = {
            "name": expected_name,
            "type": "vectorSearch",
            "definition": definition,
        }
        collection.create_search_index(model)
        deadline = time.monotonic() + settings.REQUEST_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            indexes = list(collection.list_search_indexes())
            current = next((item for item in indexes if item.get("name") == expected_name), None)
            if current and current.get("queryable"):
                break
            time.sleep(1)

    if current is None:
        print(f"Vector index '{expected_name}' is missing. Run with --create on MongoDB Atlas.")
        return 1
    if current.get("queryable") is False:
        print(f"Vector index '{expected_name}' exists but is not queryable yet.")
        return 1
    print(json.dumps({
        "name": current.get("name"),
        "type": current.get("type"),
        "status": current.get("status"),
        "queryable": current.get("queryable"),
        "embedding_dimensions_expected": settings.EMBEDDING_DIMENSIONS,
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
