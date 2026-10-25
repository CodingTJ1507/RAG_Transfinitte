import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.ingestion.parsers import load_manifest
from app.models.schemas import Citation, SourceType
from app.reasoning.investigator import investigate_query

DATASET = Path(__file__).resolve().parents[1] / "synthetic_data"


def demo_entry(source_id: str):
    root, manifest = load_manifest(DATASET)
    return root, next(item for item in manifest["sources"] if item["source_id"] == source_id)


class VerifierFallbackTests(unittest.TestCase):
    def test_answer_survives_verifier_failure(self):
        evidence = [
            Citation(
                source_id="DOC-002",
                chunk_id="c1",
                source_type=SourceType.DOCUMENT,
                title="Spec",
                location="Page 8",
                snippet="PAY-401 means request validation failed (HTTP 422).",
            )
        ]
        answer = {
            "answer": "PAY-401 is a validation error.",
            "likely_root_cause": None,
            "root_cause_chunk_ids": [],
            "is_abstention": False,
            "abstention_reason": None,
            "confidence_explanation": "",
            "claims": [
                {
                    "claim": "PAY-401 is a validation error.",
                    "classification": "confirmed",
                    "chunk_ids": ["c1"],
                }
            ],
            "conflicting_chunk_ids": [],
            "recommended_actions": [],
            "uncertainties": [],
        }
        with patch("app.reasoning.investigator.generate_json", return_value=answer), \
             patch("app.reasoning.investigator.verify_claims", side_effect=RuntimeError("bad reply")):
            report = investigate_query("Is PAY-401 an authentication error?", evidence)
        self.assertFalse(report.is_abstention)
        self.assertEqual(report.claims[0].verification_status, "not_checked")
        self.assertIn("Claims could not be automatically verified.", report.uncertainties)
        self.assertEqual(report.confidence_score, 0.0)
        self.assertEqual(
            report.confidence_explanation,
            "Claims could not be automatically verified; treat them as unchecked.",
        )
