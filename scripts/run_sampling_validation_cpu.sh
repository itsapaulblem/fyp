#!/usr/bin/env bash

set -uo pipefail

project_root="${1:-/home/paul/fypfinal_remote_20260909}"
model_tag="qwen3.5:27b"
ollama_base_url="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
timeout_seconds="${OLLAMA_TIMEOUT_SECONDS:-7200}"
clips=(B-VALID-0033 B-VALID-0038 B-VALID-0003)

cd "$project_root" || {
  echo "Project directory does not exist: $project_root" >&2
  exit 1
}

required_paths=(
  config/project_v0.3.0.json
  data/raw/gamestate/gamestate-2024/valid.zip
  data/video_b/private/soccernet_gsr_v1.3_reference.csv
  data/video_b/private/sampling_decision_v0.3.0.json
)
for required_path in "${required_paths[@]}"; do
  if [[ ! -f "$required_path" ]]; then
    echo "Required file is missing: $project_root/$required_path" >&2
    exit 1
  fi
done

readarray -t protocol_values < <(
  uv run python - <<'PY'
import json
from pathlib import Path

config = json.loads(Path("config/project_v0.3.0.json").read_text(encoding="utf-8"))
decision = json.loads(
    Path("data/video_b/private/sampling_decision_v0.3.0.json").read_text(encoding="utf-8")
)
print(config["status"])
print(config["input_feasibility"]["selected_frame_count"])
print(decision["status"])
print(decision["selected_frame_count"])
PY
)
if [[ "${protocol_values[0]:-}" != "sampling_validation" ]]; then
  echo "Config must have status sampling_validation" >&2
  exit 1
fi
if [[ "${protocol_values[1]:-}" != "30" ]]; then
  echo "Config must select F30" >&2
  exit 1
fi
if [[ "${protocol_values[2]:-}" != "candidate_for_validation" ]]; then
  echo "Sampling decision must have status candidate_for_validation" >&2
  exit 1
fi
if [[ "${protocol_values[3]:-}" != "30" ]]; then
  echo "Sampling decision must select F30" >&2
  exit 1
fi

lock_directory="output/.sampling_validation_cpu.lock"
mkdir -p output
if ! mkdir "$lock_directory" 2>/dev/null; then
  echo "Another validation batch may already be running: $lock_directory" >&2
  exit 1
fi
trap 'rmdir "$lock_directory" 2>/dev/null || true' EXIT

mkdir -p output/batch_logs
batch_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
batch_log="output/batch_logs/sampling_validation_cpu_${batch_timestamp}.log"
exec > >(tee -a "$batch_log") 2>&1

export OLLAMA_BASE_URL="$ollama_base_url"
export OLLAMA_TIMEOUT_SECONDS="$timeout_seconds"

config_sha256="$(sha256sum config/project_v0.3.0.json | awk '{print $1}')"

cell_complete() {
  local clip_id="$1"
  uv run python - "$clip_id" "$config_sha256" <<'PY'
import json
import sys
from pathlib import Path

clip_id, expected_config_hash = sys.argv[1:]
root = Path("output/B0_frames_only/qwen3.5_27b") / clip_id
for metadata_path in sorted(root.glob("*/metadata.txt")):
    metadata = {}
    try:
        for raw_line in metadata_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            key, raw_value = raw_line.split(":", 1)
            metadata[key.strip()] = json.loads(raw_value.strip())
    except (OSError, ValueError, json.JSONDecodeError):
        continue
    if (
        metadata.get("condition") == "B0_frames_only"
        and metadata.get("dataset_b_clip_id") == clip_id
        and metadata.get("dataset_b_frame_count") == 30
        and metadata.get("maximum_edge") == 672
        and metadata.get("model") == "qwen3.5:27b"
        and metadata.get("config_sha256") == expected_config_hash
        and metadata.get("run_status") == "complete"
        and metadata.get("answer_format_status") == "valid"
        and (metadata_path.parent / "response.txt").stat().st_size > 0
    ):
        raise SystemExit(0)
raise SystemExit(1)
PY
}

echo "Sampling validation batch"
echo "Project: $project_root"
echo "Model: $model_tag"
echo "Clips: ${clips[*]}"
echo "Generation: F30, edge=672, num_ctx=32768, num_gpu=0"
echo "Config SHA-256: $config_sha256"
echo "Batch log: $project_root/$batch_log"

uv run football-coach ollama-check --model "$model_tag" || {
  echo "Ollama model check failed; no validation request was sent" >&2
  exit 1
}

completed=0
for clip_id in "${clips[@]}"; do
  if cell_complete "$clip_id"; then
    echo "SKIP $clip_id: matching complete valid F30 run already exists"
    completed=$((completed + 1))
    continue
  fi

  echo
  echo "START $clip_id at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if ! uv run football-coach run-pair \
    "$clip_id" \
    --condition B0_frames_only \
    --model "$model_tag"; then
    echo "FAILED $clip_id: run-pair returned a non-zero status" >&2
    echo "The batch stopped. Diagnose the preserved failure before resuming." >&2
    exit 1
  fi
  if ! cell_complete "$clip_id"; then
    echo "FAILED $clip_id: no matching complete valid run was preserved" >&2
    echo "The batch stopped. Inspect the newest run before resuming." >&2
    exit 1
  fi
  completed=$((completed + 1))
  echo "DONE $clip_id at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
done

echo
echo "Validation cells complete: $completed/${#clips[@]}"
echo "B-VALID-0049 was intentionally excluded from this remote batch."
echo "Batch log: $project_root/$batch_log"
