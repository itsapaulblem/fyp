# Project Next Steps — v0.4 Evidence-First Prompting

## 1. Current position

Protocol v0.3 is complete at validation and preserved by the Git tag
`v0.3-validation-complete`. Its four-clip result is negative or inconclusive:
every evaluated condition missed every critical event, while the small B3 and
B4 gains were concentrated mainly in one clip. The random-case control also
improved on that clip, so the evidence does not establish that analogous-case
relevance caused the gains.

Do not modify, rerun, or reinterpret accepted v0.3 cells. The Dataset B test
split remains untouched and is not authorized for the new work.

Following supervisor review, the next phase is a separate diagnostic:

> Test whether an evidence-first, step-by-step prompting chain improves
> football-event recognition and evidence-supported coaching compared with the
> existing single-prompt approach.

Fine-tuning is a later decision gate, not the first step.

## 2. Protocol separation

The new work is protocol v0.4. It must not be mixed retroactively with B0–B5.

- Keep all v0.3 configuration, prompts, outputs, scores, hashes, and reports
  unchanged.
- Develop and tune v0.4 using Dataset B train only.
- Select and freeze a train holdout before using it for comparison.
- Use validation only after the prompt chain and model comparison are frozen.
- Do not access test without a new supervisor-approved protocol freeze.
- Describe performance as sampled-frame analysis, not native video
  understanding.

## 3. New experimental questions

**Prompting:** Does a staged evidence-first pipeline improve temporal sequence,
main-event, outcome, visible-evidence, and coaching scores relative to the
existing single prompt when the model and frames are held constant?

**Model:** Does the prompting effect differ between pretrained Qwen3.5 27B and
Qwen3.5 35B?

**Fine-tuning — conditional:** If a repeatable intermediate failure is
identified, does parameter-efficient fine-tuning on human-authored B-train
intermediate targets improve final coaching relative to the same pretrained
model and frozen prompt chain?

## 4. Planned prompting conditions

| ID | Method | Purpose |
|---|---|---|
| P0 | Existing single prompt | Pretrained prompting baseline |
| P1 | Two-turn chain | Turn 1 recognition and sequence; Turn 2 coaching |
| P2 | Five-stage verified chain | Later refinement if P1 remains unreliable |

P1 is the direct implementation of the supervisor request. P2 may later generate
at most three candidate interpretations; it is not active yet.

Across paired comparisons, preserve the same ordered frames, resolution, model
tag and digest, decoding settings, human reference, rubric, and output contract.
Record extra calls, runtime, context use, failures, and API cost.

## 5. Active P1 two-turn chain

### Turn 1 — Recognition before coaching

Using the same 30 ordered frames, extract visible evidence, construct the
chronology, identify the main event and immediate outcome, and state limitations.
Material claims must cite supporting frame numbers or ranges. No coaching is
allowed in this turn.

### Turn 2 — Coaching

Continue the same conversation using the exact Turn 1 response. Interpret the
tactical phase and provide at most one evidence-supported priority problem,
coach message, and representative practice. If Turn 1 is uncertain or
unsupported, advice must remain conditional.

There is no human correction inside an accepted P1 run. Prompt revision is
allowed only between development runs, with every failed output preserved.

## 6. Deferred P2 refinement

If P1 remains unreliable, P2 will separate visible evidence, chronology, event
hypotheses, tactical interpretation, and coaching into five stages. Its prompts
must be declared only after P1 failures justify the added complexity.

## 7. Data plan

Use the existing eight B-train pilot clips for prompt development because their
references and diagnosed failures already exist. Do not present them as unseen
evaluation data.

Before comparative evaluation:

1. Define a deterministic, label-blind rule for selecting new clips from the
   remaining B-train set.
2. Freeze selected IDs before viewing their model answers.
3. Finalize pixel-only human references before attaching or inspecting hidden
   SoccerNet labels.
4. Keep prompt-development clips separate from the internal train holdout.
5. Evaluate P0, P1, and, if justified, P2 once on the frozen train holdout.

The holdout size and selection rule remain to be decided before inference.

## 8. Model plan

Local Ollama inventory:

- `qwen3.5:27b` — pretrained baseline;
- `qwen3.5:35b` — stronger local comparison candidate;
- `qwen3-vl:2b-instruct` — retired and excluded.

Before comparing quality, record the Ollama version, model tag, full digest,
quantization, GPU, VRAM, offload state, context window, and runtime settings.
Run capacity diagnostics on development clips only.

A hosted frontier model such as Claude may later be an upper-bound comparison
using the same sampled JPEGs. External API use requires permission to transmit
frames, an exact model identifier, cost tracking, and raw response preservation.
The remote GPU does not run Claude inference.

## 9. Fine-tuning decision gate

Do not fine-tune until prompt-only diagnostics identify a stable failure that
training is intended to correct.

If fine-tuning is justified:

- train only on human-authored B-train pixel observations and targets;
- do not use validation or test examples for training;
- do not use hidden SoccerNet labels as ordinary input or coaching ground truth;
- preserve annotation and reviewer provenance;
- compare pretrained and fine-tuned models with the same frozen prompt chain;
- test parameter-efficient tuning before full-model training.

Dataset A's 25 cases remain the v0.3 coaching library. They are not sufficient
by themselves for a video-language fine-tuning dataset.

## 10. Workspace layout

```text
input_prompts/v0.4/       staged prompt templates
templates/v0.4/           human-readable intermediate/output forms
output/v0.4/diagnostics/  capacity and transport checks
output/v0.4/prompt_chain/ accepted P0/P1/P2 runs
output/v0.4/model_comparison/ cross-model runs
```

Generated outputs remain Git-ignored. Folder creation does not freeze a prompt
or configuration.

## 11. Execution gates

1. **Design:** agree the intermediate information and scoring contract.
2. **Prompt development:** use only known B-train development material.
3. **Prompt freeze:** hash prompts, schemas, frame settings, and generation
   settings.
4. **Train holdout:** perform the paired P0/P1/P2 comparison once.
5. **Model comparison:** compare 27B and 35B under frozen prompting methods.
6. **Fine-tuning decision:** proceed only with a diagnosed target and adequate
   human-authored data.
7. **Validation decision:** proceed only if train evidence warrants it.
8. **Test decision:** keep test sealed without a later approved full freeze.

## 12. Immediate next action only

Review the draft P1 prompts and rubric, then validate the local environment with:

```powershell
uv run football-coach validate-prompt-chain
uv run football-coach ollama-check --model qwen3.5:27b
```

After review, run only the declared initial B-train diagnostic clip. Do not
select a holdout, access validation/test, activate P2, or fine-tune yet.
