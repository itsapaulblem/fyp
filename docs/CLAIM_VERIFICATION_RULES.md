# Train-derived claim verification rules

Protocol: `claim-verification-v0.1.0-train`

Status: complete and validated for train development

## Purpose and boundary

This protocol converts an atomic, measurable statement from Qwen into one of
four objective evidence states: `supported`, `contradicted`, `inconclusive`,
or `not_measurable`. It evaluates only the stated tracking claim. It does not
decide whether the overall coaching advice is correct or useful.

All thresholds are **derived** exclusively from eligible training windows.
They are conservative operational choices for this experiment, not universal
football standards or SoccerNet-authored labels.

## Prerequisites

Before testing a team-specific claim, the sole reviewer must record:

1. one atomic claim rather than a paragraph of advice;
2. the applicable `before`, `around`, or `after` window, or one named
   transition;
3. a visually supported mapping from Qwen's shirt-colour description to the
   hidden SoccerNet `left` or `right` team;
4. for pressure, confirmation that the mapped team is defending;
5. for support, confirmation that the mapped team is attacking or in
   possession;
6. an eligible value in the selected window or both transition windows.

If any required item is unavailable, return `not_measurable`. Never search all
windows and report only the one that agrees with Qwen. The claim's own temporal
wording or visible evidence must determine the window in advance.

The local-count metric includes every mapped-team athlete within 10 metres of
the ball and may include the ball carrier. It is therefore a local-presence
proxy, not a pure count of supporting teammates.

## Absolute-claim rule

For each metric and window, the eligible `left` and `right` observations are
pooled. The 10th and 90th train percentiles define the low and high extremes.

- A high-direction claim is `supported` at or above p90 and `contradicted` at
  or below p10.
- A low-direction claim is `supported` at or below p10 and `contradicted` at
  or above p90.
- A value between the two thresholds is `inconclusive`.

Example around-event thresholds:

| Metric | Low p10 | High p90 |
| --- | ---: | ---: |
| Team width | 11.90 m | 34.41 m |
| Team depth | 9.07 m | 23.67 m |
| Compactness distance | 5.66 m | 15.00 m |
| Median nearest athlete to ball | 1.12 m | 11.77 m |
| Mean mapped-team athletes within 10 m | 0.37 | 3.01 |

Thresholds differ by window. The authoritative values are in
`metric_thresholds.csv`; this example must not be substituted for another
window.

## Change-claim rule

The available transitions are `before_to_around`, `around_to_after`, and
`before_to_after`. For each metric and transition, the meaningful-change
deadband is the 75th percentile of the absolute eligible train changes.

- For an increase claim, a change at or above the positive deadband is
  `supported`; at or below the negative deadband it is `contradicted`.
- For a decrease claim, the directions reverse.
- Changes inside the deadband are `inconclusive`.

| Metric | Before→around | Around→after | Before→after |
| --- | ---: | ---: | ---: |
| Width | 4.00 m | 6.39 m | 10.45 m |
| Depth | 3.10 m | 7.02 m | 7.27 m |
| Compactness distance | 1.51 m | 2.15 m | 2.96 m |
| Nearest-athlete distance | 2.42 m | 3.48 m | 7.09 m |
| Athletes within 10 m | 0.71 | 0.97 | 1.41 |

For the composite claims `became_more_stretched` and
`became_more_compact`, at least two of width, depth, and compactness must be
measurable. Two or more supported component results produce `supported`; two
or more contradicted results produce `contradicted`; every other measurable
combination is `inconclusive`.

## Claim mapping

| Claim family | Primary evidence | Expected direction |
| --- | --- | --- |
| Too wide | Team width | Absolute high |
| Too narrow | Team width | Absolute low |
| Too deep | Team depth | Absolute high |
| Poor compactness | Mean distance to centroid | Absolute high |
| Insufficient pressure | Defending-team nearest distance to ball | Absolute high |
| Strong pressure | Defending-team nearest distance to ball | Absolute low |
| Insufficient local support | Attacking-team athletes within 10 m | Absolute low |
| Strong local support | Attacking-team athletes within 10 m | Absolute high |
| Became more stretched | Width, depth and compactness changes | Increase, two-of-three |
| Became more compact | Width, depth and compactness changes | Decrease, two-of-three |
| Pressure increased/decreased | Defending-team distance change | Decrease/increase |
| Local support increased/decreased | Attacking-team local-count change | Increase/decrease |

Generic claims about decision-making, intent, communication, coaching quality,
transition quality without a measurable subclaim, penalty-area occupation,
goalkeeper positioning, progression, xT, or EPV remain `not_measurable` under
this protocol.

## Outputs and review records

- `data/processed/reference_analytics/train/metric_thresholds.csv`
- `data/processed/reference_analytics/train/metric_thresholds.json`
- `data/processed/reference_analytics/train/metric_thresholds_validation.json`
- `templates/claim_team_mapping.csv`
- `templates/claim_verification.csv`

The generated threshold files remain Git-ignored reference analytics. Human
team mappings and verification decisions must be recorded separately and must
never be included in the MLLM prompt.
