# Project Next Steps — v0.4 Human-Guided Recognition

## Current position

The researcher approved a new in-context experiment using another dataset for
corner, penalty and free-kick recognition. Its candidate declaration is
`config/in_context_event_examples_v1.json`; the readable guide is
`input_prompts/in_context_events/START_HERE.txt`. The new selection uses only
the official SoccerNet-v2 Action Spotting train matches, partitioned internally
by whole match into example, development and held-out test roles. This is a
separate source task from Dataset B GSR. The annotation selection freeze is
`config/freezes/in_context_event_selection_v1.json`; footage access, sampled
image/reference review, prior GSR overlap and pixel duplicate audits remain
execution gates. Run `python -m football_coach.event_examples verify` locally
to check the selection hashes. Do not prompt on this cohort until its media
and example text have a second approved freeze. This does not authorise use
of the existing GSR validation/test or official Action Spotting valid/test.

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

## B-TRAIN-0025 pilot comparison (P1–P3)

- **P1, explicit correction:** The initial recognition missed the restart and
  misattributed the later clearance. After frame-cited feedback that named the
  corner, grey clearance, and late stoppage, recognition improved enough to
  request coaching. The advice was more relevant, but its positioning/timing
  diagnosis was not established by the frames.
- **P2, progressive attention hints:** Three hint turns corrected an
  unsupported defensive-wall claim and reduced confidence, but recognition
  still missed the corner, grey clearance, and possible late foul/stoppage.
  Stopped without coaching.
- **P3, frozen visible cues:** One cue packet improved uncertainty and
  recognition of an apparent late stoppage, but the model still missed the
  specific restart and grey clearance. Stopped without coaching.

These are exploratory results for one known train clip, not an unseen or
matched comparison. P0 contains only a historical v0.3 B0 reference, not a
fresh v0.4 control. The local, human-readable run guide is
`output/v0.4/prompt_chain/START_HERE.txt`; raw API and review-snapshot JSON
remain in their original run folders for provenance.

The next label-informed *development* order is B-TRAIN-0054, then
B-TRAIN-0040, then B-TRAIN-0051. It is recorded in
`config/label_informed_development_order_v0.4.1.json`. The original eight-clip
cohort was selected without hidden labels, but this follow-up subset was not.
The P1 run metadata records that distinction; no private labels are sent to
the model. Review each initial answer against its 30 sampled frames before
correction or coaching. Keep a separate untouched B-train holdout for later
comparative evaluation.

The first B-TRAIN-0054 GPU attempt returned HTTP 500 at stage 1 and produced
no recognition result. At the researcher's request, its diagnostic metadata
was removed; the saved prompt remains, so this attempt cannot be audited as
a complete run. The shared remote GPU was concurrently used by another
researcher's training job; this is a possible contributor, not a confirmed
cause. Do not alter that job. If using CPU for a
fresh attempt, select `config/project_v0.4.0_cpu.json` explicitly for **every**
P1 stage. It keeps the prompts and 30-frame sampling the same but requests
`num_gpu=0` and verifies zero Ollama GPU residency. Record CPU and GPU runs as
different execution variants; CPU inference may be much slower. The default
`config/project_v0.4.0.json` remains the original GPU configuration.

## Approved fixed unattended development follow-up

The researcher approved the same three P2 hints and separate P3 visible-cue
sheets for B-TRAIN-0054, B-TRAIN-0040, and B-TRAIN-0051. Their frozen paths
and hashes are declared in `config/fixed_unattended_development_v0.4.3.json`.
This is a new `fixed_unattended_v2` variant, not a continuation of the
interactive B-TRAIN-0025 P2/P3 runs. It uses fresh recognition calls for each
condition and clip, makes three prewritten P2 hint turns or one P3 cue turn,
and stops before coaching. The batch first creates fresh initial-only P1 recognition
for B-TRAIN-0040 and B-TRAIN-0051, without feedback or coaching. The existing
B-TRAIN-0054 P1 first pass is not rerun. This is label-informed development,
not unseen evaluation. Transfer the remote P1 run folders to the local project
before reviewing those answers and editing their `initial_review.json` files.
The earlier `fixed_unattended_v1` declaration in `config/fixed_unattended_development_v0.4.2.json`
was superseded before execution; it has no accepted model results.

