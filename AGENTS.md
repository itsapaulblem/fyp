# Instructions for coding and research agents

## Active research question: protocol v0.4

Test whether human frame-based feedback on an MLLM's first recognition answer
helps it correct the football event sequence and produce useful coaching
advice. The researcher reviews the original answer, supplies specific
frame-cited corrections when needed, reviews the revised answer, and requests
coaching only after approving recognition. This is a human-assisted result.

This is analysis of ordered sampled images supplied to Ollama, not native video
understanding. The completed development runs are `P1_human_guided` and
`P2_attention_hint`; neither is an automatic no-feedback chain.
The v0.4 `prompt_chain` output has four condition folders: `P0_no_feedback`,
`P1_human_guided` (explicit correction), `P2_attention_hint`, and
`P3_visible_cue_hint`. P1 and progressive P2 are runnable; P0 and P3 are
placeholders. P2 `progressive_v1` starts from a fresh recognition call on the
same 30 frames, then allows at most three human-authored, frame-cited hint
turns with review after every answer. It is declared in
`config/p2_progressive_hints_v0.4.1.json`. It writes directly under
`output/v0.4/prompt_chain/P2_attention_hint/` and never sends P1's original
answer, explicit feedback, revision, or coaching. The old one-hint P2 run was
deleted at the researcher's request and is not a retained result. Keep the
completed B-TRAIN-0025 P1 run intact and never relabel the historical v0.3 B0
result as a v0.4 no-feedback run. The B-TRAIN-0025 progressive P2 run was
stopped after three hints because recognition remained insufficient; no P2
coaching was requested.

## Immediate work

- Follow `PROJECT_NEXT_STEPS.md` for the current execution gate.
- Review the recognition, revision, and coaching prompts in
  `input_prompts/v0.4/` and the draft rubric before the first P1 diagnostic.
- Validate the train-only setup with `football-coach validate-prompt-chain`.
- The first declared diagnostic clip is `B-TRAIN-0025` with
  `qwen3.5:27b`. Run `start-prompt-review`, review its initial answer,
  record an approval or sampled-frame corrections, use
  `revise-prompt-recognition` if corrections are needed, approve the revision,
  and only then use `finish-prompt-coaching`. A still-wrong revision must be
  rejected and closed without a coaching request.
- Preserve the original answer, review files, exact feedback, revision, and
  coaching. Permit at most one revision in this draft workflow. Never replace
  a model answer in place or add hidden labels to human feedback.
- New v0.4 runs create the actual review JSON with a pending marker; they do
  not generate separate review template JSON files. A pending review cannot
  advance to the next model call.
- Do not present the eight known B-train development clips as unseen evaluation.
  Choose and freeze a separate train holdout before comparative scoring.

## Dataset and leakage rules

- Dataset B is immutable SoccerNet GSR v1.3: 57 train, 58 valid, 49 test clips.
  Each clip contains 750 ordered JPEGs at 25 fps (30 seconds).
- P1 development may use only the declared B-train cohort. Validation is not
  authorized during draft prompt development; test remains sealed.
- The model receives the 30 selected B images, declared prompts, its earlier
  answers, and the researcher's frame-cited feedback when revision is needed.
  Frame citations refer to sampled image positions 1–30.
  Never provide hidden action labels, tracking, coordinates, identities,
  filenames that reveal events, human references, or earlier model answers from
  another run.
- Human references must be written from the visible sampled frames before
  hidden SoccerNet labels are attached or consulted. Hidden labels are
  reference/oracle information, not coaching ground truth.
- Preserve exact frame indices, image construction, resolution, and hashes.
  Report sampled-frame limitations and uncertainty.

## Experimental discipline

- Report P1 as human-assisted. Compare it with a separately declared automatic
  no-feedback condition on the same B frames and model. Record model digest, settings,
  prompt/config hashes, raw responses, timing, and failures for every run.
- Score initial recognition before giving feedback, revised recognition before
  coaching, and final advice after coaching. Report feedback validity,
  correction success, hallucination propagation, and uncertainty separately.
- Preserve malformed answers and crashes exactly. Never silently repair output
  or rerun an accepted cell because its answer is poor.
- `qwen3-vl:2b-instruct` is retired. Current local candidates are the exact
  `qwen3.5:27b` and `qwen3.5:35b` tags.
- Fine-tuning is a later experiment after diagnosing a repeatable failure.
  Use human-authored B-train pixel-derived targets, keep validation/test out of
  training, and compare the same pretrained and fine-tuned base model under a
  frozen evaluation method.
- A frontier API is a later option if local performance is insufficient. Use
  the same sampled frames and preserve provider/model provenance; obtain
  permission before transmitting private frames externally.

## Historical protocol v0.3: Dataset A retrieval

Protocol v0.3 tested whether a human-annotated analogous Dataset A coaching
case improved recognition and advice for Dataset B. Its validation result was
negative or inconclusive and is preserved by `v0.3-validation-complete`.
Do not rerun accepted B0–B5 cells or import their prompts, answers, scores, or
conclusions into a new v0.4 result. Retrieval-assisted performance is not
independent video understanding.

If historical cases or retrieval code must be inspected or extended:

- Keep advice paired with the exact sourced video segment, rights status,
  access date, human observation, tactical tags, attribution, and review status.
  Unknown rights or incomplete review prevents approval.
- B1 is a random-case control; B2 uses hidden action labels as an explicitly
  leaked oracle; B3 uses human-selected pairs; B4 uses pixel-only cosine
  nearest-neighbour retrieval; B5 supplies only B4 case advice.
- Automatic retrieval may use B pixels or embeddings derived from pixels.
  Hidden labels, tracking, and coordinates must never enter that path.
- Preserve the original v0.3 configuration, prompts, outputs, scores, freezes,
  Dataset A records, and private validation report.

## FYP and repository standards

- Demonstrate independent learning and justify material design choices.
  Preserve failed experiments and use diagnosed failures to motivate changes.
- Present rationale, advantages, evidence, limitations, and outstanding issues.
  Keep prompts and exact model answers human-readable under `input_prompts`
  and `output`. Explain decisions in chat; avoid unnecessary Markdown files.
- `data/raw` is immutable and access-controlled. Never commit or redistribute
  it. `archive/20260902-180846` is historical provenance; never modify it.
- Store secrets only in `.env`; commit only `.env.example`. Generated media,
  embeddings, private references, and outputs are Git-ignored.
- Do not invent cases, coaching advice, links, labels, relevance judgments,
  scores, or metric values.
