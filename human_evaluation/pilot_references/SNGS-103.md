# Human reference: SNGS-103

Status: `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Corner` |
| Model input | 16 uniform frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-103.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-103.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-103.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-103/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play / What actually happened: The red team takes a right-sided corner, which is cleared by a black-team defender towards the halfway line. The black team then attempts to transition into a counter-attack, but the sequence ends when a black player fouls a red opponent near the halfway line.
- Attacking team by shirt colour: Red initially during the corner, followed by black during the attempted counter-attack.
- Defending team by shirt colour: Black initially, followed by red after the change of possession.
- Attacking direction: The red team attacks from a right-sided corner. Following the clearance, the black team attempts to counter through the middle of the pitch.
- Event observed: The red team takes a right-sided corner that is cleared towards the halfway line by the black team. The black team attempts to transition forward, but the move ends when a black player fouls a red opponent.
- Visible outcome: The black team concedes a foul near the halfway line, stopping play.
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. Players from both teams are positioned in and around the penalty area for a right-sided corner taken by the red team.
2. The corner is cleared by the black team, with the ball moving towards the halfway line.
3. The black team attempts to transition into attack following the clearance.
4. Play is subsequently stopped, with a red player on the ground following a foul by a black player.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The red team takes a right-sided corner, which is cleared by a black-team defender towards the halfway line. The black team subsequently attempts to transition into a counter-attack, but the sequence ends when a black player fouls a red opponent near the halfway line.
- Full-sequence event and outcome: The red team's corner is successfully cleared by the black team. The black team attempts to counter-attack following the clearance, but the transition is stopped by a foul on a red player near the halfway line.
- Important information missing from the sampled frames: NIL

## Human coaching reference

- Main tactical problem: Red-team midfielder #33 fails to make effective use of the available space when attempting to switch the ball towards the right wing. Despite having sufficient time and space to execute the pass, the delivery is inaccurate and allows the black team to regain possession.
- Reasonable coaching recommendation: Red #33 should improve the accuracy and weight of his passes from central midfield towards the wing. With sufficient time and space available, he should assess the position and movement of the wide player before executing the pass rather than giving possession away unnecessarily.
- Why the recommendation follows from the visible evidence: Red #33 has sufficient space and time to attempt the pass towards the right wing, but the inaccurate delivery results in a turnover. This allows the black team to gain possession and attempt to transition into a counter-attack.
- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen fails to recognise that the sequence begins with a corner and instead describes the situation only as a general attack. Although it identifies passing as an area for improvement for the red team, the recommendation is too vague and is not tied to the specific passing error visible in the sequence. It also repeats the same assessment for the attacking and defensive problems rather than distinguishing between them.
- Correct observations made by Qwen: Qwen recognises that the red team successfully moves the ball from the right side towards a player positioned on the left side of the pitch. It also correctly identifies the red team's passing as an area that could be improved, although the observation lacks sufficient detail.
- Event correct? `no`
- Attacking team correct? `partly, correctly identifies the red team but does not clearly recognise the subsequent change of possession`
- Outcome correct? `partly `
- Advice clip-specific? `no`
- Major hallucination count: `1. Repeats the same assessment for the attacking problem and defensive problem`
- Confidence appropriate? `no`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 | Correctly identifies aspects of the red team's attacking play but fails to recognise the corner and does not fully account for the subsequent transition and foul. |
| Tactical correctness | 1 | Identifies passing as an area for improvement, which is broadly reasonable, but the recommendation does not address the specific passing decision or tactical situation. |
| Visual grounding | 1 | Some observations correspond to visible player and ball movement, but the response does not identify key visible events such as the corner. |
| Specificity | 0 | Does not identify specific players, positions, passing options, or the corner situation. |
| Actionability | 0 | The recommendation to improve passing is too general to provide a clear action that a player could apply to this specific situation. |
| Evidence-advice consistency | 0 | The advice is not sufficiently connected to the specific passing error, turnover, and transition visible in the sequence. |
| **Total (0–12)** | 3 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `unclear`
- Attacking team correct? `yes `
- Event correct? ` unclear`
- Outcome correct? `yes`
- Evidence visibly grounded? `partly`
- Confidence appropriate? `no`
- Recognition gate passes for this clip? ` no`
- Reviewer notes: The response is too vague and fails to identify the corner, despite it being a key event in the sequence. It demonstrates some recognition of the red team's involvement and the final outcome but does not provide sufficiently specific or visually grounded evidence.
