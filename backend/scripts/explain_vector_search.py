import argparse
import json
import time
from pathlib import Path
from typing import Any

from app.config import BACKEND_ROOT, settings
from app.core.database import get_chunks_collection, get_db
from app.retrieval.vector_search import vector_search_stage
from app.services.embeddings import embed_query


def _measure(
    chunks: Any,
    db: Any,
    stage: dict[str, Any],
    eval_dir: Path,
    num_candidates: int,
) -> dict[str, Any]:
    pipeline = [stage, {"$project": {"embedding": 0}}]

    t0 = time.perf_counter()
    docs = list(chunks.aggregate(pipeline))
    wall_time_ms = (time.perf_counter() - t0) * 1000.0

    chunk_ids = [doc.get("chunk_id") for doc in docs if doc.get("chunk_id")]

    explain_cmd = {
        "aggregate": settings.MONGODB_CHUNK_COLLECTION,
        "pipeline": pipeline,
        "cursor": {},
    }
    explain_output = db.command("explain", explain_cmd, verbosity="executionStats")

    explain_file = eval_dir / f"explain_{num_candidates}.json"
    explain_file.write_text(json.dumps(explain_output, default=str, indent=2), encoding="utf-8")

    return {
        "num_candidates": num_candidates,
        "wall_time_ms": wall_time_ms,
        "result_count": len(docs),
        "chunk_ids": chunk_ids,
        "explain_file": str(explain_file.relative_to(BACKEND_ROOT)),
    }


def _print_table(
    question: str,
    top_k: int,
    incident_id: str | None,
    rows: list[dict[str, Any]],
) -> None:
    print("\n" + "=" * 80)
    print(f"Vector Search Explain & Tuning (top_k={top_k}, incident={incident_id})")
    print(f"Question: {question}")
    print("=" * 80)
    print(f"{'numCandidates':<15} | {'Time (ms)':<10} | {'Results':<8} | {'Overlap vs Max':<15} | {'Explain JSON'}")
    print("-" * 80)

    for row in rows:
        overlap = row.get("overlap_vs_max", 1.0)
        print(
            f"{row['num_candidates']:<15} | {row['wall_time_ms']:<10.2f} | {row['result_count']:<8} | {overlap:<15.2%} | {row['explain_file']}"
        )
        print(f"  Chunk IDs: {row['chunk_ids']}")

    print("=" * 80 + "\n")


def run_explain_vector_search(
    question: str,
    top_k: int = 10,
    incident_id: str | None = "INC-2026-1042",
    num_candidates_list: list[int] | None = None,
) -> list[dict[str, Any]]:
    candidate_values = num_candidates_list or [150, 300, 600]
    candidate_values = sorted(set(candidate_values))
    filters = {"incident_id": incident_id} if incident_id else None

    print(f"Embedding question: {question!r}")
    vector = embed_query(question)

    eval_dir = BACKEND_ROOT / "eval_results"
    eval_dir.mkdir(parents=True, exist_ok=True)

    db = get_db()
    chunks = get_chunks_collection()

    results_by_candidate: dict[int, dict[str, Any]] = {}
    for num_cand in candidate_values:
        stage = vector_search_stage(vector, top_k, filters, num_candidates=num_cand)
        results_by_candidate[num_cand] = _measure(chunks, db, stage, eval_dir, num_cand)

    largest_candidate = max(candidate_values)
    largest_chunk_ids = set(results_by_candidate[largest_candidate]["chunk_ids"])

    summary_rows = []
    for num_cand in candidate_values:
        info = results_by_candidate[num_cand]
        c_ids = set(info["chunk_ids"])
        overlap = len(c_ids & largest_chunk_ids) / len(largest_chunk_ids) if largest_chunk_ids else 1.0
        info["overlap_vs_max"] = overlap
        summary_rows.append(info)

    _print_table(question, top_k, incident_id, summary_rows)
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explain and tune vector search (numCandidates) with MongoDB explain."
    )
    parser.add_argument("question", type=str, help="Question to search")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results to retrieve (default: 10)")
    parser.add_argument("--incident", type=str, default="INC-2026-1042", help="Incident ID filter")
    parser.add_argument(
        "--num-candidates",
        nargs="+",
        type=int,
        default=[150, 300, 600],
        help="List of numCandidates to test (default: 150 300 600)",
    )
    args = parser.parse_args()

    run_explain_vector_search(
        question=args.question,
        top_k=args.top_k,
        incident_id=args.incident,
        num_candidates_list=args.num_candidates,
    )


if __name__ == "__main__":
    main()
