#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_TIMEOUT_SECONDS="${OLLAMA_TIMEOUT_SECONDS:-7200}"
export PYTHONUNBUFFERED=1

uv run --frozen --system-certs python -m football_coach.remote_p1_followup \
  --manifest artifacts/transfer/p1_followup_v2_manifest.json --validate-only
uv run --frozen --system-certs python -m football_coach.remote_p1_followup \
  --manifest artifacts/transfer/p1_followup_v2_manifest.json

if [[ -e /home/paul/p1_followup_v2_results.tar.gz ]]; then
  echo 'Result archive already exists; refusing overwrite' >&2
  exit 1
fi
tar -czf /home/paul/p1_followup_v2_results.tar.gz \
  output/v0.4/prompt_chain/P1_human_guided/portable_followup_v2/qwen3.5_27b/B-TRAIN-0040 \
  output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0051/20260930T111146551522Z \
  output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/B-TRAIN-0054/20260930T083320329816Z
sha256sum /home/paul/p1_followup_v2_results.tar.gz
