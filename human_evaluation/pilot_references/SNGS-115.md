# Human reference: SNGS-115

Status: `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Shots off target` |
| Model input | 16 uniform frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-115.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-115.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-115.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-115/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play/ what actually happened: The red-and-white team attacks against a deep black-team defensive line. A red midfielder initially delivers the ball into the penalty area, but the black team clears it. The red team regains possession and works the ball towards the left wing, where another cross is delivered into the box. A red attacker meets the cross with a header, but the attempt goes wide of the goal.
- Attacking team by shirt colour: Red and white
- Defending team by shirt colour: Black
- Attacking direction: The attack develops through the centre before moving to the left wing and then back into the penalty area.
- Event observed: The red team creates a crossing opportunity from the left wing. A red attacker connects with the cross using a header, but the attempt misses the target.
- Visible outcome: Shot off target. The headed attempt goes wide and no goal is scored.
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. The red-and-white players push forward and occupy attacking positions around the black team's penalty area.
2. The black team defends deep, with several players positioned around the penalty area.
3. After the initial delivery is cleared, the red team regains possession and creates another crossing opportunity from the left side.
4. A red attacker meets the cross with a header, but the attempt goes wide of the goal and play subsequently stops.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The red-and-white team sustains an attack against a deep black-team defence. An initial delivery into the penalty area is cleared, but the red team regains possession and moves the ball towards the left wing. A cross is then delivered into the penalty area, where a red attacker attempts a header.

- Full-sequence event and outcome: The red team creates a headed goalscoring opportunity following a cross from the left wing. The attacker connects with the ball but directs the header wide of the goal, resulting in a shot off target and no goal.

- Important information missing from the sampled frames: NIL

## Human coaching reference

- Main tactical problem: For the red team, the final header lacks sufficient accuracy and is directed wide of the goal. The attacker could have focused on directing the header towards the target or, if a better-positioned teammate was available centrally, considered redirecting the ball towards that teammate. For the black team, the right-sided defender allows the cross to be delivered too easily, while the defenders inside the penalty area give the red attacker enough space to challenge for the header.

- Reasonable coaching recommendation: The red attacker should focus on improving the placement and control of the header, prioritising accuracy towards the goal rather than simply making contact with the cross. The black team's right-sided defender should close down the winger earlier to reduce the quality of the cross, while the central defenders should mark attacking players more tightly inside the penalty area.

- Why the recommendation follows from the visible evidence: The red team successfully creates a crossing opportunity and finds an attacker inside the penalty area, but the resulting header goes wide. This indicates that the attack breaks down primarily at the final execution stage. Defensively, the black team allows both the cross to enter the penalty area and the red attacker to make contact with it, suggesting that greater pressure on the crosser and tighter marking inside the box could have prevented the opportunity.

- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen fails to identify the key event and outcome of the sequence: the red attacker's headed shot going wide for a shot off target. It only recognises a general attacking sequence and describes the airborne ball as a "potential shot or pass." Its claim that the attacking team is "moving too quickly" is not clearly supported by the visible evidence. The attacking recommendation to "maintain a clear path to the goal" is also vague and does not address the actual problem of the inaccurate header.

- Correct observations made by Qwen:  Qwen correctly identifies the red-and-white team as the attacking side and the dark/black team as the defending side. It also recognises that the red team is advancing towards goal, that the black team is positioned defensively in front of goal, and that the ball is played through the air. Its defensive observation that the black team could cover the area in front of goal more effectively is broadly consistent with the red attacker being allowed to contest the cross.
- Event correct? `partly, recognises an attack and an airborne ball near goal but does not identify the headed shot`
- Attacking team correct? `yes`
- Outcome correct? `no — fails to recognise that the header goes wide for a shot off target`
- Advice clip-specific? `partly — the defensive recommendation has some relevance, but the attacking recommendation is generic and does not address the missed header`
- Major hallucination count: `1 — claims that the red team is "moving too quickly," despite insufficient visible evidence to support this as the main attacking problem`
- Confidence appropriate? `no — high confidence is not justified given that the model fails to identify the key event and final outcome`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 | Correctly identifies the red-and-white team as attacking and the black team as defending, but fails to recognise the headed shot and its off-target outcome.  |
| Tactical correctness |1  | The suggestion that the black team should cover the area in front of goal more effectively is reasonable, but the claim that the red team is attacking too quickly is not clearly supported by the sequence.|
| Visual grounding | 1 | Correctly refers to the attacking team progressing towards goal, the defending team protecting the goal, and the ball being airborne, but misses the specific cross, header, and off-target outcome.  |
| Specificity | 0 | Does not identify the cross, the red attacker making the header, the shot going wide, or any specific player or position involved in the key event. |
| Actionability |1  | The defensive recommendation to improve positioning provides a general action, but the attacking recommendation to "maintain a clear path to the goal" is too vague to guide a specific improvement. |
| Evidence-advice consistency |1  | The defensive recommendation is broadly supported by the visible attacking pressure, but the attacking recommendation is weakly connected to the actual failure, which is the inaccurate headed attempt. |
| **Total (0–12)** | 5 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `yes correctly identifies the sequence as an attacking phase `
- Attacking team correct? `yes correctly identifies the red-and-white team`
- Event correct? `no — labels the event as a goal rather than a headed shot off target`
- Outcome correct? `no — fails to recognise that the header goes wide for a shot off target`
- Evidence visibly grounded? `partly — several observations correspond to the frames, but they remain generic and omit the key even`
- Confidence appropriate? `no — "high" confidence is inappropriate because the model expresses uncertainty about whether the airborne ball is a shot or pass and misses the final outcome`
- Recognition gate passes for this clip? `no`
- Reviewer notes: Qwen correctly recognises the attacking team, general phase of play, and defensive setup. However, it fails to recognise the most important event in the sequence: the red attacker heads the cross wide for a shot off target. The recognition is therefore sufficient for the general attacking context but incomplete at the event and outcome level.
