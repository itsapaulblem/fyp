# Instructions for coding and research agents

## Research question

Test whether a human-annotated analogous football case retrieved from Dataset A
improves an MLLM's recognition and coaching advice for a new Dataset B sequence.
Do not describe retrieval-assisted performance as independent video understanding.

## FYP standard

- Demonstrate independent learning and justify every material design choice.
- Preserve failed experiments and use diagnosed failures to motivate changes.
- Present rationale, advantages, evidence, limitations, and outstanding issues.
- Keep prompts and exact model answers human-readable under `input_prompts` and
  `output`.
- Explain decisions in chat; avoid unnecessary Markdown documents.

## Dataset A: coaching case library

- Every approved case must pair advice with the exact referenced video segment.
- Record URL/provider, clip boundaries, rights status, access date, human
  observation, tactical tags, advice, reviewer identity/qualification, and date.
- Federation material may inform terminology, but unrelated advice is not a
  valid label.
- Unknown rights or incomplete human review means the case remains `draft`.
- Start with a 20–30 case feasibility pilot; scale beyond 100 only if justified.

## Dataset B: SoccerNet queries

- Source is immutable SoccerNet GSR v1.3: 57 train, 58 valid, 49 test.
- Each clip is 750 ordered JPEGs at 25 fps (30 seconds).
- SoccerNet labels are hidden reference/oracle data, not model input or coaching
  ground truth.
- Never expose action labels, tracking, coordinates, IDs, filenames revealing
  events, human references, or prior answers in an automatic visual condition.

## Retrieval and leakage discipline

- Automatic retrieval may use only B pixels or embeddings derived from pixels.
- Hidden B action labels may select A only in `B2_action_oracle` and must be
  reported as oracle leakage, not an end-to-end system.
- Human-selected pairs are `B3_human_oracle`, not automatic retrieval.
- Use cosine k-nearest neighbours for direct matching. K-means is optional
  exploratory clustering, not a substitute for nearest-neighbour retrieval.
- Fit/tune encoders, projections, normalization, tags, and k using B train only;
  select the final method on validation; run test once after freeze.

## Experimental discipline

- Maintain B0 frames-only, B1 random-case, B2 action-oracle, B3 human-oracle,
  B4 embedding-kNN, and B5 advice-only controls.
- Use identical B frames, prompts, schemas, and generation settings across paired
  model comparisons except for the intended independent variable.
- Score B recognition before coaching quality. Separately score retrieval
  relevance, blind copying, hallucination, and calibrated uncertainty.
- Ollama accepts sampled images rather than native video. Report exact frame
  count, indices, resolution, and construction method.
- Preserve raw schema failures, crashes, timing, model tag/digest, config/prompt
  hashes, frame hashes, and retrieval provenance. Never silently repair output.
- The Qwen 2B model is retired. Current candidates are exact Qwen3.5 27B/35B tags.

## Repository safety

- `data/raw` is immutable and access-controlled. Never commit or redistribute it.
- `archive/20260902-180846` is historical provenance. Never modify or import its
  prompts, outputs, scores, or conclusions into a new result.
- Store secrets only in `.env`; commit only `.env.example`.
- Generated media, embeddings, private references, and outputs are Git-ignored.
- Do not invent cases, coaching advice, reviewer credentials, links, labels,
  pair relevance, scores, or metric values.

