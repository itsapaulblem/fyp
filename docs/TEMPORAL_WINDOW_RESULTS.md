# Train temporal-window analytics

Protocol: `reference-windows-v0.1.0-train`

Status: complete and validated on all 57 train clips

## Purpose

Frame-level values are converted into event-relative summaries so measurable
parts of an MLLM claim can be compared across phases of the same sequence.
Official action timing is hidden reference information and must never be
provided to the MLLM.

## Frozen train-development windows

| Window | Relative interval | Planned frames |
| --- | --- | ---: |
| Before | `[-5, -2)` seconds | 75 |
| Around | `[-2, +2)` seconds | 100 |
| After | `[+2, +5)` seconds | 75 |

All starts are inclusive and ends are exclusive. These boundaries are used
instead of the earlier approximate ±10-second suggestion because most
SoccerNet anchors occur near 6 or 24 seconds; ±10 seconds would truncate most
outer windows and make cross-clip comparisons inconsistent.

A metric summary requires both a complete temporal window and at least 80%
eligible source frames for that metric and team. Otherwise its value is empty,
not zero. Team identities remain `left` and `right`.

## Derived metrics per team and window

- median width, depth, centroid x/y, and compactness;
- median and minimum nearest-athlete distance to the ball;
- mean visible athletes within 10 metres of the ball;
- changes in width, depth, compactness, ball distance, and local player count
  from the preceding window;
- temporal, shape, and ball eligibility counts and coverage.

## Validation result

All 171 expected rows passed protocol, boundary, ordering, eligibility,
numeric-range, and delta-consistency validation with zero errors.

| Window | Temporally complete | Both-team shape eligible | Both-team ball eligible |
| --- | ---: | ---: | ---: |
| Before | 56/57 | 42/57 | 51/57 |
| Around | 56/57 | 39/57 | 26/57 |
| After | 57/57 | 41/57 | 32/57 |

Across all three windows, 32 clips support both-team shape summaries, 22
support both-team ball summaries, and 12 support both metric families:
`SNGS-062`, `SNGS-068`, `SNGS-069`, `SNGS-074`, `SNGS-076`, `SNGS-102`,
`SNGS-109`, `SNGS-112`, `SNGS-113`, `SNGS-162`, `SNGS-164`, and `SNGS-168`.

`SNGS-060` has an unusually early anchor. Its before and around windows are
temporally incomplete and therefore ineligible. `SNGS-165` is temporally
complete but lacks sufficient visible players for reliable post-anchor team
shape summaries. These are explicit data limitations, not processing errors.

## Outputs

- `data/processed/reference_analytics/train/window_metrics.csv`
- `data/processed/reference_analytics/train/window_metrics_summary.json`
- `data/processed/reference_analytics/train/window_metrics_validation.json`

These outputs are **derived** reference analytics, remain Git-ignored, and are
not shown to Qwen. They can verify only measurable claims; they do not replace
the sole reviewer's judgement of overall coaching quality.

## Next methodological step

The train-only claim-to-metric mapping and thresholds are now complete under
`claim-verification-v0.1.0-train`; see
`docs/CLAIM_VERIFICATION_RULES.md`. The next step is a small manual application
to the existing train pilot claims before any validation or test processing.
