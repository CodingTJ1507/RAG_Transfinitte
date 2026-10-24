import unittest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from app.ingestion.chunking import chunk_evidence_units
from app.ingestion.parsers import load_manifest, parse_source
from app.retrieval.vector_search import build_vector_filter, citation_from_document


DATASET = Path(__file__).resolve().parents[1] / "synthetic_data"


def parse_demo(source_id):
    root, manifest = load_manifest(DATASET)
    entry = next(item for item in manifest["sources"] if item["source_id"] == source_id)
    return parse_source(root, entry)


class HtmlSectionTests(unittest.TestCase):
    def test_release_notes_have_one_unit_per_section(self):
        units = parse_demo("WEB-001").units
        self.assertEqual(
            [unit["locator"]["html_id"] for unit in units],
            ["intro", "overview", "breaking-changes", "migration", "3-0-1"],
        )
        self.assertIn("allow_aliases", units[2]["text"])

    def test_background_pages_have_one_unit_per_h2(self):
        for source_id, h2_count in (("WEB-002", 4), ("WEB-003", 6)):
            units = [
                unit for unit in parse_demo(source_id).units
                if unit["locator"]["html_id"] != "intro"
            ]
            self.assertEqual(len(units), h2_count, source_id)


class TextSectionTests(unittest.TestCase):
    def test_handover_note_has_one_unit_per_section(self):
        units = parse_demo("TRN-003").units
        self.assertEqual(
            [unit["locator"]["section"] for unit in units],
            ["HEADER", "STATUS", "VERIFIED", "NOT VERIFIED / STILL OPEN", "NEXT STEPS"],
        )
        self.assertNotIn(
            "INCIDENT HANDOVER NOTE",
            " ".join(unit["text"] for unit in units[1:]),
        )

    def test_plain_text_is_split_into_parts(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "notes.txt"
            path.write_text(
                "\n\n".join(("word " * 200).strip() for _ in range(5)),
                encoding="utf-8",
            )
            parsed = parse_source(
                Path(folder),
                {
                    "source_id": "TXT-1",
                    "title": "Notes",
                    "source_type": "transcript",
                    "file_path": "notes.txt",
                },
            )
            self.assertEqual(
                [unit["locator"]["section"] for unit in parsed.units],
                ["Part 1", "Part 2", "Part 3"],
            )


class PdfSectionTests(unittest.TestCase):
    @staticmethod
    def sections(source_id):
        return [
            (unit["locator"]["page"], unit["locator"].get("section_path", []))
            for unit in parse_demo(source_id).units
        ]

    def test_spec_sections_and_pages(self):
        found = self.sections("DOC-002")
        self.assertIn((7, ["4. Deprecated Fields"]), found)
        self.assertTrue(
            any(page == 8 and "5. Error Codes" in path for page, path in found)
        )

    def test_release_notes_and_architecture_sections(self):
        self.assertTrue(
            any(
                page == 4 and "2.1 Dependency Updates" in section
                for page, section in self.sections("DOC-004")
            )
        )
        self.assertTrue(
            any(
                page == 5 and "4. Compatibility" in section
                for page, section in self.sections("DOC-004")
            )
        )
        self.assertTrue(
            any(
                page == 7 and "4. Retry Behaviour Between Services" in section
                for page, section in self.sections("DOC-001")
            )
        )

    def test_cover_owner_and_noise_removed(self):
        owners = {
            source_id: parse_demo(source_id).units[0]["metadata"].get("cover_owner")
            for source_id in ("DOC-001", "DOC-002", "DOC-003", "DOC-004", "DOC-005")
        }
        self.assertEqual(
            owners,
            {
                "DOC-001": "Platform Team",
                "DOC-002": "Payments Team",
                "DOC-003": "SRE Team",
                "DOC-004": "Payments Team",
                "DOC-005": None,
            },
        )
        units = parse_demo("DOC-002").units
        text = " ".join(unit["text"] for unit in units)
        self.assertNotIn("Page 3 of 10", text)
        self.assertNotIn(". . .", text)
        self.assertFalse(any(unit["locator"]["page"] == 2 for unit in units))
        self.assertIn("Figure 1-1", text)
        self.assertIn(
            "order-service",
            " ".join(unit["text"] for unit in parse_demo("DOC-001").units),
        )


class OwnerTests(unittest.TestCase):
    def test_source_owners(self):
        owners = {
            source_id: parse_demo(source_id).source["owner"]
            for source_id in ("DOC-001", "DOC-003", "DOC-005", "WEB-001")
        }
        self.assertEqual(
            owners,
            {
                "DOC-001": "Platform Team",
                "DOC-003": "SRE Team",
                "DOC-005": "Payments Team",
                "WEB-001": "Unassigned",
            },
        )

    def test_record_chunks_use_their_own_service(self):
        parsed = parse_demo("REC-001")
        chunks = chunk_evidence_units(
            parsed.units,
            {**parsed.source, "source_type": "structured_record"},
        )
        by_log = {
            chunk["locator"]["log_id"]: chunk["owner"]
            for chunk in chunks
        }
        self.assertEqual(by_log["LOG-0001"], "Unassigned")
        self.assertEqual(by_log["LOG-0002"], "Payments Team")


class ImageReadingTests(unittest.TestCase):
    def test_image_text_comes_from_gemini(self):
        reading = {
            "description": "Debug console showing a failed payment.",
            "visible_text": [
                "HTTP/1.1 422 Unprocessable Entity",
                '"trace_id": "trc-5a10c4"',
            ],
        }
        with (
            patch("app.ingestion.parsers.describe_image", return_value=reading),
            patch("app.ingestion.parsers.settings.IMAGE_ANALYSIS_ENABLED", True),
        ):
            parsed = parse_demo("IMG-002")
        unit = parsed.units[0]
        self.assertIn("trc-5a10c4", unit["text"])
        self.assertEqual(unit["locator"]["analysis"], "gemini_vision")
        self.assertEqual(unit["metadata"]["visible_text"], reading["visible_text"])
        self.assertEqual(parsed.source["analysis_status"], "vision_analyzed")

    def test_gemini_failure_falls_back_to_metadata(self):
        with (
            patch(
                "app.ingestion.parsers.describe_image",
                side_effect=RuntimeError("quota"),
            ),
            patch("app.ingestion.parsers.settings.IMAGE_ANALYSIS_ENABLED", True),
        ):
            parsed = parse_demo("IMG-002")
        unit = parsed.units[0]
        self.assertEqual(unit["locator"]["analysis"], "metadata_only")
        self.assertEqual(parsed.source["analysis_status"], "metadata_only")


class TimestampTests(unittest.TestCase):
    def test_chunks_store_real_dates(self):
        parsed = parse_demo("TRN-002")
        chunks = chunk_evidence_units(
            parsed.units,
            {**parsed.source, "source_type": "transcript"},
        )
        cue4 = next(
            chunk for chunk in chunks
            if chunk["locator"]["cue_id"] == "cue-004"
        )
        self.assertEqual(
            cue4["timestamp"],
            datetime(2026, 10, 23, 10, 20, 52, tzinfo=timezone.utc),
        )

    def test_vector_filter_uses_datetimes(self):
        start = datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc)
        clause = build_vector_filter({"time_range_start": start})
        self.assertIsInstance(clause["timestamp"]["$gte"], datetime)

    def test_citation_timestamp_remains_iso_utc_text(self):
        citation = citation_from_document({
            "source_id": "TRN-002",
            "source_type": "transcript",
            "timestamp": datetime(2026, 10, 23, 10, 20, 52),
        })
        self.assertEqual(citation.metadata["timestamp"], "2026-10-23T10:20:52Z")
