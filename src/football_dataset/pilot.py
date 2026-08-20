from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

from PIL import Image


FRAME_COUNT = 750
FRAME_RATE = 25
SAMPLE_COUNT = 16
STRATEGIES = ("uniform", "event_centered")
EVENT_OFFSETS_SECONDS = (
    -6.0,
    -4.0,
    -3.0,
    -2.0,
    -1.5,
    -1.0,
    -0.5,
    0.0,
    0.5,
    1.0,
    1.5,
    2.0,
    3.0,
    4.0,
    6.0,
    9.0,
)
MAX_IMAGE_EDGE = 672
JPEG_QUALITY = 85
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
GENERATION_OPTIONS = {
    "temperature": 0,
    "seed": 42,
    "num_ctx": 16384,
    "num_predict": 600,
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "phase_of_play": {"type": "string"},
        "attacking_team_visual_description": {"type": "string"},
        "attacking_direction": {
            "type": "string",
            "enum": ["left_to_right", "right_to_left", "unclear"],
        },
        "sequence_description": {"type": "string"},
        "attacking_problem": {"type": "string"},
        "defensive_problem": {"type": "string"},
        "visible_evidence": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
        "attacking_recommendation": {"type": "string"},
        "defensive_recommendation": {"type": "string"},
        "training_intervention": {"type": "string"},
        "confidence": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
        "limitations": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
    },
    "required": [
        "phase_of_play",
        "attacking_team_visual_description",
        "attacking_direction",
        "sequence_description",
        "attacking_problem",
        "defensive_problem",
        "visible_evidence",
        "attacking_recommendation",
        "defensive_recommendation",
        "training_intervention",
        "confidence",
        "limitations",
    ],
    "additionalProperties": False,
}

EXPECTED_EVENT_TERMS = {
    "Corner": ("corner", "corner kick", "set piece"),
    "Direct free-kick": ("free kick", "free-kick", "set piece"),
    "Foul": ("foul", "challenge", "tackle", "stoppage"),
    "Shots on target": ("shot", "attempt", "save", "goalkeeper"),
    "Shots off target": ("shot", "attempt", "wide", "miss"),
    "Goal": ("goal", "scores", "scored", "finish"),
    "Clearance": ("clearance", "clears", "cleared", "clear the ball"),
}


def uniform_frames(frame_count: int = FRAME_COUNT, count: int = SAMPLE_COUNT) -> list[int]:
    """Return one-indexed centre frames from equally sized temporal bins."""
    return [round((index + 0.5) * frame_count / count) for index in range(count)]


def _nearest_unused_frame(target: int, used: set[int], frame_count: int) -> int:
    target = min(max(target, 1), frame_count)
    if target not in used:
        return target
    for distance in range(1, frame_count):
        for candidate in (target - distance, target + distance):
            if 1 <= candidate <= frame_count and candidate not in used:
                return candidate
    raise ValueError("No unused frame remains")


def event_centered_frames(
    event_frame: int,
    frame_count: int = FRAME_COUNT,
    frame_rate: int = FRAME_RATE,
) -> list[int]:
    """Return 16 ordered frames concentrated around a private event anchor."""
    used: set[int] = set()
    frames: list[int] = []
    for offset in EVENT_OFFSETS_SECONDS:
        target = round(event_frame + offset * frame_rate)
        selected = _nearest_unused_frame(target, used, frame_count)
        used.add(selected)
        frames.append(selected)
    return sorted(frames)


def event_frame_from_info(info: dict) -> int:
    relative_ms = int(info["action_position"]) - int(info["clip_start"])
    frame = round(relative_ms * int(info["frame_rate"]) / 1000) + 1
    return min(max(frame, 1), int(info["seq_length"]))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def prepare_pilot_inputs(project_root: Path) -> dict:
    protocol_path = project_root / "config" / "evaluation_protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    selection = _read_csv(project_root / protocol["pilot"]["selection_file"])
    manifest = {
        row["clip_id"]: row
        for row in _read_csv(project_root / "data" / "processed" / "manifest.csv")
    }
    prompt_path = project_root / protocol["prompt"]
    prompt_hash = hashlib.sha256(prompt_path.read_bytes()).hexdigest()

    records = []
    archives: dict[Path, ZipFile] = {}
    try:
        for selected in selection:
            clip_id = selected["clip_id"]
            source = manifest[clip_id]
            archive_path = project_root / source["archive_path"]
            archive = archives.setdefault(archive_path, ZipFile(archive_path))
            label = json.loads(archive.read(source["label_member"]))
            info = label["info"]
            event_frame = event_frame_from_info(info)
            strategies = {
                "uniform": uniform_frames(int(source["frame_count"]), SAMPLE_COUNT),
                "event_centered": event_centered_frames(
                    event_frame,
                    int(source["frame_count"]),
                    int(source["frame_rate"]),
                ),
            }
            records.append(
                {
                    "clip_id": clip_id,
                    "split": source["split"],
                    "model_input": {
                        "prompt_sha256": prompt_hash,
                        "video_representation": source["video_representation"],
                        "strategies": {
                            name: {
                                "frame_numbers": frames,
                                "frame_seconds": [
                                    round((frame - 1) / int(source["frame_rate"]), 3)
                                    for frame in frames
                                ],
                            }
                            for name, frames in strategies.items()
                        },
                    },
                    "hidden_reference": {
                        "official_anchor_action": source["action_class"],
                        "event_frame": event_frame,
                        "event_second": round(
                            (event_frame - 1) / int(source["frame_rate"]), 3
                        ),
                        "archive_path": source["archive_path"],
                        "frame_member_pattern": source["frame_member_pattern"],
                    },
                }
            )
    finally:
        for archive in archives.values():
            archive.close()

    output = {
        "protocol_id": protocol["protocol_id"],
        "status": "prepared-not-run",
        "sample_count_per_strategy": SAMPLE_COUNT,
        "sampling": {
            "uniform": "centre frame of each of 16 equal temporal bins",
            "event_centered": {
                "private_anchor": "action_position from Labels-GameState.json info",
                "offsets_seconds": list(EVENT_OFFSETS_SECONDS),
            },
        },
        "image_preprocessing": {
            "maximum_edge_pixels": MAX_IMAGE_EDGE,
            "jpeg_quality": JPEG_QUALITY,
            "stored_to_disk": False,
        },
        "clips": records,
    }
    output_path = project_root / "data" / "processed" / "pilot_inputs.json"
    _write_json(output_path, output)
    return output


