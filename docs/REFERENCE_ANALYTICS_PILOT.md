# Reference analytics pilot

Protocol: `reference-analytics-v0.1.0`

Status: complete and validated for three train clips

## Purpose

This pilot verifies that official SoccerNet-GSR v1.3 pitch-coordinate
annotations can support direct spatial measurements before possession,
attacking direction, xT, EPV, or tactical-quality labels are inferred.

The selected clips, in run order, are `SNGS-165`, `SNGS-067`, and `SNGS-112`.
No validation or test clip is used.

## Coordinate and visibility definitions

The location of an annotated object is taken from
`bbox_pitch.x_bottom_middle` and `bbox_pitch.y_bottom_middle`, in pitch metres.
The nominal on-pitch rectangle is x = -52.5 to 52.5 and y = -34 to 34.
Finite coordinates out to |x| = 60 and |y| = 45 are retained as plausible
off-pitch annotations, but off-pitch athletes are excluded from shape and
ball-proximity measurements.

Ball-distance metrics use a separate pitch-plus-3-metre tolerance: |x| <=
55.5 and |y| <= 37. This retains plausible throw-in and restart positions but
rejects extreme ground-plane projections of airborne balls. Passing this
geometric check does not prove that an airborne ball is correctly localized;
that remains a visibility limitation and must be considered during claim
verification.

Team labels remain SoccerNet's `left` and `right`. They are not interpreted as
attacking and defending teams in this pilot.

## Direct metrics

For each frame and each team:

- visible on-pitch outfield-player count;
- visible on-pitch goalkeeper count;
- width: 95th percentile y minus 5th percentile y;
- depth: 95th percentile x minus 5th percentile x;
- centroid: arithmetic mean x and y;
- compactness: mean Euclidean distance from the centroid;
- nearest on-pitch athlete distance to the ball;
- on-pitch athlete count within 10 metres of the ball.

Shape metrics require at least five on-pitch outfield players for that team.
Ball metrics require exactly one ball inside the ball-metric bounds and at
least one on-pitch athlete from the relevant team. Missing, ambiguous, or
geometrically implausible values are left empty and accompanied by eligibility
fields; they are never replaced by zero.

## Outputs

Project-derived outputs are written beneath
`data/processed/reference_analytics/pilot/`:

- `object_positions/{clip_id}.csv`: one row per annotated tracked object;
- `frame_metrics/{clip_id}.csv`: one row for every one of the 750 frames;
- `coordinate_checks/{clip_id}.png`: five original-frame/minimap checks;
- `analytics_pilot_summary.json`: coverage, eligibility, and diagnostics.
- `pilot_quality_control.csv`: one eligibility and warning row per pilot clip;
- `validation_report.json`: schema, range, eligibility, and visual checks.

The finalized coverage and known limitations are recorded in
`docs/REFERENCE_ANALYTICS_PILOT_RESULTS.md`.

The coordinate-check images contain NDA-controlled SoccerNet imagery and are
human-review aids only. All outputs remain Git-ignored and must never be shown
to the MLLM.

## Interpretation boundary

These metrics describe only visible, pitch-located players. Changes can be
caused by camera visibility as well as tactics. No value is called good, bad,
wide, narrow, compact, pressured, attacking, or defending in this pilot.
