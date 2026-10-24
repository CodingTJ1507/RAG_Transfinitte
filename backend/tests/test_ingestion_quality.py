import unittest
import tempfile
from pathlib import Path

from app.ingestion.parsers import load_manifest, parse_source


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
