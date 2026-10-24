import unittest

from app.config import settings
from app.retrieval.vector_search import vector_search_stage


class VectorStageTests(unittest.TestCase):
    def test_stage_uses_filter_and_override(self):
        stage = vector_search_stage(
            [0.1] * 768,
            10,
            {"incident_id": "INC-2026-1042"},
            num_candidates=300,
        )
        self.assertEqual(stage["$vectorSearch"]["numCandidates"], 300)
        self.assertEqual(stage["$vectorSearch"]["limit"], 10)
        self.assertEqual(
            stage["$vectorSearch"]["filter"],
            {"incident_id": {"$eq": "INC-2026-1042"}},
        )

    def test_stage_preserves_default_candidate_formula(self):
        stage = vector_search_stage([0.1] * 768, 10, None)
        self.assertEqual(
            stage["$vectorSearch"]["numCandidates"],
            max(10 * 15, settings.RETRIEVAL_CANDIDATE_LIMIT),
        )
