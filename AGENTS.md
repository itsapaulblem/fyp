# Instructions for coding and research agents

## Research question

This project tests whether a multimodal large language model can observe a short
football sequence, correctly identify visible game state and tactical problems,
and produce useful coaching advice. Fluent advice is not evidence of visual
understanding.

## FYP standard

- The work must demonstrate independent learning of useful new material, not
  merely apply a pre-provided course template.
- Failed experiments are valid evidence. Preserve them, diagnose why they
  failed, and use the diagnosis to justify the next design.
- Present every design choice with its rationale, advantages, limitations,
  evidence, and outstanding issues.
- Keep presentation-facing prompts and model answers as human-readable text
  files under `input_prompts` and `output`.
- Prefer explaining design decisions in the conversation. Do not create extra
  Markdown documents unless documentation is genuinely needed or requested.

## Dataset facts and boundaries

- The local source is SoccerNet Game State Reconstruction v1.3.
- The verified local release has 164 clips: 57 train, 58 valid, and 49 test.
- Each clip is 30 seconds represented by 750 ordered JPEG frames at 25 fps.
- SoccerNet annotations are reference data for recognition/analytics; SoccerNet
  does not provide coaching-advice ground truth.
- `data/raw` is immutable, access-controlled source data. Never commit, modify,
  redistribute, or upload it to an external service.
- `archive/20260902-180846` is historical provenance. Do not import its model
  responses, scores, prompts, or conclusions into the new experiment.

## Experimental discipline

- Keep `model_input`, `reference_annotations`, `human_coaching_reference`, and
  `model_output` as separate evidence layers.
- Never expose SoccerNet action labels, tracking, coordinates, IDs, filenames,
  human advice, or prior responses to a frames-only model condition.
- Ollama vision consumes sampled images, not native video. Always report the
  sampling method and never describe a frame/contact-sheet condition as native
  video understanding.
- Run recognition scoring before coaching-quality scoring.
- Use the same frozen inputs, prompt, schema, and generation settings for paired
  Qwen3.5 27B/35B comparisons. Record exact model tag/digest and raw output.
- Preserve schema-noncompliant output; never silently repair it.

## Split discipline

- Train: prompt and protocol development.
- Validation: sampling/method selection and calibration.
- Test: one final run only after protocol freeze.
- Do not tune on test clips or reveal test coaching references before freeze.
- Dataset membership is versioned and deterministic. Any change requires a new
  dataset version and written rationale.

## Human coaching references

- Clip-specific advice must be written after viewing the full 30-second clip by
  a qualified human reviewer and must include visible evidence and uncertainty.
- Online federation coaching resources may support terminology and intervention
  design, but text from unrelated examples is not a label for a SoccerNet clip.
- Record reviewer identity pseudonym, qualification, date, source links, and
  conflicts. Do not claim expert consensus or inter-rater reliability without
  the required independent reviewers.

## Repository safety

- Store secrets only in environment variables; commit only `.env.example`.
- Generated media, raw data, annotations under `annotations/private`, and model
  outputs are Git-ignored.
- Do not invent clips, labels, reviewer scores, citations, or metric values.
- Preserve raw responses and provenance before parsing or scoring.
