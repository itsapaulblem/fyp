# Train-pilot human evaluation results

Coaching protocol: `coach-eval-v0.1.1`

Recognition protocol: `event-recognition-v0.1.0`

Model: `qwen3-vl:2b-instruct`

Input: 16 uniformly sampled frames per clip

Status: complete single-reviewer train-pilot evaluation

## Scope and provenance

These are human-rated and project-derived development results for the 12 train
clips in `data/processed/pilot_selection.csv`. They are not SoccerNet-authored
scores and are not final test-set performance. The project author was the sole
reviewer and was not blinded to the model responses or hidden references.

The authoritative row-level results are in
`human_evaluation/pilot_review_index.csv`. The machine-readable aggregate is
`data/processed/pilot_human_evaluation_summary.json`.

## Coaching results

| Statistic | Result |
|---|---:|
| Reviewed clips | 12/12 |
| Total score | 40/144 |
| Mean score | 3.33/12 |
| Median score | 3/12 |
| Range | 0–6 |
| Provisional mean target met | No (target: 8/12) |

Score distribution: one clip scored 0, four scored 2, two scored 3, one
scored 4, two scored 5, and two scored 6.

### Criterion means

| Criterion | Mean (0–2) |
|---|---:|
| Factual accuracy | 0.750 |
| Tactical correctness | 0.500 |
| Visual grounding | 0.917 |
| Specificity | 0.167 |
| Actionability | 0.667 |
| Evidence-advice consistency | 0.333 |

The highest criterion was visual grounding, but specificity and
evidence-to-advice consistency were particularly weak. A derived proxy that
requires both specificity and actionability scores of at least 1 was met by
2/12 clips (16.7%). This proxy was calculated after review and is not a
separately collected binary judgement.

The reviewer recorded 13 major hallucinations across 10/12 clips (83.3%).
This fails the provisional criterion requiring major hallucinations in fewer
than 15% of clips.

### Pilot-group means

| Pilot group | Mean score (0–12) |
|---|---:|
| Corner | 4.5 |
| Direct free kick | 4.5 |
| Foul or defensive restart | 3.5 |
| Shots on target | 1.0 |
| Shots off target or goal | 3.5 |
| Clearance | 3.0 |

Each pilot group contains only two clips, so these values describe pilot
failures and must not be treated as reliable scenario-level performance.

## Recognition-gate results

A clip passes only when the attacking team, event, and visible outcome are all
judged correct. `Partly` does not pass.

| Statistic | Result |
|---|---:|
| Eligible clips | 12 |
| Gate passes | 0/12 |
| Required passes | 9/12 |
| Attacking team exactly correct | 4/12 (33.3%) |
| Event exactly correct | 1/12 (8.3%) |
| Outcome exactly correct | 1/12 (8.3%) |
| High-confidence model answers | 12/12 |
| High confidence judged appropriate | 0/12 |

The recognition prerequisite failed. The model sometimes identified a shirt
colour or general attacking phase, but it usually missed the defining event,
outcome, or a change of possession. Coaching conclusions from this condition
therefore cannot be assumed to be grounded in a correct understanding of the
sequence.

## Decision

Do not progress this condition to validation or test evaluation. The next
train-only experiment should isolate temporal input sufficiency while keeping
the recognition prompt and gate unchanged. A controlled comparison of the
current 16 uniform frames against a denser uniform sample can determine
whether sparse temporal evidence is the main bottleneck before changing the
model or resuming coaching evaluation.
