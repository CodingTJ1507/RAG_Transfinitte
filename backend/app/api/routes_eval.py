import json
import logging
import math
from pathlib import Path
from typing import TypedDict

from fastapi import APIRouter, HTTPException, Query

from app.config import settings
from app.models.schemas import (
    EvaluationCaseResult,
    EvaluationReport,
    InvestigationRequest,
)
from app.reasoning.investigator import investigate_query
from app.retrieval.hybrid_search import perform_hybrid_search

logger = logging.getLogger(__name__)
router = APIRouter()


class RetrievalMetrics(TypedDict):
    retrieved_source_ids: list[str]
    recall_at_k: float
    precision_at_k: float
    ndcg_at_k: float
    reciprocal_rank: float
    hit: bool


def retrieval_metrics(
    retrieved_source_ids: list[str],
    expected_source_ids: list[str],
    top_k: int,
) -> RetrievalMetrics:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    ranked = list(dict.fromkeys(retrieved_source_ids))[:top_k]
    relevant = list(dict.fromkeys(expected_source_ids))
    relevant_set = set(relevant)
    found = set(ranked) & relevant_set
    reciprocal_rank = next(
        (1 / rank for rank, source_id in enumerate(ranked, start=1) if source_id in relevant_set),
        0.0,
    )
    dcg = sum(
        1 / math.log2(rank + 1)
        for rank, source_id in enumerate(ranked, start=1)
        if source_id in relevant_set
    )
    ideal_dcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, min(len(relevant), top_k) + 1)
    )
    return {
        "retrieved_source_ids": ranked,
        "recall_at_k": len(found) / len(relevant) if relevant else 1.0,
        "precision_at_k": len(found) / top_k,
        "ndcg_at_k": dcg / ideal_dcg if ideal_dcg else 0.0,
        "reciprocal_rank": reciprocal_rank,
        "hit": bool(found),
    }


def _load_evaluation_files() -> tuple[list[dict], dict[str, dict], str]:
    evaluation_dir = settings.dataset_path / "evaluation"
    questions_path = evaluation_dir / "questions.json"
    expected_path = evaluation_dir / "expected_sources.json"
    if not questions_path.is_file() or not expected_path.is_file():
        raise FileNotFoundError("Dataset evaluation questions or expected sources are missing")
    question_document = json.loads(questions_path.read_text(encoding="utf-8"))
    questions = question_document["questions"]
    expected = json.loads(expected_path.read_text(encoding="utf-8"))["expected_sources"]
    return questions, {item["question_id"]: item for item in expected}, question_document["incident_id"]


@router.get("/benchmark", response_model=EvaluationReport)
def run_benchmark(
    question_ids: list[str] | None = Query(default=None),
    top_k: int = Query(default=10, ge=1, le=50),
    generate_answers: bool = Query(default=False),
) -> EvaluationReport:
    try:
        questions, expected_by_id, incident_id = _load_evaluation_files()
        if question_ids:
            requested = set(question_ids)
            questions = [item for item in questions if item["question_id"] in requested]
            missing = requested - {item["question_id"] for item in questions}
            if missing:
                raise HTTPException(status_code=404, detail=f"Unknown question IDs: {sorted(missing)}")

        results: list[EvaluationCaseResult] = []
        for item in questions:
            question_id = item["question_id"]
            expected_sources = list(dict.fromkeys(expected_by_id[question_id]["required_source_ids"]))
            filters = {"incident_id": item.get("incident_id", incident_id)}
            citations = perform_hybrid_search(item["question"], top_k=top_k, filters=filters)
            metrics = retrieval_metrics(
                [citation.source_id for citation in citations],
                expected_sources,
                top_k,
            )
            retrieved = metrics["retrieved_source_ids"]
            recall = metrics["recall_at_k"]
            abstention_expected = bool(item.get("abstention_required"))
            abstained: bool | None = None
            citations_valid: bool | None = None
            faithfulness: float | None = None
            answer_evaluated = False
            failures = []
            if not metrics["hit"] and expected_sources:
                failures.append("No required expected source was retrieved")

            if generate_answers:
                report = investigate_query(
                    item["question"],
                    citations,
                    {"benchmark_question_id": question_id},
                )
                abstained = report.is_abstention
                citations_valid = all(
                    citation.chunk_id and citation.chunk_id in {item.chunk_id for item in citations}
                    for citation in [*report.supporting_evidence, *report.conflicting_evidence]
                )
                factual_claims = [
                    claim for claim in report.claims
                    if claim.classification != "unknown"
                ]
                faithfulness = (
                    sum(claim.verification_status == "verified" for claim in factual_claims)
                    / len(factual_claims)
                    if factual_claims
                    else 1.0 if report.is_abstention else 0.0
                )
                answer_evaluated = True
                if abstained != abstention_expected:
                    failures.append("Abstention behavior did not match expected behavior")
                if not citations_valid:
                    failures.append("Response contains a citation not present in retrieved evidence")
            results.append(EvaluationCaseResult(
                question_id=question_id,
                category=item["category"],
                expected_source_ids=expected_sources,
                retrieved_source_ids=retrieved,
                recall_at_k=recall,
                precision_at_k=metrics["precision_at_k"],
                ndcg_at_k=metrics["ndcg_at_k"],
                reciprocal_rank=metrics["reciprocal_rank"],
                hit=metrics["hit"],
                abstention_expected=abstention_expected,
                abstained=abstained,
                citations_valid=citations_valid,
                faithfulness=faithfulness,
                answer_evaluated=answer_evaluated,
                passed=not failures,
                failure_reasons=failures,
            ))
        count = len(results)
        aggregate = {
            "mean_recall_at_k": sum(result.recall_at_k for result in results) / count if count else 0.0,
            "mean_reciprocal_rank": sum(result.reciprocal_rank for result in results) / count if count else 0.0,
            "hit_rate": sum(result.hit for result in results) / count if count else 0.0,
            "mean_precision_at_k": sum(result.precision_at_k for result in results) / count if count else 0.0,
            "mean_ndcg_at_k": sum(result.ndcg_at_k for result in results) / count if count else 0.0,
            "pass_rate": sum(result.passed for result in results) / count if count else 0.0,
        }
        evaluated_answers = [result.faithfulness for result in results if result.faithfulness is not None]
        if evaluated_answers:
            aggregate["mean_faithfulness"] = sum(evaluated_answers) / len(evaluated_answers)
        return EvaluationReport(
            status="completed" if count else "no_cases",
            cases_run=count,
            aggregate=aggregate,
            results=results,
        )
    except HTTPException:
        raise
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=f"Evaluation data is invalid: {exc}") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
