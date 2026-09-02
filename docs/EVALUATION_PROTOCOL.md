# Evaluation protocol v0.1.0 (draft)

Do not run the test split while this document is marked draft.

## Models

Compare exact Ollama tags `qwen3.5:27b` and `qwen3.5:35b` using the same remote
host class, inputs, prompt, JSON schema, context, and generation settings. Save
the model digest returned by Ollama. Do not include Qwen 2B.

## Input

Ollama accepts image inputs. It does not receive the original 25 fps sequence as
native video. Candidate conditions are 8 and 16 uniformly spaced chronological
frames. Frame selection must not use the hidden event time. A contact sheet, if
tested, is a separate condition.

Choose the sampling condition using train pilots and validation performance,
then freeze it. Never choose per clip or select whichever condition looks best
on test.

## Stage A: recognition gate

Score independently whether the response correctly identifies, when visible:

- team in possession;
- phase of play;
- direction/progression;
- the principal visible event;
- the cited player/team relationships;
- uncertainty caused by the broadcast view.

An answer that fails recognition cannot be evidence that the model understood
the clip, even when its advice sounds plausible.

## Stage B: coaching quality

Blind human reviewers to model identity and score:

- grounding in visible evidence;
- correctness and relevance of diagnosis;
- specificity of intervention;
- feasibility of practice design;
- clarity of success cues;
- calibration/uncertainty;
- absence of fabricated events or players.

Predefine scale anchors, aggregation, exclusions, missing-data rules, and the
success threshold before test. Report per-model paired results with uncertainty,
not only means.

## Required provenance

For each run save clip ID, split, frame indices and hashes, prompt/schema/config
hashes, exact model tag/digest, Ollama version, options, timestamps, duration,
raw HTTP response, raw model text, parse status, and any error. Never repair the
raw response in place.

