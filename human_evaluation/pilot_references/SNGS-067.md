# Human reference: SNGS-067

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
| Full review video | `data/processed/review_videos/SNGS-067.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-067.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-067.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-067/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play: Corner followed by a transition into open play.
- Attacking team by shirt colour: White and blue initially; green following the change of possession.
- Defending team by shirt colour: Green initially; white and blue during the subsequent counter-attack.
- Attacking direction: The white-and-blue team takes a corner from the right side. After regaining possession, the green team counter-attacks from left to right.
- Event observed: The white-and-blue team takes a corner that is cleared by the green team. The green team then attempts to counter-attack, but the move is intercepted. Possession returns to the white-and-blue team, and the ball is played back to their goalkeeper, who sends it long.
- Visible outcome: Open play, with neither the corner nor the subsequent counter-attack resulting in a goal.
- What actually happened: : The white-and-blue team takes a corner from the right side, which is cleared by the green team. The green team attempts to transition quickly into a counter-attack but loses possession after an intercepted pass. The ball is subsequently played back to the white-and-blue goalkeeper, who restarts the attack with a long pass.
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. Players from both teams are positioned in and around the penalty area for a right-sided corner taken by the white-and-blue team.
2. Following the corner, the green team gains possession, with a player on the left wing carrying the ball forward to initiate a counter-attack.
3. The green team's attempted progression is intercepted, and possession returns to the white-and-blue team.
4. The ball is eventually played back to the white-and-blue goalkeeper.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The white-and-blue team takes a right-sided corner, which is headed clear by a green defender. The green team then attempts to counter-attack but loses possession after an intercepted pass. The ball is subsequently recycled back to the white-and-blue goalkeeper, who sends a long ball forward.

- Full-sequence event and outcome: The white-and-blue team's corner does not create a successful goalscoring opportunity. The green team's subsequent counter-attack is also unsuccessful, and play continues without a goal.

- Important information missing from the sampled frames: The full sequence clearly shows that the white-and-blue team's corner is headed away by a green defender.

## Human coaching reference

- Main tactical problem: There are separate tactical issues for both teams. For the white-and-blue team, the corner delivery is too close to the goalkeeper and does not provide sufficient height or accuracy to reach a teammate in a more dangerous area, allowing the green team to clear the ball. For the green team, the subsequent counter-attack is wasted by an inaccurate or poorly selected pass that is easily intercepted rather than exploiting the available space.

- Reasonable coaching recommendation: The white-and-blue corner taker should aim for a higher and more accurate delivery into a dangerous area where teammates have a better opportunity to challenge for the ball. During the subsequent counter-attack, the green player in possession should assess the available space and the positions of teammates before attempting the forward pass, rather than forcing a pass that can be easily intercepted.

- Why the recommendation follows from the visible evidence: The corner is cleared without producing a clear goalscoring opportunity, indicating that the delivery does not effectively find an attacking teammate. After the turnover, the green team has an opportunity to transition quickly, but the counter-attack ends when a pass is easily intercepted. Both attacking opportunities therefore break down because of ineffective ball delivery.

- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen fails to recognise the corner as the initial event despite the set-piece setup being visible in the sampled frames. It also does not clearly recognise the change of possession and the two distinct attacking phases involving the white-and-blue team's corner and the green team's counter-attack. In addition, it repeats the attacking problem as the defensive problem rather than providing separate tactical assessments for the two phases.

- Correct observations made by Qwen: Qwen correctly suggests that the white-and-blue team's initial delivery should have been directed further to the left, which is relevant to improving the effectiveness of the corner despite the model not explicitly identifying the event as a corner. It also correctly recognises the need for the white-and-blue team to be prepared to prevent a counter-attack after losing possession.

- Event correct? `no`
- Attacking team correct? `partly`
- Outcome correct? `no`
- Advice clip-specific? `no`
- Major hallucination count: 1 (gave the same answer of the attacking problem to the defensive problem) 
- Confidence appropriate? `no`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 |  Correctly identifies one attacking team but fails to recognise the corner and does not adequately distinguish the two attacking phases. |
| Tactical correctness | 2|  Provides tactically reasonable suggestions regarding the initial delivery and the need for the white-and-blue team to prevent the subsequent counter-attack. |
| Visual grounding |  1| Some recommendations correspond to visible actions in the clip, but the response fails to explicitly identify the clearly visible corner and provides limited reference to specific events. |
| Specificity | 1 | Provides some context-specific advice but does not identify individual players, specific positions, or key football events such as the corner and transition. |
| Actionability | 1 | The recommendations provide actions that could be implemented, but they remain relatively general and are not clearly assigned to the correct phases of play. |
| Evidence-advice consistency | 1 | Some recommendations are supported by the visible sequence, particularly regarding the delivery and defensive transition, but the failure to recognise the event and change of possession weakens the connection between the evidence and advice. |
| **Total (0–12)** | 7 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `unclear`
- Attacking team correct? `partly`
- Event correct? `partly`
- Outcome correct? `no`
- Evidence visibly grounded? `yes`
- Confidence appropriate? `no`
- Recognition gate passes for this clip? `yes`
- Reviewer notes: The response demonstrates some visual understanding of the sequence and identifies relevant aspects of the attacking and defensive play. However, it fails to explicitly recognise the corner and does not clearly distinguish the change of possession between the white-and-blue team's set piece and the green team's subsequent counter-attack.
