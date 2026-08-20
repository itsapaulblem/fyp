# Human reference: SNGS-066

Status: `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Direct free-kick` |
| Model input | 16 uniform frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-066.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-066.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-066.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-066/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play / what actually happened: The green team takes a direct free kick while the white-and-blue team sets up defensively. The free kick is unsuccessful and is caught by the white-and-blue goalkeeper, who then distributes the ball to the left wing to initiate a counter-attack.
- Attacking team by shirt colour: Green initially; white and blue after gaining possession.
- Defending team by shirt colour: White and blue initially; green after the change of possession.
- Attacking direction: Left to right for the white and blue team
- Event observed: The green team's free kick is headed towards goal but is caught by the white-and-blue goalkeeper. The goalkeeper distributes the ball to the left wing to initiate a counter-attack. Instead of progressing forward, the left winger passes backwards to a defender, who then attempts a long ball through the middle.
- Visible outcome: The free kick is unsuccessful and possession changes to the white-and-blue team. Their subsequent counter-attacking opportunity does not result in a clear shot or goal.
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. The players are positioned for a direct free kick, with the green team attacking and the white-and-blue team defending.
2. The green team's #36 heads the free-kick delivery towards goal, but the goalkeeper catches the ball.
3. The goalkeeper distributes the ball to the left wing, after which the winger passes backwards to a defender.
4. The defender attempts to progress play with a long ball through the middle.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The green team takes a direct free kick against the white-and-blue defensive setup. The attempt is caught by the goalkeeper, who quickly distributes the ball to the left wing to initiate a counter-attack. The winger then passes backwards to a defender, who attempts a long ball through the middle.

- Full-sequence event and outcome: The green team's free kick is unsuccessful. The white-and-blue team subsequently attempts to counter-attack but fails to create a clear goalscoring opportunity.

- Important information missing from the sampled frames: NIL

## Human coaching reference

- Main tactical problem: There are tactical issues for both teams during the sequence. For the green team, #36's header lacks sufficient power and is directed upwards rather than forcefully towards goal, allowing the goalkeeper to make a comfortable catch. For the white-and-blue team, the left winger slows down a potential counter-attack by passing backwards instead of looking to progress the ball forward while the green team is still recovering defensively.

- Reasonable coaching recommendation: Green #36 should aim to direct the header more powerfully and towards goal rather than upwards. After the goalkeeper gains possession, the white-and-blue left winger should look to progress the ball forward, either by carrying it into space or finding a forward passing option, before choosing to recycle possession backwards.

- Why the recommendation follows from the visible evidence: he goalkeeper is able to catch the green team's headed attempt without significant difficulty, suggesting that the header poses limited threat. Following the turnover, the white-and-blue team has an opportunity to transition quickly, but the backward pass from the left wing slows the attack and gives the green team additional time to recover defensively. Neither attacking sequence ultimately produces a goal or a clear subsequent shot on target.

- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen does not clearly recognise the change of possession and therefore fails to distinguish between the two attacking phases in the sequence. It also repeats the attacking problem and recommendation as the defensive problem and recommendation, resulting in advice being assigned to the wrong team. The response lacks specific references to the free kick, #36's header, the goalkeeper's distribution, and the white-and-blue team's attempted counter-attack.
- Correct observations made by Qwen: : Qwen identifies the green team only and provides a generally applicable recommendation about progressing the ball towards the opponent's goal. It also suggests passing drills to improve ball control, although this recommendation is not well matched to the specific events in the clip.
- Event correct? `unclear`
- Attacking team correct? `partly, the clip contains a change of possession, resulting in two distinct attacking phases`
- Outcome correct? `no`
- Advice clip-specific? `partly`
- Major hallucination count: 1 (the attacking problem and recommendation were repeated as the defensive problem and recommendation, causing advice to be attributed to the wrong team)
- Confidence appropriate? `no`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 |  Identifies one of the attacking teams but fails to account adequately for the change of possession and the second attacking phase. |
| Tactical correctness | 1 | Provides broadly reasonable advice about progressing towards the opponent's goal, but the recommendation is generic and does not address the specific tactical decisions visible in the sequence. |
| Visual grounding | 1 | Identifies the green and white-and-blue teams but provides few references to specific visible actions, players, or events. |
| Specificity | 0 | Does not identify specific players, actions, passing decisions, or moments from the sequence. |
| Actionability | 1 | The recommendation to practise passing and improve ball control is actionable in general, but it is assigned to the wrong team and does not directly address the main tactical problems in the clip.  |
| Evidence-advice consistency | 0 | The recommendation does not follow clearly from the observed evidence and is attributed to the wrong team. |
| **Total (0–12)** | 4 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `unclear`
- Attacking team correct? `partly`
- Event correct? `partly`
- Outcome correct? `no`
- Evidence visibly grounded? `no`
- Confidence appropriate? `no`
- Recognition gate passes for this clip? `no`
- Reviewer notes: The response contains some generally reasonable tactical advice, but it attributes the recommendation to the wrong team and fails to clearly recognise the change of possession and the two distinct attacking phases.
