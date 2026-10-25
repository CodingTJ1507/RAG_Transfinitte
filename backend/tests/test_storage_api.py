import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from app.api.errors import QUOTA_MESSAGE, is_quota_error
from app.ingestion.parsers import load_manifest
from app.main import app

DATASET = Path(__file__).resolve().parents[1] / "synthetic_data"


def demo_entry(source_id: str):
    root, manifest = load_manifest(DATASET)
    return root, next(item for item in manifest["sources"] if item["source_id"] == source_id)


def quota_runtime_error() -> RuntimeError:
    try:
        try:
            raise genai_errors.ClientError(
                429,
                {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED"}},
            )
        except genai_errors.ClientError as inner:
            raise RuntimeError("Gemini query embedding failed") from inner
    except RuntimeError as outer:
        return outer


class QuotaTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_quota_is_detected(self):
        self.assertTrue(is_quota_error(quota_runtime_error()))
        self.assertFalse(is_quota_error(RuntimeError("MongoDB is unavailable")))
        self.assertFalse(is_quota_error(None))

    def test_investigate_returns_429(self):
        with patch("app.api.routes_investigate.perform_hybrid_search", side_effect=quota_runtime_error()):
            response = self.client.post(
                "/api/investigate/",
                json={"query": "Is PAY-401 an auth error?", "incident_id": "INC-2026-1042"},
            )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], QUOTA_MESSAGE)

    def test_investigate_other_runtime_error_returns_503(self):
        with patch("app.api.routes_investigate.perform_hybrid_search", side_effect=RuntimeError("Database down")):
            response = self.client.post(
                "/api/investigate/",
                json={"query": "Is PAY-401 an auth error?", "incident_id": "INC-2026-1042"},
            )
        self.assertEqual(response.status_code, 503)

    def test_upload_returns_429_on_quota(self):
        with patch("app.api.routes_ingest.run_in_threadpool", side_effect=quota_runtime_error()):
            response = self.client.post(
                "/api/ingest/upload",
                data={"source_type": "document"},
                files={"file": ("test.txt", b"hello world", "text/plain")},
            )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], QUOTA_MESSAGE)

    def test_batch_returns_429_on_quota(self):
        with patch("app.api.routes_ingest.ingest_dataset", side_effect=quota_runtime_error()):
            response = self.client.post("/api/ingest/batch")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json()["detail"], QUOTA_MESSAGE)
