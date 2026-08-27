import unittest

from streamlit_lib import DEFAULT_WEIGHTS, load_analytics, normalize_weights, score_decision_pairs, valid_data_contract


class StreamlitAnalyticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_analytics()

    def test_public_aggregate_satisfies_contract(self):
        self.assertTrue(valid_data_contract(self.data))
        self.assertEqual(self.data["quality"]["valid_transactions"], 148668)

    def test_all_market_scope_reconciles_to_quality_total(self):
        scope = self.data["scopes"]["All markets|All years"]
        self.assertEqual(scope["metrics"]["valid_transactions"], self.data["quality"]["valid_transactions"])

    def test_weights_are_normalized(self):
        normalized = normalize_weights(DEFAULT_WEIGHTS)
        self.assertAlmostEqual(sum(normalized.values()), 1.0)

    def test_decision_scoring_matches_guardrails_and_ordering(self):
        rows = score_decision_pairs(self.data["cuisine_views"]["All years"]["pairs"], 100, DEFAULT_WEIGHTS, True)
        self.assertGreater(len(rows), 0)
        self.assertEqual([row["rank"] for row in rows], list(range(1, len(rows) + 1)))
        self.assertTrue(all(row["allocated_orders"] >= 100 for row in rows))
        self.assertTrue(all(rows[index]["lab_score"] >= rows[index + 1]["lab_score"] for index in range(len(rows) - 1)))


if __name__ == "__main__":
    unittest.main()
