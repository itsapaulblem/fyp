# Project instructions for coding agents

## Research objective

This project evaluates whether a multimodal large language model (MLLM) can
observe short football sequences, identify visible tactical problems, and
produce useful coaching advice. Objective tracking analytics may verify
measurable claims, but they are not ground-truth coaching advice.

The current local model is `qwen3-vl:2b-instruct`. The current experiment is
defined in `docs/EVALUATION_PROTOCOL.md` and
`config/evaluation_protocol.json`. Read both before changing evaluation code,
prompts, sampling, metrics, or result files.

The selected pilot membership is recorded in
`data/processed/pilot_selection.csv`. Do not silently substitute pilot clips;
record the reason and update the protocol version if selection changes.

The 12-clip train comparison provisionally selected uniform 16-frame sampling.
Read `docs/SAMPLING_PILOT_RESULTS.md` before changing it. This decision is not
frozen until validation confirms it, and it does not imply that the observed
coaching responses were good.

The separate recognition-only gate is defined in
`config/event_recognition_gate.json` and documented in
`docs/EVENT_RECOGNITION_GATE.md`. Its 12 model runs are complete, but its human
pass/fail result is pending. Do not replace the sole reviewer's judgement with
automatic anchor-term matching.

Train-wide direct reference analytics are complete under
`reference-analytics-v0.2.0-train`; see
`docs/TRAIN_REFERENCE_ANALYTICS_RESULTS.md`. Event-relative aggregation is
complete under `reference-windows-v0.1.0-train`; see
`docs/TEMPORAL_WINDOW_RESULTS.md`. Its non-overlapping train-development
windows are before `[-5,-2)`, around `[-2,+2)`, and after `[+2,+5)` seconds
relative to the hidden SoccerNet anchor. A summary requires a complete window
and at least 80% eligible frames for that team and metric. Do not replace
missing/ineligible summaries with zero, and do not expose anchor timing or
window analytics to the MLLM.

Train-derived claim thresholds are complete under
`claim-verification-v0.1.0-train`; read
`docs/CLAIM_VERIFICATION_RULES.md` before classifying any model claim. A shirt
colour must be human-verified as reference `left`/`right`, and pressure/support
also require the team's phase role to be verified. Missing prerequisites yield
`not_measurable`. Do not automatically select whichever window best supports a
claim, and do not describe the percentile rules as football ground truth.

Human pilot references live in `human_evaluation/pilot_references`. The project
has one reviewer; never claim inter-rater agreement or invent a second rating.

Full-sequence review MP4s under `data/processed/review_videos` are derived from
the official JPEG sequences and remain NDA-controlled and Git-ignored. They are
human-review aids, not MLLM inputs. Do not imply that Qwen saw all 750 frames.

## Verified dataset facts

- The local source is the official SoccerNet Game State Reconstruction v1.3
  release.
- The downloaded archives contain 164 clips: 57 train, 58 valid, and 49 test.
  Do not report 166 clips merely because an older task page advertises that
  number.
- Each clip contains 750 ordered JPEG frames representing 30 seconds at
  25 fps. The JPEG sequence is the video representation.
- `Labels-GameState.json` contains player, goalkeeper, referee, ball, pitch,
  tracking, and pitch-position annotations.
- SoccerNet does not supply coaching-advice ground truth.
- `Clearance` is an official GSR anchor action. Preserve that label exactly in
  project-derived scenario groupings.
- The public release has one penalty clip and no indirect-free-kick anchor
  class. Do not claim balanced evaluation for those categories.

Use `docs/DATASET_CARD.md`, `data/processed/summary.json`, and
`data/processed/validation_report.json` as the local evidence for dataset
claims. Inspect the source data before making any stronger claim.

## Experimental separation

The MLLM may receive only temporally ordered sampled frames and the frozen
prompt. Do not expose label JSON, action classes, bounding boxes, coordinates,
track IDs, filenames that reveal the event, or derived analytics to it.

Annotations may be used privately for sampling, objective verification, and
human review. Keep these three evidence layers separate:

1. `model_input`: frames and neutral prompt only.
2. `reference_analytics`: calculations derived from hidden annotations.
3. `human_evaluation`: rubric scores and reviewer comments.

Never describe xG, tracking measurements, or SoccerNet event labels as the
ground truth for overall coaching quality. xG is outside the current protocol
unless the user explicitly reintroduces it as a separate experiment.

## Split discipline

- Train: prompt, sampling, metric, and rubric development; includes the
  12-clip pilot.
- Validation: method selection and final checks.
- Test: one final evaluation after the protocol is frozen.

Do not tune prompts, thresholds, sampling, claim mappings, or success criteria
on test results. Record every protocol change and increment its version. Once
test evaluation begins, do not alter the frozen protocol for that experiment.

## Provenance and repository safety

- Treat files in `data/raw` as immutable official SoccerNet data.
- Treat files in `data/processed` as project-generated metadata or results,
  not SoccerNet-authored labels.
- Do not commit raw SoccerNet frames, archives, credentials, or model weights.
- Never invent missing annotations, clips, expert scores, model responses, or
  metric values.
- Verify paths on disk; IDE tabs may refer to files that were removed.
- Preserve unrelated user changes and do not delete data without explicit
  authorization.

## Reporting language

Use `verified`, `derived`, `human-rated`, or `model-generated` to identify the
provenance of important results. State visibility and calibration limitations,
especially when off-screen players or a missing ball can bias a metric.
