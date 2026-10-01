#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_TIMEOUT_SECONDS="${OLLAMA_TIMEOUT_SECONDS:-7200}"
export PYTHONUNBUFFERED=1

uv run --frozen --system-certs python -m football_coach.remote_p1_revisions \
  --manifest artifacts/transfer/p1_remote_revisions_v1_manifest.json --validate-only
uv run --frozen --system-certs python -m football_coach.remote_p1_revisions \
  --manifest artifacts/transfer/p1_remote_revisions_v1_manifest.json
