# Dataset protocol v0.1.0

## Source

Use only the local SoccerNet Game State Reconstruction v1.3 train, valid, and
test ZIPs. They contain 164 verified clips (57/58/49). Each clip is a 30-second
JPEG sequence with 750 frames at 25 fps. The data remains access-controlled and
must not be committed or redistributed.

SoccerNet GSR is a tracking and identification benchmark, not a coaching-advice
dataset. Its action anchor may stratify selection and privately verify factual
claims, but it is never shown to the model and is not coaching ground truth.

Official project: https://github.com/SoccerNet/sn-gamestate

## Frozen candidate cohort

Version `football-coaching-120-v0.1.0` selects 40 clips independently within
each official split. Within a split, allocation is proportional to official
action-class frequency, with at least one clip from every class present when
capacity permits. Selection within each stratum is pseudorandom with seed
`20260902` and stable sorting.

This gives 120 clips while preserving an untouched remainder in every official
split. Membership is written to a manifest with the config hash. Changing the
seed, counts, strata, or prerequisites creates a new dataset version.

## Data layers

1. `source_video`: ordered official JPEGs.
2. `reference_annotations`: hidden SoccerNet labels and derived checks.
3. `human_coaching_reference`: clip-specific human observations/advice.
4. `model_input`: sampled frames plus frozen neutral prompt only.
5. `model_output`: immutable raw response and parsed view.
6. `human_evaluation`: blinded rubric scores.

Do not pool these layers or expose layers 2, 3, or 6 to a frames-only model.

## Completion definition

The dataset is not complete merely when 120 clips are selected. It becomes an
annotated coaching-reference dataset only when every selected clip has:

- a validated full-sequence human review;
- at least one approved coaching reference matching the JSON schema;
- reviewer qualification and timestamp provenance;
- explicit visible evidence and visibility limitations;
- independent quality control or a clearly disclosed single-reviewer limit.

