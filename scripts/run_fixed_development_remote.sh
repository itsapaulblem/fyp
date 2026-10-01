#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

# The batch declaration selects num_gpu=0 because this is a shared GPU host.
# Use the Ollama service on this workstation, not a laptop SSH tunnel.
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_TIMEOUT_SECONDS="${OLLAMA_TIMEOUT_SECONDS:-3600}"
export PYTHONUNBUFFERED=1

uv run --frozen --system-certs football-coach validate-fixed-development
uv run --frozen --system-certs football-coach run-fixed-development
