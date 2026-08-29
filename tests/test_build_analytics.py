import unittest

import pandas as pd

from scripts.build_analytics import (
    DISPLAY_YEAR_OFFSET,
    EXPECTED_SOURCE_COLUMNS,
    REQUIRED_SOURCE_COLUMNS,
    display_date_iso,
    display_month,
    display_window_label,
    display_year_for_source,
    source_year_for_display,
    validate_source_frame,
)


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


class PresentationYearMappingTest(unittest.TestCase):
    def test_source_and_display_years_round_trip(self):
        source_years = [2017, 2018, 2019, 2020]
        display_years = [2023, 2024, 2025, 2026]

        self.assertEqual(DISPLAY_YEAR_OFFSET, 6)
        self.assertEqual([display_year_for_source(year) for year in source_years], display_years)
        self.assertEqual([source_year_for_display(year) for year in display_years], source_years)

    def test_date_month_and_window_labels_shift_without_changing_month_day(self):
        start = pd.Timestamp("2019-06-28")
        end = pd.Timestamp("2020-06-26")

        self.assertEqual(display_date_iso(pd.Timestamp("2017-10-04")), "2023-10-04")
        self.assertEqual(display_month(pd.Timestamp("2020-06-01")), "2026-06")
        self.assertEqual(display_window_label(start, end), "28 Jun 2025–26 Jun 2026")


if __name__ == "__main__":
    unittest.main()
