from __future__ import annotations

import unittest

from football_dataset.analytics_index import _quality_tier


class AnalyticsIndexTests(unittest.TestCase):
    def test_fully_eligible_requires_all_metric_families_in_all_windows(self) -> None:
        self.assertEqual(
            _quality_tier(
                structural_pass=True,
                expected_windows=3,
                complete_windows=3,
                shape_windows=3,
                ball_windows=3,
            ),
            "fully_eligible",
        )

    def test_partial_and_tracking_only_are_distinct(self) -> None:
        self.assertEqual(
            _quality_tier(
                structural_pass=True,
                expected_windows=3,
                complete_windows=3,
                shape_windows=1,
                ball_windows=0,
            ),
            "partially_eligible",
        )
        self.assertEqual(
            _quality_tier(
                structural_pass=True,
                expected_windows=3,
                complete_windows=0,
                shape_windows=0,
                ball_windows=0,
            ),
            "tracking_only",
        )

    def test_structural_failure_is_invalid(self) -> None:
        self.assertEqual(
            _quality_tier(
                structural_pass=False,
                expected_windows=3,
                complete_windows=3,
                shape_windows=3,
                ball_windows=3,
            ),
            "invalid",
        )


if __name__ == "__main__":
    unittest.main()
