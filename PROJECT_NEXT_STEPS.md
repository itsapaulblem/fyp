# Project Next Steps — Slow, Controlled Guide

## 1. What you are trying to find

Research question:

> Does providing a human-annotated similar Dataset A case improve an MLLM's recognition and coaching advice for a new Dataset B sequence?

Measure two outcomes separately:

1. **Recognition:** Did the model correctly describe the visible possession, event order, phase, main event, and outcome?
2. **Coaching:** Was its advice relevant, specific, actionable, and supported by the B frames?

Also check for hallucination, blind copying from A, etc. A fluent answer is not automatically correct.

Before comparing conditions, this is what B0–B5 mean:

| Condition | Input given to the model | What the test measures |
|---|---|---|
| **B0: frames only** | Dataset B frames with no Dataset A case | The unassisted baseline for recognition and coaching |
| **B1: random case from A** | The same B frames plus a seeded, label-independent random A case | Whether any extra case helps, distracts, or causes copying |
| **B2: hidden-label matched case from A** | The same B frames plus an A case selected using the hidden B action label | Whether knowing the event category would help select a useful case; this is a diagnostic test, not a usable automatic system |
| **B3: human-selected best-match case from A** | The same B frames plus the complete A case selected by the researcher as the strongest analogy | The best-case improvement when a person chooses the most similar case |
| **B4: embedding k-NN** | The same B frames plus the complete A case automatically selected from B pixels using CLIP embeddings and cosine nearest-neighbour retrieval | The improvement produced by the automatic retrieval-assisted system |
| **B5: advice only** | The same B frames plus only the advice from the exact A case retrieved in B4 | Whether B4's effect comes from advice text alone or from the complete analogous case |

All conditions use the same B frames, common task, model, generation settings, and plain-text answer format. Only the intended Dataset A assistance changes. Detailed input rules and limitations for each condition are recorded under **Experimental design** below.

The study will answer the research question through **both B3 versus B0 and B4 versus B0**:

- **B3 versus B0** tests whether adding a human-annotated case that a person selected as the most similar can improve the model.
- **B4 versus B0** tests whether the automatic pixel-only retriever can select a human-annotated case that improves the model.
- **B3 versus B4** shows whether automatic case selection performs as well as case selection by a person.

These comparisons answer related but different parts of the thesis and should be reported separately rather than merged into one score.

## 2. Current position

Already completed:

