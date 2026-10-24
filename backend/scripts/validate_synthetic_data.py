#!/usr/bin/env python3
"""Validate the reorganized TraceIQ dataset and its evaluation references."""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ingestion.parsers import load_manifest, parse_source


def read_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def validate(dataset_root: Path) -> list[str]:
    errors = []
    try:
        root, manifest = load_manifest(dataset_root)
        sources = manifest["sources"]
        source_ids = [source["source_id"] for source in sources]
        known_sources = set(source_ids)

        if len(source_ids) != len(known_sources):
            errors.append("Manifest contains duplicate source IDs.")
        source_types = Counter(source["source_type"] for source in sources)
        required_types = {"document", "image", "structured", "transcript", "webpage"}
        missing_types = required_types - source_types.keys()
        if missing_types:
            errors.append(f"Manifest is missing source types: {sorted(missing_types)}.")

        for source in sources:
            parsed = parse_source(root, source)
            if parsed.source["source_id"] != source["source_id"] or not parsed.units:
                errors.append(f"Source failed parsing or had no evidence units: {source['source_id']}.")

        questions = read_json(root / "evaluation" / "questions.json")["questions"]
        expected = read_json(root / "evaluation" / "expected_sources.json")["expected_sources"]
        answers = read_json(root / "evaluation" / "answer_key.json")["answers"]
        claims = read_json(root / "metadata" / "claims_ledger.json")["claims"]
        questions_by_id = {item["question_id"]: item for item in questions}
        expected_by_id = {item["question_id"]: item for item in expected}
        answers_by_id = {item["question_id"]: item for item in answers}
        claims_by_id = {item["claim_id"]: item for item in claims}

        if len(questions_by_id) != len(questions):
            errors.append("Evaluation contains duplicate question IDs.")
        if set(questions_by_id) != set(expected_by_id) or set(questions_by_id) != set(answers_by_id):
            errors.append("Questions, expected sources, and answer key IDs do not match.")

        for question_id, question in questions_by_id.items():
            expected_sources = set(question.get("expected_source_ids", []))
            expected_record = expected_by_id.get(question_id)
            answer = answers_by_id.get(question_id)
            if not expected_sources <= known_sources:
                errors.append(f"{question_id} references unknown expected sources.")
            if expected_record and expected_sources != set(expected_record["required_source_ids"]):
                errors.append(f"{question_id} expected source lists disagree.")
            if answer and question.get("abstention_required") != answer.get("abstention_required"):
                errors.append(f"{question_id} abstention requirements disagree.")
            for claim_id in question.get("expected_claim_ids", []):
                claim = claims_by_id.get(claim_id)
                if claim is None:
                    errors.append(f"{question_id} references unknown claim {claim_id}.")
                elif not set(claim["supporting_source_ids"]) <= known_sources:
                    errors.append(f"Claim {claim_id} references unknown sources.")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Dataset validation could not complete: {exc}")

    return errors


def main() -> int:
    dataset_root = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "synthetic_data"
    )
    errors = validate(dataset_root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print(f"[PASS] Dataset files, source parsing, and evaluation references: {dataset_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
