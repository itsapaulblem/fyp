# Reference analytics pilot results

Protocol: `reference-analytics-v0.1.0`

Status: complete and validated on three train clips

These results are **derived** from hidden SoccerNet-GSR v1.3 annotations. They
are reference analytics for later claim verification, not inputs to the MLLM
and not ground-truth coaching advice.

## Validation outcome

All three clips passed the automated schema, row-count, eligibility, range,
and artifact checks with zero errors. The output contains 2,250 frame rows in
total: 750 each for `SNGS-165`, `SNGS-067`, and `SNGS-112`. Five coordinate
check frames per clip were also reviewed; the image-space boxes and pitch
minimaps aligned plausibly in all 15 checks.

| Clip | Ball-metric coverage | Both-team shape coverage | Object rows | Off-pitch athlete annotations | Excluded implausible ball projections |
| --- | ---: | ---: | ---: | ---: | ---: |
| SNGS-165 | 88.5% | 64.3% | 11,525 | 593 | 55 |
| SNGS-067 | 82.5% | 100.0% | 14,739 | 151 | 71 |
| SNGS-112 | 96.3% | 82.1% | 11,840 | 55 | 18 |

An off-pitch annotation is not automatically an annotation error. It can be a
legitimate player outside the touchline, including a throw-in participant.
Those rows are retained in the object-position tables but excluded from the
frame-level tactical measurements.

## Important limitations

- `SNGS-165` has low simultaneous team-shape coverage. Its shape metrics are
  available for only 64.3% of frames because the broadcast view does not show
  enough on-pitch outfield players from both teams.
- Ball-distance coverage is below 90% in `SNGS-165` and `SNGS-067`.
- The SoccerNet ground-plane projection can place an airborne ball at
  impossible pitch coordinates. The pilot excludes 55, 71, and 18 such ball
  annotations respectively; it does not silently convert them to zero.
- A ball coordinate that passes the geometric bounds can still be inaccurate
  when the ball is airborne. Ball-proximity claims therefore require visual
  checking around the relevant time window.
- Team identities remain `left` and `right`. This pilot does not infer
  possession, attacking direction, attack/defence roles, xT, or EPV.

The warnings are data and measurement limitations rather than failed output
generation. The pilot is suitable for proceeding to time-window aggregation
and claim verification, provided the eligibility flags are respected.
