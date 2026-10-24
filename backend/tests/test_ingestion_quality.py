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
