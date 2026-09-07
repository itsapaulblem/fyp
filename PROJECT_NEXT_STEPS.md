# Project Next Steps — Slow, Controlled Guide

## 1. What you are trying to find

Research question:

> Does providing a human-annotated analogous Dataset A case improve an MLLM's recognition and coaching advice for a new Dataset B sequence?

Measure two outcomes separately:

1. **Recognition:** Did the model correctly describe the visible possession, event order, phase, main event, and outcome?
2. **Coaching:** Was its advice relevant, specific, actionable, and supported by the B frames?

Also check hallucination, blind copying from A, unsupported transfer, retrieval relevance, and uncertainty. A fluent answer is not automatically correct.

Before comparing conditions, this is what B0–B5 mean:

| Condition | Input given to the model | What the test measures |
|---|---|---|
| **B0: frames only** | Dataset B frames with no Dataset A case | The unassisted baseline for recognition and coaching |
| **B1: random case** | The same B frames plus a seeded, label-independent random A case | Whether any extra case helps, distracts, or causes copying |
| **B2: hidden-label matched case** | The same B frames plus an A case selected using the hidden B action label | Whether knowing the event category would help select a useful case; this is a diagnostic test, not a usable automatic system |
| **B3: human-selected best-match case** | The same B frames plus the complete A case selected by the researcher as the strongest analogy | The best-case improvement when a person chooses the most similar case |
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

- SoccerNet Dataset B indexing;
- 25 approved Dataset A cases (`validate-a` reports 25/25);
- eight fixed train-pilot clips;
- human review of F10/F20/F30/F60 for those clips;
- all eight private train references finalized;
- prompt, output, rubric, retrieval, and freeze infrastructure;
- SSH/tunnel connectivity and text-only Qwen test.

Current state is `draft_train_only`. The next experiment is only the 32-cell B0 sampling pilot. Previous image failures occurred while other users occupied most GPU memory; preserve them as infrastructure failures.

Do **not** run B1–B5 or access test yet.

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

### Planned comparisons

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

## 3. While the GPU is busy

### Step 3.1 — Read literature slowly

Open [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md). Read S08 first, then S11, then S16.

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

**Stop here until the large external processes finish.**

---

## 4. When the GPU becomes free

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

### Step 4.3 — Test exactly one image

```powershell
$testImagePath = "C:\Projects\fypfinal\artifacts\model_inputs\dataset_b\B-TRAIN-0025\uniform_10_edge_672\01_frame_000001.jpg"
$testImage = [Convert]::ToBase64String([IO.File]::ReadAllBytes($testImagePath))
$testBody = @{
    model = "qwen3.5:27b"
    messages = @(@{
        role = "user"
        content = "Reply with exactly OK if you can process the attached image."
        images = @($testImage)
    })
    think = $false
    stream = $false
    options = @{ temperature = 0; num_ctx = 4096 }
} | ConvertTo-Json -Depth 6

try {
    $result = Invoke-RestMethod -Uri "http://127.0.0.1:11435/api/chat" -Method Post -ContentType "application/json" -Body $testBody
    $result.message.content
}
catch {
    $_.Exception.Message
    $_.ErrorDetails.Message
}
```

Expected: `OK`.

If HTTP 500 persists while the GPU is genuinely free, stop. Diagnose Ollama vision inference before any experiment run.

---

## 5. Run the sampling pilot

Only after the one-image test succeeds:

```powershell
cd C:\Projects\fypfinal
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11435"
uv run football-coach pilot-plan
uv run football-coach run-sampling-pilot --model qwen3.5:27b
```

Keep the tunnel open. Do not change prompts, frame counts, resolution, or generation settings during the matrix.

Expected final summary:

```text
pilot_cells=32
pilot_failures=0
```

If failures are nonzero, stop and inspect them. Do not hide or delete failures.

---

## 6. Analyse F10/F20/F30/F60

Compare each answer with its blind human reference. Record:

- recognition rubric dimensions;
- hallucinations and missed events;
- repetition/confusion;
- elapsed time;
- F60 capacity result.

Select the smallest count that reliably preserves needed temporal events without unacceptable failures or cost. Do not select based on answer length.

B-TRAIN-0040 is an important test: lower human-review counts suggested a save, while F60 revealed a goal.

Create the private decision:

```powershell
uv run football-coach init-sampling-decision
```

Fill `data/video_b/private/sampling_decision_v0.3.0.json` using real output paths, model tag/digest, F60 evidence, findings, latency, and rationale. Candidate status is `candidate_for_validation`.

**Stop and ask Codex to check the form before changing config status.**

---

## 7. Confirm sampling on four validation clips

