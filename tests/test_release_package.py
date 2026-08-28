import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleasePackageTest(unittest.TestCase):
    def test_portfolio_case_study_is_evidence_backed_and_bounded(self):
        portfolio = (ROOT / "docs" / "portfolio_case_study.md").read_text(encoding="utf-8")
        for expected in [
            "150,281",
            "148,668",
            "₹986,564,268",
            "Repeat rate",
            "not affiliated with a food-delivery company",
            "delivery-time, cancellation, discount, commission, funnel or campaign",
            "Decision Lab",
        ]:
            self.assertIn(expected, portfolio)

    def test_release_readiness_records_public_read_only_decision(self):
        readiness = (ROOT / "docs" / "release_readiness.md").read_text(encoding="utf-8")
        for expected in [
            "Public Streamlit deployment",
            "Public Streamlit deployment | **Live**",
            "Decision:       [ ] Keep private   [ ] Invite-only   [x] Public read-only",
            "exclude raw records, secrets and private hosting metadata",
            "server-backed team sharing",
        ]:
            self.assertIn(expected, readiness)

    def test_representative_screenshots_are_real_artifacts(self):
        for filename in ["01-overview.jpg", "02-decision-lab.jpg", "03-cuisine-opportunity.jpg"]:
            contents = (ROOT / "docs" / "screenshots" / filename).read_bytes()
            self.assertGreater(len(contents), 10_000, filename)
            self.assertEqual(contents[:3], b"\xff\xd8\xff", filename)


if __name__ == "__main__":
    unittest.main()
