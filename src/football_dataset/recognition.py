from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from football_dataset.pilot import (
    GENERATION_OPTIONS,
    MAX_IMAGE_EDGE,
    _call_ollama,
    _event_term_match,
    _load_images,
    _parse_model_json,
    _write_json,
    uniform_frames,
)


RECOGNITION_CONDITIONS = ("uniform16", "uniform32")
RECOGNITION_CONFIGS = {
    "uniform16": "config/event_recognition_gate.json",
    "uniform32": "config/event_recognition_uniform32.json",
}


RECOGNITION_SCHEMA = {
    "type": "object",
    "properties": {
        "phase_of_play": {"type": "string"},
        "attacking_team_visual_description": {"type": "string"},
        "event": {"type": "string"},
        "outcome": {"type": "string"},
        "visible_evidence": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
    },
    "required": [
        "phase_of_play",
        "attacking_team_visual_description",
        "event",
        "outcome",
        "visible_evidence",
        "confidence",
    ],
    "additionalProperties": False,
}

RECOGNITION_OPTIONS = {
    **GENERATION_OPTIONS,
    "num_predict": 300,
}


def _recognition_anchor_term_match(action: str, response: dict | None) -> bool:
    if not response:
        return False
    adapted = {
        "phase_of_play": response.get("phase_of_play", ""),
        "sequence_description": " ".join(
            (str(response.get("event", "")), str(response.get("outcome", "")))
        ),
        "visible_evidence": response.get("visible_evidence", []),
    }
    return _event_term_match(action, adapted)


def _load_recognition_config(project_root: Path, condition: str) -> dict:
    try:
        relative_path = RECOGNITION_CONFIGS[condition]
    except KeyError as exc:
        choices = ", ".join(RECOGNITION_CONDITIONS)
        raise ValueError(f"Unknown recognition condition {condition!r}; use {choices}") from exc
    return json.loads((project_root / relative_path).read_text(encoding="utf-8"))


def prepare_recognition_inputs(project_root: Path, condition: str) -> dict:
    """Prepare an isolated recognition input manifest for a configured condition."""
    config = _load_recognition_config(project_root, condition)
    sampling = config["sampling"]
    base_source = sampling.get("base_source")
    if not base_source:
        raise ValueError(
            f"Condition {condition!r} reuses an existing input manifest and "
            "does not require preparation"
        )

    base = json.loads((project_root / base_source).read_text(encoding="utf-8"))
    if base.get("protocol_id") != config["source_coaching_protocol_id"]:
        raise ValueError("Base pilot input protocol does not match recognition configuration")

    frame_count = int(sampling["source_frame_count"])
    frame_rate = int(sampling["source_frame_rate"])
    sample_count = int(sampling["frame_count"])
    strategy_key = sampling["strategy_key"]
    prompt_path = project_root / config["prompt"]
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()

    clips = []
    for base_clip in base["clips"]:
        clip = deepcopy(base_clip)
        frames = uniform_frames(frame_count, sample_count)
        clip["model_input"] = {
            "prompt_sha256": prompt_hash,
            "video_representation": base_clip["model_input"]["video_representation"],
            "strategies": {
                strategy_key: {
                    "frame_numbers": frames,
                    "frame_seconds": [
                        round((frame - 1) / frame_rate, 3) for frame in frames
                    ],
                }
            },
        }
        clips.append(clip)

    output = {
        "recognition_protocol_id": config["protocol_id"],
        "source_coaching_protocol_id": config["source_coaching_protocol_id"],
        "status": "prepared-not-run",
        "condition": condition,
        "sample_count": sample_count,
        "sampling": (
            f"centre frame of each of {sample_count} equal temporal bins over "
            f"{frame_count} frames"
        ),
        "clips": clips,
    }
    _write_json(project_root / sampling["source"], output)
    return output


