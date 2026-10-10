#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_TIMEOUT_SECONDS="${OLLAMA_TIMEOUT_SECONDS:-7200}"
export PYTHONUNBUFFERED=1

uv run --frozen --system-certs python -m football_coach.remote_p1_exploratory_coaching \
  --manifest artifacts/transfer/p1_0054_exploratory_coaching_v1_manifest.json --validate-only
uv run --frozen --system-certs python -m football_coach.remote_p1_exploratory_coaching \
  --manifest artifacts/transfer/p1_0054_exploratory_coaching_v1_manifest.json

if [[ -e /home/paul/p1_0054_exploratory_coaching_v1_results.tar.gz ]]; then
  echo 'Result archive already exists; refusing overwrite' >&2
  exit 1
fi
tar -czf /home/paul/p1_0054_exploratory_coaching_v1_results.tar.gz \
  output/v0.4/prompt_chain/P1_human_guided/exploratory_unapproved_recognition_v1/qwen3.5_27b/B-TRAIN-0054
sha256sum /home/paul/p1_0054_exploratory_coaching_v1_results.tar.gz
