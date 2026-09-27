# Project Next Steps — v0.4 Human-Guided Recognition

## Current position

Protocol v0.3 completed four-clip validation with a negative or inconclusive
retrieval result. The state is preserved by Git tag
`v0.3-validation-complete`. All evaluated B0–B5 conditions missed the critical
event in all four clips. Do not rerun or alter those accepted results.

The supervisor's next direction is to guide the model through event
recognition before coaching. The active v0.4 experiment includes a deliberate
human checkpoint: the researcher reviews the first recognition answer against
the same 30 sampled frames, gives frame-cited corrections if needed, reviews
the revised answer, and requests coaching only after approval.

The final advice is a human-assisted result. An automatic no-feedback chain
must be run and reported separately if it is used as a comparator. The first
`B-TRAIN-0025` P1 run is complete and preserved under `P1_human_guided`.
Its retrospective score is development-only, not a blinded comparison.

## Research question

Does specific human feedback on a model's sampled-frame recognition answer
correct material event errors and lead to more useful, evidence-supported
coaching advice?

Measure initial recognition, revised recognition, feedback validity, and final
coaching separately. Do not combine them into one score or claim that
human-guided advice demonstrates independent video understanding.

## Active workflow: `P1_human_guided`

1. The model receives 30 ordered F30 frames and describes visible evidence,
   event order, main event, outcome, and uncertainty. It gives no coaching.
2. The researcher reviews the original answer against those sampled frames.
   The review either approves it or records specific corrections citing sampled
   image positions 1–30. Hidden SoccerNet labels are not used.
3. If corrections were needed, the model receives the exact frame-cited
   feedback and produces one complete revised recognition answer.
4. The researcher reviews the revision. If it is still wrong, record
   frame-cited feedback and stop without coaching; the draft workflow allows
   one revision.
5. The model receives the approved recognition history and produces coaching
   advice. The original answer, review, feedback, revision, prompts, raw API
   responses, hashes, and timing remain in the run folder.

If the first recognition answer is accurate, the researcher can approve it and
go directly to coaching without a revision. Do not create an artificial
correction.

## Files to use

| Purpose | File |
|---|---|
| Train-only protocol and model settings | `config/project_v0.4.0.json` |
| P2 progressive condition declaration | `config/p2_progressive_hints_v0.4.1.json` |
| P3 frozen cue declaration and SHA-256 | `config/p3_visible_cues_v0.4.0.json` |
| P3 approved cue sheet (local, Git-ignored) | `output/v0.4/prompt_chain/P3_visible_cue_hint/B-TRAIN-0025_visible_cues.v1.txt` |
| P3 cue revision wrapper | `input_prompts/v0.4/p3_visible_cue_revision.txt` |
| Eight known development clips | `config/prompt_development_cohort_v0.4.0.json` |
| Initial recognition prompt | `input_prompts/v0.4/p1_recognition.txt` |
| Revision prompt | `input_prompts/v0.4/p1_revision.txt` |
| Coaching prompt | `input_prompts/v0.4/p1_coaching.txt` |
| P2 per-turn hint wrapper | `input_prompts/v0.4/p2_progressive_hint.txt` |
| Draft human scoring rubric | `config/scoring_rubric_v0.4.txt` |
| Draft score form | `templates/v0.4/prompt_chain_score.template.txt` |
| P2 draft score form | `templates/v0.4/attention_hint_score.template.txt` |
| Generated run artifacts | `output/v0.4/prompt_chain/P1_human_guided/` |

The draft rubric is for development. Freeze it before a separate train
holdout. The eight known B-train clips are not unseen evaluation examples.

## Prompt-chain condition folders

| Condition | Output folder | Current status |
|---|---|---|
| No feedback | `output/v0.4/prompt_chain/P0_no_feedback/` | Contains only a byte-for-byte historical v0.3 B0 B-TRAIN-0025 reference; no v0.4 P0 run yet |
| Explicit frame-based correction | `output/v0.4/prompt_chain/P1_human_guided/` | Contains the completed B-TRAIN-0025 diagnostic |
| Progressive human hints | `output/v0.4/prompt_chain/P2_attention_hint/` | B-TRAIN-0025 stopped after three hints; no coaching requested |
| Visible cues without event labels | `output/v0.4/prompt_chain/P3_visible_cue_hint/` | B-TRAIN-0025 stopped after one frozen cue packet; no coaching requested |

