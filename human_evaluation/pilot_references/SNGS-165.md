# Human Reference: SNGS-165

**Status:** `Complete`

## Provenance

| Field | Value |
|---|---|
| Reviewer | Project author |
| Reviewer count | 1 |
| Review blinded | No — pilot outputs and labels were inspected before this form was created |
| Dataset split | Train |
| Official SoccerNet anchor | `Goal` |
| Model input | 16 uniformly sampled frames |
| Frame numbers | 23, 70, 117, 164, 211, 258, 305, 352, 398, 445, 492, 539, 586, 633, 680, 727 |
| Full review video | `data/processed/review_videos/SNGS-165.mp4` |
| Coaching run | `data/processed/pilot_runs/uniform/SNGS-165.json` |
| Recognition run | `data/processed/recognition_runs/uniform/SNGS-165.json` |
| Official label source | `data/raw/gamestate/gamestate-2024/train.zip/SNGS-165/Labels-GameState.json` |

The official anchor is verified SoccerNet metadata. All observations and coaching references below are single-reviewer human judgements.

## Human observation from the same 16 frames

- **Review date:** 20 August 2026
- **Human-observed phase of play / What actually happened:** The white team begins the sequence with a long throw-in from the left side of the pitch. The black-and-red team intercepts the ball and immediately transitions into a fast counter-attack through the centre. The black-and-red players progress quickly towards the white team's goal and successfully convert the counter-attack into a goal.
- **Attacking team by shirt colour:** White initially during the throw-in, followed by black and red after regaining possession and launching the decisive counter-attack.
- **Defending team by shirt colour:** Black and red initially, followed by white during the counter-attack.
- **Attacking direction:** The black-and-red team attacks quickly through the centre towards the white team's goal.
- **Event observed:** The black-and-red team regains possession following the white team's long throw-in, launches a fast central counter-attack, and scores.
- **Visible outcome:** Goal scored by the black-and-red team.
- **Was the official anchor visible in these 16 frames?** `yes`

**Visible evidence:**

1. The white team takes a long throw-in from the left side of the pitch.
2. The black-and-red team intercepts the ball and immediately transitions forward.
3. Multiple black-and-red players advance quickly through the centre while the white team retreats defensively.
4. The black-and-red team progresses into a goalscoring position near the white team's goal.
5. The sequence ends with the black-and-red team scoring.

## Optional full-sequence observation

- **Full-sequence phase:** The white team begins with a long throw-in from the left side. The black-and-red team wins possession and immediately launches a fast counter-attack through the centre. The white team struggles to recover its defensive shape while the black-and-red team progresses directly towards goal.
- **Full-sequence event and outcome:** The black-and-red team successfully converts a turnover into a rapid counter-attack and scores a goal. The white team's attacking restart therefore results in a loss of possession and a goal conceded at the opposite end.
- **Important information missing from the sampled frames:** NIL

## Human coaching reference

- **Main tactical problem:** The white team loses possession following the long throw-in while several players are positioned high up the pitch. After the turnover, the team does not apply enough immediate pressure to slow the transition and is unable to recover its defensive shape before the black-and-red team attacks through the centre. The black-and-red team executes the counter-attack effectively and does not display a major attacking problem in this sequence.
- **Reasonable coaching recommendation:** The white team should provide closer supporting options around the throw-in so that possession can be retained more securely. If possession is lost, the nearest players should immediately counter-press or delay the ball carrier while the remaining players recover into a compact defensive shape. The black-and-red team should continue using the same successful counter-attacking principles: immediate forward progression after winning possession, quick supporting runs, and direct exploitation of central space.
- **Why the recommendation follows from the visible evidence:** The black-and-red team moves quickly from regaining possession to creating a goalscoring opportunity. The white team fails to stop or sufficiently delay the initial transition, allowing the black-and-red players to exploit the open central space before the defence can reorganise. The counter-attack ultimately results in a goal.
- **Claims that cannot be determined from the frames:** The intended tactical structure of the white team's throw-in routine, individual defensive responsibilities, and whether specific players were instructed to counter-press cannot be determined from the sampled frames.

## Original coaching-output error audit

- **Qwen's specific errors:** Qwen incorrectly treats the white team as the attacking team throughout the clip and fails to recognise the decisive change of possession. It does not identify the black-and-red team's counter-attack or the goal that concludes the sequence. Its attacking problem, `"the ball is not being passed effectively"`, does not address the actual tactical issue of the turnover and poor defensive transition. The defensive problem simply repeats the attacking problem, and the defensive recommendation is incorrectly directed at the white team rather than analysing how the white team should defend the black-and-red counter-attack. The response also fails to recognise the successful nature of the black-and-red team's transition.
- **Correct observations made by Qwen:** Qwen correctly recognises that the sequence contains an attacking phase and that the white team is initially involved in possession. It also observes that the ball moves across the pitch and that passing occurs during the sequence.
- **Event correct?** `no — Qwen does not identify the goal or the counter-attack that leads to it`
- **Attacking team correct?** `partly — correctly recognises the white team as initially in possession but fails to recognise that the black-and-red team becomes the decisive attacking team`
- **Outcome correct?** `no — does not identify that the black-and-red team scores`
- **Advice clip-specific?** `no — the recommendation to pass to a teammate closer to goal is generic and does not address the turnover, counter-attack, or goal`
- **Major hallucination count:** `2 — treats the white team as the attacking team throughout the sequence and repeats the attacking problem as the defensive problem`
- **Confidence appropriate?** `no — high confidence is not justified because the model misses the possession change, counter-attack, and goal`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 0 | Fails to recognise the decisive black-and-red counter-attack and the goal, and incorrectly treats the white team as the attacking side throughout. |
| Tactical correctness | 0 | The identified tactical problem is unrelated to the main issue of losing possession and failing to defend the transition. |
| Visual grounding | 1 | Refers to the white team's initial possession and the ball moving across the pitch, but misses the most important visible events. |
| Specificity | 0 | Does not identify the throw-in, turnover, counter-attack, defensive recovery problem, or goal. |
| Actionability | 1 | The recommendation to pass to a teammate closer to goal is actionable in a general sense but is not useful for the actual tactical problem in the clip. |
| Evidence-advice consistency | 0 | The advice does not follow from the key visible evidence and is based on an incorrect understanding of the attacking team and sequence. |
| **Total (0–12)** | **2** | |

## Recognition-gate review

- **Phase correct?** `yes — correctly identifies an attacking phase`
- **Attacking team correct?** `partly — identifies the white team, which begins in possession, but fails to recognise the black-and-red team as the team that counter-attacks and scores`
- **Event correct?** `yes — correctly identifies the event as a goal`
- **Outcome correct?** `yes — correctly identifies that the sequence ends in a goal`
- **Evidence visibly grounded?** `partly — some generic statements correspond to the early part of the sequence, but the key turnover, counter-attack, and goal are omitted`
- **Confidence appropriate?** `no`
- **Recognition gate passes for this clip?** `no`
- **Reviewer notes:** Qwen correctly identifies the goal and final outcome, but incorrectly identifies the white team as the attacking team. The white team begins with the long throw-in; the black-and-red team wins possession, counter-attacks, and scores. Because the attacking-team component is not correct, the clip does not pass the all-three-correct gate.
