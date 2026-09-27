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
hidden SoccerNet action label is permitted only in B2, a clearly labelled
diagnostic condition with deliberate label access.

## Experimental conditions

| ID | Dataset B input | Dataset A input | Question |
|---|---|---|---|
| B0 | frames | none | Visual-only baseline |
| B1 | frames | seeded random case, selected without B labels | Does any example help? |
| B2 | frames | mapped same-action case selected with hidden label | Diagnostic only: does action-label matching help when label leakage is deliberately allowed? |
| B3 | frames | human-selected analogous case | How well could case assistance work if a person chose the best analogy? |
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

The feasibility library now contains 25 approved cases: 14 sourced from the
[FIFA Training Centre Game Library](https://www.fifatrainingcentre.com/en/resources/game-library/)
and 11 from [UEFA Champions League Performance Insights](https://www.uefa.com/uefachampionsleague/news/).
Each case retains its exact source URL. `validate-a` currently reports 25/25.
Scale beyond this feasibility library only if the experiment provides a clear
reason to do so.

## Dataset B workflow

The official ZIP files remain compressed and Git-ignored:

```text
data/raw/gamestate/gamestate-2024/train.zip
data/raw/gamestate/gamestate-2024/valid.zip
data/raw/gamestate/gamestate-2024/test.zip
```

`index-b` builds a manifest directly from the ZIPs and checks v1.3, 750 frames,
25 fps, unique clip IDs, and expected split counts. Hidden action labels are
stored for evaluation and the B2 hidden-label diagnostic but are never placed in automatic
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
   a label-free snapshot before attaching the hidden SoccerNet label. Training
   pilot references require all four frame levels. Validation and test references
   require exactly the single candidate or frozen frame level.
3. Only after the blind references are finalized, run B0 on all pilot cells. The
   current Qwen3.5 27B CPU workflow uses
   `scripts/run_sampling_pilot_cpu.ps1`. Its dry-run mode lists completed and
   pending cells, and the real mode runs pending cells sequentially. It preserves
   successful runs, answer-format omissions, capacity failures, crashes, model
   digest, frame indices/hashes, and timing.
4. Run `football-coach prepare-pilot-grading` once to verify all 32 cells and
   create the randomized private grading package. The 32 forms have now been
   scored, validated, unblinded, and analysed by frame count.
5. Complete the sampling decision, confirm F30 on the fixed four-clip validation
   cohort, and create the immutable sampling freeze with `freeze-sampling`.
6. In `frozen_validation`, build and verify the pixel-only Dataset A index with
   `build-a-index`; B4 and B5 automatically use its rank-1 cosine neighbour.
7. Document B3 human-selected pairings without hidden labels or B4 results.
8. Run B0–B5 with identical frozen B frames and generation settings. This
   validation stage is complete for every evaluable condition: B0, B1, B3, B4,
   and B5 on four fixed clips. B2 was not evaluable for these clips. Comparable
   runs were randomized, recognition was scored before condition reveal, and
   all post-reveal case-dependent fields were checked against the private maps.
9. Review the completed validation report with the supervisor. Only if an
   untouched test run is explicitly justified should the final decision be
   recorded with `init-protocol-decision`, frozen with `freeze-protocol`, and
   the project status changed to `frozen_test`.

Each frozen test clip/condition/model cell receives one private attempt marker
immediately before inference. A preserved crash counts as that cell's attempt;
the command refuses accidental reruns.

B1 selection hashes only the fixed seed, condition, and neutral B ID; relevance
is scored after generation. B2 alone reads the hidden action label. Its explicit
mapping currently supports `Corner` and `Direct free-kick`; other actions are
reported as not evaluable and never receive a substitute case. This limitation
must be reported rather than treating the B2 diagnostic as coverage of all
SoccerNet events.

B4 uses the pinned `openai/clip-vit-base-patch32` image encoder. The same
preprocessor embeds uniformly sampled A and B pixels; per-frame normalized
embeddings are mean-pooled and normalized, then matched by cosine nearest
neighbour. This is retrieval-assisted analysis, not independent video
understanding.

## Human scoring workflow

`config/scoring_rubric.txt` is the single authoritative rubric and declares
`Rubric version: 1.0`. `templates/score.template.txt` is only a blank form, not
a second rubric. For the completed sampling pilot, the package and all 32 blank
forms are created together:

```powershell
uv run football-coach prepare-pilot-grading
```

This command verifies the source responses and frame hashes, randomizes their
order behind `PILOT-001` to `PILOT-032`, writes the revealing mapping separately
under private data, and refuses to overwrite an existing package. For a
same-clip comparison, create an equivalent randomized package by supplying the
completed run directories:

```powershell
uv run football-coach prepare-comparison-grading PACKAGE_ID CLIP_ID RUN_PATH_1 RUN_PATH_2 RUN_PATH_3
```

The command checks complete and valid responses, the exact model digest, frozen
frame count, identical Dataset B frame hashes, and unique conditions. It then
creates generic `COMPARE-*` folders and keeps the revealing mapping private.
For an isolated response, create and validate an individual private form with:

```powershell
uv run football-coach init-score BLIND_RUN_ID CLIP_ID data/video_b/review/scores/BLIND_RUN_ID.txt
uv run football-coach validate-score data/video_b/review/scores/BLIND_RUN_ID.txt
```

Fill the form between these commands. Score recognition before revealing the
case or condition. Missing values and out-of-range scores are rejected. Because
the blinded validator cannot know the hidden condition, perform a mapping-aware
check after unblinding to confirm that `N/A` was used only for B0 case-dependent
fields. Report dimensions separately and do not combine them into one overall
mark.

## Current boundary

Protocol v0.3 remains in `frozen_validation`, but validation execution and
human grading are complete. The state is preserved by the Git tag
`v0.3-validation-complete`. All 32 B0 train-pilot cells and all 20 evaluable
validation cells are complete. The validation matrix contains B0, B1, B3, B4,
and B5 on four fixed clips; B2 was excluded as not evaluable rather than given a
substitute case. All score forms validate, the private maps were revealed only
after grading, and the final post-unblinding consistency checks passed.

F30 remains frozen as the best tested operational trade-off, not because
frames-only performance was accurate. Every condition missed the critical event
on all four validation clips. B3 and B4 produced identical mean recognition and
coaching scores and only small descriptive gains over B0, concentrated mainly in
one clip. B1 also improved some dimensions on that clip, weakening any claim
that the gains were caused by analogy relevance. Human-selected B3 cases had
higher mean judged relevance than B4 cases, but this did not translate into
better aggregate recognition or coaching. B5 advice-only did not improve over
B0.

The private report is
`data/video_b/private/frozen_validation_post_unblinding_v1/VALIDATION_COMPARISON_REPORT.txt`.
It reports each rubric dimension separately and does not calculate one overall
mark. The validation evidence does not establish a reliable benefit from case
assistance. Following supervisor review, the project is preparing a separate
v0.4 train-first diagnostic of evidence-first staged prompting. This new work
must not alter or be mixed with completed v0.3 evidence. Its active plan is in
`PROJECT_NEXT_STEPS.md`. No test-split inference is currently authorized.

## v0.4 human-guided recognition and coaching

The active P1 workflow stops for researcher review. The model first describes
the 30 ordered B frames. The researcher approves the answer or gives specific,
sampled-frame feedback. If needed, the model revises recognition once and the
researcher approves that revision before requesting coaching. The final advice
is a human-assisted result.

Validate the train-only environment, then start the first development clip:

```powershell
uv run football-coach validate-prompt-chain
uv run football-coach ollama-check --model qwen3.5:27b
uv run football-coach start-prompt-review B-TRAIN-0025 --model qwen3.5:27b
```

The start command prints a timestamped `RUN_DIR` under
`output/v0.4/prompt_chain/P1_human_guided/`. Read
`stage_1_response.txt`, copy `initial_review.template.json` to
`initial_review.json`, and record your decision using only the sampled frames.
For `approve`, remove the example feedback item. For `revise`, replace it
with frame-cited evidence and a specific correction:

```powershell
uv run football-coach revise-prompt-recognition RUN_DIR
```

Read the revised answer and complete `revision_review.json` from its
template. Set `approve` if recognition is supported, or `reject` if it
remains wrong. Then close the review:

```powershell
uv run football-coach finish-prompt-coaching RUN_DIR
```

A rejected revision is preserved without a coaching request. Frame citations
in review files refer to sampled image positions 1–30.

The commands preserve each prompt, model answer, raw API response, human
review, exact feedback, model digest, timing, frame hashes, and crashes. They
accept only the declared B-train development clips. The former automatic
`run-prompt-chain` command has been removed. See
`PROJECT_NEXT_STEPS.md` for the full procedure.

The active protocol, prompts, and evaluation files are
`config/project_v0.4.0.json`,
`config/prompt_development_cohort_v0.4.0.json`,
`input_prompts/v0.4/p1_recognition.txt`,
`input_prompts/v0.4/p1_revision.txt`,
`input_prompts/v0.4/p1_coaching.txt`,
`config/scoring_rubric_v0.4.txt`, and
`templates/v0.4/prompt_chain_score.template.txt`.
