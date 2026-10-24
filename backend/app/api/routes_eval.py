import json
import logging
from pathlib import Path

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
            expected_sources = expected_by_id[question_id]["required_source_ids"]
            filters = {"incident_id": item.get("incident_id", incident_id)}
            citations = perform_hybrid_search(item["question"], top_k=top_k, filters=filters)
            retrieved = [citation.source_id for citation in citations]
            expected_rank = next(
                (rank for rank, source_id in enumerate(retrieved, start=1) if source_id in expected_sources),
                None,
            )
            found = set(retrieved) & set(expected_sources)
            recall = len(found) / len(expected_sources) if expected_sources else 1.0
            reciprocal_rank = 1 / expected_rank if expected_rank else 0.0
            abstention_expected = bool(item.get("abstention_required"))
            abstained: bool | None = None
            citations_valid: bool | None = None
            answer_evaluated = False
            failures = []
            if not found and expected_sources:
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
                reciprocal_rank=reciprocal_rank,
                hit=bool(found),
                abstention_expected=abstention_expected,
                abstained=abstained,
                citations_valid=citations_valid,
                answer_evaluated=answer_evaluated,
                passed=not failures,
                failure_reasons=failures,
            ))
        count = len(results)
        aggregate = {
            "mean_recall_at_k": sum(result.recall_at_k for result in results) / count if count else 0.0,
            "mean_reciprocal_rank": sum(result.reciprocal_rank for result in results) / count if count else 0.0,
            "hit_rate": sum(result.hit for result in results) / count if count else 0.0,
            "pass_rate": sum(result.passed for result in results) / count if count else 0.0,
        }
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
