# Event-recognition gate

Protocol: `event-recognition-v0.1.0`

Status: 12 model runs complete; single-reviewer assessment pending

## Purpose

The original coaching pilot mixed perception, tactical interpretation, and
coaching in one request. Its advice was vague and frequently based on an
incorrect understanding of the sequence. This gate isolates the prerequisite:
can Qwen identify the visible phase, attacking team, event, and outcome from
the same 16 uniform frames?

No coaching questions are included. SoccerNet labels, tracking annotations,
clip IDs, coaching responses, and human references remain hidden from Qwen.

## Fixed condition

- Model: `qwen3-vl:2b-instruct`
- Split: the same 12 train-pilot clips
- Input: the exact same 16 resized uniform frames used by the coaching run
- Image verification: resized-image SHA-256 hashes match the coaching inputs
- Prompt: `prompts/qwen_event_recognition_v1.txt`
- Output: six-field JSON with a 300-token limit

## Model-generated preliminary results

| Diagnostic | Result |
|---|---:|
| Completed calls | 12/12 |
| Complete JSON schemas | 12/12 |
| Automatic anchor-term matches | 2/12 |
| High-confidence answers | 12/12 |
| Mean runtime | 28.393 seconds |

The model described eight clips as goal-like events and four as pass-like
events. It did not differentiate the full set of corners, direct free kicks,
fouls, shots, goals, and clearances. The first smoke clip, `SNGS-067`, was
officially anchored as a Corner but was described as a high-confidence goal
with the same evidence repeated three times.

Automatic term matching remains a weak diagnostic. It does not decide whether
the gate passes. The project author must review each response against the same
16 frames using `human_evaluation/pilot_references/`.

## Human gate

A clip passes when the sole reviewer judges the attacking team, event, and
visible outcome correct. The pilot-level gate requires at least 9 of 12
eligible clips to pass. A clip can be excluded only if those facts genuinely
cannot be determined from the sampled frames, with a written explanation.

The project uses one reviewer. No inter-rater agreement will be reported, and
the final report must identify single-reviewer subjectivity as a limitation.

## Interpretation boundary

The recognition gate is not the project objective by itself. It is a validity
check for the causal chain:

`visible frames → event understanding → tactical interpretation → coaching advice`

If event understanding fails, downstream coaching may sound plausible while
being grounded in the wrong team, phase, or outcome. Tracking analytics cannot
repair that perceptual failure; they can only verify measurable claims after a
response is grounded in the correct sequence.