Run `football-coach validate-fixed-development` before
`football-coach run-fixed-development`. The CPU-only batch reads only the 90
pre-sampled JPEGs, code, and frozen prompt inputs. It does not need raw video
archives or hidden reference contents on the remote workstation; the two P1
reference hashes are frozen in the batch declaration for later local
continuation. The completed remote batch used a hashed transfer bundle and
a tmux launcher. Its one-off packaging and transfer helpers were removed
after the results were imported locally. A prior attempted
fixed cell blocks a new batch; inspect its preserved output or error before
planning any retry. The assistant's sandbox cannot SSH to the workstation,
so the researcher must transfer and launch the bundle.

The batch finished on 2026-09-30 and all eight run folders were transferred
locally. P1 initial reviews for 0040, 0051, and 0054 were prepared for the
subsequent unattended P1 recognition revisions. Their portable preflight checked
the frozen Stage 1 answers, reviews, prompts, sampled-frame hashes, CPU
configuration, and model digest without copying private reference contents.
It records that the private references were not reverified on the remote host,
and it stops before coaching. Do not rerun an attempted revision silently.
As of 2026-10-01, the local B-TRAIN-0040 sampled image 1 differs from its
frozen hash; preserve it and investigate before any local continuation or
coaching. The remote preflight must confirm the workstation still has the
original frozen frame set before sending a revision call.

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
   frame-cited feedback. The original draft workflow stops without coaching
   after one revision. An opt-in, separately reported train-only P1 extension
   allows up to three total recognition revisions; it preserves every turn.
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
| Optional P1 multi-revision development extension | `config/p1_multi_revision_extension_v0.4.4.json` |
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
| No feedback | `output/v0.4/prompt_chain/P0_no_feedback/` | Contains byte-for-byte historical v0.3 B0 references for B-TRAIN-0025, B-TRAIN-0054, B-TRAIN-0040, and B-TRAIN-0051; no v0.4 P0 run yet |
| Explicit frame-based correction | `output/v0.4/prompt_chain/P1_human_guided/` | Contains the completed B-TRAIN-0025 diagnostic |
| Progressive human hints | `output/v0.4/prompt_chain/P2_attention_hint/` | B-TRAIN-0025 stopped after three hints; no coaching requested |
| Visible cues without event labels | `output/v0.4/prompt_chain/P3_visible_cue_hint/` | B-TRAIN-0025 stopped after one frozen cue packet; no coaching requested |

Outputs now use `condition/B-TRAIN-####/UTC-run-timestamp/`; see
`output/v0.4/prompt_chain/START_HERE.txt` for the run index. The model and
variant are recorded in each run's metadata, not in intermediate folders.
Archived remote-transfer scripts and original metadata may still contain the
paths used when those completed runs were created; do not rerun accepted cells
from those scripts. The frozen P3 cue masters remain at their config-declared
paths and were not changed.

The P0 copy is under `P0_no_feedback/B-TRAIN-0025/20260908T094048609964Z/`.
It is the 30-frame PILOT-010 B0 run, copied from
`output/B0_frames_only/qwen3.5_27b/B-TRAIN-0025/20260908T094048609964Z/`.
Its original v0.3 metadata and prompt remain unchanged. This is context, not
a matched v0.4 no-feedback result; the pilot score remains in
`data/video_b/review/pilot_grading_v1/PILOT-010/score.txt`.

The B-TRAIN-0054 historical copy is under
`P0_no_feedback/B-TRAIN-0054/20260908T123501974922Z/`.
It is the 30-frame v0.3 B0 run associated with PILOT-014. Its four files
were copied byte-for-byte from `output/B0_frames_only/`; it is likewise not
a fresh or matched v0.4 P0 result.

The B-TRAIN-0040 and B-TRAIN-0051 historical copies are the completed
30-frame v0.3 B0 runs under the same historical-reference tree, timestamped
`20260910T071517605837Z` and `20260908T162234274547Z`, respectively.
Their four source files were copied byte-for-byte. The 10-, 20-, and 60-frame
historical runs remain only in `output/B0_frames_only/`.

P1, progressive P2, and frozen-cue P3 are implemented; P0 is not. The earlier
one-hint P2 run that reused P1's first answer was deleted at the researcher's
request; do not report it as a retained result. New P2 runs begin with a fresh
call on the same 30 frames and are stored directly under
`P2_attention_hint/<model>/<clip>/<timestamp>/`. No P1 answer or feedback is
sent to the model.

