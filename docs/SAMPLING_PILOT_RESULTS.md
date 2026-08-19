# Sixteen-frame sampling pilot results

Protocol: `coach-eval-v0.1.1`

Split: train only

Model: `qwen3-vl:2b-instruct`

Runs: 12 uniform + 12 event-centred

## Decision

Use **uniform 16-frame sampling** as the provisional baseline. Confirm this
choice on validation data before freezing the test protocol.

This is an operational and methodological selection, not a claim that the
uniform answers were high-quality coaching. Both strategies showed weak event
understanding, generic advice, and unjustifiably high confidence.

## Strategies compared

Uniform sampling selected the centre frame from each of 16 equal temporal bins
over the complete 30-second clip. It did not use SoccerNet event timing.

Event-centred sampling selected frames at fixed offsets from the private
SoccerNet `action_position`: -6, -4, -3, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5,
2, 3, 4, 6, and 9 seconds. The action time and label were never shown to Qwen.

Both strategies used the same prompt, 672-pixel maximum image edge, model,
16K context, deterministic decoding, and 600-token output limit.

## Observed results

| Diagnostic | Uniform | Event-centred |
|---|---:|---:|
| Completed model calls | 12/12 | 12/12 |
| Complete JSON schemas | 12/12 | 11/12 |
| Hidden-anchor term matches | 2/12 | 2/12 |
| Mean runtime per clip | 85.6 s | 88.6 s |
| Total inference time | 1,027.0 s | 1,062.8 s |
| Same problem assigned to both teams | 8/12 | 5/12 |
| Same recommendation assigned to both teams | 2/12 | 1/12 |
| Responses claiming high confidence | 12/12 | 11/11 valid |

`SNGS-159` under event-centred sampling reached the 600-token output limit and
ended with incomplete JSON. It was retained as a failure and not repaired.

Anchor-term matching checks only whether the model description includes terms
associated with the hidden SoccerNet action. It is a diagnostic, not a measure
of coaching quality. Both strategies usually returned the generic phase
`Attack` and failed to identify corners, direct free kicks, fouls, or
clearances explicitly.

## Why uniform was selected

1. It returned a complete structured response for every pilot clip.
2. Event-centred sampling produced no improvement in anchor-term recognition.
3. It was slightly faster on average.
4. It does not use a hidden event timestamp to decide which images the model
   sees, making it a cleaner baseline for general clip observation.

There is counterevidence: event-centred responses assigned identical problems
to both teams less often, suggesting that concentrating frames near the event
may sometimes improve specificity. This was not sufficient to outweigh its
schema failure and lack of event-recognition improvement, but it should be
mentioned in the report and revisited during paired human review.

## Interpretation

The main finding is not that uniform sampling works well. The finding is that
Qwen3-VL-2B struggled under both 16-frame conditions. It frequently produced
generic or internally inconsistent coaching statements while rating every
valid answer as high confidence.

The selected uniform strategy is therefore only the baseline for the next
stage. Human reviewers must still score factual accuracy, tactical correctness,
visual grounding, specificity, actionability, and evidence-advice consistency.
Tracking-derived analytics have not yet been used in this comparison.

## Artifacts

- Sampling inputs: `data/processed/pilot_inputs.json`
- Unedited runs: `data/processed/pilot_runs/{strategy}/{clip_id}.json`
- Machine comparison: `data/processed/pilot_comparison.json`
- Failed initial prompt smoke run:
  `data/processed/pilot_runs/smoke_failed/coach-eval-v0.1.0__uniform__SNGS-067.json`

The result files are project-generated and excluded from Git with the rest of
`data/processed`. They are not SoccerNet annotations.
