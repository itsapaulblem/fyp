from __future__ import annotations

import math
import unittest

from football_dataset.reference_analytics import (
    _configured_clip_ids,
    _percentile,
    _shape_metrics,
)


class ReferenceAnalyticsTests(unittest.TestCase):
    def test_percentile_interpolates(self) -> None:
        values = [0.0, 10.0, 20.0, 30.0, 40.0]
        self.assertEqual(_percentile(values, 0.05), 2.0)
        self.assertEqual(_percentile(values, 0.95), 38.0)

    def test_shape_metrics_use_visible_points(self) -> None:
        points = [(0.0, 0.0), (10.0, 10.0), (20.0, 20.0), (30.0, 30.0), (40.0, 40.0)]
        result = _shape_metrics(points, minimum_players=5)
        self.assertTrue(result["eligible"])
        self.assertEqual(result["centroid_x"], 20.0)
        self.assertEqual(result["centroid_y"], 20.0)
        self.assertEqual(result["width"], 36.0)
        self.assertEqual(result["depth"], 36.0)
        expected = mean_distance = sum(
            math.hypot(x - 20.0, y - 20.0) for x, y in points
        ) / len(points)
        self.assertAlmostEqual(result["compactness"], mean_distance)

    def test_shape_metrics_reject_too_few_players(self) -> None:
        result = _shape_metrics([(0.0, 0.0)] * 4, minimum_players=5)
        self.assertFalse(result["eligible"])
        self.assertIsNone(result["width"])
        self.assertIsNone(result["compactness"])

    def test_all_split_selection_is_sorted_and_scoped(self) -> None:
        manifest = [
            {"clip_id": "SNGS-002", "split": "valid"},
            {"clip_id": "SNGS-003", "split": "train"},
            {"clip_id": "SNGS-001", "split": "train"},
        ]
        config = {
            "split": "train",
            "selection": "all_manifest_clips_in_split",
            "expected_clip_count": 2,
        }
        self.assertEqual(
            _configured_clip_ids(config, manifest),
            ["SNGS-001", "SNGS-003"],
        )


if __name__ == "__main__":
    unittest.main()