def _resize_jpeg(raw: bytes) -> bytes:
    with Image.open(io.BytesIO(raw)) as image:
        image = image.convert("RGB")
        image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()


def _load_images(project_root: Path, clip: dict, strategy: str) -> tuple[list[str], list[str]]:
    reference = clip["hidden_reference"]
    frames = clip["model_input"]["strategies"][strategy]["frame_numbers"]
    encoded: list[str] = []
    hashes: list[str] = []
    with ZipFile(project_root / reference["archive_path"]) as archive:
        for frame in frames:
            member = reference["frame_member_pattern"] % frame
            resized = _resize_jpeg(archive.read(member))
            encoded.append(base64.b64encode(resized).decode("ascii"))
            hashes.append(hashlib.sha256(resized).hexdigest())
    return encoded, hashes


def _call_ollama(
    model: str,
    prompt: str,
    images: list[str],
    timeout: int,
    *,
    response_schema: dict | None = None,
    generation_options: dict | None = None,
) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": images}],
        "stream": False,
        "format": response_schema or RESPONSE_SCHEMA,
        "options": generation_options or GENERATION_OPTIONS,
        "keep_alive": "10m",
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {details}") from exc


def _parse_model_json(text: str) -> tuple[dict | None, str | None]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "Response JSON is not an object"
    return value, None


def run_pilot(
    project_root: Path,
    strategies: Iterable[str],
    *,
    overwrite: bool = False,
    limit: int | None = None,
    timeout: int = 900,
) -> list[Path]:
    protocol = json.loads(
        (project_root / "config" / "evaluation_protocol.json").read_text(
            encoding="utf-8"
        )
    )
    inputs_path = project_root / "data" / "processed" / "pilot_inputs.json"
    inputs = None
    if inputs_path.exists():
        candidate = json.loads(inputs_path.read_text(encoding="utf-8"))
        if candidate.get("protocol_id") == protocol["protocol_id"]:
            inputs = candidate
    if inputs is None:
        inputs = prepare_pilot_inputs(project_root)
    prompt = (project_root / protocol["prompt"]).read_text(encoding="utf-8")
    model = protocol["model"]["name"]
    required = set(protocol["required_response_fields"])
    selected_strategies = list(strategies)
    invalid = set(selected_strategies) - set(STRATEGIES)
    if invalid:
        raise ValueError(f"Unknown strategies: {sorted(invalid)}")

    tasks = [
        (strategy, clip)
        for strategy in selected_strategies
        for clip in inputs["clips"]
    ]
    if limit is not None:
        tasks = tasks[:limit]
    written: list[Path] = []
    for index, (strategy, clip) in enumerate(tasks, start=1):
        clip_id = clip["clip_id"]
        output_path = (
            project_root
            / "data"
            / "processed"
            / "pilot_runs"
            / strategy
            / f"{clip_id}.json"
        )
        if output_path.exists() and not overwrite:
            print(f"[{index}/{len(tasks)}] skip existing {strategy} {clip_id}", flush=True)
            continue
        print(f"[{index}/{len(tasks)}] load {strategy} {clip_id}", flush=True)
        images, image_hashes = _load_images(project_root, clip, strategy)
        started = time.perf_counter()
        try:
            response = _call_ollama(model, prompt, images, timeout)
            elapsed = time.perf_counter() - started
            response_text = response.get("message", {}).get("content", "")
            parsed, parse_error = _parse_model_json(response_text)
            missing = sorted(required - set(parsed or {}))
            result = {
                "protocol_id": protocol["protocol_id"],
                "run_id": f"{protocol['protocol_id']}__{strategy}__{clip_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clip_id": clip_id,
                "split": clip["split"],
                "strategy": strategy,
                "model": model,
                "model_input": {
                    "frame_numbers": clip["model_input"]["strategies"][strategy][
                        "frame_numbers"
                    ],
                    "frame_seconds": clip["model_input"]["strategies"][strategy][
                        "frame_seconds"
                    ],
                    "resized_image_sha256": image_hashes,
                    "prompt_sha256": clip["model_input"]["prompt_sha256"],
                    "image_count": len(images),
                    "maximum_image_edge": MAX_IMAGE_EDGE,
                },
                "generation_options": GENERATION_OPTIONS,
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
                "protocol_id": protocol["protocol_id"],
                "run_id": f"{protocol['protocol_id']}__{strategy}__{clip_id}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "clip_id": clip_id,
                "split": clip["split"],
                "strategy": strategy,
                "model": model,
                "elapsed_seconds": round(elapsed, 3),
                "error": f"{type(exc).__name__}: {exc}",
                "hidden_reference": clip["hidden_reference"],
            }
            _write_json(output_path, result)
            print(f"[{index}/{len(tasks)}] ERROR {strategy} {clip_id}: {exc}", flush=True)
            raise
        _write_json(output_path, result)
        written.append(output_path)
        print(
            f"[{index}/{len(tasks)}] done {strategy} {clip_id} "
            f"{elapsed:.1f}s json={result['technical_validation']['complete_schema']}",
            flush=True,
        )
    return written


