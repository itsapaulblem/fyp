# Human Reference: SNGS-159

**Status:** `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Shots on target` |
| Model input | 16 uniformly sampled frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-159.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-159.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-159.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-159/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- **Review date:** 20 August 2026
- **Human-observed phase of play / What actually happened:** The black team attacks from the right side. After the initial attacking move is partially cleared by the white team, a black player regains possession and attempts a long-range shot. The shot is on target and is saved by the white-team goalkeeper. The goalkeeper then distributes the ball to a defender, but the defender misplays the pass and gives possession back to the black team.
- **Attacking team by shirt colour:** Black initially, followed briefly by white after the goalkeeper's save, before possession is lost back to the black team.
- **Defending team by shirt colour:** Predominantly white during the black team's attack.
- **Attacking direction:** The black team's attack develops from the right side towards the centre.
- **Event observed:** A black-team player takes a long-range shot on target, which is saved by the white-team goalkeeper.
- **Visible outcome:** The shot is saved. The goalkeeper then attempts to restart possession through a defender, but the defender misplays the ball and gives possession back to the black team.
- **Was the official anchor visible in these 16 frames?** `yes`

**Visible evidence:**

1. The black team progresses forward from the right side while the white team drops back defensively.
2. A black player receives the ball centrally and attempts a long-range shot.
3. The white-team goalkeeper makes a save, confirming that the attempt is on target.
4. After the save, the goalkeeper distributes the ball to a white defender.
5. The defender subsequently misplays the ball and gives possession back to the black team.

## Optional full-sequence observation

- **Full-sequence phase:** The black team attacks from the right side before the white team partially clears the danger. The black team regains possession, and a player takes a long-range shot on target. The white-team goalkeeper saves the attempt and distributes the ball to a defender. However, the defender fails to retain possession and plays the ball back to a black-team player.

- **Full-sequence event and outcome:** The black team records a shot on target from distance, which is saved by the white-team goalkeeper. The white team initially regains possession after the save but fails to transition successfully because of a misplaced pass from the defender, allowing the black team to regain the ball and continue the attack.

- **Important information missing from the sampled frames:** NIL

## Human coaching reference

- **Main tactical problem:** For the black team, the long-range shot is on target but is directed too close to the goalkeeper and does not generate enough power or placement to make the save difficult. For the white team, the main problem occurs after the save, when the defender forces an inaccurate pass instead of securing possession or choosing a safer passing option.

- **Reasonable coaching recommendation:** The black-team shooter should aim to strike the ball with greater power and place the shot further away from the goalkeeper, particularly towards the corners of the goal. After the save, the white defender should avoid forcing a difficult pass and instead take an extra touch, assess nearby passing options, or recycle possession safely if there is no clear forward option.

- **Why the recommendation follows from the visible evidence:** Although the black player's shot is on target, the goalkeeper is able to save it without being significantly displaced, suggesting that the placement and power could be improved. Following the save, the white team has an opportunity to regain control of possession, but the defender's misplaced pass immediately returns the ball to the opposition. Better shot placement from the black team and safer decision-making from the white defender would improve both phases of play.

- **Claims that cannot be determined from the frames:** NIL

## Original coaching-output error audit

- **Qwen's specific errors:** Qwen incorrectly identifies the white team as the attacking side throughout the sequence, when the primary attacking team is black. It fails to recognise the long-range shot on target, the goalkeeper's save, and the white defender's subsequent misplaced pass. It also repeats essentially the same sentence across the attacking problem, defensive problem, visible evidence, recommendations, training intervention, and limitations. As a result, the response provides almost no meaningful tactical analysis of the actual sequence.

- **Correct observations made by Qwen:** Qwen correctly identifies that the sequence is an attacking phase and recognises that the ball is in play and moving through the field. It also identifies the presence of the white team, although it assigns the team the wrong tactical role.

- **Event correct?** `no — the model fails to identify the shot on target and goalkeeper's save`
- **Attacking team correct?** `no — the model identifies the white team as attacking when the black team is the primary attacking side`
- **Outcome correct?** `no — the model does not identify the save or the subsequent turnover`
- **Advice clip-specific?** `no — the recommendation to "continue to move towards the right side of the field" is generic and unrelated to the key events`
- **Major hallucination count:** `2 — incorrectly identifies the white team as the attacking team and claims that the white team is consistently moving right with possession despite the black team creating the main attacking sequence`
- **Confidence appropriate?** `no — high confidence is inappropriate given the incorrect team identification and failure to recognise the key event`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 0 | Incorrectly identifies the attacking team and fails to recognise the long-range shot, goalkeeper's save, and subsequent turnover. |
| Tactical correctness | 0 | The response does not identify a meaningful tactical problem and simply restates that the white team should continue moving towards the right side. |
| Visual grounding | 0 | The visible-evidence statements are repeated generic claims and do not correspond to the key visible events in the sequence. |
| Specificity | 0 | Does not identify the shooter, goalkeeper, save, defender's mistake, shot location, or any specific tactical action. |
| Actionability | 0 | "Continue to move towards the right side of the field" does not provide a useful or actionable coaching intervention for either team. |
| Evidence-advice consistency | 0 | The recommendations are not supported by the actual sequence and are based on an incorrect interpretation of which team is attacking. |
| **Total (0–12)** | **0** | |

## Recognition-gate review

- **Phase correct?** `partly — correctly identifies that an attacking sequence is occurring but misunderstands which team is attacking`
- **Attacking team correct?** `no`
- **Event correct?** `no`
- **Outcome correct?** `no`
- **Evidence visibly grounded?** `no`
- **Confidence appropriate?** `no`
- **Recognition gate passes for this clip?** `no`
- **Reviewer notes:** Qwen substantially misinterprets the sequence. It identifies the white team as the attacking side and repeatedly states that they are moving towards the right, while failing to recognise the black team's long-range shot on target, the goalkeeper's save, and the white defender's subsequent misplaced pass. The high-confidence response is therefore not supported by the visible evidence.