## P2 progressive-hint workflow and completed B-TRAIN-0025 diagnostic

The B-TRAIN-0025 run at
`P2_attention_hint/B-TRAIN-0025/20260927T153631433589Z/`
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
`P3_visible_cue_hint/B-TRAIN-0025/20260927T163258749494Z/`
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

For an existing P1 run still awaiting review after its first revision, the
optional `P1_multi_revision_development_v0.4.4` extension allows another
frame-cited correction without changing the original v0.4.0 config hash:

```powershell
uv run --system-certs football-coach continue-prompt-recognition RUN_DIR
```

For the B-TRAIN-0054/0040/0051 CPU-only runs, append
`--config-path config/project_v0.4.0_cpu.json` to both continuation and
coaching commands. Their recorded config hash does not match the GPU config.

First fill `revision_review.json` with the remaining frame-cited errors.
The command preserves that review and creates `stage_3_revision_response.txt`
and `revision_review_2.json`. After reviewing the new answer, empty feedback
approves it for `finish-prompt-coaching`; more feedback can trigger one final
continuation, creating stage 4 recognition and `revision_review_3.json`.
At most three total recognition revisions are permitted. Coaching is never
automatic, and these extended P1 runs must be reported separately from the
original one-revision P1 results. The original prompts, answers, reviews,
feedback, and hashes remain unchanged.

An optional `--coaching-focus-file RUN_DIR/coaching_focus.txt` on
`finish-prompt-coaching` adds a researcher-authored, run-local coaching focus
after the frozen base coaching prompt. Its file hash and exact combined prompt
are preserved. Label such outputs `P1_researcher_focused_development` and do
not pool them with the standard one-team P1 coaching cell. B-TRAIN-0040 uses
this option to request advice for both teams, prioritising red-and-black
defending while keeping unsupported tactical faults conditional.

The old `run-prompt-chain` command that automatically generated both answers
has been removed.

## Current P1 remote follow-up gate

The first P1 revisions for B-TRAIN-0040, 0051, and 0054 have returned and
were reviewed locally. B-TRAIN-0040's local coaching call stopped after its
stage-3 prompt and `coaching_started` status were saved, without a response,
raw result, or error. The researcher explicitly requested deletion of that
incomplete coaching prompt and review snapshot. The stage-1 and stage-2
answers, reviews, and frame hashes remain. The metadata records the removal;
the interrupted call has no scorable result. The portable follow-up creates
a separate 0040 coaching run from the reviewed recognition and researcher
coaching focus, rather than reusing the interrupted attempt. It also requests
standard coaching for approved 0051 recognition and
sends one explicit, human-supplied left-corner recognition correction for 0054.
It does not request 0054 coaching. None of these calls measures independent
event recognition.

The completed follow-up used a hashed, incremental v2 transfer archive and
a tmux launcher on the remote workstation. Its preflight checked CPU-only
residency and the exact model digest. The returned answers remain in their
clip-specific output folders; the one-off packaging and transfer helpers
have been removed. Review returned outputs and 0054's
`revision_review_2.json` before any further coaching.

For B-TRAIN-0054, the second explicit correction still did not produce an
approved event sequence. At the researcher's request, the optional
`p1_unapproved_recognition_coaching_probe_v1` asks the existing coaching
prompt what advice it gives anyway. This is an exploratory diagnostic, not a
successful P1 coaching cell, and must not be pooled with approved-recognition
advice. It keeps the original `revision_review_2.json` pending and writes to
`P1_human_guided/B-TRAIN-0054/20261001T125442080Z/`. This remote probe has
finished and its outputs were returned locally. Its transfer manifest is
preserved under that run's `provenance/remote_transfer_manifest.json`;
the redundant archives and launch helpers were removed. Interpret any advice as conditional on unapproved recognition and
the researcher's prior explicit correction, not as independent video understanding.

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
- Consider Qwen3.5 35B or fine-tuning only after the first
  development findings identify a specific need. Compare pretrained and
  fine-tuned versions of the same model under a declared feedback policy.
- Validation is not authorized during draft development. The Dataset B test
  split remains sealed until a new supervisor-approved protocol freeze.
