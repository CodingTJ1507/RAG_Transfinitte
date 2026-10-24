import unittest
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
