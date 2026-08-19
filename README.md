# MLLM Football Coach Evaluation Dataset

This repository evaluates whether a multimodal model can observe football
video, identify visible tactical problems, and produce useful coaching advice.
It combines a verified SoccerNet-GSR corpus, a local Qwen3-VL model, hidden
tracking-derived reference analytics, and human coaching-quality review.

## Dataset decision

The target corpus is all **164 clips actually present in the current public
SoccerNet Game State Reconstruction v1.3 archives**: 57 train, 58 validation,
and 49 test. The SoccerNet web page advertises 57/59/50 (166 total), but the
official archives and their bundled `sequences_info.json` contain 57/58/49.

GSR expands SoccerNet-Tracking, and each downloaded `Labels-GameState.json`
already includes the inherited `ball` tracking category alongside players,
goalkeepers, referees, pitch geometry, teams, roles, jersey numbers, and pitch
coordinates. A second copy of the Tracking footage is therefore not required
for this corpus.

The preparation process preserves three distinct layers:

1. Official raw SoccerNet archives and files (`data/raw`).
2. Extracted, immutable source datasets (`data/extracted`).
3. Generated inventories and manifests (`data/processed`).

No SoccerNet video or annotation data is committed to Git.

## Setup

```powershell
uv sync
```

Download the public GSR splits:

```powershell
uv run soccernet-dataset download --source gamestate
```

Download SoccerNet-Tracking for ball/object annotations:

```powershell
uv run soccernet-dataset download --source tracking
```

If an official download requests a password, provide it only for the running
process:

```powershell
$env:SOCCERNET_PASSWORD = Read-Host "SoccerNet password"
uv run soccernet-dataset download --source tracking
Remove-Item Env:SOCCERNET_PASSWORD
```

The password is never written by this project.

## Current scope

The final manifest must be based on inspected official files. In particular,
the tooling must verify clip counts, video-label pairs, GSR version, and the
actual overlap between GSR and Tracking before describing the corpus as fully
matched or balanced by action.

Build and validate the manifest without extracting the large archives:

```powershell
uv run soccernet-dataset manifest
uv run soccernet-dataset validate
```

The official release represents each 30-second video as 750 ordered JPEG
frames at 25 fps. Generated metadata is written to `data/processed`; archives
remain immutable in `data/raw`.

See [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md) for verified counts, action
coverage, known gaps, and intended use.

## Evaluation protocol

The first experimental artifact is the pilot protocol in
[`docs/EVALUATION_PROTOCOL.md`](docs/EVALUATION_PROTOCOL.md). It defines:

- the fixed questions and output expected from Qwen;
- which SoccerNet annotations remain hidden from the model;
- which claims can be checked using tracking-derived analytics;
- the human coaching-quality rubric;
- train, validation, and test responsibilities;
- provisional success criteria and the 12-clip train pilot.

The current model-facing prompt is
[`prompts/qwen_coach_v1_1.txt`](prompts/qwen_coach_v1_1.txt), while
[`config/evaluation_protocol.json`](config/evaluation_protocol.json) is the
machine-readable protocol record. Blank score and verification sheets are in
`templates/`. The exact 12 selected train clips are recorded in
[`data/processed/pilot_selection.csv`](data/processed/pilot_selection.csv).
No pilot model responses or human scores have been fabricated at this stage.

Future coding agents must read [`AGENTS.md`](AGENTS.md) before modifying the
experiment. In particular, tracking analytics verify only measurable claims;
they are not treated as ground-truth coaching advice. The protocol is currently
`pilot-draft` and must be frozen before the test split is used.

The completed train-pilot sampling comparison provisionally selected uniform
16-frame sampling over event-centred sampling. The decision, measurements, and
important negative result—that both strategies showed weak event
understanding—are documented in
[`docs/SAMPLING_PILOT_RESULTS.md`](docs/SAMPLING_PILOT_RESULTS.md).

## Local MLLM

The selected first local model is `qwen3-vl:2b-instruct`, installed through
Ollama as a Q4_K_M quantized 2.1B-parameter vision-language model. Its exact
local configuration and verification status are recorded in
`config/model.json`.

Ollama manages model weights in its machine-level model store; the 1.9 GB
weight blob is not duplicated in this repository or committed to Git. The
model has been load-tested successfully on the local RTX 3050 Laptop GPU using
mixed GPU/CPU execution.

Start an interactive session with:

```powershell
ollama run qwen3-vl:2b-instruct
```
