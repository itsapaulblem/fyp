# Human Reference: SNGS-169

**Status:** `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Clearance` |
| Model input | 16 uniformly sampled frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-169.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-169.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-169.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-169/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- **Review date:** 20 August 2026
- **Human-observed phase of play / What actually happened:** The white team builds up from the back after a short goalkeeper distribution. A white defender then plays a long forward pass, and the team progresses possession from the left side through the middle and towards the right. The white team continues advancing up the pitch while the black-and-red team remains out of possession. The sequence ends while the attack is still ongoing.
- **Attacking team by shirt colour:** White
- **Defending team by shirt colour:** Black and red
- **Attacking direction:** The attack develops from deep positions and progresses through different areas of the pitch, moving from the left through the centre and towards the right.
- **Event observed:** The white team progresses possession from the back into the attacking half following a clearance or long defensive pass.
- **Visible outcome:** Ongoing open play. The white team remains in possession and continues the attack when the sampled sequence ends, so no final attacking outcome is visible.
- **Was the official anchor visible in these 16 frames?** `partly — a long defensive clearance or forward ball is visible, but the exact clearance event is not clearly distinguishable from the sampled frames`

**Visible evidence:**

1. The white goalkeeper distributes the ball short to a nearby defender.
2. A white defender subsequently plays a long ball forward from a deep position.
3. The white team continues to move possession across the pitch and advances into higher areas.
4. The black-and-red team remains predominantly without possession and retreats to defend.
5. The clip ends while the white team's attacking sequence is still ongoing.

## Optional full-sequence observation

- **Full-sequence phase:** The white team progresses the ball from deep inside its own half after a short goalkeeper distribution. A defender plays a long forward ball, and the team moves possession through the left, central, and right areas of the pitch while advancing into the opposition half.

- **Full-sequence event and outcome:** The white team successfully progresses possession from a deep defensive position into an ongoing attacking phase. The black-and-red team does not regain possession during the observed sequence, and no shot or goal occurs before the clip ends.

- **Important information missing from the sampled frames:** The sampled frames do not make the exact nature of the official `Clearance` event fully clear. The overall progression of the white team's attack is visible, but the precise clearance action may occur between sampled frames.

## Human coaching reference

- **Main tactical problem:** The white team progresses the ball successfully from the back, but the build-up relies heavily on longer passes rather than consistently exploiting shorter forward options between the black-and-red defensive lines. As the attack develops, the team could improve the speed and precision of its progression to create a clearer attacking opportunity before the defence has time to reorganise.

- **Reasonable coaching recommendation:** The white team should continue using the width of the pitch but look for earlier forward passes into teammates positioned between the opposition lines. When a clear forward option is available, the player in possession should avoid unnecessary lateral circulation and move the ball into more advanced areas quickly.

- **Why the recommendation follows from the visible evidence:** The white team retains possession and successfully advances from deep positions, showing that the build-up is generally effective. However, the attack remains ongoing without producing a clear shot or decisive final action within the visible sequence. Quicker and more purposeful progression could help turn the possession into a more dangerous attacking opportunity.

- **Claims that cannot be determined from the frames:** Whether the white team eventually creates a shot, scores, loses possession, or completes the attack successfully cannot be determined because the clip ends before the attacking sequence concludes.

## Original coaching-output error audit

- **Qwen's specific errors:** Qwen correctly identifies the white team as the attacking side but provides an overly generic description of the sequence. It does not identify the goalkeeper's short distribution, the long forward ball from the defender, or the progression of possession from deep inside the white team's half. It also fails to recognise or discuss the official `Clearance` anchor. The `defensive_problem` incorrectly repeats the attacking problem, and the defensive recommendation is directed at the white team rather than the black-and-red defending team. The claim that the ball is "not in the right position for a clear shot" is also not clearly supported by the visible evidence.
- **Correct observations made by Qwen:** Qwen correctly identifies the white team as the attacking team and recognises that the team is in possession and progressing towards the opposition goal. It also correctly notes that the ball is being passed between teammates during the attacking sequence.
- **Event correct?** `partly — correctly recognises an attacking sequence but does not identify the clearance or long defensive progression that anchors the clip`
- **Attacking team correct?** `yes`
- **Outcome correct?** `partly — correctly treats the sequence as ongoing attacking play but does not explicitly recognise that no final outcome is visible before the clip ends`
- **Advice clip-specific?** `partly — recommending a forward pass is somewhat relevant, but the advice is generic and not tied to specific players or passing options visible in the sequence`
- **Major hallucination count:** `2 — repeats the attacking problem as the defensive problem and incorrectly gives the defensive recommendation to the white team rather than the black-and-red team`
- **Confidence appropriate?** `no — high confidence is not justified because the model misses the official anchor and provides generic, partially incorrect tactical analysis`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 1 | Correctly identifies the white team as attacking and in possession, but misses the clearance-related event and provides an unsupported claim about the ball not being in a clear shooting position. |
| Tactical correctness | 1 | The suggestion to play towards a teammate closer to goal is broadly reasonable, but the defensive analysis is incorrect and directed at the wrong team. |
| Visual grounding | 1 | The response is grounded in the general fact that the white team is advancing and passing the ball, but it does not identify the goalkeeper distribution, long forward pass, or specific progression visible in the clip. |
| Specificity | 1 | Identifies the white team and general attacking direction but does not reference specific players, positions, or the actual sequence of passes. |
| Actionability | 1 | The recommendation to pass to a teammate closer to goal is actionable but too generic to provide meaningful clip-specific coaching. |
| Evidence-advice consistency | 1 | The attacking recommendation is loosely connected to the observed forward progression, but the defensive recommendation is inconsistent because it is assigned to the attacking team. |
| **Total (0–12)** | **6** | |

## Recognition-gate review

- **Phase correct?** `yes — correctly identifies the clip as an attacking phase`
- **Attacking team correct?** `yes — correctly identifies the white team`
- **Event correct?** `partly — recognises the attack and passing sequence but does not identify the official clearance event`
- **Outcome correct?** `partly — recognises that the white team is still attacking but does not explicitly state that the sequence ends without a visible final outcome`
- **Evidence visibly grounded?** `partly — references possession, passing, and forward movement, but the evidence remains generic and misses the key clearance-related action`
- **Confidence appropriate?** `no — high confidence is too strong given the missed anchor event and generic visual evidence`
- **Recognition gate passes for this clip?** `yes`
- **Reviewer notes:** Qwen correctly recognises the white team as the attacking side and understands that the team is progressing possession towards goal. However, it does not identify the official `Clearance` anchor or the specific build-up sequence beginning with the goalkeeper and defender. Its supporting evidence and tactical advice are generic, and the defensive recommendation is incorrectly assigned to the white team. The recognition gate nevertheless passes because the model correctly identifies the attacking phase, team in possession, and general progression of play.