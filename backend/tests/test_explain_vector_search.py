import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.retrieval.vector_search import vector_search_stage
from scripts.explain_vector_search import run_explain_vector_search


class VectorStageTests(unittest.TestCase):
    def test_stage_uses_filter_and_override(self):
        stage = vector_search_stage([0.1] * 768, 10, {"incident_id": "INC-2026-1042"}, num_candidates=300)
        self.assertEqual(stage["$vectorSearch"]["numCandidates"], 300)
        self.assertEqual(stage["$vectorSearch"]["limit"], 10)
        self.assertEqual(stage["$vectorSearch"]["filter"], {"incident_id": {"$eq": "INC-2026-1042"}})

    def test_stage_default_candidate_formula(self):
        stage = vector_search_stage([0.1] * 768, 5, None)
        # default: max(5 * 15, 30) = 75
        self.assertEqual(stage["$vectorSearch"]["numCandidates"], 75)
        self.assertEqual(stage["$vectorSearch"]["limit"], 5)
        self.assertNotIn("filter", stage["$vectorSearch"])


class ExplainScriptTests(unittest.TestCase):
    @patch("scripts.explain_vector_search.embed_query")
    @patch("scripts.explain_vector_search.get_db")
    @patch("scripts.explain_vector_search.get_chunks_collection")
    def test_run_explain_vector_search(self, mock_chunks_col, mock_db_fn, mock_embed):
        mock_embed.return_value = [0.05] * 768
        mock_db = MagicMock()
        mock_db.command.return_value = {"stages": [{"$vectorSearch": {"numCandidates": 150}}]}
        mock_db_fn.return_value = mock_db

        mock_chunks = MagicMock()
        mock_chunks.aggregate.side_effect = [
            [{"chunk_id": "c1"}, {"chunk_id": "c2"}],
            [{"chunk_id": "c1"}, {"chunk_id": "c2"}, {"chunk_id": "c3"}],
        ]
        mock_chunks_col.return_value = mock_chunks

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("scripts.explain_vector_search.BACKEND_ROOT", Path(tmpdir)):
                rows = run_explain_vector_search(
                    question="Why did payments fail?",
                    top_k=5,
                    incident_id="INC-2026-1042",
                    num_candidates_list=[150, 300],
                )
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]["num_candidates"], 150)
                self.assertEqual(rows[1]["num_candidates"], 300)
                self.assertAlmostEqual(rows[0]["overlap_vs_max"], 2 / 3)
                self.assertAlmostEqual(rows[1]["overlap_vs_max"], 1.0)

                eval_dir = Path(tmpdir) / "eval_results"
                self.assertTrue((eval_dir / "explain_150.json").is_file())
                self.assertTrue((eval_dir / "explain_300.json").is_file())
