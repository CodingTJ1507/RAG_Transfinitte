import argparse
import time
from pathlib import Path
from typing import Any

from bson import json_util

from app.config import settings
from app.core.database import get_chunks_collection, get_db
from app.retrieval.vector_search import vector_search_stage
from app.services.embeddings import embed_query


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Atlas Vector Search candidate counts using executionStats."
    )
    parser.add_argument("question", help="Question to embed and search")
    parser.add_argument("--top-k", type=_positive_int, default=10)
    parser.add_argument("--incident", help="Restrict results to one incident ID")
    parser.add_argument(
        "--num-candidates",
        type=_positive_int,
        nargs="+",
        default=[150, 300, 600],
        help="One or more candidate counts to compare (default: 150 300 600)",
    )
    args = parser.parse_args()
    if args.top_k > 100:
        parser.error("--top-k must be between 1 and 100")
    if any(value < args.top_k for value in args.num_candidates):
        parser.error("each --num-candidates value must be greater than or equal to --top-k")
    if len(set(args.num_candidates)) != len(args.num_candidates):
        parser.error("--num-candidates values must be unique")
    return args


def _run(question: str, top_k: int, incident: str | None, candidates: list[int]) -> int:
    vector = embed_query(question)
    filters = {"incident_id": incident} if incident else None
    collection = get_chunks_collection()
    explain_dir = Path(__file__).resolve().parents[1] / "eval_results"
    explain_dir.mkdir(parents=True, exist_ok=True)
    results_by_candidate: dict[int, tuple[list[dict[str, Any]], float]] = {}

    for num_candidates in candidates:
        stage = vector_search_stage(vector, top_k, filters, num_candidates)
        explain_command = {
            "aggregate": settings.MONGODB_CHUNK_COLLECTION,
            "pipeline": [stage, {"$project": {"embedding": 0}}],
            "cursor": {},
        }
        explain = get_db().command(
            "explain",
            explain_command,
            verbosity="executionStats",
        )
        explain_path = explain_dir / f"explain_{num_candidates}.json"
        explain_path.write_text(json_util.dumps(explain, indent=2), encoding="utf-8")

        pipeline = [
            stage,
            {"$addFields": {"retrieval_score": {"$meta": "vectorSearchScore"}}},
        ]
        start = time.perf_counter()
        results = list(collection.aggregate(
            pipeline,
            maxTimeMS=int(settings.REQUEST_TIMEOUT_SECONDS * 1000),
        ))
        elapsed_ms = (time.perf_counter() - start) * 1000
        results_by_candidate[num_candidates] = (results, elapsed_ms)

    largest_results = results_by_candidate[max(candidates)][0]
    largest_ids = {item.get("chunk_id") for item in largest_results}
    largest_ids.discard(None)
    print("numCandidates | wall_time_ms | result_count | overlap_with_largest | chunk_ids")
    for num_candidates in candidates:
        results, elapsed_ms = results_by_candidate[num_candidates]
        chunk_ids = [item.get("chunk_id") for item in results]
        result_ids = {chunk_id for chunk_id in chunk_ids if chunk_id is not None}
        overlap = (
            len(result_ids & largest_ids) / len(largest_ids)
            if largest_ids
            else 1.0
        )
        print(
            f"{num_candidates} | {elapsed_ms:.2f} | {len(results)} | "
            f"{overlap:.4f} | {chunk_ids}"
        )
        print(f"Saved explain output: {explain_dir / f'explain_{num_candidates}.json'}")
    return 0


def main() -> int:
    args = _parse_args()
    return _run(args.question, args.top_k, args.incident, args.num_candidates)


if __name__ == "__main__":
    raise SystemExit(main())
