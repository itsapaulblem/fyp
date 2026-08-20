# Human reference: SNGS-100

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
| Full review video | `data/processed/review_videos/SNGS-100.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-100.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-100.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-100/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play/What actually happened: The red team takes a direct free kick, but the attempt is unsuccessful and is caught by the black team's goalkeeper. The goalkeeper then distributes the ball to initiate a counter-attack. The black team progresses down the left side, but the left winger's cross is overhit and fails to reach any of his teammates, ending the attacking opportunity.

- Attacking team by shirt colour: Red initially, followed by black after the change of possession.

- Defending team by shirt colour: Black initially, followed by red during the counter-attack.

- Attacking direction: The red team takes a direct free kick towards the black team's goal. Following the save, the black team counter-attacks from the left side towards the centre.

- Event observed: The red team takes a direct free kick that is caught by the black goalkeeper. The goalkeeper distributes the ball to the left side, allowing the black team to initiate a counter-attack. The move ends when the black left winger delivers an overhit and inaccurate cross that fails to reach a teammate.

- Visible outcome: An unsuccessful direct free kick by the red team, followed by an unsuccessful counter-attack by the black team.

- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. The red-team players are positioned for a direct free kick.

2. The free kick is caught by the black-team goalkeeper, ending the red team's attacking opportunity.

3. The goalkeeper distributes the ball to the left side, allowing the black team to transition quickly into attack.

4. The black-team left winger attempts a cross, but the delivery is overhit and fails to reach any of his teammates.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The red team takes a direct free kick, which is caught by the black-team goalkeeper. The goalkeeper then distributes the ball to initiate a counter-attack. The black team progresses down the left side before the left winger attempts a cross into the attacking area.

- Full-sequence event and outcome: : The red team's free kick is unsuccessful and is comfortably caught by the goalkeeper. The black team subsequently launches a counter-attack, but the move also fails because the left winger's cross is overhit and does not reach a teammate. Neither attacking phase results in a goal.

- Important information missing from the sampled frames: NIL

## Human coaching reference

- Main tactical problem: There are separate tactical problems for both attacking phases. For the red team, the free-kick delivery is not accurate or threatening enough and is caught by the goalkeeper. A better option may have been to deliver the ball towards a teammate in a position to challenge for a header rather than sending an easily catchable ball towards goal. For the black team, the counter-attack develops successfully down the left side, but the final cross is overhit and inaccurate, preventing any teammate from reaching the ball.

- Reasonable coaching recommendation: The red-team free-kick taker should aim for a more accurate delivery into an area where teammates can challenge for the ball, potentially creating a headed opportunity. During the subsequent counter-attack, the black-team left winger should reduce the power of the cross and aim the delivery towards the movement and position of an available teammate.

- Why the recommendation follows from the visible evidence: The red team's free kick is caught by the goalkeeper without producing a clear goalscoring opportunity. Following the turnover, the black team successfully progresses into an attacking position but wastes the counter-attack because the final cross is too powerful and inaccurate to reach a teammate. In both phases, the quality of the final delivery prevents the attacking team from creating a more dangerous opportunity.
- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen fails to recognise the second attacking phase of the sequence. Although it correctly analyses the red team's free kick and the goalkeeper's save, it does not identify that the black team subsequently transitions into a counter-attack or that the move ends with an inaccurate cross from the left wing.

- Correct observations made by Qwen: Qwen correctly identifies the direct free kick and recognises that the black-team goalkeeper catches the ball, resulting in an unsuccessful attacking attempt by the red team. Its analysis of the initial free-kick phase is therefore strongly grounded in the visible sequence.

- Event correct? `yes `
- Attacking team correct? `partly correctly identifies the red team during the free-kick phase but does not recognise the black team's subsequent attacking phase`
- Outcome correct? `partly correctly identifies the unsuccessful free kick but misses the outcome of the subsequent counter-attack`
- Advice clip-specific? `partly`
- Major hallucination count: 0 
- Confidence appropriate? `yes`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 2 | Correctly identifies the direct free kick, the red team as the initial attacking team, and the goalkeeper's save. However, it omits the subsequent black-team counter-attack.  |
| Tactical correctness |  2| The tactical assessment of the free-kick phase is reasonable and appropriate to the observed situation, although the second attacking phase is not analysed. |
| Visual grounding | 2 | Correctly grounds its analysis in visible events, particularly the free kick and the goalkeeper's save. |
| Specificity | 2 | Provides specific observations regarding the free kick and goalkeeper rather than relying solely on generic attacking advice. |
| Actionability |2  |  Provides a clear recommendation that could be applied to improve the red team's free-kick execution.|
| Evidence-advice consistency | 2 | The recommendation for the free kick follows directly from the observed unsuccessful attempt and goalkeeper's save. |
| **Total (0–12)** | 12 |  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? `yes`
- Attacking team correct? `partly`
- Event correct? `partly`
- Outcome correct? `partly`
- Evidence visibly grounded? `yes`
- Confidence appropriate? `yes`
- Recognition gate passes for this clip? `yes`
- Reviewer notes: Qwen accurately recognises and describes the initial free-kick phase, including the goalkeeper's save. However, it fails to identify the second half of the clip, in which the black team gains possession, launches a counter-attack, and ends the move with an overhit cross.
