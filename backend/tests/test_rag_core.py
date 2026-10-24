import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.ingestion.chunking import chunk_document_with_location, chunk_evidence_units
from app.ingestion.parsers import load_manifest, parse_source
from app.models.schemas import Citation, SourceType
from app.retrieval.hybrid_search import reciprocal_rank_fusion
from app.retrieval.vector_search import build_vector_filter
from app.main import app


class DatasetContractTests(unittest.TestCase):
    def test_ground_truth_points_to_canonical_dataset_incident(self):
        backend_root = Path(__file__).resolve().parents[1]
        legacy = json.loads((Path(__file__).parent / "ground_truth.json").read_text(encoding="utf-8"))
        self.assertEqual(legacy["incident_id"], "INC-2026-1042")
        root, manifest = load_manifest(backend_root / "synthetic_data")
        self.assertEqual(manifest["incident_id"], legacy["incident_id"])
        known_sources = {entry["source_id"] for entry in manifest["sources"]}
        questions = json.loads((root / "evaluation" / "questions.json").read_text(encoding="utf-8"))["questions"]
        expected = json.loads((root / "evaluation" / "expected_sources.json").read_text(encoding="utf-8"))["expected_sources"]
        claims = json.loads((root / "metadata" / "claims_ledger.json").read_text(encoding="utf-8"))["claims"]
        answers = json.loads((root / "evaluation" / "answer_key.json").read_text(encoding="utf-8"))["answers"]
        expected_by_id = {item["question_id"]: item for item in expected}
        claims_by_id = {claim["claim_id"]: claim for claim in claims}
        answers_by_id = {answer["question_id"]: answer for answer in answers}

        self.assertEqual(len(questions), 20)
        self.assertEqual(set(expected_by_id), {item["question_id"] for item in questions})
        self.assertEqual(set(answers_by_id), {item["question_id"] for item in questions})
        for question in questions:
            question_id = question["question_id"]
            self.assertTrue(set(question["expected_source_ids"]) <= known_sources, question_id)
            self.assertEqual(question["expected_source_ids"], expected_by_id[question_id]["required_source_ids"])
            self.assertEqual(question["abstention_required"], answers_by_id[question_id]["abstention_required"])
            for claim_id in question["expected_claim_ids"]:
                self.assertIn(claim_id, claims_by_id, question_id)
                self.assertTrue(set(claims_by_id[claim_id]["supporting_source_ids"]) <= known_sources)
        for source in manifest["sources"]:
            parsed = parse_source(root, source)
            self.assertEqual(parsed.source["source_id"], source["source_id"])
            self.assertEqual(parsed.source_hash, source["sha256"])
            self.assertTrue(parsed.units, source["source_id"])


class ChunkingTests(unittest.TestCase):
    def test_chunks_are_deterministic_and_keep_locator(self):
        source = {
            "source_id": "DOC-X",
            "source_type": "document",
            "title": "Example",
            "source_hash": "abc",
            "incident_id": "INC-X",
        }
        unit = {"text": " ".join(f"word{i}" for i in range(20)), "locator": {"page": 4}}
        first = chunk_evidence_units([unit], source, chunk_size=8, overlap=2)
        second = chunk_evidence_units([unit], source, chunk_size=8, overlap=2)
        self.assertGreater(len(first), 1)
        self.assertEqual([item["chunk_id"] for item in first], [item["chunk_id"] for item in second])
        self.assertTrue(all(item["locator"] == {"page": 4} for item in first))
        self.assertTrue(all(item["source_id"] == "DOC-X" for item in first))

    def test_small_evidence_unit_stays_intact_with_locator(self):
        chunks = chunk_document_with_location(
            "A transcript cue is one searchable unit.",
            "TRN-1",
            SourceType.TRANSCRIPT,
            chunk_size=100,
            locator={"cue_id": "cue-1", "start": "00:00:01.000"},
        )
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["locator"]["cue_id"], "cue-1")


class RetrievalLogicTests(unittest.TestCase):
    @staticmethod
    def citation(source_id: str, chunk_id: str) -> Citation:
        return Citation(
            source_id=source_id,
            chunk_id=chunk_id,
            source_type=SourceType.DOCUMENT,
            title=source_id,
            location="Page 1",
            snippet="Evidence",
        )

    def test_rrf_deduplicates_and_rewards_cross_method_results(self):
        shared = self.citation("DOC-1", "chunk-shared")
        vector_only = self.citation("DOC-2", "chunk-vector")
        lexical_only = self.citation("REC-1", "chunk-lexical")
        fused = reciprocal_rank_fusion(
            [[shared, vector_only], [shared, lexical_only]],
            top_k=3,
        )
        self.assertEqual(fused[0].chunk_id, "chunk-shared")
        self.assertEqual(fused[0].metadata["retrieval_methods"], ["lexical", "vector"])
        self.assertEqual(len({citation.chunk_id for citation in fused}), 3)

    def test_vector_filter_builds_expected_metadata_predicates(self):
        actual = build_vector_filter({
            "incident_id": "INC-1",
            "version": "2.4.0",
            "source_types": [SourceType.DOCUMENT, SourceType.TRANSCRIPT],
            "time_range_start": "2026-10-01T00:00:00Z",
        })
        self.assertEqual(actual["$and"][0], {"incident_id": {"$eq": "INC-1"}})
        self.assertEqual(actual["$and"][1], {"version": {"$eq": "2.4.0"}})
        self.assertEqual(actual["$and"][2], {"source_type": {"$in": ["document", "transcript"]}})
        self.assertIn("timestamp", actual["$and"][3])


class ApiContractTests(unittest.TestCase):
    def test_health_route_is_live(self):
        with TestClient(app) as client:
            response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_invalid_investigation_filter_is_rejected_before_services(self):
        with TestClient(app) as client:
            response = client.post("/api/investigate/", json={
                "query": "Find deployment details",
                "time_range_start": "2026-10-24T00:00:00",
            })
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
