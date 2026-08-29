import copy
import unittest

from streamlit_lib import (
    AGGREGATE_VERSION,
    DEFAULT_WEIGHTS,
    add_rank_movement,
    customer_cohort_frame,
    customer_mix_frame,
    cuisine_heatmap_frame,
    cuisine_ranking_frame,
    cuisine_summary_frame,
    decision_frame,
    eligible_cuisine_pairs,
    eligible_market_rows,
    frequency_frame,
    lifecycle_frame,
    load_analytics,
    market_monthly_frame,
    market_ranking_frame,
    market_summary_frame,
    monthly_performance_frame,
    normalize_weights,
    parse_feature_flags,
    rank_movement_label,
    reliability_issue_rows,
    restaurant_observation_frame,
    score_decision_pairs,
    scenario_summary,
    valid_data_contract,
)


class StreamlitAnalyticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_analytics()

    def test_public_aggregate_satisfies_contract(self):
        self.assertTrue(valid_data_contract(self.data))
        self.assertEqual(self.data["aggregate_version"], AGGREGATE_VERSION)
        self.assertEqual(self.data["quality"]["valid_transactions"], 148668)
        self.assertEqual(self.data["quality"]["analysis_transactions"], 126519)
        self.assertEqual(self.data["quality"]["high_value_excluded_transactions"], 22149)
        self.assertEqual(self.data["quality"]["missing_rating_rows"], 88755)
        self.assertEqual(self.data["quality"]["missing_menu_attribute_rows"], 138145)

    def test_contract_rejects_missing_or_inconsistent_quality_fields(self):
        invalid = copy.deepcopy(self.data)
        invalid["quality"].pop("missing_rating_rows")
        self.assertFalse(valid_data_contract(invalid))

        invalid = copy.deepcopy(self.data)
        invalid["quality"]["valid_transactions"] += 1
        self.assertFalse(valid_data_contract(invalid))

    def test_all_market_scope_reconciles_to_quality_total(self):
        scope = self.data["scopes"]["All markets|All years"]
        self.assertEqual(scope["metrics"]["analysis_transactions"], self.data["quality"]["analysis_transactions"])

    def test_weights_are_normalized(self):
        normalized = normalize_weights(DEFAULT_WEIGHTS)
        self.assertAlmostEqual(sum(normalized.values()), 1.0)

    def test_decision_scoring_matches_guardrails_and_ordering(self):
        rows = score_decision_pairs(self.data["cuisine_views"]["All years"]["pairs"], 100, DEFAULT_WEIGHTS, True)
        self.assertGreater(len(rows), 0)
        self.assertEqual([row["rank"] for row in rows], list(range(1, len(rows) + 1)))
        self.assertTrue(all(row["allocated_orders"] >= 100 for row in rows))
        self.assertTrue(all(rows[index]["lab_score"] >= rows[index + 1]["lab_score"] for index in range(len(rows) - 1)))

    def test_shared_evidence_helpers_match_default_counts(self):
        market_view = self.data["market_views"]["All years"]
        self.assertEqual(len(eligible_market_rows(market_view["markets"])), 18)
        self.assertEqual(
            len(eligible_market_rows(self.data["market_views"]["2026"]["markets"])),
            13,
        )

        cuisine_view = self.data["cuisine_views"]["All years"]
        self.assertEqual(len(eligible_cuisine_pairs(cuisine_view["pairs"])), 71)

    def test_evidence_tables_have_stable_parity_columns(self):
        cohort = customer_cohort_frame(self.data["scopes"]["All markets|All years"]["cohorts"])
        self.assertEqual(list(cohort.columns), ["Cohort", "Size", "M0", "M1", "M2", "M3", "M4", "M5", "M6"])
        self.assertEqual(cohort.shape, (8, 9))

        lifecycle = lifecycle_frame(self.data["scopes"]["All markets|All years"])
        self.assertEqual(
            list(lifecycle.columns),
            ["Segment", "Customers", "Share", "Orders / customer", "Sales / customer", "Repeat rate", "Median recency", "Suggested action"],
        )
        self.assertEqual(lifecycle["Customers"].sum(), 71947)

    def test_phase_two_chart_builders_preserve_audited_series(self):
        scope = self.data["scopes"]["All markets|All years"]
        orders = monthly_performance_frame(scope, "orders")
        sales = monthly_performance_frame(scope, "sales")
        self.assertEqual(len(orders), 33)
        self.assertEqual(orders.iloc[0]["Value"], 3656)
        self.assertEqual(orders.iloc[-1]["Value"], 2353)
        self.assertEqual(sales.iloc[0]["Value"], 4034983)
        self.assertEqual(sales.iloc[-1]["Value"], 2637924)
        self.assertEqual(len(customer_mix_frame(scope)), 66)
        self.assertEqual(customer_mix_frame(scope).iloc[1]["Customers"], 0)
        self.assertEqual(
            frequency_frame(scope)["Customers"].tolist(),
            [35801, 22713, 9568, 2956, 909],
        )
        self.assertEqual(market_summary_frame(self.data).iloc[0]["Market"], "Bangalore")
        self.assertEqual(market_summary_frame(self.data).iloc[0]["Transactions"], 11952)

    def test_phase_three_market_frames_match_default_eligibility(self):
        view = self.data["market_views"]["All years"]
        eligible = eligible_market_rows(view["markets"])
        ranking = market_ranking_frame(eligible)
        self.assertEqual(ranking.shape, (18, 8))
        self.assertEqual(list(ranking.columns), ["Market", "Transactions", "Growth", "Customers", "Repeat rate", "Avg. order value", "Txn share", "Confidence"])
        self.assertEqual(ranking.iloc[0]["Market"], "Bangalore")
        self.assertEqual(ranking.iloc[0]["Transactions"], 5389)

        pulse = market_monthly_frame(eligible[:4])
        self.assertEqual(list(pulse.columns), ["Market", "Month", "Transactions"])
        self.assertEqual(set(pulse["Market"]), {"Bangalore", "Delhi", "Pune", "Chennai"})
        totals = pulse.groupby("Market")["Transactions"].sum().to_dict()
        self.assertEqual(totals["Bangalore"], 5389)
        self.assertEqual(totals["Delhi"], 3573)

    def test_reliability_issue_register_uses_raw_row_counts(self):
        issues = reliability_issue_rows(self.data)
        self.assertEqual([row["Issue"] for row in issues], ["Zero sales", "Missing sales", "Unsupported currency", "Order value above ₹7,500", "Missing rating", "Missing menu attributes"])
        self.assertEqual(issues[3]["Affected rows"], 22149)
        self.assertEqual(issues[3]["Sales impact (INR)"], 847032211.0)
        self.assertEqual(issues[4]["Affected rows"], 88755)
        self.assertEqual(issues[5]["Affected rows"], 138145)

    def test_phase_four_cuisine_and_restaurant_frames_match_reference(self):
        view = self.data["cuisine_views"]["All years"]
        eligible = eligible_cuisine_pairs(view["pairs"])
        summary = cuisine_summary_frame(view["cuisines"][:10])
        self.assertEqual(summary.iloc[0]["Cuisine"], "Chinese")
        self.assertEqual(summary.iloc[0]["Allocated txns"], 5291.0)
        self.assertEqual(summary.shape, (10, 6))

        ranking = cuisine_ranking_frame(eligible)
        self.assertEqual(ranking.shape, (71, 11))
        self.assertEqual(ranking.iloc[0]["Market · Cuisine"], "Bangalore · Desserts")
        self.assertAlmostEqual(ranking.iloc[0]["Signal"], 96.857143)
        self.assertEqual(
            list(ranking.columns),
            ["Market · Cuisine", "Signal", "Allocated txns", "Growth", "Customers", "Listings", "Demand / listing", "Rating cov.", "Menu cov.", "Confidence", "Recommended action"],
        )

        heatmap = cuisine_heatmap_frame(view["pairs"])
        self.assertEqual(heatmap.shape, (56, 3))
        self.assertEqual(heatmap["Market"].nunique(), 7)
        self.assertEqual(heatmap["Cuisine"].nunique(), 8)

        observations = restaurant_observation_frame(self.data["restaurant_observations"])
        self.assertEqual(observations.shape, (7, 6))
        self.assertEqual(observations.iloc[0]["Normalized name"], "domino s pizza")
        self.assertEqual(observations.iloc[0]["Observed rows"], 370)

    def test_rank_movement_is_positive_when_a_pair_moves_up(self):
        baseline = [{"market": "Bangalore", "cuisine": "Desserts", "rank": 4}]
        current = [{"market": "Bangalore", "cuisine": "Desserts", "rank": 1}]
        moved = add_rank_movement(current, baseline)[0]
        self.assertEqual(moved["rank_delta"], 3)
        self.assertEqual(moved["baseline_rank"], 4)
        self.assertEqual(rank_movement_label(moved["rank_delta"]), "↑3")
        self.assertEqual(rank_movement_label(None), "New")

    def test_phase_five_decision_lab_default_and_scenario_contract(self):
        pairs = self.data["cuisine_views"]["All years"]["pairs"]
        baseline = score_decision_pairs(pairs, 100, DEFAULT_WEIGHTS, True)
        self.assertEqual(len(baseline), 71)
        self.assertEqual((baseline[0]["market"], baseline[0]["cuisine"]), ("Bangalore", "Desserts"))
        self.assertAlmostEqual(baseline[0]["lab_score"], 88.87323943661973)
        current = add_rank_movement(
            score_decision_pairs(pairs, 100, {"demand": 50, "growth": 0, "reach": 0, "gap": 0, "quality": 0}, True),
            baseline,
        )
        self.assertEqual((current[0]["market"], current[0]["cuisine"]), ("Bangalore", "Chinese"))
        self.assertGreater(current[0]["rank_delta"], 0)
        frame = decision_frame(current)
        self.assertEqual(frame.shape, (71, 16))
        self.assertIn("Baseline rank", frame.columns)
        self.assertIn("Move", frame.columns)
        self.assertEqual(scenario_summary({"weights": DEFAULT_WEIGHTS}), "D25 · G25 · R20 · Gap15 · Q15")

    def test_feature_flags_default_to_all_and_support_staged_allowlists(self):
        self.assertTrue(all(parse_feature_flags("").values()))
        staged = parse_feature_flags("shell_v2,markets_v2")
        self.assertTrue(staged["shell_v2"])
        self.assertTrue(staged["markets_v2"])
        self.assertFalse(staged["overview_v2"])
        self.assertFalse(staged["decision_v2"])
        self.assertTrue(all(parse_feature_flags("all").values()))


if __name__ == "__main__":
    unittest.main()
