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

- **Main tactical problem:** The main tactical problem for the white team is the loss of possession following the long throw-in while several players are positioned high up the pitch. After losing the ball, the white team does not apply enough immediate pressure to slow the transition and is unable to recover its defensive shape before the black-and-red team progresses through the centre. The black-and-red team executes the counter-attack effectively and does not display a major attacking problem in this sequence.
- **Reasonable coaching recommendation:** The white team should provide closer supporting options around the long throw-in to improve the chances of retaining possession. If the ball is lost, the nearest players should immediately counter-press or delay the ball carrier while the remaining defenders recover into shape. The black-and-red team should continue to use the same principles demonstrated in this sequence: immediate forward progression after winning possession, quick support runs, and direct exploitation of central space.
- **Why the recommendation follows from the visible evidence:** The black-and-red team is able to transition rapidly from winning possession to creating a goalscoring opportunity. The white team does not stop or sufficiently delay the initial counter-attack, allowing the black-and-red players to exploit the available central space before the defence can reorganise. The transition ultimately results in a goal.
- **Claims that cannot be determined from the frames:** The intended tactical structure of the white team's throw-in routine, individual defensive assignments, and whether specific players were instructed to counter-press or recover cannot be determined from the sampled frames.

## Original coaching-output error audit

The Qwen output contains only event-recognition fields and does not provide any tactical problems, coaching recommendations, or training interventions. Therefore, the model fails to provide the required coaching analysis for this clip.

- **Qwen's specific errors:** Qwen does not provide any coaching analysis or recommendations. It also incorrectly identifies the white team as the attacking team for the decisive phase of the sequence. The black-and-red team is the side that regains possession, launches the counter-attack, and scores.
- **Correct observations made by Qwen:** Qwen correctly identifies the phase as attacking and correctly recognises both the event and outcome as a goal.
- **Event correct?** `yes`
- **Attacking team correct?** `partly — identifies the white team, which begins the sequence in possession, but fails to recognise the black-and-red team as the decisive attacking team`
- **Outcome correct?** `yes`
- **Advice clip-specific?** `no — no coaching advice is provided`
- **Major hallucination count:** `1 — incorrectly identifies the white team as the attacking team for the goalscoring phase`
- **Confidence appropriate?** `no — high confidence is not appropriate because the attacking team is misidentified and the supporting evidence is extremely limited`

| Human rubric criterion | Score (0–2) | Evidence or reason |
|---|---:|---|
| Factual accuracy | 0 | No coaching response is provided from which an accurate tactical description can be evaluated. |
| Tactical correctness | 0 | No tactical problem or tactical analysis is provided. |
| Visual grounding | 0 | No coaching analysis is grounded in specific visual evidence from the sequence. |
| Specificity | 0 | No player-specific, team-specific, or situation-specific coaching analysis is provided. |
| Actionability | 0 | No actionable coaching recommendation is provided. |
| Evidence-advice consistency | 0 | No coaching advice is provided that can be connected to the visible evidence. |
| **Total (0–12)** | **0** | No coaching response was provided. |

## Recognition-gate review

- **Phase correct?** `yes — correctly identifies the sequence as an attacking phase`
- **Attacking team correct?** `partly — identifies the white team, which begins the sequence in possession, but fails to recognise that the black-and-red team becomes the decisive attacking team after the turnover`
- **Event correct?** `yes — correctly identifies the event as a goal`
- **Outcome correct?** `yes — correctly identifies that the sequence ends in a goal`
- **Evidence visibly grounded?** `partly — references the goal and goalkeeper but provides almost no description of the actual visible sequence`
- **Confidence appropriate?** `no — high confidence is too strong given the incorrect attacking-team identification and weak supporting evidence`
- **Recognition gate passes for this clip?** `yes`
- **Reviewer notes:** Qwen successfully recognises the most important event and final outcome, correctly identifying that the sequence ends in a goal. However, it incorrectly identifies the white team as the attacking team. The white team only initiates the sequence with the long throw-in; the decisive attacking phase belongs to the black-and-red team, which wins possession, launches a counter-attack, and scores. The visible-evidence field is also extremely weak, consisting only of the generic terms `"goal"`, `"goalkeeper"`, and `"goal"` rather than describing the turnover, transition, attacking team, or scoring action. Despite these limitations, the recognition gate passes because the official SoccerNet anchor event and final outcome are correctly identified.