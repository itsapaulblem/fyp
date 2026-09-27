#!/usr/bin/env bash

# Resumable unattended B0-B5 validation runner for the three remaining clips.
# B0 is skipped when a matching complete run exists. B2 is skipped when the
# frozen hidden-label mapping marks the clip not evaluable. All model requests
# are sequential so this script can run safely inside one tmux session.

set -uo pipefail
umask 077

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$script_directory/.." && pwd)"
dry_run=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      dry_run=true
      shift
      ;;
    --project-root)
      if [[ $# -lt 2 ]]; then
        echo "--project-root requires a path" >&2
        exit 2
      fi
      project_root="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: $0 [--dry-run] [--project-root PATH]" >&2
      exit 2
      ;;
  esac
done

model_tag="qwen3.5:27b"
model_directory="qwen3.5_27b"
ollama_base_url="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
timeout_seconds="${OLLAMA_TIMEOUT_SECONDS:-7200}"
clips=(B-VALID-0033 B-VALID-0038 B-VALID-0003)
conditions=(
  B0_frames_only
  B1_random_case
  B2_action_oracle
  B3_human_oracle
  B4_embedding_knn
  B5_advice_only
)

declare -A b3_case=(
  [B-VALID-0033]="A-0017"
  [B-VALID-0038]="A-0012"
  [B-VALID-0003]="A-0007"
)

cd "$project_root" || {
  echo "Project directory does not exist: $project_root" >&2
  exit 1
}

required_files=(
  config/project_v0.3.0.json
  config/freezes/sampling_v0.3.0.json
  data/raw/gamestate/gamestate-2024/valid.zip
  data/video_b/private/soccernet_gsr_v1.3_reference.csv
  data/video_b/private/sampling_decision_v0.3.0.json
  data/embeddings/dataset_a_clip_v0.3.0.npz
  data/pairs/private/B-VALID-0033__A-0017.json
  data/pairs/private/B-VALID-0038__A-0012.json
  data/pairs/private/B-VALID-0003__A-0007.json
)
for required_file in "${required_files[@]}"; do
  if [[ ! -f "$required_file" ]]; then
    echo "Required file is missing: $project_root/$required_file" >&2
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
print(config["input_feasibility"]["maximum_edge"])
print(config["generation"]["num_ctx"])
print(config["generation"]["num_gpu"])
print(decision["status"])
print(decision["model_digest"])
PY
)

if [[ "${protocol_values[0]:-}" != "frozen_validation" ]]; then
  echo "Config must have status frozen_validation" >&2
  exit 1
fi
if [[ "${protocol_values[1]:-}" != "30" || "${protocol_values[2]:-}" != "672" ]]; then
  echo "Frozen validation must use F30 and maximum edge 672" >&2
  exit 1
fi
if [[ "${protocol_values[3]:-}" != "32768" || "${protocol_values[4]:-}" != "0" ]]; then
  echo "Frozen generation must use num_ctx=32768 and num_gpu=0" >&2
  exit 1
fi
if [[ "${protocol_values[5]:-}" != "approved" ]]; then
  echo "Sampling decision must be approved" >&2
  exit 1
fi
model_digest="${protocol_values[6]:-}"
if [[ ! "$model_digest" =~ ^[0-9a-f]{64}$ ]]; then
  echo "Sampling decision lacks a valid model digest" >&2
  exit 1
fi

if ! uv run python - <<'PY'
import json
from pathlib import Path

from football_coach.experiment import validate_sampling_freeze

root = Path.cwd()
config = json.loads((root / "config/project_v0.3.0.json").read_text(encoding="utf-8"))
validate_sampling_freeze(config, root)
PY
then
  echo "Frozen sampling evidence is missing or has changed" >&2
  exit 1
fi

# Every approved A case may be selected by B1 or B4, so all source videos and
# advice files must be present before an unattended batch starts.
if ! uv run football-coach validate-a >/dev/null; then
  echo "Dataset A validation failed" >&2
  exit 1
fi

config_sha256="$(sha256sum config/project_v0.3.0.json | awk '{print $1}')"
index_sha256="$(sha256sum data/embeddings/dataset_a_clip_v0.3.0.npz | awk '{print $1}')"
expected_index_sha256="933b1a773ec82943f8673409443db1192d7954326e7fdaf28b2bfbbd823d6e1a"
if [[ "$index_sha256" != "$expected_index_sha256" ]]; then
  echo "Retrieval index hash does not match the verified frozen index" >&2
  exit 1
fi

for clip_id in "${clips[@]}"; do
  pair_path="data/pairs/private/${clip_id}__${b3_case[$clip_id]}.json"
  if ! uv run football-coach validate-human-pair \
    "$pair_path" "$clip_id" "${b3_case[$clip_id]}" >/dev/null; then
    echo "B3 pairing validation failed: $pair_path" >&2
    exit 1
  fi
done

cell_complete() {
  local clip_id="$1"
  local condition="$2"
  local expected_case="${3:-}"
  uv run python - \
    "$clip_id" "$condition" "$expected_case" "$config_sha256" "$model_digest" \
    "$model_directory" <<'PY'
import json
import sys
from pathlib import Path

clip_id, condition, expected_case, config_hash, model_digest, model_directory = sys.argv[1:]
root = Path("output") / condition / model_directory / clip_id
for metadata_path in sorted(root.glob("*/metadata.txt"), reverse=True):
    metadata = {}
    try:
        for raw_line in metadata_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip() or ":" not in raw_line:
                continue
            key, raw_value = raw_line.split(":", 1)
            metadata[key.strip()] = json.loads(raw_value.strip())
    except (OSError, ValueError, json.JSONDecodeError):
        continue
    response_path = metadata_path.parent / "response.txt"
    valid = (
        metadata.get("condition") == condition
        and metadata.get("dataset_b_clip_id") == clip_id
        and metadata.get("dataset_b_frame_count") == 30
        and metadata.get("maximum_edge") == 672
        and metadata.get("model") == "qwen3.5:27b"
        and metadata.get("model_digest") == model_digest
        and metadata.get("run_status") == "complete"
        and metadata.get("answer_format_status") == "valid"
        and response_path.is_file()
        and response_path.stat().st_size > 0
    )
    # B0 was generated during sampling_validation, before the status-only config
    # transition. Later conditions must match the current frozen config exactly.
    if condition != "B0_frames_only":
        valid = valid and metadata.get("config_sha256") == config_hash
    if expected_case:
        valid = valid and metadata.get("dataset_a_case_id") == expected_case
    if valid:
        raise SystemExit(0)
raise SystemExit(1)
PY
}

b2_supported() {
  local clip_id="$1"
  uv run python - "$clip_id" <<'PY'
import csv
import json
import sys
from pathlib import Path

clip_id = sys.argv[1]
config = json.loads(Path("config/project_v0.3.0.json").read_text(encoding="utf-8"))
with Path("data/video_b/private/soccernet_gsr_v1.3_reference.csv").open(
    encoding="utf-8", newline=""
) as handle:
    row = next((item for item in csv.DictReader(handle) if item["clip_id"] == clip_id), None)
if row is None:
    raise SystemExit(2)
mapping = config["action_oracle"]["label_to_case_family"]
raise SystemExit(0 if mapping.get(row["action_class"]) is not None else 1)
PY
}

command_for_cell() {
  local clip_id="$1"
  local condition="$2"
  cell_command=(uv run football-coach run-pair "$clip_id" --condition "$condition" --model "$model_tag")
  case "$condition" in
    B3_human_oracle)
      cell_command+=(
        --case-a-id "${b3_case[$clip_id]}"
        --pairing-judgement-path "data/pairs/private/${clip_id}__${b3_case[$clip_id]}.json"
      )
      ;;
    B4_embedding_knn|B5_advice_only)
      cell_command=(uv run --extra retrieval football-coach run-pair
        "$clip_id" --condition "$condition" --model "$model_tag"
        --embedding-device cpu --embedding-batch-size 8)
      ;;
  esac
}

