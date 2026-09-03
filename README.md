# Retrieval-Assisted Football Coaching with MLLMs

This FYP studies whether a human-annotated analogous football case can help a
multimodal model understand and coach a new football sequence more reliably
than frames alone.

The two video collections have different roles:

- **Dataset A** is a sourced coaching case library. Every approved case must
  pair an exact video segment with human-authored observation, tactical
  diagnosis, coaching advice, source/rights provenance, and review provenance.
- **Dataset B** is the immutable SoccerNet Game State Reconstruction v1.3
  collection: 57 train, 58 validation, and 49 test clips. It supplies new query
  sequences and hidden reference annotations, not coaching ground truth.

The automatic system must retrieve from Dataset A using only information
available from Dataset B pixels or pixel-derived embeddings. Matching with a
hidden SoccerNet action label is permitted only as a clearly labelled oracle
condition.

## Experimental conditions

| ID | Dataset B input | Dataset A input | Question |
|---|---|---|---|
| B0 | frames | none | Visual-only baseline |
| B1 | frames | random unrelated case | Does any example help? |
| B2 | frames | same-action case selected with hidden label | Oracle action upper bound |
| B3 | frames | human-selected analogous case | Oracle analogy upper bound |
| B4 | frames | embedding k-NN case | Automatic retrieval system |
| B5 | frames | retrieved advice without A frames | Does text, rather than A video, drive improvement? |

Recognition of Dataset B is scored before coaching quality. Retrieval relevance,
blind copying, hallucination, and uncertainty are measured separately.

## Setup

Python 3.11 or 3.12 and `uv` are required.

```powershell
uv sync --extra dev --system-certs
Copy-Item .env.example .env
uv run football-coach index-b
uv run football-coach validate-a
uv run pytest
```

Set the remote Ollama endpoint in `.env`. Prefer running this code on the GPU
host or using an SSH tunnel; do not expose an unauthenticated Ollama port to the
public internet.

```powershell
uv run football-coach ollama-check --model qwen3.5:27b
uv run football-coach ollama-check --model qwen3.5:35b
```

## Dataset A workflow

Create a case template without overwriting existing work:

```powershell
uv run football-coach init-case-a A-0001
```

This creates:

```text
data/video_a/cases/A-0001.json     structured metadata and human review
data/video_a/advice/A-0001.txt     presentation-friendly coaching advice
data/video_a/media/A-0001.mp4      user-supplied local video, Git-ignored
```

Do not mark a case `approved` unless the advice concerns that exact segment,
the reviewer provenance is complete, and usage rights are recorded. Online
advice from an unrelated clip is not an acceptable label.

The first milestone is a 20–30 case pilot. Scale beyond 100 only after an
oracle-pair experiment shows that analogous cases help.

## Dataset B workflow

The official ZIP files remain compressed and Git-ignored:

```text
data/raw/gamestate/gamestate-2024/train.zip
data/raw/gamestate/gamestate-2024/valid.zip
data/raw/gamestate/gamestate-2024/test.zip
```

`index-b` builds a manifest directly from the ZIPs and checks v1.3, 750 frames,
25 fps, unique clip IDs, and expected split counts. Hidden action labels are
stored for evaluation/oracle experiments but are never placed in automatic
retrieval prompts.

## Inputs and outputs

All presentation-facing prompt templates are plain text under `input_prompts/`.
Each run directory under `output/` contains:

- `prompt.txt`: exact readable messages and image order;
- `response.txt`: exact model answer;
- `metadata.txt`: condition, model, hashes, timing, and retrieval provenance;
- `raw_api_response.json`: untouched machine-readable Ollama response.

Generated media, embeddings, private data, raw SoccerNet data, and outputs are
Git-ignored. Never use `git add -f` on them.

## Split discipline

- Dataset B train: prompts, representations, retrieval, and rubric development.
- Dataset B validation: choose the final method and calibrate thresholds.
- Dataset B test: one final run after protocol freeze.

The project config begins in `draft_train_only` state, and run commands reject
test clips. A protocol/version change is required before test execution.

## Current boundary

The repository is a working foundation, not a completed Dataset A and not an
experimental result. It does not yet choose a video encoder. Failed capacity,
retrieval, and model runs must be preserved and analyzed rather than hidden.

