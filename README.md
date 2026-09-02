# Football MLLM Coach Evaluation

This clean restart evaluates whether Qwen3.5 multimodal models can infer what is
visibly happening in a 30-second football sequence and produce specific,
feasible coaching advice grounded in that sequence.

The project uses 120 access-controlled SoccerNet Game State Reconstruction v1.3
clips (40 train, 40 validation, 40 test). SoccerNet provides video frames and
tracking labels, not coaching advice. Clip-specific reference advice therefore
requires documented human review; online coaching resources are methodological
sources, not substitute labels.

## Current status

- Official train/valid/test ZIPs are restored under `data/raw` and Git-ignored.
- Project code, protocols, schemas, and remote Ollama configuration are fresh.
- Dataset membership must be generated deterministically from the raw ZIPs.
- Human coaching annotation has not yet been performed. Until it is complete,
  this is a dataset framework—not a finished coaching-ground-truth dataset.
- Exact prompts are human-readable text files under `input_prompts/`. Each model
  run writes its exact answer and readable provenance under `output/`.

## Setup

Install Python 3.11 or 3.12 and `uv`, then run:

```powershell
uv sync --extra dev
Copy-Item .env.example .env
uv run football-coach index
uv run football-coach select
uv run pytest
```

The default archive locations are:

```text
data/raw/gamestate/gamestate-2024/train.zip
data/raw/gamestate/gamestate-2024/valid.zip
data/raw/gamestate/gamestate-2024/test.zip
```

## Remote GPU and Ollama

Install Ollama on the GPU host, pull exact tags, and run the project on that host
or connect through an SSH tunnel:

```bash
ollama pull qwen3.5:27b
ollama pull qwen3.5:35b
ollama list
```

Set `OLLAMA_BASE_URL` in `.env`. Avoid exposing Ollama's unauthenticated local
API directly to the public internet. Confirm connectivity and installed model
metadata with:

```powershell
uv run football-coach ollama-check --model qwen3.5:27b
uv run football-coach ollama-check --model qwen3.5:35b
```

The official Ollama tags currently describe `qwen3.5:27b` as a 17 GB image-input
model and `qwen3.5:35b`/`35b-a3b` as a 24 GB image-input model. Actual VRAM
requirements include context/KV cache and runtime overhead; verify full GPU
offload on the remote host rather than inferring it from model-file size.

## Research workflow

1. Index the immutable SoccerNet ZIPs and verify v1.3, 750 frames, and 25 fps.
2. Freeze the 120-clip stratified membership.
3. Create full-sequence review MP4s for human annotators only.
4. Collect and validate clip-specific coaching references using the schema.
5. Pilot frame sampling on train, choose it on validation, then freeze it.
6. Run a recognition-only gate for both models.
7. Score coaching quality only alongside recognition correctness.
8. Run the sealed test once and report limitations and failures.

See `docs/DATASET_PROTOCOL.md`, `docs/ANNOTATION_PROTOCOL.md`, and
`docs/EVALUATION_PROTOCOL.md` before generating results.

## Provenance

- SoccerNet GSR official repository: https://github.com/SoccerNet/sn-gamestate
- Ollama vision API: https://docs.ollama.com/capabilities/vision
- Ollama chat API: https://docs.ollama.com/api/chat
- Qwen3.5 Ollama tags: https://ollama.com/library/qwen3.5/tags
