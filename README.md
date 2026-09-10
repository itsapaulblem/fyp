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
| B1 | frames | seeded random case, selected without B labels | Does any example help? |
| B2 | frames | mapped same-action case selected with hidden label | Diagnostic: does action-label matching help when label leakage is deliberately allowed? |
| B3 | frames | human-selected analogous case | Upper bound: how well could case assistance work if a knowledgeable human chose the analogy? |
| B4 | frames | embedding k-NN case | Automatic retrieval system |
| B5 | frames | advice from the same B4-retrieved case, with no other A fields | Does advice text, rather than A video/context, drive improvement? |

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

Install the optional frozen CLIP retrieval pipeline only on the machine that
will build/query embeddings:

```powershell
uv sync --extra dev --extra retrieval --system-certs
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
Their names describe their roles:

- `dataset_a_full_case_context.txt`: A frames plus human case notes and advice;
- `dataset_a_advice_only_context.txt`: only the advice used by B5;
- `dataset_b_analysis_task.txt`: the common question and plain-text answer layout.

The first two are alternatives: a run uses the full-case context, the advice-only
context, or neither. Every condition then uses the same Dataset B analysis task.
The obsolete v0.2 JSON-output prompts were replaced by these current templates.
Each run directory under `output/` contains:

- `prompt.txt`: exact readable messages and image order;
- `response.txt`: exact plain-text model answer, never converted to JSON;
- `metadata.txt`: condition, model, hashes, timing, and retrieval provenance;
- `raw_api_response.json`: untouched machine-readable Ollama response.

The last file is only the Ollama transport envelope retained for reproducibility;
the model's actual answer is the normal text in `response.txt`.

Generated media, embeddings, private data, raw SoccerNet data, and outputs are
Git-ignored. Never use `git add -f` on them.

## Split discipline

- `draft_train_only`: only B0 F10/F20/F30/F60 runs on the fixed eight-clip
  neutral pilot cohort.
- `sampling_validation`: only B0 at the chosen candidate frame count on the
  fixed four-clip neutral validation cohort. A real F60 capacity result and
  train-pilot evidence are required to enter this state.
- `frozen_validation`: B0–B5 validation after an approved sampling decision and
  immutable sampling freeze.
- `frozen_test`: one final test run after the protocol freeze hashes prompts,
  plain-text output contract, generation settings, rubric, Dataset A cases/advice/media, retrieval
  index, encoder/revision, model tag/digest, and validation evidence.

Changing the status string alone cannot unlock validation/test commands.

## Experiment setup workflow

1. Inspect the preregistered label-blind matrix with `football-coach pilot-plan`.
2. Run `football-coach sample-pilot-frames` to create every neutral F10/F20/F30/F60
   review input without contacting the MLLM. Complete the forms created by
   `init-reference-b`, then use `finalize-reference-b`; this preserves and hashes
   a label-free snapshot before attaching the hidden SoccerNet label.
3. Only after the blind references are finalized, run B0 on all pilot cells with
   `football-coach run-sampling-pilot --model qwen3.5:27b` (or the selected
   exact 35B tag). One invocation fixes the model for all 32 cells and preserves
   successful runs, answer-format omissions, capacity failures, crashes, model digest,
   frame indices/hashes, and timing.
4. Copy `templates/sampling_decision.template.json` with
   `init-sampling-decision`; document the train decision and real F60 result.
5. Change status to `sampling_validation`, run only the fixed validation cohort,
   complete the decision, then create the sampling freeze with `freeze-sampling`.
6. Change status to `frozen_validation`. Build the pixel-only Dataset A index
   with `build-a-index`; B4 and B5 automatically use its rank-1 cosine neighbour.
7. Run B0–B5 with identical frozen B frames and generation settings. Score
   recognition first, then retrieval and coaching, using
   `config/scoring_rubric.txt` and blinded plain-text score forms.
8. Record the final validation choice in `init-protocol-decision`, run
   `freeze-protocol`, then and only then change status to `frozen_test`.

Each frozen test clip/condition/model cell receives one private attempt marker
immediately before inference. A preserved crash counts as that cell's attempt;
the command refuses accidental reruns.

B1 selection hashes only the fixed seed, condition, and neutral B ID; relevance
is scored after generation. B2 alone reads the hidden action label. Its explicit
mapping currently supports `Corner` and `Direct free-kick`; other actions are
reported as not evaluable and never receive a substitute case. This limitation
must be reported rather than treating the oracle as coverage of all SoccerNet
events.

B4 uses the pinned `openai/clip-vit-base-patch32` image encoder. The same
preprocessor embeds uniformly sampled A and B pixels; per-frame normalized
embeddings are mean-pooled and normalized, then matched by cosine nearest
neighbour. This is retrieval-assisted analysis, not independent video
understanding.

## Current boundary

The repository now defines the experiment and its gates, but no sampling choice,
human Dataset B reference, model result, retrieval relevance judgement, or score
is claimed until the corresponding real evidence is produced. Failed capacity,
retrieval, and model runs must be preserved and analyzed rather than hidden.
