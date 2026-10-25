import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from app.api.errors import QUOTA_MESSAGE, is_quota_error
from app.ingestion.parsers import load_manifest
from app.main import app
from app.services.ingestion import _store_original

DATASET = Path(__file__).resolve().parents[1] / "synthetic_data"


def demo_entry(source_id: str):
    root, manifest = load_manifest(DATASET)
    return root, next(item for item in manifest["sources"] if item["source_id"] == source_id)


class OriginalFileTests(unittest.TestCase):
    def test_route_serves_pdf_inline(self):
        with patch(
            "app.api.routes_ingest.get_source_original",
            return_value=(b"%PDF-1.4 demo", "application/pdf", "spec.pdf"),
        ):
            response = TestClient(app).get("/api/ingest/sources/DOC-002/original")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_route_returns_404_when_missing(self):
        with patch("app.api.routes_ingest.get_source_original", return_value=None):
            self.assertEqual(TestClient(app).get("/api/ingest/sources/NOPE/original").status_code, 404)

    def test_original_is_stored_once(self):
        root, entry = demo_entry("IMG-002")
        bucket = MagicMock()
        bucket.find_one.return_value = None
        with patch("app.services.ingestion.get_originals_bucket", return_value=bucket):
            _store_original(root / entry["file_path"], "IMG-002", "INC-2026-1042", entry["sha256"])
            bucket.find_one.return_value = MagicMock(_id="abc")
            self.assertEqual(
                _store_original(root / entry["file_path"], "IMG-002", "INC-2026-1042", entry["sha256"]),
                "abc",
            )
        bucket.put.assert_called_once()

    def test_html_served_as_text_plain(self):
        root, entry = demo_entry("WEB-001")
        bucket = MagicMock()
        bucket.find_one.return_value = None
        with patch("app.services.ingestion.get_originals_bucket", return_value=bucket):
            _store_original(root / entry["file_path"], "WEB-001", "INC-2026-1042", entry["sha256"])
        _, kwargs = bucket.put.call_args
        self.assertEqual(kwargs["metadata"]["content_type"], "text/plain; charset=utf-8")

    def test_route_runtime_error_returns_503(self):
        with patch("app.api.routes_ingest.get_source_original", side_effect=RuntimeError("GridFS down")):
            response = TestClient(app).get("/api/ingest/sources/DOC-002/original")
        self.assertEqual(response.status_code, 503)

    def test_safe_filename_header(self):
        with patch(
            "app.api.routes_ingest.get_source_original",
            return_value=(b"hello", "text/plain; charset=utf-8", "unsafe name; @#$!.txt"),
        ):
            response = TestClient(app).get("/api/ingest/sources/TRN-003/original")
        self.assertEqual(response.status_code, 200)
        self.assertIn('filename="unsafe_name______.txt"', response.headers["content-disposition"])


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