echo "Frozen validation matrix"
echo "Project: $project_root"
echo "Model: $model_tag"
echo "Model digest: $model_digest"
echo "Clips: ${clips[*]}"
echo "Conditions: ${conditions[*]}"
echo "Generation: F30, edge=672, num_ctx=32768, num_gpu=0"
echo "Config SHA-256: $config_sha256"
echo "Index SHA-256: $index_sha256"

pending=0
skipped_complete=0
skipped_not_evaluable=0
for clip_id in "${clips[@]}"; do
  for condition in "${conditions[@]}"; do
    expected_case=""
    if [[ "$condition" == "B3_human_oracle" ]]; then
      expected_case="${b3_case[$clip_id]}"
    fi
    if cell_complete "$clip_id" "$condition" "$expected_case"; then
      echo "SKIP $clip_id $condition: matching complete valid run exists"
      skipped_complete=$((skipped_complete + 1))
    elif [[ "$condition" == "B2_action_oracle" ]] && ! b2_supported "$clip_id"; then
      echo "SKIP $clip_id $condition: frozen mapping marks this clip not evaluable"
      skipped_not_evaluable=$((skipped_not_evaluable + 1))
    else
      echo "RUN  $clip_id $condition"
      pending=$((pending + 1))
    fi
  done
done