def run_recognition_gate(
    project_root: Path,
    *,
    condition: str = "uniform16",
    overwrite: bool = False,
    limit: int | None = None,
    timeout: int = 900,
) -> list[Path]:
    config = _load_recognition_config(project_root, condition)
    inputs = json.loads(
        (project_root / config["sampling"]["source"]).read_text(encoding="utf-8")
    )
    if "base_source" in config["sampling"]:
        if inputs.get("recognition_protocol_id") != config["protocol_id"]:
            raise ValueError("Recognition input protocol does not match configuration")
    elif inputs.get("protocol_id") != config["source_coaching_protocol_id"]:
        raise ValueError("Pilot input protocol does not match recognition configuration")

    prompt_path = project_root / config["prompt"]
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    required = set(config["required_response_fields"])
    model = config["model"]["name"]
    generation_options = {
        **RECOGNITION_OPTIONS,
        **config.get("generation_options", {}),
    }
    strategy_key = config["sampling"].get("strategy_key", "uniform")
    output_condition = config["sampling"].get("condition", condition)
    run_directory = config.get("output", {}).get(
        "run_directory", f"data/processed/recognition_runs/{output_condition}"
    )
    clips = inputs["clips"][:limit] if limit is not None else inputs["clips"]
    written: list[Path] = []

    for index, clip in enumerate(clips, start=1):
        clip_id = clip["clip_id"]
        output_path = (
            project_root
            / run_directory
            / f"{clip_id}.json"
        )
        if output_path.exists() and not overwrite:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            if existing.get("protocol_id") != config["protocol_id"]:
                raise ValueError(f"Existing result has another protocol: {output_path}")
            print(
                f"[{index}/{len(clips)}] skip existing {output_condition} {clip_id}",
                flush=True,
            )
            continue

        print(f"[{index}/{len(clips)}] load {output_condition} {clip_id}", flush=True)
        images, image_hashes = _load_images(project_root, clip, strategy_key)
        started = time.perf_counter()
        try:
            response = _call_ollama(
                model,
                prompt,
                images,
                timeout,
                response_schema=RECOGNITION_SCHEMA,
                generation_options=generation_options,
            )
            elapsed = time.perf_counter() - started
            response_text = response.get("message", {}).get("content", "")
            parsed, parse_error = _parse_model_json(response_text)
            missing = sorted(required - set(parsed or {}))
            result = {
                "protocol_id": config["protocol_id"],
                "run_id": f"{config['protocol_id']}__{output_condition}__{clip_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clip_id": clip_id,
                "split": clip["split"],
                "strategy": output_condition,
                "model": model,
                "model_input": {
                    "frame_numbers": clip["model_input"]["strategies"][strategy_key][
                        "frame_numbers"
                    ],
                    "frame_seconds": clip["model_input"]["strategies"][strategy_key][
                        "frame_seconds"
                    ],
                    "resized_image_sha256": image_hashes,
                    "prompt_sha256": prompt_hash,
                    "image_count": len(images),
                    "maximum_image_edge": MAX_IMAGE_EDGE,
                },
                "generation_options": generation_options,
                "elapsed_seconds": round(elapsed, 3),
                "response_text": response_text,
                "response_json": parsed,
                "technical_validation": {
                    "json_object": parsed is not None,
                    "parse_error": parse_error,
                    "missing_required_fields": missing,
                    "complete_schema": parsed is not None and not missing,
                },
                "ollama_metrics": {
                    key: response.get(key)
                    for key in (
                        "total_duration",
                        "load_duration",
                        "prompt_eval_count",
                        "prompt_eval_duration",
                        "eval_count",
                        "eval_duration",
                    )
                },
                "hidden_reference": clip["hidden_reference"],
            }
        except Exception as exc:
            elapsed = time.perf_counter() - started
            result = {
                "protocol_id": config["protocol_id"],
                "run_id": f"{config['protocol_id']}__{output_condition}__{clip_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clip_id": clip_id,
                "split": clip["split"],
                "strategy": output_condition,
                "model": model,
                "elapsed_seconds": round(elapsed, 3),
                "error": f"{type(exc).__name__}: {exc}",
                "hidden_reference": clip["hidden_reference"],
            }
            _write_json(output_path, result)
            print(
                f"[{index}/{len(clips)}] ERROR {output_condition} {clip_id}: {exc}",
                flush=True,
            )
            raise

        _write_json(output_path, result)
        written.append(output_path)
        print(
            f"[{index}/{len(clips)}] done {output_condition} {clip_id} "
            f"{elapsed:.1f}s json={result['technical_validation']['complete_schema']}",
            flush=True,
        )
    return written


def summarize_recognition_gate(
    project_root: Path, condition: str = "uniform16"
) -> dict:
    config = _load_recognition_config(project_root, condition)
    output_condition = config["sampling"].get("condition", condition)
    run_directory = config.get("output", {}).get(
        "run_directory", f"data/processed/recognition_runs/{output_condition}"
    )
    run_dir = project_root / run_directory
    rows = []
    for path in sorted(run_dir.glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        response = run.get("response_json")
        action = run["hidden_reference"]["official_anchor_action"]
        rows.append(
            {
                "clip_id": run["clip_id"],
                "official_anchor_action": action,
                "complete_schema": run.get("technical_validation", {}).get(
                    "complete_schema", False
                ),
                "anchor_term_match": _recognition_anchor_term_match(action, response),
                "model_event": (response or {}).get("event"),
                "model_outcome": (response or {}).get("outcome"),
                "model_confidence": (response or {}).get("confidence"),
                "elapsed_seconds": run.get("elapsed_seconds"),
                "human_review_status": "pending",
            }
        )

    elapsed = [row["elapsed_seconds"] for row in rows if row["elapsed_seconds"]]
    summary = {
        "protocol_id": config["protocol_id"],
        "status": "awaiting-single-reviewer-human-reference",
        "completed_runs": len(rows),
        "complete_schema_runs": sum(row["complete_schema"] for row in rows),
        "automatic_anchor_term_matches": sum(row["anchor_term_match"] for row in rows),
        "automatic_metric_warning": (
            "Term matching is diagnostic only. The project reviewer must judge event, "
            "outcome, and attacking-team correctness from the exact sampled frames."
        ),
        "confidence_counts": dict(
            Counter(row["model_confidence"] for row in rows if row["model_confidence"])
        ),
        "mean_elapsed_seconds": (
            round(sum(elapsed) / len(elapsed), 3) if elapsed else None
        ),
        "human_success_gate": config["human_review"]["success_gate"],
        "per_clip": rows,
    }
    _write_json(
        project_root
        / config.get("output", {}).get(
            "summary_file", "data/processed/recognition_summary.json"
        ),
        summary,
    )
    return summary
