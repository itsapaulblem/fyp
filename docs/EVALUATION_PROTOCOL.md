# MLLM football coaching evaluation protocol

Protocol ID: `coach-eval-v0.1.1`

Status: pilot draft

Model under evaluation: `qwen3-vl:2b-instruct`

Dataset: SoccerNet Game State Reconstruction v1.3

## 1. Research question

Can a locally run MLLM observe a 30-second football sequence, identify visible
tactical problems, and provide coaching advice that is factually grounded,
tactically plausible, specific, and actionable?

This protocol evaluates three different things:

1. Video understanding against hidden SoccerNet annotations.
2. Measurable tactical claims against tracking-derived analytics.
3. Overall coaching quality through human review.

Tracking analytics are evidence for particular claims. They are not complete
ground truth for coaching quality. xG is not part of this first experiment.

## 2. Experimental unit

One experimental unit is one official 30-second SoccerNet-GSR clip. The source
contains 750 ordered JPEG frames at 25 fps. A future runner will select a fixed,
ordered subset of these frames for the model; the sampling strategy must be
chosen during train/validation development and frozen before test evaluation.

Each model run must record the clip ID privately, protocol version, model ID,
prompt version, frame numbers, generation settings, raw response, and run time.

## 3. Information boundary

### Visible to the model

- Temporally ordered sampled frames from one clip.
- The neutral prompt in `prompts/qwen_coach_v1_1.txt`.
- The knowledge that the images represent one chronological football sequence.

### Hidden from the model

- `Labels-GameState.json` and `sequences_info.json`.
- Official anchor action and scenario grouping.
- Bounding boxes, pitch coordinates, calibration, roles, teams, jersey numbers,
  and track IDs.
- All derived tactical metrics and reviewer judgements.
- Clip filenames or metadata that reveal the event.

Official labels may be used privately to stratify the sample. They must never
be placed in the model prompt or images as overlays in the baseline condition.

## 4. Questions asked of the model

The same questions are asked for every clip:

1. What phase of play is visible?
2. Which visually distinguishable team is attacking, and in what direction?
3. What happens during the sequence, using only visible evidence?
4. What is the main tactical problem for the attacking team?
5. What is the main tactical problem for the defending team?
6. What visible evidence supports each claimed problem?
7. What should the attacking team do differently?
8. What should the defending team do differently?
9. What concrete training or coaching intervention addresses the most
   important problem?
10. How confident is the analysis: low, medium, or high?
11. What relevant information is unclear, off-screen, or not visible?

The model is explicitly allowed to answer `unclear` or `insufficient visual
evidence`. It must not infer identities, intent, communication, or off-screen
positions without visible evidence.

## 5. Required response fields

The prompt requests one JSON object with these fields:

- `phase_of_play`
- `attacking_team_visual_description`
- `attacking_direction`
- `sequence_description`
- `attacking_problem`
- `defensive_problem`
- `visible_evidence`
- `attacking_recommendation`
- `defensive_recommendation`
- `training_intervention`
- `confidence`
- `limitations`

Structured output supports consistent scoring, but a syntactically invalid
response is retained rather than silently repaired. Parsing success is a
technical measure and is separate from coaching quality.

## 6. Objective claim verification

Only claims with a valid measurement mapping receive an objective result.
Other claims are marked `not_measurable`, not incorrect.

| Claim family | Tracking-derived evidence |
|---|---|
| Team too wide/narrow | Team width using visible pitch positions |
| Team too deep/stretched | Team depth and dispersion |
| Poor compactness | Distance-to-centroid and/or visible-player hull area |
| Ball carrier under pressure | Nearest opponent distance to the ball |
| Player isolated | Teammate and opponent counts within a fixed local radius |
| Local overload/underload | Attacker-versus-defender counts in the local area |
| Too few players in the box | Visible team counts inside the penalty area |
| Goalkeeper poorly positioned | Goalkeeper position relative to ball and goal |
| Ball moving toward/away from goal | Smoothed ball trajectory over consecutive frames |
| Player moving toward/away from goal | Track trajectory and change in goal distance |

Before computing a metric, the implementation must establish pitch-axis
orientation, the attacking goal, team identity, coordinate units, a temporal
window, and minimum visibility requirements. Frames that fail eligibility are
reported as unavailable rather than imputed into confident tactical evidence.

Relative claims such as "among the least compact 10%" use thresholds learned
from eligible training clips. A provisional definition is the clip-level
median of a fixed pre-event window compared with the training distribution.
The final definition and thresholds must be frozen before test evaluation.

Objective claim results use four states:

- `supported`
- `contradicted`
- `inconclusive`
- `not_measurable`

## 7. Human scoring rubric (Maybe)

A football-knowledgeable reviewer scores each category from 0 to 2. Two
independent reviewers are preferred; disagreements should be retained and
inter-rater agreement reported.

| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Factual accuracy | Mostly incorrect | Partly correct | Correct |
| Tactical correctness | Invalid | Plausible but incomplete | Strong interpretation |
| Visual grounding | Unsupported | Vague evidence | Clear visible evidence |
| Specificity | Generic | Some clip detail | Precise and clip-specific |
| Actionability | Not applicable | Partly actionable | Clear coaching action |
| Evidence-advice consistency | Disconnected | Partly connected | Advice follows evidence |