echo "Completed cells to skip: $skipped_complete"
echo "B2 cells not evaluable: $skipped_not_evaluable"
echo "Pending cells to run: $pending"
if $dry_run; then
  echo "Dry run only. No Ollama request was sent."
  exit 0
fi

lock_directory="output/.frozen_validation_matrix_cpu.lock"
mkdir -p output
if ! mkdir "$lock_directory" 2>/dev/null; then
  echo "Another frozen validation batch may already be running: $lock_directory" >&2
  exit 1
fi
trap 'rmdir "$lock_directory" 2>/dev/null || true' EXIT

mkdir -p output/batch_logs
batch_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
batch_log="output/batch_logs/frozen_validation_matrix_cpu_${batch_timestamp}.log"
exec > >(tee -a "$batch_log") 2>&1

export OLLAMA_BASE_URL="$ollama_base_url"
export OLLAMA_TIMEOUT_SECONDS="$timeout_seconds"

echo "Batch log: $project_root/$batch_log"
if ! uv run football-coach ollama-check --model "$model_tag"; then
  echo "Ollama model check failed; no validation request was sent" >&2
  exit 1
fi

completed_now=0
failures=0
for clip_id in "${clips[@]}"; do
  for condition in "${conditions[@]}"; do
    expected_case=""
    if [[ "$condition" == "B3_human_oracle" ]]; then
      expected_case="${b3_case[$clip_id]}"
    fi
    if cell_complete "$clip_id" "$condition" "$expected_case"; then
      continue
    fi
    if [[ "$condition" == "B2_action_oracle" ]] && ! b2_supported "$clip_id"; then
      continue
    fi

    command_for_cell "$clip_id" "$condition"
    echo
    echo "START $clip_id $condition at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if "${cell_command[@]}" && cell_complete "$clip_id" "$condition" "$expected_case"; then
      completed_now=$((completed_now + 1))
      echo "DONE  $clip_id $condition at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      continue
    fi

    failures=$((failures + 1))
    echo "FAILED $clip_id $condition: inspect the preserved run before retrying" >&2
    if ! uv run football-coach ollama-check --model "$model_tag" >/dev/null; then
      echo "Ollama is unavailable after the failure; stopping the batch" >&2
      echo "Batch log: $project_root/$batch_log" >&2
      exit 1
    fi
    echo "Ollama remains available; continuing to the next independent cell"
  done
done

echo
echo "Newly completed cells: $completed_now"
echo "Failed cells: $failures"
echo "B2 not-evaluable cells: $skipped_not_evaluable"
echo "Batch log: $project_root/$batch_log"

if (( failures > 0 )); then
  exit 1
fi
