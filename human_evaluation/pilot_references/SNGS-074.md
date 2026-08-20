# Human reference: SNGS-074

Status: `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Clearance` |
| Model input | 16 uniform frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-074.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-074.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-074.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-074/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play / What actually happened: The white-and-blue goalkeeper restarts play with a long goal kick. The ball is not successfully retained by the white-and-blue team and instead falls to the green team, who gain possession and begin an attack.
- Attacking team by shirt colour: White and blue initially, followed by green after the change of possession.
- Defending team by shirt colour: Green initially, followed by white and blue after the change of possession.
- Attacking direction: The green team initially progresses down the left side before moving the ball towards the centre.
- Event observed: The white-and-blue goalkeeper plays a long goal kick, but possession is subsequently won by the green team. The green team then transitions into attack.
- Visible outcome: Open play, with the green team gaining possession and attacking.
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. The players are positioned upfield while the white-and-blue goalkeeper prepares to restart play with a long kick.
2. Following the goalkeeper's distribution, possession changes to the green team.
3. A green player on the left side begins progressing forward to initiate an attack.
4. The white-and-blue defenders retreat and reorganise to defend against the green team's attack.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The white-and-blue goalkeeper restarts play with a long kick, but the team fails to retain possession. The ball falls to the green team, who transition into attack and progress forward.

- Full-sequence event and outcome: The white-and-blue team loses possession following the goalkeeper's long distribution. The green team subsequently attacks and creates a shooting opportunity, but the attempt appears to go wide. No goal is scored.

- Important information missing from the sampled frames: The full sequence shows a green midfielder taking a shot from distance that appears to go wide.

## Human coaching reference

- Main tactical problem: The white-and-blue goalkeeper's long distribution fails to find a teammate, resulting in an avoidable loss of possession and allowing the green team to attack. After winning possession, however, the green team does not exploit the transition quickly enough and ultimately settles for a low-probability shot from distance.

- Reasonable coaching recommendation: The white-and-blue goalkeeper should aim for a more controlled and accurate distribution towards a teammate in a position to retain possession. After winning the ball, the green team's left-sided player should progress forward more quickly to exploit the available space. As the attack develops, the green midfielder should assess available passing options rather than immediately attempting a speculative shot from distance.

- Why the recommendation follows from the visible evidence: The white-and-blue team gives possession away following the goalkeeper's long distribution, creating an attacking opportunity for the green team. The green team is able to progress forward but fails to convert the turnover into a clear goalscoring opportunity. In the full sequence, the attack ends with a long-range attempt that appears to go wide.

- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen fails to recognise the second phase of the sequence, in which the green team gains possession following the goalkeeper's distribution and transitions into attack. As a result, its analysis focuses primarily on the white-and-blue team's distribution and does not adequately evaluate the green team's subsequent attacking opportunity.
- Correct observations made by Qwen: Qwen correctly identifies that the white-and-blue team loses possession too easily following the goalkeeper's distribution. It also recognises issues with the white-and-blue team's positioning and readiness to retain possession after the restart.
- Event correct? `yes`
- Attacking team correct? `partly the model recognises the white-and-blue team's initial phase but does not adequately recognise the green team's subsequent attack`
- Outcome correct? `no`
- Advice clip-specific? `yes `
- Major hallucination count: 0
- Confidence appropriate? `no`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 0 | The response treats the white team as attacking throughout and misses the decisive turnover and green-team attack. |
| Tactical correctness | 0 | The claims that the white team advances too quickly and that a receiver is poorly positioned are not supported by the reviewed sequence. |
| Visual grounding | 1 | It identifies the two shirt colours and a general attacking context, but it does not ground the analysis in the goalkeeper distribution or turnover. |
| Specificity | 0 | It does not identify the goalkeeper, distribution, change of possession, green transition, or a concrete receiving position. |
| Actionability | 1 | Passing to a better-positioned teammate and improving defensive coverage are actions, but they remain generic and are applied to an incorrect reading of the sequence. |
| Evidence-advice consistency | 0 | The recommendations follow unsupported claims and do not address the actual loss of possession or green-team attack. |
| **Total (0–12)** | 2 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `partly `
- Attacking team correct? `partly`
- Event correct? `partly`
- Outcome correct? `partly`
- Evidence visibly grounded? `partly`
- Confidence appropriate? `no`
- Recognition gate passes for this clip? `no`
- Reviewer notes: The response correctly identifies elements of the initial white-and-blue phase but fails to recognise the second half of the clip, where the green team gains possession and transitions into attack.
