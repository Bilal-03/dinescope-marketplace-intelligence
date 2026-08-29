import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AnalyticsArtifactContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analytics = json.loads((ROOT / "data" / "analytics.json").read_text(encoding="utf-8"))
        cls.all_scope = cls.analytics["scopes"]["All markets|All years"]

    def test_source_contract_and_reconciliation_are_exact(self):
        analytics = self.analytics
        self.assertEqual(analytics["aggregate_version"], "1.2.0")
        self.assertEqual(analytics["source"]["rows"], 150_281)
        self.assertEqual(analytics["source"]["columns"], 36)
        self.assertEqual(analytics["source"]["expected_columns"], 36)
        self.assertEqual(analytics["source"]["sha256"], "fc5ca0ca1043e3cfb17ab467a7b87bbcc0a516cd766e962b4850a202d5a88be7")
        self.assertTrue(analytics["source"]["schema_matches"])
        self.assertEqual(analytics["source"]["date_format"], "MM/DD/YYYY")
        self.assertEqual(analytics["quality"]["valid_transactions"], 148_668)
        self.assertEqual(analytics["quality"]["analysis_transactions"], 126_519)
        self.assertEqual(analytics["quality"]["high_value_excluded_transactions"], 22_149)
        self.assertEqual(analytics["quality"]["invalid_order_value_excluded_transactions"], 0)
        self.assertEqual(analytics["quality"]["analysis_sales"], 139_532_057)
        self.assertEqual(analytics["quality"]["high_value_excluded_sales"], 847_032_211)
        self.assertEqual(
            analytics["quality"]["analysis_sales"] + analytics["quality"]["high_value_excluded_sales"],
            analytics["quality"]["source_valid_sales"],
        )
        self.assertEqual(
            analytics["quality"]["analysis_transactions"] + analytics["quality"]["high_value_excluded_transactions"],
            analytics["quality"]["valid_transactions"],
        )
        self.assertEqual(
            analytics["quality"]["valid_transactions"]
            + analytics["quality"]["excluded_transactions"],
            analytics["quality"]["raw_rows"],
        )
        self.assertEqual(analytics["quality"]["missing_rating_rows"], 88_755)
        self.assertEqual(analytics["quality"]["missing_menu_attribute_rows"], 138_145)
        self.assertEqual(analytics["quality"]["duplicate_order_ids"], 0)
        self.assertEqual(analytics["quality"]["invalid_dates"], 0)
        self.assertEqual(analytics["cleaning"]["max_order_value_inr"], 7_500)
        self.assertEqual(analytics["cleaning"]["source_valid_distribution"]["q1"], 176)
        self.assertEqual(analytics["cleaning"]["source_valid_distribution"]["q3"], 3_065)
        self.assertEqual(analytics["cleaning"]["source_valid_distribution"]["upper_fence"], 7_398.5)
        self.assertAlmostEqual(analytics["cleaning"]["analysis_retention_rate"], 126_519 / 148_668)
        self.assertAlmostEqual(analytics["cleaning"]["high_value_excluded_sales_share"], 847_032_211 / 986_564_268)

    def test_commercial_metrics_reconcile(self):
        metrics = self.all_scope["metrics"]
        self.assertEqual(metrics["analysis_transactions"], 126_519)
        self.assertEqual(metrics["gross_sales"], 139_532_057)
        self.assertEqual(metrics["active_customers"], 71_947)
        self.assertEqual(metrics["repeat_customers"], 36_146)
        self.assertAlmostEqual(metrics["repeat_rate"], 36_146 / 71_947)
        self.assertAlmostEqual(metrics["average_transaction_value"], 139_532_057 / 126_519)
        self.assertEqual(metrics["median_transaction_value"], 375)

    def test_customer_distributions_reconcile(self):
        self.assertEqual(
            sum(row["customers"] for row in self.all_scope["frequency"]),
            self.all_scope["metrics"]["active_customers"],
        )
        self.assertEqual(
            sum(row["customers"] for row in self.all_scope["segments"]),
            self.all_scope["metrics"]["active_customers"],
        )
        self.assertTrue(all(row["retention"][0] == 100 for row in self.all_scope["cohorts"]))

    def test_every_filter_combination_has_a_scope(self):
        for market in self.analytics["filters"]["markets"]:
            for period in self.analytics["filters"]["periods"]:
                self.assertIn(f"{market}|{period}", self.analytics["scopes"])

    def test_location_mapping_reconciles(self):
        mapping = self.analytics["location_mapping"]
        self.assertEqual(mapping["raw_labels"], 822)
        self.assertEqual(mapping["mapped_rows"] + mapping["unknown_rows"], self.analytics["source"]["rows"])
        self.assertLessEqual(mapping["high_confidence_rows"], mapping["mapped_rows"])
        self.assertIn("Bangalore", self.analytics["filters"]["markets"])
        self.assertIn("Delhi", self.analytics["filters"]["markets"])
        self.assertTrue(all("," not in market for market in self.analytics["filters"]["markets"]))

    def test_market_eligibility_and_monthly_totals(self):
        view = self.analytics["market_views"]["All years"]
        eligible = [row for row in view["markets"] if row["eligible_default"]]
        self.assertEqual(view["summary"]["eligible_markets"], len(eligible))
        self.assertTrue(
            all(
                row["orders"] >= 200
                and row["previous_orders"] >= 100
                and row["growth_orders"] is not None
                for row in eligible
            )
        )
        top_five_share = sum(row["order_share"] for row in view["markets"][:5])
        self.assertAlmostEqual(top_five_share, view["summary"]["top_five_concentration"])
        for row in view["markets"][:20]:
            self.assertEqual(sum(point["orders"] for point in row["monthly_orders"]), row["orders"])

    def test_cuisine_allocation_and_scores_are_bounded(self):
        self.assertEqual(self.analytics["cuisine_mapping"]["raw_tokens"], 126)
        self.assertEqual(self.analytics["cuisine_mapping"]["canonical_cuisines"], 110)
        self.assertEqual(self.analytics["cuisine_mapping"]["excluded_token_rows"], 22)
        for view in self.analytics["cuisine_views"].values():
            self.assertAlmostEqual(view["allocated_order_total"], view["covered_order_count"])
            self.assertTrue(all(0 <= row["opportunity_score"] <= 100 for row in view["pairs"]))
            eligible = [row for row in view["pairs"] if row["eligible_default"]]
            self.assertEqual(view["summary"]["eligible_pairs"], len(eligible))
            self.assertTrue(
                all(
                    row["allocated_orders"] >= 100
                    and row["previous_allocated_orders"] >= 50
                    and row["growth"] is not None
                    for row in eligible
                )
            )

    def test_restaurant_identity_evidence_is_conservative(self):
        mapping = self.analytics["restaurant_mapping"]
        self.assertEqual(mapping["restaurant_ids"], 148_541)
        self.assertEqual(mapping["restaurant_ids_repeated"], 123)
        self.assertLess(mapping["restaurant_ids_repeated"] / mapping["restaurant_ids"], 0.001)


if __name__ == "__main__":
    unittest.main()
