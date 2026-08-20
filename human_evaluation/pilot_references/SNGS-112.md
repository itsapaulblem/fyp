# Human reference: SNGS-112

Status: `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Shots on target` |
| Model input | 16 uniform frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-112.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-112.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-112.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-112/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and
coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- Review date: 20 August 2026
- Human-observed phase of play: The red-and-white team attacks through the centre of the pitch. A red-and-white attacker progresses into a shooting position and produces a shot on target, which is saved by the black-team goalkeeper.
- Attacking team by shirt colour: Red and white
- Defending team by shirt colour: Black
- Attacking direction: Through the centre towards the black team's goal.
- Event observed: The red-and-white team progresses through the middle and creates a shooting opportunity. The attacker takes a shot on target, which is caught by the black-team goalkeeper.
- Visible outcome: Shot on target, saved by the goalkeeper 
- Was the official anchor visible in these 16 frames? `yes`

Visible evidence:

1. The red-and-white team is in possession and progresses forward through the centre of the pitch.
2. The black team defends relatively deep as the red-and-white team approaches the goal.
3. A red-and-white attacker is able to take a shot from a central position.
4. The black-team goalkeeper catches the ball following the shot, confirming that the attempt is on target.

## Optional full-sequence observation

Complete this separately if you inspect all 750 frames. Do not use information
visible only in the full sequence to unfairly score what Qwen saw in 16 frames.

- Full-sequence phase: The red-and-white team attacks through the centre and creates a shooting opportunity. A red-and-white attacker takes a shot on target, which is successfully saved by the black-team goalkeeper.
- Full-sequence event and outcome: The red-and-white team successfully progresses into a shooting position and records a shot on target. However, the attempt is saved by the black-team goalkeeper and does not result in a goal.
- Important information missing from the sampled frames: NIL

## Human coaching reference

- Main tactical problem: For the red-and-white team, the attacker is able to create a shot on target, but the attempt is directed too close to the goalkeeper and does not have sufficient power to seriously challenge him. For the black team, the defenders allow the attacker too much space in a central shooting position instead of closing him down before the shot.
- Reasonable coaching recommendation: The red-and-white attacker should aim to place the shot further away from the goalkeeper while generating greater power, making the attempt more difficult to save. Defensively, the black-team players should close down the attacker more quickly and reduce the available shooting space before he is able to take the shot.
- Why the recommendation follows from the visible evidence: The red-and-white attacker is given sufficient space to take a shot from a central position, demonstrating that the black team's defensive pressure is inadequate. Although the shot is on target, it is directed close enough to the goalkeeper for him to make the save. This indicates opportunities for improvement in both the attacker's shot placement and the defenders' closing down.
- Claims that cannot be determined from the frames: NIL

## Original coaching-output error audit

- Qwen's specific errors: Qwen correctly recognises that the red-and-white team is attacking and progressing towards goal but fails to identify the key outcome of the sequence: a shot on target that is saved by the black-team goalkeeper. It also repeats the attacking problem as the defensive problem, resulting in its defensive analysis being incorrectly focused on the red-and-white team rather than the black team's defending.
- Correct observations made by Qwen: Qwen correctly identifies the red-and-white team as the attacking team and recognises that they are progressing towards the black team's goal. Its attacking recommendation is also relevant to the visible attacking situation, although it does not explicitly account for the eventual shot on target.
- Event correct? ` partly, recognises the attacking phase but does not explicitly identify the shot on target `
- Attacking team correct? `yes`
- Outcome correct? `partly, recognises the attacking progression but misses the saved shot on target`
- Advice clip-specific? `yes `
- Major hallucination count: 1 — the attacking problem is repeated as the defensive problem, causing the defensive recommendation to incorrectly focus on the red-and-white team rather than the black team
- Confidence appropriate? `no`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy |1  |  Correctly identifies the red-and-white team as attacking and progressing towards goal but fails to identify the shot on target and goalkeeper's save.|
| Tactical correctness | 1 |Provides reasonable attacking advice for the red team but does not adequately analyse the black team's defensive problem of allowing the attacker space to shoot.  |
| Visual grounding | 1 | Grounds the response in the red-and-white team's forward movement but fails to reference the most important visible event, the shot and subsequent save. |
| Specificity | 0 | Does not identify the shooter, shot on target, goalkeeper's save, or the specific defensive space that allowed the attempt. |
| Actionability |1 | The recommendation provides an action that could be applied by the attacking team, even though the defensive recommendation is incorrectly attributed. |
| Evidence-advice consistency |1  | The attacking advice is broadly consistent with the visible attacking sequence, but the defensive advice does not properly follow from the black team's defensive actions. |
| **Total (0–12)** |  5|  |

## Recognition-gate review

Complete this after reading the separate recognition-only response.

- Phase correct? ` partly `
- Attacking team correct? `yes`
- Event correct? `yes `
- Outcome correct? `no`
- Evidence visibly grounded? `yes `
- Confidence appropriate? ` no`
- Recognition gate passes for this clip? `yes`
- Reviewer notes: Qwen correctly recognises the attacking team and the general attacking sequence but fails to identify the final outcome: a shot on target that is saved by the black-team goalkeeper.