Maximum total: 12 points per reviewer per clip.

Reviewers separately count major hallucinations, such as invented events,
players, identities, or confident claims about unseen areas. Reviewers should
not punish an appropriate statement of uncertainty.

## 8. Split policy

| Split | Clips | Permitted use |
|---|---:|---|
| Train | 57 | Prompt, sampling, metrics, rubric development, and pilot |
| Validation | 58 | Compare candidate methods and freeze the final protocol |
| Test | 49 | One final evaluation with no tuning |

No test-derived observation may change the prompt, frame sampling, analytics,
thresholds, rubric, or success criteria for the same reported experiment.

## 9. Pilot design

The first run uses 12 train clips:

- 2 corners
- 2 direct free kicks
- 2 fouls or defensive restarts
- 2 shots on target
- 2 shots off target or goals
- 2 clearances

The single penalty clip is not required in the pilot and must not be
oversampled. Selection should prefer clips with sufficient visible players and
ball coverage for analytics, while recording those eligibility criteria.

The pilot checks prompt clarity, response structure, frame sufficiency,
measurability of claims, reviewer usability, and failure cases. Pilot results
are developmental and are not final model-performance estimates.

### Selected pilot clips

Selection is complete but the pilot has not yet been run. All clips come from
the train split. The selection uses two clips per scenario group and four clips
from each of training game IDs 4, 6, and 9 so that one source match does not
dominate the pilot.

| Pilot group | Selected clips | Official anchor actions |
|---|---|---|
| Corner | `SNGS-067`, `SNGS-103` | Corner, Corner |
| Direct free kick | `SNGS-066`, `SNGS-100` | Direct free-kick, Direct free-kick |
| Foul or defensive restart | `SNGS-062`, `SNGS-164` | Foul, Foul |
| Shots on target | `SNGS-112`, `SNGS-159` | Shots on target, Shots on target |
| Shots off target or goal | `SNGS-115`, `SNGS-165` | Shots off target, Goal |
| Clearance | `SNGS-074`, `SNGS-169` | Clearance, Clearance |

The preliminary eligibility check requires at least five pitch-located
outfield players from each team in at least 60% of the clip's frames. All 12
clips pass. Their mean ball-annotation coverage is 98.86%. This is a pilot
usability filter, not a claim that every tactical metric will be valid in every
frame. Metric-specific eligibility must still be checked in the selected
analysis window.

The two clearance clips retain SoccerNet's official `Clearance` anchor label.
The model will not see that label; it must determine the visible phase from
the sampled frames.

The authoritative row-level selection record is
`data/processed/pilot_selection.csv`. It is project-derived metadata and is not
an official SoccerNet annotation file.

## 10. Why the pilot contains 12 clips

Twelve is a development sample, not the final evaluation size. It is the
smallest convenient number that gives two examples in each of the six pilot
scenario groups. One example can expose a problem; the second helps reveal
whether it is clip-specific. Twelve 30-second clips also represent six minutes
of source footage and a manageable first manual-review workload while the
prompt, frame sampling, analytics, and rubric can still change.

The pilot cannot establish statistically reliable model performance. Final
claims will use the frozen protocol on the 49-clip test split, with validation
used before that to select the method. If the pilot reveals unstable or
scenario-specific behaviour, the development sample may be expanded using
additional train clips without touching the test set.

### Sampling comparison outcome

Both 16-frame strategies were run on all 12 pilot clips. Uniform sampling is
the provisional baseline because it produced 12/12 complete schemas versus
11/12 for event-centred sampling, matched the hidden anchor terminology equally
often (2/12 each), ran slightly faster, and does not depend on hidden event
timing. This choice remains subject to validation confirmation and human
coaching-quality review. See `docs/SAMPLING_PILOT_RESULTS.md` for the complete
comparison and limitations.

## 11. Provisional success criteria

Before test evaluation, the final protocol must state numeric criteria. The
pilot begins with these provisional targets:

- Mean human score at least 8/12.
- At least 70% of eligible measurable claims are supported by analytics.
- Major hallucinations occur in fewer than 15% of clips.
- At least 70% of clips contain a specific, actionable recommendation.
- Results are reported separately for major scenario groups rather than only
  as one aggregate.

These thresholds are research design choices, not established industry
standards. They may be revised using train and validation evidence, with the
reason recorded, but must be frozen before the test run.

## 12. Change control

The protocol is currently `pilot-draft`. Any material change must increment
the version in this document, `config/evaluation_protocol.json`, the prompt,
and future result records. A protocol becomes `frozen` only after the pilot and
validation decisions are complete. Results from different protocol versions
must not be pooled without explicit analysis.

### Draft change history

- `v0.1.0`: initial protocol and prompt; one uniform smoke run reached the
  output limit while repeating limitations and produced incomplete JSON.
- `v0.1.1`: concise field limits and a strict JSON schema were added before the
  paired sampling comparison. The failed v0.1.0 smoke result is retained as a
  development artifact and excluded from the comparison.
