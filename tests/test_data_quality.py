import unittest

import pandas as pd

from scripts.data_quality import MAX_ORDER_VALUE_INR, build_quality_masks


class DataQualityRuleTest(unittest.TestCase):
    def test_cutoff_is_inclusive_and_quantity_is_not_filtered(self):
        frame = pd.DataFrame(
            {
                "Order ID": ["at-cutoff", "above-cutoff", "zero-sales", "ordinary", "missing-value"],
                "Order Date": ["01/01/2020"] * 5,
                "Sales Amount": [7500, 7501, 0, 100, 100],
                "Order Value": [7500, 7501, 0, 100, None],
                "Sales Quantity": [99999, 1, 1, 1, 1],
                "Order Currency": ["INR"] * 5,
                "Sales Amount Valid": [True, True, False, True, True],
            }
        )

        masks = build_quality_masks(frame)

        self.assertEqual(MAX_ORDER_VALUE_INR, 7500)
        self.assertEqual(masks["source_valid"].sum(), 4)
        self.assertEqual(masks["analysis_eligible"].sum(), 2)
        self.assertTrue(masks["analysis_eligible"].iloc[0])
        self.assertTrue(masks["analysis_eligible"].iloc[3])
        self.assertFalse(masks["analysis_eligible"].iloc[1])
        self.assertEqual(masks["high_value_excluded"].sum(), 1)
        self.assertEqual(masks["invalid_order_value_excluded"].sum(), 1)
        self.assertEqual(masks["plausibility_excluded"].sum(), 2)
        self.assertEqual(
            masks["analysis_eligible"].sum() + masks["plausibility_excluded"].sum(),
            masks["source_valid"].sum(),
        )


if __name__ == "__main__":
    unittest.main()