Fixed clips:

```text
B-VALID-0049
B-VALID-0033
B-VALID-0038
B-VALID-0003
```

After candidate evidence is valid, status changes to `sampling_validation`. Intended B0 commands:

```powershell
uv run football-coach run-pair B-VALID-0049 --condition B0_frames_only --model qwen3.5:27b
uv run football-coach run-pair B-VALID-0033 --condition B0_frames_only --model qwen3.5:27b
uv run football-coach run-pair B-VALID-0038 --condition B0_frames_only --model qwen3.5:27b
uv run football-coach run-pair B-VALID-0003 --condition B0_frames_only --model qwen3.5:27b
```

### Blocker to correct first

The current B-reference finalizer requires visibility judgments for all four counts, but `sampling_validation` permits only the chosen count. Do not fabricate missing judgments. Correct and test this validation-reference workflow before running this section.

After genuine confirmation:

1. Add validation evidence paths to the decision.
2. Change its status to `approved`.
3. Run:

```powershell
uv run football-coach freeze-sampling
```

Do not enter `frozen_validation` until this succeeds.

---

## 8. Build the automatic Dataset A index

After the sampling freeze, set status to `frozen_validation`.

```powershell
uv sync --extra dev --extra retrieval --system-certs
uv run football-coach build-a-index --device cpu --batch-size 16
```

Expected file:

```text
data/embeddings/dataset_a_clip_v0.3.0.npz
```

It must contain exactly the 25 approved cases. B4 uses pinned CLIP pixel embeddings, mean pooling, cosine similarity, and `k=1`.

---

## 9. Prepare B3 human-selected best-match pairings

For each included validation clip, select the strongest A analogy using only frozen B frames and approved A cases. Do not use hidden labels, model answers, or B4 results.

Example only—A-0007 is not a real selection:

```powershell
uv run football-coach init-human-pair B-VALID-0049 A-0007 data/pairs/private/B-VALID-0049__A-0007.json
uv run football-coach validate-human-pair data/pairs/private/B-VALID-0049__A-0007.json B-VALID-0049 A-0007
```

Between commands, fill the form with rationale, transferable principles, important differences, reviewer/time, approval, and both leakage flags set false.

---

## 10. Run B0–B5 validation

Start only after the sampling freeze, sample size, two core comparisons, model plan, index, B3 pairs, and blinding plan are fixed.

For one clip:

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

---

## 11. Score outputs

Rubric: `config/scoring_rubric_v0.3.0.json`.

Score in order: recognition, retrieval relevance, coaching, failure modes, uncertainty.

```powershell
uv run football-coach init-score BLIND_RUN_ID CLIP_ID data/video_b/review/scores/BLIND_RUN_ID.json
uv run football-coach validate-score data/video_b/review/scores/BLIND_RUN_ID.json
```

Fill the form between commands. Recognition must be scored before condition/model/A context is revealed.

### Blocker to correct first

The repo creates score forms but does not create a randomized mapping from run folders to blind IDs. Because you are also the scorer, establish this process before main validation. Do not claim blinding unless it actually occurred.

Report each dimension separately; do not hide hallucination or copying in one total.

---

## 12. Select and freeze the final protocol

Use validation only to choose the model, analysis, clip plan, outcomes, B2 handling, and limitations. Preserve both B3–B0 and B4–B0 as the core comparisons.

```powershell
uv run football-coach init-protocol-decision
```

Fill `data/video_b/private/protocol_decision_v0.3.0.json` with real validation paths, selected model/digest, index path, eligibility/rubric notes, and outstanding issues.

After review:

```powershell
uv run football-coach freeze-protocol
```

Only after success may status become `frozen_test`.

---

## 13. Run test once and conclude

Use the Step 10 command patterns with only frozen test IDs/settings. A preserved crash counts as that cell's attempt. Do not change prompts, frames, encoder, `k`, Dataset A, rubric, or model after viewing test answers.

Compare paired scores for both core tests: B3–B0 and B4–B0. Then compare B3–B4 to see whether automatic case selection performs as well as selection by a person. Analyse B1, B2, and B5 as supporting controls and diagnostics.

Conclude with wording such as:

> Under the frozen sampled-frame protocol, retrieval-assisted prompting improved—or did not improve—the measured recognition and coaching dimensions relative to the frames-only baseline.

Do not claim the model independently understood the video better.

---

## Your next action only

1. Read S08 while waiting.
2. Occasionally check `nvidia-smi`.
3. When the GPU is free, start the tunnel.
4. Run the one-image diagnostic.
5. Stop and report whether it returned `OK`.

Do not run the 32-cell pilot until that diagnostic succeeds.
