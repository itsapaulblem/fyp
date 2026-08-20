# Human Reference: SNGS-164

**Status:** `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Foul` |
| Model input | 16 uniformly sampled frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-164.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-164.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-164.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-164/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- **Review date:** 20 August 2026
- **Human-observed phase of play / What actually happened:** The black-and-red team takes a throw-in from the right side of the pitch. Possession changes several times, with the black-and-red team initially losing the ball before regaining it. The white-and-blue team then attempts to counter-attack through a white player carrying the ball forward. The player is pressed and tackled by a black-and-red defender, causing the white team to lose possession. The black-and-red team subsequently recycles the ball through the back before one of its defenders is fouled.
- **Attacking team by shirt colour:** Black and red initially, followed briefly by white and blue during the attempted counter-attack, before possession returns to the black-and-red team.
- **Defending team by shirt colour:** White and blue initially, followed by black and red during the white-and-blue counter-attack.
- **Attacking direction:** The sequence develops from the right side towards the centre of the pitch.
- **Event observed:** After several changes of possession, a black-and-red player is fouled during the build-up phase.
- **Visible outcome:** Play is stopped for a foul committed against the black-and-red team.
- **Was the official anchor visible in these 16 frames?** `yes`

**Visible evidence:**

1. A black-and-red player takes a throw-in from the right side of the pitch.
2. The white-and-blue team gains possession and attempts to progress the ball forward.
3. A white-and-blue player is pressed and tackled by a black-and-red defender, resulting in another change of possession.
4. The black-and-red team recycles possession through the back.
5. A black-and-red player is subsequently fouled, causing play to stop.

## Optional full-sequence observation

- **Full-sequence phase:** The black-and-red team restarts play with a throw-in from the right side. Possession changes between both teams before the white-and-blue team attempts a counter-attack. A white player carrying the ball is pressed and dispossessed by a black-and-red defender. The black-and-red team then retains possession and circulates the ball through its defensive line before one of its players is fouled.

- **Full-sequence event and outcome:** The sequence contains multiple turnovers and ends with a foul committed against a black-and-red player. Play is stopped and the black-and-red team is awarded the restart.

- **Important information missing from the sampled frames:** NIL

## Human coaching reference

- **Main tactical problem:** For the white-and-blue team, the counter-attacking player holds onto the ball for too long while under pressure and is dispossessed instead of releasing the ball earlier to a teammate. For the black-and-red team, the recovery pressure is effective, but the subsequent build-up is relatively slow and ultimately ends with a foul rather than meaningful forward progression.

- **Reasonable coaching recommendation:** During the counter-attack, the white-and-blue ball carrier should scan for nearby passing options and release the ball earlier when being closed down rather than attempting to retain possession under heavy pressure. After regaining the ball, the black-and-red team should look to progress possession more quickly when forward options are available rather than circulating the ball unnecessarily across the back.

- **Why the recommendation follows from the visible evidence:** The white-and-blue player loses possession after being pressed and tackled, suggesting that an earlier pass could have maintained the counter-attacking opportunity. The black-and-red team successfully regains possession but then spends several actions recycling the ball through the defensive line before the sequence is stopped by a foul.

- **Claims that cannot be determined from the frames:** NIL

## Original coaching-output error audit

- **Qwen's specific errors:** Qwen focuses almost entirely on the temporary white-and-blue attacking phase and fails to recognise the full sequence of possession changes. It does not identify the initial black-and-red throw-in, the white player's eventual loss of possession, the black-and-red team's subsequent build-up, or the foul that ends the sequence. It also incorrectly treats the white team as the attacking side for the entire clip and assigns high confidence despite missing the official anchor event.

- **Correct observations made by Qwen:** Qwen correctly recognises that the white-and-blue team temporarily gains possession and attempts to advance the ball. It also identifies that the black-and-red team is defending during this phase and is positioned to intercept or challenge the ball. Its suggestion that the white team should improve ball control is broadly related to the eventual turnover, although it remains generic.

- **Event correct?** `no — the model does not identify the foul that ends the sequence`
- **Attacking team correct?** `partly — correctly recognises the white-and-blue team's temporary attacking phase but fails to recognise the black-and-red team's attacking phases before and after it`
- **Outcome correct?** `no — the model does not identify the turnover back to the black-and-red team or the final foul`
- **Advice clip-specific?** `partly — advice about ball control is loosely relevant to the white player's loss of possession, but it does not address the actual sequence in sufficient detail`
- **Major hallucination count:** `1 — treats the white team as the attacking side throughout the clip despite multiple changes of possession`
- **Confidence appropriate?** `no — high confidence is not justified because the model fails to recognise the foul and several major changes of possession`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 | Correctly recognises the white-and-blue team's temporary attacking phase but misses the initial throw-in, later turnover, black-and-red build-up, and final foul. |
| Tactical correctness | 1 | The recommendation to improve ball control is broadly reasonable, but it does not address the specific decision-making problem of releasing the ball earlier under pressure. |
| Visual grounding | 1 | The response refers to the white team's forward movement and the black-and-red team's defensive positioning, but it omits several important visible events from the sequence. |
| Specificity | 0 | Does not identify the throw-in, tackle, change of possession, final foul, or any specific player or tactical moment. |
| Actionability | 1 | The recommendation to improve dribbling and passing provides a general training direction but is not sufficiently specific to the decision-making error in the clip. |
| Evidence-advice consistency | 1 | The advice about improving control has some connection to the white player's loss of possession, but it does not follow from the complete sequence and ignores the foul outcome. |
| **Total (0–12)** | **5** | |

## Recognition-gate review

- **Phase correct?** `partly — correctly recognises one attacking phase but fails to capture the multiple transitions in possession`
- **Attacking team correct?** `partly — identifies the white-and-blue team during its temporary counter-attack but treats it as the attacking team for the entire sequence`
- **Event correct?** `no — does not recognise the foul`
- **Outcome correct?** `no — fails to identify the final foul and stoppage of play`
- **Evidence visibly grounded?** `partly — some descriptions correspond to the white-and-blue counter-attacking phase, but the evidence is incomplete`
- **Confidence appropriate?** `no`
- **Recognition gate passes for this clip?** `no`
- **Reviewer notes:** Qwen recognises the white-and-blue team's temporary attacking phase and the black-and-red team's defensive pressure but fails to understand the complete sequence. In particular, it misses the changes of possession, the black-and-red team's subsequent build-up, and the final foul, which is the official SoccerNet anchor event. Its `high` confidence is therefore not supported by the accuracy of the recognition.