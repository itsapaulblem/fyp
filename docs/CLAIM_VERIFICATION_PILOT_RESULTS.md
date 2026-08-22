# Three-clip claim-verification usability check

Protocol: `claim-verification-v0.1.0-train`

Clips: `SNGS-062`, `SNGS-074`, `SNGS-112`

Reviewer: one sole human reviewer

## Result

The reviewer successfully mapped all six outfield-team shirt descriptions to
SoccerNet `left`/`right` and described the actual phase roles. Eight distinct
model assertions were extracted after exact duplicates were collapsed and
compound sentences were separated.

| Result | Assertions |
| --- | ---: |
| Supported | 0 |
| Contradicted by tracking threshold | 0 |
| Inconclusive | 0 |
| Not measurable | 8 |

This does not mean the assertions were correct. It means none stated one of the
frozen measurable tactical claims with a usable window and prerequisites.
Qwen mainly repeated phase descriptions, ball-state descriptions, vague
positioning statements, or advice. Recommendations remain part of the human
coaching-quality rubric rather than being converted into tracking claims.

## Classification decisions

- “Advancing too quickly” is an attacking-tempo claim, not `too_deep`.
- A poorly positioned receiver is not automatically `insufficient_support`.
- “Not fully covering the area” is too vague to force into width or
  compactness.
- “Not in a good position to stop the ball” is not an explicit nearest-player
  pressure claim. In `SNGS-074`, the claimed green defending role also
  conflicts with the human reference: green is attacking after the first
  second.
- “Continue to advance” and “defend the goal” are recommendations, not
  objective claims. They remain human-rated.

The statements were assigned `unspecified` rather than a favourable window
because Qwen did not tie them to the hidden anchor or an identifiable period.
For `SNGS-074`, the white-team possession occurs in approximately the first
second, before the configured `before` window begins at 1.2 seconds.

## Decision

Do not extend this laborious annotation exercise to the remaining nine pilot
clips yet. The three-clip usability check demonstrates that the recording
process works, but the current Qwen outputs do not provide sufficiently
specific measurable tactical claims. The next research decision should address
claim specificity or use the result as evidence of the model's limitation;
analytics must not reinterpret vague statements merely to obtain a numeric
verdict.