The P0 copy is under `historical_v0.3_B0_reference/qwen3.5_27b/B-TRAIN-0025/20260908T094048609964Z/`.
It is the 30-frame PILOT-010 B0 run, copied from
`output/B0_frames_only/qwen3.5_27b/B-TRAIN-0025/20260908T094048609964Z/`.
Its original v0.3 metadata and prompt remain unchanged. This is context, not
a matched v0.4 no-feedback result; the pilot score remains in
`data/video_b/review/pilot_grading_v1/PILOT-010/score.txt`.

P1, progressive P2, and frozen-cue P3 are implemented; P0 is not. The earlier
one-hint P2 run that reused P1's first answer was deleted at the researcher's
request; do not report it as a retained result. New P2 runs begin with a fresh
call on the same 30 frames and are stored directly under
`P2_attention_hint/<model>/<clip>/<timestamp>/`. No P1 answer or feedback is
sent to the model.

## P2 progressive-hint workflow and completed B-TRAIN-0025 diagnostic

The B-TRAIN-0025 run at
`P2_attention_hint/qwen3.5_27b/B-TRAIN-0025/20260927T153631433589Z/`
was stopped after three hints. The final answer withdrew the unsupported
defensive-wall claim and lowered confidence, but did not resolve the specific
restart, credited the clearance to the wrong team, and missed the late
stoppage. No coaching call was made. This is a development-only,
human-assisted recognition failure, not a matched no-feedback comparison.
Generated run files remain Git-ignored and local.

Read `config/p2_progressive_hints_v0.4.1.json` and
`input_prompts/v0.4/p2_progressive_hint.txt` before running. Keep the remote
Ollama tunnel open and use PowerShell from the project root:

```powershell
uv run --system-certs football-coach ollama-check --model qwen3.5:27b --require-gpu
uv run --system-certs football-coach start-progressive-review B-TRAIN-0025 --model qwen3.5:27b
```

The command makes a fresh stage-1 recognition request and prints a new P2 run
directory. Read `stage_1_response.txt` and review it against the 30 sampled
frames. Edit the already-created `review_stage_1.json`. Its `PENDING` decision
cannot advance the run; fill
`decision` as `hint`, `approve`, or `stop`:

- For `hint`, fill `frame_numbers_1_based` and your own `hint` text. Use
  sampled-frame questions or cues, not hidden labels, P1's full correction,
  or the complete event answer. Then run `continue-progressive-review`.
- For `approve` or `stop`, leave frame numbers as `[]` and `hint` empty. Run
  `finish-progressive-coaching`. Approval generates coaching; stop closes the
  run without coaching.

```powershell
uv run --system-certs football-coach continue-progressive-review "P2_RUN_DIR"
```

Each continuation produces `stage_N_revision_response.txt` and a matching
`review_stage_N.json`, initially marked `PENDING`. Review every response
before the next hint; no extra template JSON file is generated.
Repeat at most three hint turns. If recognition remains wrong after the third
hint, record `stop` rather than continuing until the model succeeds. To close
an approved or stopped run:

```powershell
uv run --system-certs football-coach finish-progressive-coaching "P2_RUN_DIR"
```

Score the initial answer and every revision separately using the P2 draft
score form. P2 is human-assisted; the v0.3 B0 copy is not a matched control.

## P3 frozen visible-cue workflow and completed B-TRAIN-0025 diagnostic

The first P3 run at
`P3_visible_cue_hint/qwen3.5_27b/B-TRAIN-0025/20260927T163258749494Z/`
was stopped after its single cue revision. The answer became more cautious
and noticed the apparent late stoppage, but did not identify the specific
restart or grey-team clearance and still suggested red moved the ball away
from goal. No coaching call was made. This is a known B-train development
result, not a blinded test or a matched automatic control.

The researcher approved the cue observations in
`B-TRAIN-0025_visible_cues.draft.txt`. A separate v1 copy is frozen at the
path above; its SHA-256 is
`5e698bc8f2aba86ab6d7377f4010a1472c45b1cd2fd39079d36cfda4bacd1f08`.
The declaration checks this digest before every P3 stage and each run stores
its own byte-for-byte cue snapshot. Do not change the frozen file; make a
new version and declaration if the cues need correction. The frozen cue file
is Git-ignored and must be retained locally for reproducibility.

Keep the Ollama tunnel open. From local PowerShell in the project root, begin
a fresh run with the same 30 frames, model, and generation settings:

