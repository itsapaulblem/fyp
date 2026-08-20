from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
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
)


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


def run_recognition_gate(
    project_root: Path,
    *,
    overwrite: bool = False,
    limit: int | None = None,
    timeout: int = 900,
) -> list[Path]:
    config = json.loads(
        (project_root / "config" / "event_recognition_gate.json").read_text(
            encoding="utf-8"
        )
    )
    inputs = json.loads(
        (project_root / config["sampling"]["source"]).read_text(encoding="utf-8")
    )
    if inputs.get("protocol_id") != config["source_coaching_protocol_id"]:
        raise ValueError("Pilot input protocol does not match recognition configuration")

    prompt_path = project_root / config["prompt"]
    prompt = prompt_path.read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()
    required = set(config["required_response_fields"])
    model = config["model"]["name"]
    clips = inputs["clips"][:limit] if limit is not None else inputs["clips"]
    written: list[Path] = []

    for index, clip in enumerate(clips, start=1):
        clip_id = clip["clip_id"]
        output_path = (
            project_root
            / "data"
            / "processed"
            / "recognition_runs"
            / "uniform"
            / f"{clip_id}.json"
        )
        if output_path.exists() and not overwrite:
            existing = json.loads(output_path.read_text(encoding="utf-8"))
            if existing.get("protocol_id") != config["protocol_id"]:
                raise ValueError(f"Existing result has another protocol: {output_path}")
            print(f"[{index}/{len(clips)}] skip existing uniform {clip_id}", flush=True)
            continue

        print(f"[{index}/{len(clips)}] load uniform {clip_id}", flush=True)
        images, image_hashes = _load_images(project_root, clip, "uniform")
        started = time.perf_counter()
        try:
            response = _call_ollama(
                model,
                prompt,
                images,
                timeout,
                response_schema=RECOGNITION_SCHEMA,
                generation_options=RECOGNITION_OPTIONS,
            )
            elapsed = time.perf_counter() - started
            response_text = response.get("message", {}).get("content", "")
            parsed, parse_error = _parse_model_json(response_text)
            missing = sorted(required - set(parsed or {}))
            result = {
                "protocol_id": config["protocol_id"],
                "run_id": f"{config['protocol_id']}__uniform__{clip_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clip_id": clip_id,
                "split": clip["split"],
                "strategy": "uniform",
                "model": model,
                "model_input": {
                    "frame_numbers": clip["model_input"]["strategies"]["uniform"][
                        "frame_numbers"
                    ],
                    "frame_seconds": clip["model_input"]["strategies"]["uniform"][
                        "frame_seconds"
                    ],
                    "resized_image_sha256": image_hashes,
                    "prompt_sha256": prompt_hash,
                    "image_count": len(images),
                    "maximum_image_edge": MAX_IMAGE_EDGE,
                },
                "generation_options": RECOGNITION_OPTIONS,
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
                "run_id": f"{config['protocol_id']}__uniform__{clip_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clip_id": clip_id,
                "split": clip["split"],
                "strategy": "uniform",
                "model": model,
                "elapsed_seconds": round(elapsed, 3),
                "error": f"{type(exc).__name__}: {exc}",
                "hidden_reference": clip["hidden_reference"],
            }
            _write_json(output_path, result)
            print(f"[{index}/{len(clips)}] ERROR uniform {clip_id}: {exc}", flush=True)
            raise

        _write_json(output_path, result)
        written.append(output_path)
        print(
            f"[{index}/{len(clips)}] done uniform {clip_id} "
            f"{elapsed:.1f}s json={result['technical_validation']['complete_schema']}",
            flush=True,
        )
    return written


def summarize_recognition_gate(project_root: Path) -> dict:
    config = json.loads(
        (project_root / "config" / "event_recognition_gate.json").read_text(
            encoding="utf-8"
        )
    )
    run_dir = project_root / "data" / "processed" / "recognition_runs" / "uniform"
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
            "outcome, and attacking-team correctness from the same 16 frames."
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
        project_root / "data" / "processed" / "recognition_summary.json", summary
    )
    return summary

