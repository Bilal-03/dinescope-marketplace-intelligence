import unittest

import pandas as pd

from scripts.build_analytics import EXPECTED_SOURCE_COLUMNS, REQUIRED_SOURCE_COLUMNS, validate_source_frame


class AnalyticsBuilderContractTest(unittest.TestCase):
    def test_source_schema_requires_all_columns(self):
        frame = pd.DataFrame(columns=sorted(REQUIRED_SOURCE_COLUMNS - {"Order ID"}))
        with self.assertRaisesRegex(ValueError, "Order ID"):
            validate_source_frame(frame)

    def test_source_schema_requires_exact_column_count(self):
        columns = sorted(REQUIRED_SOURCE_COLUMNS) + [f"extra_{index}" for index in range(EXPECTED_SOURCE_COLUMNS)]
        frame = pd.DataFrame(columns=columns)
        with self.assertRaisesRegex(ValueError, "columns"):
            validate_source_frame(frame)


if __name__ == "__main__":
    unittest.main()