```powershell
uv run --system-certs football-coach start-visible-cue-review B-TRAIN-0025 --model qwen3.5:27b
```

Read the printed P3 run directory's `stage_1_response.txt` against the
sampled frames. Edit its actual `review_stage_1.json`: use
`{"decision":"continue","notes":"..."}` to send the frozen cue sheet, or
`{"decision":"stop","notes":"..."}` to close without a cue or coaching call.
`PENDING` cannot advance. For `continue`, run:

```powershell
uv run --system-certs football-coach continue-visible-cue-review "P3_RUN_DIR"
```

Read `stage_2_revision_response.txt`. Edit `review_stage_2.json` with
`decision` `approve` only if the recognition is sufficiently supported by
the frames; otherwise use `stop`. Close the run with:

```powershell
uv run --system-certs football-coach finish-visible-cue-coaching "P3_RUN_DIR"
```

The finish command sends a coaching request only after stage-2 approval.
P3 remains human-assisted, and B-TRAIN-0025 remains a known development clip.
Score recognition before cues, recognition after cues, and any final coaching
separately. Do not treat the historical v0.3 B0 copy as a matched control.

## First development clip

Review the three prompts and the rubric. Validate the local setup without
contacting the model:

```powershell
uv run football-coach validate-prompt-chain
```

Check the exact installed model, then generate only the initial recognition:

```powershell
uv run football-coach ollama-check --model qwen3.5:27b --require-gpu
uv run football-coach start-prompt-review B-TRAIN-0025 --model qwen3.5:27b
```

The GPU check preloads the model without sending frames. It fails if Ollama
reports CPU-only placement. v0.4 does not inherit v0.3's `num_gpu: 0` CPU
setting. Each prompting stage checks GPU residency before and after inference
and records the reported VRAM bytes in its run metadata. Partial offload is
allowed but must be reported; the model is not guaranteed to fit entirely in
VRAM. On the remote host, `ollama ps` shows CPU/GPU placement and `nvidia-smi`
shows available VRAM. Do not change the frozen v0.3 configuration.

The start command prints a timestamped run directory. Open its
`stage_1_response.txt` and review the 30 sampled images. Edit the generated
`initial_review.json` directly: replace `PENDING_REVIEW` in `notes` and fill
`feedback` if needed, using the sampled frames and not hidden labels:

- Empty `feedback` (`[]`) means the first recognition is approved; request
  coaching without a revision.
- One or more feedback items, each with sampled frame numbers, visible
  evidence, and a specific correction, request a revision. Then run:

```powershell
uv run football-coach revise-prompt-recognition RUN_DIR
```

The revision command creates `stage_2_revision_response.txt` and
`revision_review.json`. Review the revised answer, then replace `PENDING_REVIEW`
in `notes` and edit `feedback` if needed.
Empty feedback approves the revision; frame-cited feedback records remaining
errors and rejects it. Then close the review:

```powershell
uv run football-coach finish-prompt-coaching RUN_DIR
```

With remaining errors, the finish command records `recognition_rejected` and sends no
coaching request. For a correct first answer, run `finish-prompt-coaching`
after completing `initial_review.json`; skip revision. `RUN_DIR` is the full
timestamped path printed by the start command. Each command checks the
reviewed answer against its raw model response, sampled frame hashes, prompt/config hashes, train split,
and exact model digest before continuing.

The old `run-prompt-chain` command that automatically generated both answers
has been removed.

## Evaluation and later decisions

- Score the first recognition before reading model coaching or writing
  feedback. Record every mistaken and correct visible claim.
- Score any revised recognition before generating coaching. Record whether
  the correction fixed the event without creating another error.
- Score final advice for relevance, specificity, practice quality, visible
  support, hallucination, and uncertainty.
- For a fair comparison, separately define an automatic no-feedback condition
  using the same frames, model, and scoring criteria. Its advice must be
  labelled automatic; P1 advice must be labelled human-assisted.
- Select a new label-blind B-train holdout and freeze all prompts, review
  rules, rubric, model, and frame settings before comparative evaluation.
- Consider Qwen3.5 35B, fine-tuning, or a frontier API only after the first
  development findings identify a specific need. Compare pretrained and
  fine-tuned versions of the same model under a declared feedback policy.
- Validation is not authorized during draft development. The Dataset B test
  split remains sealed until a new supervisor-approved protocol freeze.
