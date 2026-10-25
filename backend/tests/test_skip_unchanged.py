import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.ingestion.parsers import load_manifest
from app.services.ingestion import _index_source

DATASET = Path(__file__).resolve().parents[1] / "synthetic_data"


def demo_entry(source_id):
    root, manifest = load_manifest(DATASET)
    return root, next(item for item in manifest["sources"] if item["source_id"] == source_id)


class SkipUnchangedTests(unittest.TestCase):
    def test_unchanged_source_is_not_parsed(self):
        root, entry = demo_entry("DOC-002")
        sources = MagicMock()
        sources.find_one.return_value = {
            "source_hash": entry["sha256"],
            "ingestion_status": "indexed",
            "chunk_count": 14,
            "file_id": "file_123",
        }
        with patch("app.services.ingestion._store_original", return_value="file_123"), \
             patch("app.services.ingestion.get_sources_collection", return_value=sources), \
             patch("app.services.ingestion.get_chunks_collection"), \
             patch("app.services.ingestion.parse_source", side_effect=AssertionError("parsed")):
            self.assertEqual(_index_source(root, entry), ("skipped", 0, 0))

    def test_unchanged_source_backfills_missing_file_id(self):
        root, entry = demo_entry("DOC-002")
        sources = MagicMock()
        sources.find_one.return_value = {
            "source_hash": entry["sha256"],
            "ingestion_status": "indexed",
            "chunk_count": 14,
        }
        with patch("app.services.ingestion._store_original", return_value="new_file_id"), \
             patch("app.services.ingestion.get_sources_collection", return_value=sources), \
             patch("app.services.ingestion.get_chunks_collection"), \
             patch("app.services.ingestion.parse_source", side_effect=AssertionError("parsed")):
            self.assertEqual(_index_source(root, entry), ("skipped", 0, 0))
            sources.update_one.assert_called_once_with(
                {"source_id": "DOC-002"},
                {"$set": {"file_id": "new_file_id"}},
            )

    def test_changed_source_is_parsed(self):
        root, entry = demo_entry("DOC-002")
        sources = MagicMock()
        sources.find_one.return_value = {
            "source_hash": "different",
            "ingestion_status": "indexed",
            "chunk_count": 14,
            "file_id": "file_123",
        }
        with patch("app.services.ingestion._store_original", return_value="file_123"), \
             patch("app.services.ingestion.get_sources_collection", return_value=sources), \
             patch("app.services.ingestion.get_chunks_collection"), \
             patch("app.services.ingestion.parse_source", side_effect=RuntimeError("parsed")) as parse:
            with self.assertRaises(RuntimeError):
                _index_source(root, entry)
            sources.find_one.assert_called_once()
            parse.assert_called_once()