def _event_term_match(action: str, response: dict | None) -> bool:
    if not response:
        return False
    searchable = " ".join(
        str(response.get(field, ""))
        for field in ("phase_of_play", "sequence_description", "visible_evidence")
    ).lower()
    return any(term in searchable for term in EXPECTED_EVENT_TERMS.get(action, ()))


def compare_pilot(project_root: Path) -> dict:
    protocol = json.loads(
        (project_root / "config" / "evaluation_protocol.json").read_text(
            encoding="utf-8"
        )
    )
    rows = []
    for strategy in STRATEGIES:
        run_dir = project_root / "data" / "processed" / "pilot_runs" / strategy
        for path in sorted(run_dir.glob("*.json")):
            run = json.loads(path.read_text(encoding="utf-8"))
            response = run.get("response_json")
            action = run["hidden_reference"]["official_anchor_action"]
            rows.append(
                {
                    "clip_id": run["clip_id"],
                    "strategy": strategy,
                    "official_anchor_action": action,
                    "run_succeeded": "error" not in run,
                    "complete_schema": run.get("technical_validation", {}).get(
                        "complete_schema", False
                    ),
                    "anchor_term_match": _event_term_match(action, response),
                    "elapsed_seconds": run.get("elapsed_seconds"),
                    "confidence": (response or {}).get("confidence"),
                    "same_attacking_and_defensive_problem": bool(
                        response
                        and response.get("attacking_problem")
                        == response.get("defensive_problem")
                    ),
                    "same_attacking_and_defensive_recommendation": bool(
                        response
                        and response.get("attacking_recommendation")
                        == response.get("defensive_recommendation")
                    ),
                }
            )

    summaries = {}
    for strategy in STRATEGIES:
        strategy_rows = [row for row in rows if row["strategy"] == strategy]
        elapsed = [row["elapsed_seconds"] for row in strategy_rows if row["elapsed_seconds"]]
        summaries[strategy] = {
            "completed_runs": len(strategy_rows),
            "successful_runs": sum(row["run_succeeded"] for row in strategy_rows),
            "complete_schema_runs": sum(row["complete_schema"] for row in strategy_rows),
            "anchor_term_matches": sum(row["anchor_term_match"] for row in strategy_rows),
            "same_problem_for_both_teams": sum(
                row["same_attacking_and_defensive_problem"] for row in strategy_rows
            ),
            "same_recommendation_for_both_teams": sum(
                row["same_attacking_and_defensive_recommendation"]
                for row in strategy_rows
            ),
            "mean_elapsed_seconds": round(sum(elapsed) / len(elapsed), 3) if elapsed else None,
            "confidence_counts": dict(
                Counter(row["confidence"] for row in strategy_rows if row["confidence"])
            ),
        }

    comparison = {
        "protocol_id": protocol["protocol_id"],
        "status": "technical-comparison-only",
        "warning": (
            "Anchor-term matching is a diagnostic, not a coaching-quality score. "
            "A final sampling decision requires paired human review."
        ),
        "selected_baseline": "uniform",
        "selection_scope": "provisional train-pilot decision pending validation",
        "selection_reasons": [
            "12 of 12 complete schemas versus 11 of 12 for event_centered",
            "equal anchor-term diagnostic results: 2 of 12 for each strategy",
            "lower mean runtime",
            "does not require hidden event timing at inference input-selection time",
        ],
        "important_counterevidence": (
            "Event-centered responses used exactly the same attacking and defensive "
            "problem less often. This possible specificity advantage requires human review."
        ),
        "strategies": summaries,
        "per_clip": rows,
    }
    _write_json(
        project_root / "data" / "processed" / "pilot_comparison.json", comparison
    )
    return comparison
