# Human reference: SNGS-062

Status: `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No, pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Foul` |
| Model input | 16 uniform frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-062.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-062.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-062/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play / What happened: Slow build-up play from the back by the green team, with passes across the pitch deep inside their own half. The green team then played a long ground pass to a teammate in midfield, where the move ended with a foul by the white-and-blue team.
- Attacking team by shirt colour: Green
- Defending team by shirt colour: White and Blue
- Attacking direction: Middle
- Event observed: Foul
- Visible outcome: Foul
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. The ball is passed around deep inside the green team’s half.
2. The referee signals for a foul and stops play, causing the players to stop running.
3. Green team’s number 14 is tackled and falls to the ground.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: Slow build up play from the back by the green team, passing across the pitch deep in the green half, green team layed a long ground pass to the teammate at the middle pitch and ended with a foul by the white and blue team in the middle of the pitch.
- Full-sequence event and outcome: The green team builds up play by passing at the back before being fouled.
- Important information missing from the sampled frames: NIL, all information is visible

## Human coaching reference

- Main tactical problem: The green team spent too much time passing at the back instead of progressing the ball through the wings. The central midfielders were already tightly marked by the white team, limiting viable passing options through the middle.
- Reasonable coaching recommendation: Green team player #50 should have played the ball to the left wing earlier rather than recycling possession backwards and continuing to pass across the back line.
- Why the recommendation follows from the visible evidence: The slow build-up allowed the white team enough time to recover their defensive shape and tightly mark the green team’s midfielders, making it more difficult for the green team to progress through the centre. 
- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen does not identify the foul as the final outcome of the sequence and provides overly general tactical advice without identifying specific players or passing options.
- Correct observations made by Qwen: Qwen correctly identifies the green team as the team in possession and recognises that the team is attempting to build up play from the back.
- Event correct? `partly`
- Attacking team correct? `yes`
- Outcome correct? `partly`
- Advice clip-specific? `partly`
- Major hallucination count: 1 (Defensive recommendation is completely wrong, gave attacking recommendation instead)
- Confidence appropriate? `no`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 | Correctly identifies the green team as the team in possession but does not identify the foul as the final outcome. |
| Tactical correctness | 0 | It does not identify a tactical problem; the response merely repeats that the green team is advancing with the ball. |
| Visual grounding | 1 | Refers to the general build-up situation but does not sufficiently ground the analysis in specific players or actions. |
| Specificity | 0 | Identifying only the green team is not enough to make the advice clip-specific; no player, position, event, or passing option is identified. |
| Actionability | 0 | “Continue to advance with the ball” does not state a corrective coaching action. |
| Evidence-advice consistency | 0 | The recommendation is not connected to the missed foul or to a clearly identified tactical problem. |
| **Total (0–12)** | 2 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `partly`
- Attacking team correct? `yes`
- Event correct? `no`
- Outcome correct? `no`
- Evidence visibly grounded? `partly`
- Confidence appropriate? `no`
- Recognition gate passes for this clip? `no`
- Reviewer notes: The recognition-only response identifies generic passing but does not recognise the foul or stoppage. Coaching recommendations are assessed separately and are not part of this gate.
