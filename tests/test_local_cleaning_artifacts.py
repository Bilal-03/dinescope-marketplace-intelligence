import unittest
from pathlib import Path

import pandas as pd

from scripts.data_quality import build_quality_masks


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = Path("/Users/bilal/Downloads/zomato_business_complete.csv")
CLEANED_PATH = ROOT / "data" / "cleaned" / "zomato_business_complete_cleaned.csv"
AUDIT_PATH = ROOT / "data" / "cleaned" / "zomato_business_complete_exclusion_audit.csv"


@unittest.skipUnless(
    SOURCE_PATH.exists() and CLEANED_PATH.exists() and AUDIT_PATH.exists(),
    "local source, cleaned and exclusion-audit artifacts are not all present",
)
class LocalCleaningArtifactTest(unittest.TestCase):
    def test_cleaned_and_exclusion_artifacts_reconcile(self):
        raw = pd.read_csv(SOURCE_PATH, low_memory=False, encoding="utf-8-sig")
        cleaned = pd.read_csv(CLEANED_PATH, low_memory=False)
        audit = pd.read_csv(AUDIT_PATH, low_memory=False)

        self.assertEqual(cleaned.shape, (126_519, 36))
        self.assertEqual(audit.shape, (22_149, 6))
        self.assertEqual(list(cleaned.columns), list(raw.columns))
        self.assertLessEqual(cleaned["Order Value"].max(), 7_500)
        self.assertEqual(audit["Exclusion Reason"].value_counts().to_dict(), {"Order Value above ₹7,500": 22_149})
        self.assertEqual(list(audit.columns), ["Order ID", "Order Date", "Order Value", "Sales Quantity", "Restaurant City", "Exclusion Reason"])
        masks = build_quality_masks(raw)
        self.assertEqual(
            cleaned["Order ID"].astype(str).tolist(),
            raw.loc[masks["analysis_eligible"], "Order ID"].astype(str).tolist(),
        )


if __name__ == "__main__":
    unittest.main()
