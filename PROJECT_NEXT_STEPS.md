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
must be run and reported separately if it is used as a comparator. No P1 model
response has been generated yet.

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
4. The researcher reviews the revision. If it is still wrong, record `reject`
   and stop without coaching; the draft workflow allows one revision.
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
| Eight known development clips | `config/prompt_development_cohort_v0.4.0.json` |
| Initial recognition prompt | `input_prompts/v0.4/p1_recognition.txt` |
| Revision prompt | `input_prompts/v0.4/p1_revision.txt` |
| Coaching prompt | `input_prompts/v0.4/p1_coaching.txt` |
| Draft human scoring rubric | `config/scoring_rubric_v0.4.txt` |
| Draft score form | `templates/v0.4/prompt_chain_score.template.txt` |
| Generated run artifacts | `output/v0.4/prompt_chain/P1_human_guided/` |

The draft rubric is for development. Freeze it before a separate train
holdout. The eight known B-train clips are not unseen evaluation examples.

## First development clip

Review the three prompts and the rubric. Validate the local setup without
contacting the model:

```powershell
uv run football-coach validate-prompt-chain
```

Check the exact installed model, then generate only the initial recognition:

```powershell
uv run football-coach ollama-check --model qwen3.5:27b
uv run football-coach start-prompt-review B-TRAIN-0025 --model qwen3.5:27b
```

The start command prints a timestamped run directory. Open its
`stage_1_response.txt` and review the 30 sampled images. Copy
`initial_review.template.json` to `initial_review.json`; fill reviewer,
date, frame-use declarations, and a decision:

- `approve`: remove the template's example feedback item, then request
  coaching.
- `revise`: replace the example item with your actual sampled frame numbers,
  visible evidence, and requested correction. Then run the revision command.

```powershell
uv run football-coach revise-prompt-recognition RUN_DIR
```

The revision command creates `stage_2_revision_response.txt` and
`revision_review.template.json`. Review the revised answer. Copy that
template to `revision_review.json`, complete it, and set `decision` to
`approve` only if the answer is sufficiently supported. Set `reject` if
recognition remains materially wrong. Then close the review:

```powershell
uv run football-coach finish-prompt-coaching RUN_DIR
```

With `reject`, the finish command records `recognition_rejected` and sends no
coaching request. For a correct first answer, run `finish-prompt-coaching`
after completing `initial_review.json`; skip revision. `RUN_DIR` is the full
timestamped path printed by the start command. Each command checks the
reviewed answer hash, sampled frame hashes, prompt/config hashes, train split,
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
