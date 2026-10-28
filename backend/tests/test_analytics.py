import unittest
from datetime import datetime, timezone

from app.analytics import as_utc, build_analysis, normalize_actuals, select_forecasts


class VintageTests(unittest.TestCase):
    def row(self, publish, start="2026-01-02T10:00:00Z", generation=1000):
        return {"publishTime": publish, "startTime": start, "generation": generation}

    def test_forecasts_after_cutoff_cannot_leak(self):
        selected = select_forecasts([
            self.row("2025-12-31T10:30:00Z", generation=100),
            self.row("2026-01-01T12:30:00Z", generation=200),
            self.row("2026-01-01T13:00:00Z", generation=300),
        ])
        self.assertEqual(selected[as_utc("2026-01-02T10:00:00Z")]["generation"], 100)

    def test_equal_cutoff_is_eligible_and_latest_eligible_wins(self):
        selected = select_forecasts([
            self.row("2026-01-01T10:30:00Z", generation=100),
            self.row("2026-01-01T12:00:00Z", generation=250),
        ])
        self.assertEqual(selected[as_utc("2026-01-02T10:00:00Z")]["generation"], 250)

    def test_actual_duplicates_keep_latest_publication(self):
        rows = [
            {"fuelType": "WIND", **self.row("2026-01-02T10:31:00Z", "2026-01-02T10:00:00Z", 10)},
            {"fuelType": "WIND", **self.row("2026-01-02T11:00:00Z", "2026-01-02T10:00:00Z", 20)},
        ]
        self.assertEqual(normalize_actuals(rows)[as_utc("2026-01-02T10:00:00Z")]["generation"], 20)

    def test_naive_timestamps_assume_utc(self):
        self.assertEqual(as_utc("2026-01-02T10:00:00"), datetime(2026, 1, 2, 10, tzinfo=timezone.utc))

    def test_metrics_match_delivery_intervals_and_skip_unmatched(self):
        actuals = [{"fuelType": "WIND", "publishTime": "2026-01-02T10:30Z", "startTime": "2026-01-02T10:00Z", "generation": 100}]
        forecasts = [self.row("2026-01-01T12:00Z", "2026-01-02T10:00Z", 125), self.row("2026-01-01T12:00Z", "2026-01-02T10:30Z", 999)]
        result = build_analysis(actuals, forecasts)
        self.assertEqual(result["metrics"]["matchedIntervals"], 1)
        self.assertEqual(result["metrics"]["maeMw"], 25)
        self.assertEqual(result["metrics"]["biasMw"], 25)

    def test_records_outside_january_delivery_scope_are_omitted(self):
        actuals = [{"fuelType": "WIND", "publishTime": "2026-01-01T00:30Z", "startTime": "2025-12-31T23:30Z", "generation": 12}]
        self.assertEqual(build_analysis(actuals, []) ["intervals"], [])


if __name__ == "__main__":
    unittest.main()

