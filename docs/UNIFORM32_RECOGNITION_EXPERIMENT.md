# Uniform 32-frame recognition experiment

Protocol: `event-recognition-v0.2.0`

Status: 12 model runs complete; single-reviewer assessment pending

## Purpose

This train-only diagnostic tests whether the failed 16-frame recognition gate
was materially affected by sparse temporal sampling. It changes only the
number of uniformly sampled frames from 16 to 32.

The same 12 train clips, `qwen3-vl:2b-instruct` model, recognition prompt,
image preprocessing, deterministic decoding, hidden-information boundary,
human reviewer, and all-three-correct gate are retained. The context capacity
is increased from 16,384 to 32,768 tokens because the 32 images require more
than 16,384 input tokens; this prevents truncation and does not change the
requested output length. Results must not be pooled with the 16-frame
condition.

## Commands

Prepare the separate 32-frame input manifest:

```powershell
uv run soccernet-dataset recognition-prepare --condition uniform32
```

Run one smoke clip:

```powershell
uv run soccernet-dataset recognition-run --condition uniform32 --limit 1
```

Run all remaining clips without overwriting the smoke result:

```powershell
uv run soccernet-dataset recognition-run --condition uniform32
```

Create the model-generated technical summary:

```powershell
uv run soccernet-dataset recognition-summarize --condition uniform32
```

## Artifacts

- Inputs: `data/processed/recognition_inputs_uniform32.json`
- Unedited model runs: `data/processed/recognition_runs/uniform32/`
- Technical summary: `data/processed/recognition_summary_uniform32.json`

These project-derived files remain Git-ignored because they refer to
NDA-controlled source imagery. Human gate judgements will be recorded later
and must remain separate from these model-generated outputs.

## Model-generated technical result

| Diagnostic | Result |
|---|---:|
| Completed calls | 12/12 |
| Complete JSON schemas | 12/12 |
| Automatic anchor-term matches | 3/12 |
| High-confidence responses | 12/12 |
| Mean runtime per clip | 73.617 seconds |

Automatic anchor-term matching remains diagnostic only and does not determine
whether any clip passes. The sole reviewer must record the 32-frame condition
separately in `human_evaluation/recognition_uniform32_review.csv`. The original
16-frame judgements must not be overwritten.
