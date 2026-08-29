import unittest
import os

from streamlit.testing.v1 import AppTest


class StreamlitAppSmokeTest(unittest.TestCase):
    def test_all_public_modules_render_without_exceptions(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
        self.assertFalse(app.exception)
        for page in [
            "Overview",
            "Customer growth",
            "Market demand",
            "Cuisine gaps",
            "Decision lab",
            "Data reliability",
        ]:
            app.radio(key="pl_page").set_value(page).run()
            self.assertFalse(app.exception, f"{page} raised a Streamlit exception")

    def test_shell_uses_original_navigation_and_page_aware_market_scope(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
        self.assertEqual(
            list(app.radio(key="pl_page").options),
            ["Overview", "Customer growth", "Market demand", "Cuisine gaps", "Data reliability", "Decision lab"],
        )
        app.selectbox(key="pl_market").set_value("Bangalore").run()
        self.assertEqual(app.selectbox(key="pl_market").value, "Bangalore")
        app.radio(key="pl_page").set_value("Market demand").run()
        self.assertFalse(any(selectbox.label == "Clean market" for selectbox in app.selectbox))
        self.assertTrue(app.button(key="pl_comparison_scope").disabled)
        self.assertEqual(app.selectbox(key="pl_period").value, "All years")

        app.radio(key="pl_page").set_value("Overview").run()
        self.assertEqual(app.selectbox(key="pl_market").value, "All markets")
        app.selectbox(key="pl_market").set_value("Delhi").run()
        app.button(key="pl_reset_filters").click().run()
        self.assertEqual(app.selectbox(key="pl_market").value, "All markets")
        self.assertEqual(app.selectbox(key="pl_period").value, "All years")

    def test_methodology_dialog_exposes_contract_and_definitions(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
        app.button(key="pl_methodology").click().run()
        self.assertFalse(app.exception)
        self.assertIn("Source contract", [item.value for item in app.subheader])
        self.assertIn("Metric dictionary", [item.value for item in app.subheader])
        self.assertTrue(any("SHA-256" in item.value for item in app.caption))

    def test_feature_flags_can_stage_only_selected_modules(self):
        previous = os.environ.get("DINESCOPE_FEATURE_FLAGS")
        os.environ["DINESCOPE_FEATURE_FLAGS"] = "shell_v2,markets_v2"
        try:
            app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
            self.assertTrue(any("staged for private validation" in item.value for item in app.info))
            app.radio(key="pl_page").set_value("Market demand").run()
            self.assertFalse(any("staged for private validation" in item.value for item in app.info))
        finally:
            if previous is None:
                os.environ.pop("DINESCOPE_FEATURE_FLAGS", None)
            else:
                os.environ["DINESCOPE_FEATURE_FLAGS"] = previous

    def test_phase_two_overview_and_customer_values_match_reference(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=20).run()
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric],
            [
                ("Included transactions", "126,519"),
                ("Filtered sales", "₹14.0 Cr"),
                ("Active customers", "71,947"),
                ("Repeat customer rate", "50.2%"),
                ("Avg. order value", "₹1,103"),
            ],
        )
        self.assertEqual(app.dataframe[0].value.shape, (5, 5))
        self.assertEqual(app.dataframe[-1].value.shape, (7, 8))
        app.radio(key="pl_overview_metric").set_value("Sales").run()
        self.assertTrue(any("Filtered sales · 33 monthly points" in item.value for item in app.caption))

        app.selectbox(key="pl_market").set_value("Bangalore").run()
        app.selectbox(key="pl_period").set_value("2020").run()
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric],
            [
                ("Included transactions", "2,480"),
                ("Filtered sales", "₹44.5 L"),
                ("Active customers", "2,449"),
                ("Repeat customer rate", "1.3%"),
                ("Avg. order value", "₹1,796"),
            ],
        )

        app.radio(key="pl_page").set_value("Customer growth").run()
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric],
            [
                ("Active customers", "2,449"),
                ("New customers", "2,233"),
                ("Repeat customers", "31"),
                ("Repeat customer rate", "1.3%"),
                ("Transactions / customer", "1.01"),
            ],
        )
        self.assertEqual(app.dataframe[0].value.shape, (6, 9))
        self.assertEqual(app.dataframe[-1].value.shape, (3, 8))

    def test_phase_three_market_and_reliability_surfaces_match_reference(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=30).run()
        app.radio(key="pl_page").set_value("Market demand").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric[:5]],
            [
                ("Active cleaned markets", "210"),
                ("Largest market", "Bangalore"),
                ("Fastest eligible growth", "Guwahati"),
                ("Highest repeat rate", "Bangalore"),
                ("Top-five concentration", "44.7%"),
            ],
        )
        ranking = app.dataframe[0].value
        self.assertEqual(ranking.shape, (18, 8))
        self.assertEqual(ranking.iloc[0]["Market"], "Bangalore")
        self.assertEqual(ranking.iloc[0]["Transactions"], 5389)

        app.selectbox(key="pl_market_sort").set_value("Rank by growth").run()
        self.assertEqual(app.dataframe[0].value.iloc[0]["Market"], "Guwahati")
        app.slider(key="pl_market_minimum").set_value(1000).run()
        self.assertTrue((app.dataframe[0].value["Transactions"] >= 1000).all())

        app.radio(key="pl_page").set_value("Data reliability").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric],
            [
                ("Source-valid rate", "98.9%"),
                ("Analysis retention", "85.1%"),
                ("Rating coverage", "40.9%"),
                ("Menu coverage", "8.1%"),
                ("Schema integrity", "36 / 36"),
            ],
        )
        self.assertEqual(app.dataframe[0].value.shape, (6, 5))
        self.assertIn("150,281 raw rows − 1,613 source-invalid rows = 148,668 source-valid rows", " ".join(item.value for item in app.markdown))
        self.assertIn("148,668 source-valid rows − 22,149 Order Value exclusions = 126,519 included analytical transactions", " ".join(item.value for item in app.markdown))
        self.assertEqual(app.code[0].value, self._source_sha())

    @staticmethod
    def _source_sha():
        return "fc5ca0ca1043e3cfb17ab467a7b87bbcc0a516cd766e962b4850a202d5a88be7"

    def test_phase_four_cuisine_and_restaurant_surfaces_match_reference(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=30).run()
        app.radio(key="pl_page").set_value("Cuisine gaps").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric[:5]],
            [
                ("Canonical cuisines", "110"),
                ("Highest observed demand", "Chinese"),
                ("Eligible opportunities", "71"),
                ("Top opportunity signal", "Bangalore · Desserts"),
                ("Cuisine field coverage", "98.9%"),
            ],
        )
        self.assertEqual(app.dataframe[0].value.shape, (71, 11))
        self.assertEqual(app.dataframe[0].value.iloc[0]["Market · Cuisine"], "Bangalore · Desserts")
        self.assertEqual(app.dataframe[1].value.shape, (7, 6))
        self.assertTrue(any(button.label == "Export cuisine evidence" for button in app.download_button))

        app.selectbox(key="pl_period").set_value("2020").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [(metric.label, metric.value) for metric in app.metric[:5]],
            [
                ("Canonical cuisines", "110"),
                ("Highest observed demand", "Chinese"),
                ("Eligible opportunities", "24"),
                ("Top opportunity signal", "Bangalore · North Indian"),
                ("Cuisine field coverage", "98.9%"),
            ],
        )
        self.assertEqual(app.dataframe[0].value.shape, (24, 11))

        app.selectbox(key="pl_cuisine_sort").set_value("Rank by demand").run()
        self.assertEqual(app.dataframe[0].value.iloc[0]["Market · Cuisine"], "Delhi · North Indian")

    def test_phase_five_decision_lab_scenarios_and_rank_movement(self):
        app = AppTest.from_file("../streamlit_app.py", default_timeout=30).run()
        app.radio(key="pl_page").set_value("Decision lab").run()
        self.assertFalse(app.exception)
        self.assertEqual(
            [(slider.label, slider.value) for slider in app.slider],
            [
                ("Minimum allocated transactions", 100),
                ("Demand scale weight", 25),
                ("Growth momentum weight", 25),
                ("Customer reach weight", 20),
                ("Coverage gap weight", 15),
                ("Data quality weight", 15),
            ],
        )
        self.assertEqual(app.metric[0].label, "Weight total")
        self.assertEqual(app.metric[0].value, "100%")
        self.assertEqual(app.metric[1].value, "Bangalore · Desserts")
        self.assertEqual(app.dataframe[0].value.shape, (25, 16))
        self.assertEqual(app.dataframe[0].value.iloc[0]["Move"], "—")
        self.assertTrue(any(button.label == "Export decision brief" for button in app.download_button))
        self.assertTrue(any("Stored in this Streamlit session only" in item.value for item in app.caption))

        app.slider(key="pl_decision_weight_demand").set_value(50).run()
        app.slider(key="pl_decision_weight_growth").set_value(0).run()
        app.slider(key="pl_decision_weight_reach").set_value(0).run()
        app.slider(key="pl_decision_weight_gap").set_value(0).run()
        app.slider(key="pl_decision_weight_quality").set_value(0).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[0].value.iloc[0]["Market"], "Bangalore")
        self.assertTrue(any(value != "—" for value in app.dataframe[0].value["Move"].tolist()))

        app.text_input(key="pl_decision_scenario_name").set_value("Demand-led").run()
        app.button(key="pl_decision_save_scenario").click().run()
        self.assertFalse(app.exception)
        self.assertIn("Demand-led", list(app.selectbox(key="pl_decision_comparison_name").options))
        self.assertEqual(app.selectbox(key="pl_decision_comparison_name").value, "Demand-led")
        self.assertTrue(any(button.label == "Remove" for button in app.button))


if __name__ == "__main__":
    unittest.main()
