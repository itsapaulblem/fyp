from __future__ import annotations

import unittest

from football_dataset.temporal_analytics import _eligible, _window_for_offset


WINDOWS = [
    {"name": "before", "start_offset_seconds": -5.0, "end_offset_seconds": -2.0},
    {"name": "around", "start_offset_seconds": -2.0, "end_offset_seconds": 2.0},
    {"name": "after", "start_offset_seconds": 2.0, "end_offset_seconds": 5.0},
]


class TemporalAnalyticsTests(unittest.TestCase):
    def test_window_boundaries_are_non_overlapping(self) -> None:
        self.assertEqual(_window_for_offset(-5.0, WINDOWS), "before")
        self.assertEqual(_window_for_offset(-2.0, WINDOWS), "around")
        self.assertEqual(_window_for_offset(2.0, WINDOWS), "after")
        self.assertIsNone(_window_for_offset(5.0, WINDOWS))

    def test_metric_summary_requires_complete_window(self) -> None:
        self.assertTrue(_eligible(80, 100, True, 0.8))
        self.assertFalse(_eligible(79, 100, True, 0.8))
        self.assertFalse(_eligible(80, 100, False, 0.8))


if __name__ == "__main__":
    unittest.main()
