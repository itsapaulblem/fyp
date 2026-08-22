# Train-wide reference analytics results

Protocol: `reference-analytics-v0.2.0-train`

Status: structurally passed with data-quality warnings

These outputs are **derived** from hidden official SoccerNet-GSR v1.3
annotations. They are reference measurements for later verification of
specific MLLM claims. They are not model inputs and are not ground-truth
coaching advice.

## Extraction result

- All 57 manifest-listed train clips were processed.
- Every clip has exactly 750 ordered frame rows: 42,750 total.
- The object-position tables contain 733,001 rows.
- All 57 frame tables, 57 object tables, and 57 coordinate-check images exist.
- Schema, identifier, numeric-range, eligibility, and artifact validation found
  zero errors.
- All 11 project unit tests pass.

The extraction therefore passes structural quality control. The overall QC
status is `pass_with_data_quality_warnings` because broadcast visibility and
some source annotations limit which metrics are usable in each clip.

## Coverage result

| Measurement | Provisional threshold | Clips meeting threshold | Train mean | Train minimum |
| --- | ---: | ---: | ---: | ---: |
| Both-team shape | 80% of frames | 26/57 | 75.8% | 32.7% |
| Ball metrics | 90% of frames | 16/57 | 79.2% | 35.1% |
| Both conditions | Both thresholds | 7/57 | — | — |

The seven clips meeting both thresholds are `SNGS-062`, `SNGS-068`,
`SNGS-074`, `SNGS-109`, `SNGS-112`, `SNGS-113`, and `SNGS-168`. These are not
the only usable clips: a clip below the whole-clip threshold may still have an
eligible event window. Eligibility must be checked for the exact time window
and metric being used.

## Significant source-data limitations

- Six clips contain frames with two distinct plausible ball tracks. Those 645
  ambiguous frames are excluded from ball metrics: `SNGS-061` (8),
  `SNGS-102` (7), `SNGS-105` (236), `SNGS-164` (119), `SNGS-166` (252), and
  `SNGS-169` (23).
- There are 4,617 object annotations without pitch coordinates across 22
  clips. The largest concentrations are `SNGS-077` (3,047) and `SNGS-072`
  (1,161). Missing values are retained but never treated as zero.
- The ground-plane projection produced 3,769 geometrically implausible
  coordinates, predominantly from airborne balls. They are retained in the
  object tables with failed eligibility and excluded from direct metrics.
- `SNGS-065`, `SNGS-071`, and `SNGS-106` have ball-metric coverage below 50%.
- `SNGS-101`, `SNGS-106`, `SNGS-114`, `SNGS-155`, `SNGS-157`, and `SNGS-158`
  have both-team shape coverage below 50%.
- Off-pitch athlete annotations can represent legitimate throw-ins or players
  outside the touchline; they are retained but excluded from team-shape and
  proximity calculations.

These are not extraction crashes or fabricated repairs. They are explicit
eligibility limitations in the official annotation-derived data.

## Output locations

- `frame_metrics/{clip_id}.csv`: 750 frame-level metric rows per clip.
- `object_positions/{clip_id}.csv`: annotation-derived object positions.
- `coordinate_checks/{clip_id}.png`: five diagnostic frames per clip.
- `train_quality_control.csv`: one searchable QC row per clip.
- `analytics_train_summary.json`: detailed extraction summary.
- `validation_report.json`: complete structural and coverage validation.

All are stored under `data/processed/reference_analytics/train/` and remain
Git-ignored because they are derived from NDA-controlled SoccerNet data.

## Decision

Proceed to train-only temporal-window aggregation, but apply metric-specific
eligibility. Do not calculate a confident team-shape, ball-pressure, xT, or
EPV value for a window whose required annotations fail coverage checks. Do
not process validation or test until the temporal definitions and claim
mapping have been developed on train and then frozen according to the split
policy.