- SoccerNet Dataset B preparation (Train/Valid/Development from SoccerNet v1.3 Development Set);
- 25 approved Dataset A cases in total (`validate-a` reports 25/25);
- 14 Dataset A cases sourced from the [FIFA Training Centre Game Library](https://www.fifatrainingcentre.com/en/resources/game-library/), which contains match clips from FIFA international tournaments;
- 11 Dataset A cases sourced from [UEFA Champions League Performance Insights](https://www.uefa.com/uefachampionsleague/news/), with each case retaining its exact UEFA article URL;
- eight fixed train-pilot clips;
- human review of F10/F20/F30/F60 for those clips;
- all eight private train references finalized;
- prompt, output, rubric, retrieval, and freeze infrastructure;
- SSH tunnel connectivity and Ollama model checks;
- a successful one-image Qwen3.5 27B vision diagnostic in CPU-only mode;
- the active context window increased from 4,096 to 32,768 tokens;
- the Ollama client timeout increased from 900 to 7,200 seconds for slow CPU inference;
- a successful F60 technical capacity run for B-TRAIN-0025;
- all 32 complete, valid B0 sampling-pilot cells; and
- a verified randomized grading package containing 32 blind folders and 960
  hash-checked frame copies;
- all 32 human score forms completed and validated;
- the mapping revealed only after grading was complete; and
- dimension-by-dimension results aggregated for F10, F20, F30, and F60;
- four B0 F30 validation responses completed and scored;
- F30 frozen as the best tested operational trade-off, despite poor accuracy;
- the pixel-only CLIP index built and verified for all 25 Dataset A cases;
- four valid B3 human-selected pairing forms completed;
- all 20 evaluable validation cells completed for B0, B1, B3, B4, and B5
  across the four fixed validation clips;
- B2 recorded as not evaluable for these clips, without substitute cases;
- every comparison package graded before its private mapping was revealed;
- all 21 validation-related score forms validated, including the additional
  B-VALID-0049 B0 grading record; and
- a verified private post-unblinding master index and final validation report.

Current repository state remains `frozen_validation`, but validation execution,
grading, unblinding, and descriptive analysis are complete. The fixed settings are Qwen3.5 27B,
`num_gpu=0`, `num_ctx=32768`, F30 uniform endpoint sampling, maximum edge 672,
and a 7,200-second client timeout. F30 is frozen because it was the best tested
balance of descriptive recognition, hallucination severity, runtime, and room
for later Dataset A context. It is not evidence of accurate frames-only football
understanding: all four F30 validation responses missed the critical event.

Earlier failures have been preserved rather than treated as experimental results:

- image requests failed with HTTP 500 when GPU memory was heavily occupied;
- an F20 attempt under the original 4,096-token context was used as a context-capacity diagnostic; and
- the first 32,768-context F20 attempt reached the old 900-second client timeout, after which the timeout was increased and F20 completed successfully.

These are diagnosed infrastructure or capacity failures. They must not be included as model-quality scores. The completed CPU runs are pilot and validation evidence, not test results.

Do **not** rerun accepted validation cells or access the test split. The next
decision belongs to supervisor review: stop with the negative/inconclusive
validation finding, define a separate train/validation diagnostic, or authorize
one final frozen test protocol.

## Experimental design

### Core design

This is a **within-sequence controlled comparison**. The same Dataset B sequence is shown to the same model under several conditions. The B frames, common question, model, generation settings, and answer format stay fixed. Only the type of Dataset A assistance changes.

The independent variable is the **Dataset A information supplied to the model**. The measured outcomes are:

1. Dataset B recognition;
2. Dataset B coaching quality;
3. retrieval relevance;
4. hallucination, blind copying, and unsupported transfer; and
5. calibrated uncertainty.

Recognition is scored before coaching because plausible coaching language could conceal incorrect visual understanding.

### B0 — Frames-only baseline

**Input:** Frozen sampled frames from one B sequence and the common prompt. No A case.

**Question:** How well can the MLLM recognise and coach the sequence without case assistance?

**Purpose:** This is the control. Every claimed improvement is measured relative to B0 on the same B sequence.

**Limit:** It measures the sampled-frame protocol, not the complete native video.

### B1 — Random-case control

**Input:** The same B frames plus one complete approved A case chosen by a fixed seeded rule that does not use the hidden B label.

**Question:** Does merely supplying any worked football example help, or must it be relevant?

**Purpose:** Controls for extra context, images, coaching vocabulary, and prompt length. It can reveal distraction or copying from an irrelevant case.

**Rule:** The repository selects the case deterministically. The researcher must not replace it manually.

### B2 — Hidden-label matched-case diagnostic

**Input:** The same B frames plus an A case selected using the hidden SoccerNet action label and an explicit action-to-case-family mapping.

**Question:** If the event category were known, would a same-action case help?

**Purpose:** Diagnoses the potential value of coarse action matching. It is not a deployable system.

**Use of hidden information:** This condition deliberately uses an event label that a normal automatic system would not know. The label selects the case but is not sent to the model. Report B2 separately as a diagnostic test, not as automatic-system performance.

**Coverage:** The current mapping supports Corner and Direct free-kick. Other actions are not evaluable; never invent a substitute.

### B3 — Human-selected best-match case

**Input:** The same B frames plus the full approved A case selected by the researcher as the strongest analogy: A frames, human observation, tactical context, problem, and advice.

**Question:** How much could case assistance help when a knowledgeable human chooses the analogy?

**Purpose:** Estimates the best-case result when a person selects the most relevant analogy.

**Rule:** Select the pair before viewing the model answer and without the hidden B label. Record the rationale, transferable principles, and important differences.

**Limit:** B3 is not automatic retrieval and must not be reported as B4 system performance.

### B4 — Automatic embedding k-NN case

**Input:** The same B frames plus the complete A case returned as the rank-1 cosine nearest neighbour.

**Question:** Can automatic label-free visual retrieval choose a case that improves recognition or coaching?

**Purpose:** This is the end-to-end automatic retrieval-assisted system and the likely primary deployable comparison against B0.

**Retrieval rule:** The pinned CLIP image encoder processes only B pixels. Normalised frame embeddings are mean-pooled and normalised, then matched to the frozen A index by cosine similarity with `k=1`. B text, labels, tracking, coordinates, prior answers, and human B references are excluded.

**Interpretation:** Any improvement is retrieval-assisted performance, not independent video understanding.

### B5 — Advice-only control

**Input:** The same B frames plus only the advice text from the exact case retrieved by B4. A frames, observation, phase, action family, outcome, and problem are omitted.

**Question:** Is a B4 improvement mainly caused by advice language, or by the complete visual and tactical analogy?

**Purpose:** This is a mechanism control. B4 and B5 must use the same retrieved A case.

**Interpretation:** B4 outperforming B5 suggests the full case adds value beyond advice. Similar results suggest advice text may drive much of the effect. B5 below B0 suggests decontextualised advice may distract.

### Analysis comparisons

| Comparison | Meaning |
|---|---|
| B3 vs B0 | Core comparison 1: effect of a human-annotated analogy selected as most similar by a person |
| B4 vs B0 | Core comparison 2: effect of an automatically retrieved, human-annotated analogy |
| B4 vs B1 | Relevant automatic retrieval versus a random case |
| B3 vs B4 | Whether automatic selection performs as well as selection by a person |
| B4 vs B5 | Full retrieved case versus its advice only |
| B2 vs B0 | Hidden-label matching diagnostic on supported actions |

The two core comparisons are B3–B0 and B4–B0. Do not decide success from one overall score. Report recognition, coaching, retrieval, failure-mode, and uncertainty dimensions separately. Compare conditions clip by clip because they use the same B sequence.

### Short meeting explanation

> I first establish a frames-only baseline, B0. My first core comparison, B3 versus B0, tests whether a human-annotated analogy selected as the best match by a person can improve recognition and coaching. My second core comparison, B4 versus B0, tests whether an automatic pixel-only cosine retriever can produce an improvement using the same human-annotated case library. B3 versus B4 then shows whether automatic selection performs as well as selection by a person. B1, B2, and B5 test random context, hidden-label matching, and advice-only effects. I hold the B frames and generation settings fixed and score recognition before coaching, followed by retrieval relevance and failure modes.

---

## 3. Work that can continue while the GPU is busy

### Step 3.1 — Read literature slowly

The priority papers and their human reviews are already recorded in [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md).


For one paper:

1. Read the abstract.
2. State its research problem in one sentence.
3. Read introduction and conclusion.
4. Fill the reading-note template.
5. Record a page/table/figure for each claim.

Look for evidence about frame sampling, temporal understanding, relevant versus random examples, CLIP/cosine retrieval, football MLLMs, and hallucination evaluation.

### Step 3.2 — Check GPU availability

From Windows:

```powershell
ssh -J paulc@stujump.comp.nus.edu.sg paul@172.26.191.227
```

On the server:

```bash
nvidia-smi
ollama ps
```

The GPU remains busy if other compute processes occupy most memory or utilisation stays near 100%. To identify shown PIDs:

```bash
ps -o user,pid,etime,cmd -p PID1,PID2
```

Do not kill another user's work. Empty `ollama ps` does not mean the GPU is free; `nvidia-smi` shows all GPU processes.

The pilot can continue on CPU while this external GPU process runs. Do not try to share the remaining GPU memory with the 27B vision runner, because the one-image GPU requests already stopped with HTTP 500 under that condition.

---

## 4. Current CPU-only execution setup

### Step 4.1 — Start tunnel in PowerShell window 1

```powershell
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 127.0.0.1:11435:127.0.0.1:11434 -J paulc@stujump.comp.nus.edu.sg paul@172.26.191.227
```

Enter both passwords. A blank/stuck window means the tunnel is running. Keep it open.

### Step 4.2 — Check tunnel in PowerShell window 2

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:11435/api/tags" -Method Get
cd C:\Projects\fypfinal
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
uv run football-coach ollama-check --model qwen3.5:27b
```

### Step 4.3 - Confirm the active CPU settings

```powershell
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
$env:OLLAMA_TIMEOUT_SECONDS = "7200"
Select-String -Path "config\project_v0.3.0.json" -Pattern 'num_ctx','num_gpu'
```

Expected active values:

```text
num_ctx: 32768
num_gpu: 0
```

The one-image CPU diagnostic has already returned `OK`, so it does not need to be repeated before every cell. On the server, `ollama ps` should show `100% CPU` and context `32768` while a request is running.

Do not run `ollama stop qwen3.5:27b` while a pilot cell is running. It can terminate the active request.

### Step 4.4 - Later GPU use

All accepted pilot and validation inference was completed with the fixed CPU-only
settings. A later GPU run would be a backend change and must not be mixed into
these accepted results as though it were directly interchangeable. If GPU
inference is approved for a new diagnostic or final protocol, record and freeze
that change before running it.

---

## 5. Run the sampling pilot

The pilot matrix contains 8 training clips multiplied by 4 frame counts, for 32
cells. All 32 are complete and valid in the local repository.

First preview what the resumable runner will do:

```powershell
cd C:\Projects\fypfinal
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
$env:OLLAMA_TIMEOUT_SECONDS = "7200"
powershell.exe -ExecutionPolicy Bypass -File .\scripts\run_sampling_pilot_cpu.ps1 -DryRun
```

The dry run must report:

```text
Completed cells to skip: 32
Pending cells to run: 0
```

This completion check has passed. Do not rerun the pilot cells.

---

## 6. Analyse F10/F20/F30/F60

### Evidence collected so far

The completed B-TRAIN-0025 runs demonstrate that all four frame counts fit and finish with the current CPU settings:

| Count | Prompt tokens | Approximate total time | Status |
|---|---:|---:|---|
| F10 | 2,852 | 10.95 minutes | Complete, valid format |
| F20 | 5,392 | 17.14 minutes | Complete, valid format |
| F30 | 7,932 | 25.17 minutes | Complete, valid format |
| F60 | 15,552 | 60.35 minutes | Complete, valid format |

This passes the required F60 technical capacity check for one pilot clip. It does not by itself prove that F60 is the best sampling count.

The early answers also show why quality must be reviewed against the private human references. For B-TRAIN-0025, the model described a free kick and later a headed miss, while the human review identified a red-team corner, an attempted shot or deflection from a grey defender, and a clearance. More frames therefore did not automatically correct the event interpretation.

### Why the pilot stops at F60 rather than F100

Each Dataset B clip contains 750 frames over 30 seconds. Uniform sampling provides approximately:

| Count | Sampling density | Approximate time between sampled frames |
|---|---:|---:|
| F10 | 0.33 frames/second | 3.3 seconds |
| F20 | 0.67 frames/second | 1.6 seconds |
| F30 | 1 frame/second | 1 second |
| F60 | 2 frames/second | 0.5 seconds |
| F100 | 3.3 frames/second | 0.3 seconds |

F60 was chosen as the pilot's practical upper bound, not as a claim that 60 is universally optimal. The reasons are:

1. Human review showed that F60 revealed an important missed goal in B-TRAIN-0040, while most other pilot clips gained no additional event information beyond F20 or F30.
2. The real F60 run already used 15,552 prompt tokens and took about one hour on CPU.
3. At the observed token growth, F100 would use roughly 25,700 prompt tokens before the model answer and before adding Dataset A case material in B3 or B4. That leaves much less room within the 32,768-token context.
4. F100 would add many visually similar frames, substantially increase CPU runtime, and might add confusion without adding meaningful temporal evidence.
5. Adding F100 now would require preparing and human-reviewing another frame level and changing the planned pilot matrix.

F100 was not added because the completed pilot did not justify that expansion.
Any later higher-rate diagnostic must be declared as a separate protocol rather
than appended retroactively to this pilot.

All 32 answers were compared with their blind human references and validated.
The private result report is
`data/video_b/review/pilot_grading_v1/pilot_results.txt`.

The main unblinded results are:

| Measure | F10 | F20 | F30 | F60 |
|---|---:|---:|---:|---:|
| Critical events missed | 8/8 | 7/8 | 7/8 | 8/8 |
| Mean main-event score, max 2 | 0.125 | 0.125 | 0.250 | 0.125 |
| Mean outcome score, max 2 | 0.125 | 0.250 | 0.250 | 0.000 |
| Mean hallucination severity, lower is better | 2.750 | 2.750 | 2.625 | 2.875 |
| Mean runtime in minutes | 10.28 | 16.42 | 28.07 | 55.52 |

Visible-evidence scores were zero at every count. Coaching advice was generally
plausible but generic and was not supported by correct recognition. The model
therefore performed poorly at all frame counts, and these findings cannot support
a claim of reliable independent football-video understanding.

The completed review recorded:

- recognition rubric dimensions;
- hallucinations and missed events;
- repetition/confusion;
- elapsed time;
- F60 capacity result.

F30 was the validation candidate. It had the strongest descriptive recognition
profile and the lowest mean hallucination severity, while F60 approximately
doubled runtime without improving critical-event recognition. This is a pilot
finding, not proof of a statistically reliable gain.

The randomized package was created at
`data/video_b/review/pilot_grading_v1`. Its revealing mapping is stored separately
at `data/video_b/private/pilot_grading_mapping_v1.json`. The mapping was revealed
only after all 32 score forms passed validation.

B-TRAIN-0040 is an important test: lower human-review counts suggested a save, while F60 revealed a goal.

The private decision was completed and later approved after validation:

```powershell
uv run football-coach init-sampling-decision
```

The immutable sampling freeze now records F30 as the best tested operational
trade-off, not as an accurate frames-only setting.

---

## 7. Confirm sampling on four validation clips

Fixed clips:

```text
B-VALID-0049
B-VALID-0033
B-VALID-0038
B-VALID-0003
```

At this completed stage, the status changed to `sampling_validation`. The B0
command forms used were:

```powershell
uv run football-coach run-pair B-VALID-0049 --condition B0_frames_only --model qwen3.5:27b
uv run football-coach run-pair B-VALID-0033 --condition B0_frames_only --model qwen3.5:27b
uv run football-coach run-pair B-VALID-0038 --condition B0_frames_only --model qwen3.5:27b
uv run football-coach run-pair B-VALID-0003 --condition B0_frames_only --model qwen3.5:27b
```

### Validation-reference workflow

This blocker has been corrected and tested. Training-pilot references continue
to require F10/F20/F30/F60. During `sampling_validation`, a new validation
reference contains and requires only F30, the selected candidate. During later
frozen stages, a new reference requires only the frozen frame count. Do not add
or fabricate judgments for unobserved sampling levels.

This validation stage is complete. All four F30 responses had complete run
status and valid answer format, and all four blinded score forms passed
validation. Each response missed the critical event, confirming that the
sampling setting is operationally feasible but the B0 model quality is poor.
The decision was approved and frozen with:

```powershell
uv run football-coach freeze-sampling
```

The repository then entered `frozen_validation`.

---

## 8. Build the automatic Dataset A index

This step is complete under `frozen_validation`.

```powershell
uv sync --extra dev --extra retrieval --system-certs
uv run --system-certs --extra retrieval football-coach build-a-index --device cpu --batch-size 8
```

Expected file:

```text
data/embeddings/dataset_a_clip_v0.3.0.npz
```

The verified index contains exactly 25 approved cases, with one normalized
512-dimensional vector per case and 20 sampled frames per case. Its SHA-256 is
`933b1a773ec82943f8673409443db1192d7954326e7fdaf28b2bfbbd823d6e1a`.
B4 uses pinned CLIP pixel embeddings, mean pooling, cosine similarity, and `k=1`.

---

## 9. Prepare B3 human-selected best-match pairings

This step is complete for all four fixed validation clips. Each pairing was
selected using only frozen B frames and approved A cases, documented in a
private form, and validated before the corresponding B3 run. The selections
were not based on hidden labels, model answers, or B4 results.

The private forms retain rationale, transferable principles, important
differences, reviewer/time, approval, and leakage checks. Their identities were
revealed only after the corresponding comparison scores were completed.

---

## 10. Completed B0–B5 validation

Validation execution is complete. Each of the four fixed clips has accepted B0,
B1, B3, B4, and B5 runs, giving 20 evaluable condition-by-clip responses. B2 was
not evaluable for these clips under the frozen mapping and was excluded rather
than replaced. The final three-clip remote batch completed 12/12 pending cells
with zero failures.

The command forms below are retained only as reproducibility documentation. Do
not rerun accepted cells:

```powershell
uv run football-coach run-pair CLIP_ID --condition B0_frames_only --model MODEL_TAG
uv run football-coach run-pair CLIP_ID --condition B1_random_case --model MODEL_TAG
uv run football-coach run-pair CLIP_ID --condition B2_action_oracle --model MODEL_TAG
uv run football-coach run-pair CLIP_ID --condition B3_human_oracle --model MODEL_TAG --case-a-id CASE_ID --pairing-judgement-path PAIR_FILE
uv run football-coach run-pair CLIP_ID --condition B4_embedding_knn --model MODEL_TAG --embedding-device cpu
uv run football-coach run-pair CLIP_ID --condition B5_advice_only --model MODEL_TAG --embedding-device cpu
```

Rules:

- B1 selects its own seeded random case; omit `--case-a-id`.
- B2 deliberately uses the hidden action mapping. Unsupported labels are not evaluable; never substitute.
- B3 needs a real documented human pair.
- B4 automatically uses rank-1 retrieval.
- B5 automatically uses only advice from that same B4 case.
- Never manually choose B4/B5.

Replace all uppercase placeholders with real frozen values.

### Completed four-clip validation result

All packages were graded before their private mappings were opened. The
post-unblinding master index is:

`data/video_b/private/frozen_validation_post_unblinding_v1/MASTER_INDEX.txt`

The full tables and written findings are:

`data/video_b/private/frozen_validation_post_unblinding_v1/VALIDATION_COMPARISON_REPORT.txt`

Condition means across four clips were:

| Condition | Temporal | Main event | Outcome | Advice quality | Hallucination severity | Critical misses |
|---|---:|---:|---:|---:|---:|---:|
| B0 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 4/4 |
| B1 | 0.00 | 0.25 | 0.25 | 0.25 | 2.50 | 4/4 |
| B3 | 0.25 | 0.25 | 0.50 | 0.50 | 2.75 | 4/4 |
| B4 | 0.25 | 0.25 | 0.50 | 0.50 | 2.75 | 4/4 |
| B5 | 0.00 | 0.00 | 0.00 | 0.00 | 3.00 | 4/4 |

Lower hallucination severity is better; higher values are better for the other
scored dimensions. These columns are not combined into one overall mark.

B3 and B4 produced identical aggregate recognition and coaching scores. Their
small gains over B0 were concentrated mainly in B-VALID-0038, while B1 also
improved on that clip. Human-selected B3 cases had mean analogy relevance 1.00,
compared with 0.50 for B4, but the relevance difference did not produce better
downstream scores. B5 advice-only did not improve over B0. Every condition
missed the critical event in all four clips, and temporal hallucination occurred
for every condition on every clip.

The validation evidence therefore does not establish a reliable benefit from
case assistance. It supports a negative or inconclusive validation finding, not
a claim that retrieval improved independent video understanding.

One completed reviewer note used the phrase `B5-type response` for the B3 item.
The private mapping proves the run was B3. Preserve the original score form and
treat that phrase only as a wording slip in the note, not as a condition change.

The post-unblinding consistency check also found that 14 case-assisted forms
still contained B0-only `N/A` placeholders for analogy relevance, blind
copying, and unsupported transfer. Those dimensions are intentionally assessed
after case reveal. The reviewer completed only those missing case-dependent
judgements and reasons; recognition and all previously completed scores were
left unchanged. All 21 validation-related forms then passed both normal
validation and the mapping-aware consistency check.

---

## 11. Score outputs

Rubric: `config/scoring_rubric.txt` (the single authoritative rubric, version 1.0).

Score in order: recognition, retrieval relevance, coaching, failure modes, uncertainty.

This step is complete for the sampling pilot and frozen validation evidence. The
commands below are retained for reproducibility or a separately approved future
protocol:

```powershell
uv run football-coach init-score BLIND_RUN_ID CLIP_ID data/video_b/review/scores/BLIND_RUN_ID.txt
uv run football-coach validate-score data/video_b/review/scores/BLIND_RUN_ID.txt
```

Fill the form between commands. Recognition must be scored before condition/model/A context is revealed.

For B0, use `N/A` for analogy relevance, blind copying, and unsupported transfer,
and explain that B0 supplied no Dataset A material. For B1 to B5, those three
fields require numeric scores. Every other scoring dimension requires a numeric
score and a written reason.

For the sampling pilot, `prepare-pilot-grading` has already created the forms,
recognition-only views, full responses, human visual references, and generic frame
copies in randomized `PILOT-001` to `PILOT-032` folders. Follow
`GRADING_INSTRUCTIONS.txt` inside that package. Do not rerun the preparation
command because it intentionally refuses to overwrite the grading package.

For any separately approved future same-clip comparison, use the reusable
blinded packager:

```powershell
uv run football-coach prepare-comparison-grading PACKAGE_ID CLIP_ID RUN_PATH_1 RUN_PATH_2 RUN_PATH_3
```

It checks complete and valid source runs, a shared exact model digest, frozen
F30 inputs, identical B frame hashes, and unique conditions. It randomizes the
runs into equal `COMPARE-*` folders and writes the revealing mapping separately
under private data. Do not inspect that mapping until every score validates.

Report each dimension separately; do not hide hallucination or copying in one total.

---

## 12. Select and freeze the final protocol

The validation report is complete, but a final test protocol is not yet
authorized. Review the negative/inconclusive result with the supervisor before
creating or completing this decision. Preserve both B3–B0 and B4–B0 as the core
comparisons if a test run is approved.

```powershell
uv run football-coach init-protocol-decision
```

Fill `data/video_b/private/protocol_decision_v0.3.0.json` with real validation paths, selected model/digest, index path, eligibility/rubric notes, and outstanding issues.

After review:

```powershell
uv run football-coach freeze-protocol
```

Only after a real supervisor-informed decision and successful freeze may status
become `frozen_test`. Do not use the command merely to advance the project
despite poor validation.

---

## 13. Run test once and conclude

This step is conditional and has not started. If it is explicitly authorized,
use the Step 10 command patterns with only frozen test IDs/settings. A preserved
crash counts as that cell's attempt. Do not change prompts, frames, encoder,
`k`, Dataset A, rubric, or model after viewing test answers.

Compare paired scores for both core tests: B3–B0 and B4–B0. Then compare B3–B4 to see whether automatic case selection performs as well as selection by a person. Analyse B1, B2, and B5 as supporting controls and diagnostics.

Conclude with wording such as:

> Under the frozen sampled-frame protocol, retrieval-assisted prompting improved—or did not improve—the measured recognition and coaching dimensions relative to the frames-only baseline.

Do not claim the model independently understood the video better.

---

## Your next action only

1. Read the private validation report and prepare its short supervisor summary.
2. Show that B3 and B4 had only small, clip-specific descriptive gains, B1 also
   improved on the same clip, and every condition missed all four critical
   events.
3. Ask the supervisor to choose among:
   - stopping the current protocol at validation and reporting the
     negative/inconclusive finding;
   - approving a separate train/validation diagnostic using simple observable
     pass or kick counts and a newly declared sampling-rate protocol; or
   - authorizing a final protocol freeze and one untouched test run.
4. Record the decision before changing configuration or running new inference.

Do not rerun completed validation cells, do not silently alter completed score
forms, and do not access the test split without the explicit decision and freeze.
