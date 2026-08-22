from __future__ import annotations

import unittest

from football_dataset.claim_thresholds import (
    classify_absolute,
    classify_change,
    combine_component_results,
)


class ClaimThresholdTests(unittest.TestCase):
    def test_absolute_high_rule(self) -> None:
        self.assertEqual(classify_absolute(12.0, 3.0, 10.0, "absolute_high"), "supported")
        self.assertEqual(classify_absolute(2.0, 3.0, 10.0, "absolute_high"), "contradicted")
        self.assertEqual(classify_absolute(6.0, 3.0, 10.0, "absolute_high"), "inconclusive")
        self.assertEqual(classify_absolute(None, 3.0, 10.0, "absolute_high"), "not_measurable")

    def test_change_decrease_rule(self) -> None:
        self.assertEqual(classify_change(-4.0, 3.0, "change_decrease"), "supported")
        self.assertEqual(classify_change(4.0, 3.0, "change_decrease"), "contradicted")
        self.assertEqual(classify_change(1.0, 3.0, "change_decrease"), "inconclusive")

    def test_composite_requires_two_measurable_agreements(self) -> None:
        self.assertEqual(
            combine_component_results(
                ["supported", "supported", "inconclusive"], 2
            ),
            "supported",
        )
        self.assertEqual(
            combine_component_results(
                ["supported", "not_measurable", "not_measurable"], 2
            ),
            "not_measurable",
        )
        self.assertEqual(
            combine_component_results(
                ["supported", "contradicted", "inconclusive"], 2
            ),
            "inconclusive",
        )


if __name__ == "__main__":
    unittest.main()
