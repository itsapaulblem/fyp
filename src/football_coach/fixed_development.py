"""Unattended train diagnostic: fixed P2/P3 and initial P1 only."""

from __future__ import annotations

import hashlib
import json
import re
import traceback
from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

from .ollama_client import OllamaClient
from .prompting import PromptMessage, readable_transcript
from .provenance import sha256_file, timestamp_utc
from .staged_prompting import (
    RECOGNITION_HEADINGS,
    heading_issues,
    pending_guided_review,
    progressive_messages,
    recognition_messages,
    response_text,
    revision_messages,
    write_json,
    write_metadata,
)

CONDITIONS = ("P2_attention_hint", "P3_visible_cue_hint")
P1_METHOD = "P1_human_guided"
VARIANT = "fixed_unattended_v2"
HINT_HEADER = re.compile(r"^HINT ([1-3]) — .*?$", re.MULTILINE)
FRAME_NAME = re.compile(r"^(\d{2})_frame_\d{6}\.jpg$")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes project root: {relative}")
    return path


def _frozen_file(root: Path, relative: str, expected_hash: str) -> Path:
    path = _inside(root, relative)
    if not path.is_file() or sha256_file(path) != expected_hash:
        raise ValueError(f"Missing or changed frozen input: {relative}")
    return path


def parse_fixed_hints(value: str) -> list[str]:
    headers = list(HINT_HEADER.finditer(value))
    if [match.group(1) for match in headers] != ["1", "2", "3"]:
        raise ValueError("Frozen P2 input must contain exactly HINT 1, HINT 2, HINT 3")
    hints = [
        value[match.end() : headers[index + 1].start() if index < 2 else len(value)].strip()
        for index, match in enumerate(headers)
    ]
    if not all(hints):
        raise ValueError("Each frozen P2 hint must have text")
    return hints


def frame_set_sha256(images: list[Path]) -> str:
    entries = "\n".join(f"{image.name}:{sha256_file(image)}" for image in images)
    return hashlib.sha256(entries.encode("utf-8")).hexdigest()


def validate_fixed_batch(root: Path, batch_path: Path) -> dict[str, Any]:
    """Check all frozen inputs without contacting Ollama or reading references."""
    root = root.resolve()
    batch_path = batch_path.resolve()
    if not batch_path.is_relative_to(root / "config"):
        raise ValueError("Batch declaration must be under config")
    batch = _load_json(batch_path)
    if (
        batch.get("protocol_id") != "evidence-first-football-v0.4.0"
        or batch.get("variant") != VARIANT
        or batch.get("status") != "approved_train_development"
        or batch.get("split") != "train"
        or batch.get("conditions_in_order") != list(CONDITIONS)
        or batch.get("fresh_recognition_per_condition") is not True
        or batch.get("pause_before_coaching") is not True
        or batch.get("human_review_during_batch") is not False
        or batch.get("maximum_p2_hints") != 3
        or batch.get("maximum_p3_cue_packets") != 1
        or batch.get("p1_stops_after_initial_recognition") is not True
        or batch.get("batch_execution_order") != "p1_initial_first_then_p2_p3"
        or batch.get("model") != "qwen3.5:27b"
    ):
        raise ValueError("Invalid fixed train-only P2/P3 batch declaration")
    clip_ids = batch.get("clip_ids_in_order")
    if clip_ids != ["B-TRAIN-0054", "B-TRAIN-0040", "B-TRAIN-0051"]:
        raise ValueError("Batch clip order differs from the approved development order")
    p1_ids = batch.get("p1_initial_only_clip_ids")
    if p1_ids != ["B-TRAIN-0040", "B-TRAIN-0051"]:
        raise ValueError("P1 initial-only clips must be 0040 and 0051; 0054 is already done")
    reference_hashes = batch.get("p1_local_reference_sha256")
    if (
        not isinstance(reference_hashes, dict)
        or set(reference_hashes) != set(p1_ids)
        or any(
            not isinstance(value, str)
            or re.fullmatch(r"[0-9a-f]{64}", value) is None
            for value in reference_hashes.values()
        )
    ):
        raise ValueError("P1 needs frozen local human-reference hashes, not reference text")
    for clip_id in p1_ids:
        local_reference = root / "data/video_b/review" / f"{clip_id}.json"
        if local_reference.is_file() and sha256_file(local_reference) != reference_hashes[clip_id]:
            raise ValueError(f"Local P1 human reference changed: {clip_id}")
    selection_path = _inside(root, batch["selection_manifest_path"])
    selection = _load_json(selection_path)
    if (
        selection.get("split") != "train"
        or selection.get("selection_used_hidden_labels") is not True
        or selection.get("clip_ids_in_order") != clip_ids
    ):
        raise ValueError("Invalid label-informed development selection")
    device_path = _inside(root, batch["device_config_path"])
    device = _load_json(device_path)
    generation = device.get("generation", {})
    cohort_path = _inside(root, batch["cohort_path"])
    cohort = _load_json(cohort_path)
    if (
        cohort.get("split") != "train"
        or cohort.get("selection_used_hidden_labels") is not False
        or not set(clip_ids).issubset(set(cohort.get("clip_ids", [])))
        or device.get("development", {}).get("cohort_path") != batch["cohort_path"]
    ):
        raise ValueError("Invalid P1 development cohort")
    if (
        device.get("protocol_id") != batch["protocol_id"]
        or generation.get("require_gpu") is not False
        or generation.get("options", {}).get("num_gpu") != 0
    ):
        raise ValueError("Fixed unattended batch requires the declared CPU-only config")
    recognition_path = _inside(root, batch["recognition_prompt_path"])
    p1_revision_path = _inside(root, batch["p1_revision_prompt_path"])
    p1_coaching_path = _inside(root, batch["p1_coaching_prompt_path"])
    p1_paths = device.get("prompts", {}).get(P1_METHOD, {})
    if p1_paths != {
        "recognition": batch["recognition_prompt_path"],
        "revision": batch["p1_revision_prompt_path"],
        "coaching": batch["p1_coaching_prompt_path"],
    }:
        raise ValueError("P1 prompt paths differ from the CPU protocol config")
    p2_wrapper_path = _inside(root, batch["p2_hint_wrapper_path"])
    p3_wrapper_path = _inside(root, batch["p3_cue_wrapper_path"])
    for path in (
        recognition_path, p1_revision_path, p1_coaching_path,
        p2_wrapper_path, p3_wrapper_path,
    ):
        if not path.is_file():
            raise ValueError(f"Missing prompt: {path}")
    hints_path = _frozen_file(
        root, batch["p2_fixed_hints_path"], batch["p2_fixed_hints_sha256"]
    )
    hints = parse_fixed_hints(hints_path.read_text(encoding="utf-8"))
    if set(batch.get("p3_cues", {})) != set(clip_ids):
        raise ValueError("P3 must have one frozen cue sheet for each selected clip")
    if set(batch.get("frame_set_sha256", {})) != set(clip_ids):
        raise ValueError("Each selected clip needs a frozen 30-image digest")
    cues: dict[str, Path] = {}
    frames: dict[str, list[Path]] = {}
    for clip_id in clip_ids:
        cue = batch["p3_cues"][clip_id]
        if not cue["path"].startswith("output/v0.4/prompt_chain/P3_visible_cue_hint/"):
            raise ValueError("P3 cue must stay under its private output directory")
        cues[clip_id] = _frozen_file(root, cue["path"], cue["sha256"])
        image_dir = _inside(
            root, batch["sampled_image_directory_pattern"].format(clip_id=clip_id)
        )
        if not image_dir.is_dir():
            raise ValueError(f"Missing staged sampled images: {image_dir}")
        images = sorted(image_dir.glob("*.jpg"))
        numbers = []
        for image_path in images:
            match = FRAME_NAME.fullmatch(image_path.name)
            if match is None:
                raise ValueError(f"Unexpected staged image: {image_path}")
            numbers.append(int(match.group(1)))
        if numbers != list(range(1, 31)):
            raise ValueError(f"Expected exactly 30 ordered sampled JPEGs: {image_dir}")
        if frame_set_sha256(images) != batch["frame_set_sha256"][clip_id]:
            raise ValueError(f"Changed sampled image set: {image_dir}")
        frames[clip_id] = images
    return {
        "batch": batch,
        "batch_path": batch_path,
        "selection_path": selection_path,
        "device_path": device_path,
        "device": device,
        "generation": generation,
        "cohort_path": cohort_path,
        "recognition_path": recognition_path,
        "p1_revision_path": p1_revision_path,
        "p1_coaching_path": p1_coaching_path,
        "p2_wrapper_path": p2_wrapper_path,
        "p3_wrapper_path": p3_wrapper_path,
        "hints_path": hints_path,
        "hints": hints,
        "cues": cues,
        "frames": frames,
    }


def _run_root(root: Path, condition: str, model: str, clip_id: str) -> Path:
    return (
        root / "output/v0.4/prompt_chain" / condition / VARIANT
        / model.replace(":", "_") / clip_id
    )


def existing_cells(root: Path, prepared: dict[str, Any]) -> list[str]:
    """List cells already attempted; never silently rerun them."""
    batch = prepared["batch"]
    found = []
    for clip_id in batch["clip_ids_in_order"]:
        for condition in CONDITIONS:
            cell_root = _run_root(root, condition, batch["model"], clip_id)
            if cell_root.is_dir() and any(cell_root.iterdir()):
                found.append(f"{condition}/{clip_id}")
    for clip_id in batch["p1_initial_only_clip_ids"]:
        cell_root = _run_root(root, P1_METHOD, batch["model"], clip_id)
        if cell_root.is_dir() and any(cell_root.iterdir()):
            found.append(f"{P1_METHOD}/{clip_id}")
    return found


def _cpu_status(
    client: OllamaClient, model: str, options: dict, digest: str, *, preload: bool = True
) -> dict:
    status = client.gpu_status(model, options, preload=preload)
    if status["digest"] != digest or status["size_vram_bytes"] != 0:
        raise RuntimeError("CPU-only preflight failed: model digest or GPU residency changed")
    return status


def _save_stage(
    root: Path,
    run_dir: Path,
    stage: int,
    messages: list[PromptMessage],
    client: OllamaClient,
    model: str,
    generation: dict,
    digest: str,
    metadata: dict,
) -> str:
    prefix = f"stage_{stage}"
    prompt_path = run_dir / f"{prefix}_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, root), encoding="utf-8")
    metadata[f"{prefix}_prompt_sha256"] = sha256_file(prompt_path)
    metadata["run_status"] = f"{prefix}_started"
    write_metadata(run_dir / "metadata.txt", metadata)
    options = dict(generation["options"])
    metadata[f"{prefix}_cpu_preflight"] = _cpu_status(client, model, options, digest)
    write_metadata(run_dir / "metadata.txt", metadata)
    started = perf_counter()
    raw = client.chat(model, messages, options, bool(generation["think"]))
    answer = response_text(raw)
    write_json(run_dir / f"{prefix}_raw_api_response.json", raw)
    response_path = run_dir / f"{prefix}_response.txt"
    response_path.write_text(answer, encoding="utf-8")
    metadata[f"{prefix}_response_sha256"] = sha256_file(response_path)
    metadata[f"{prefix}_elapsed_seconds"] = perf_counter() - started
    issues = heading_issues(answer, RECOGNITION_HEADINGS)
    metadata[f"{prefix}_format_status"] = "valid" if not issues else "invalid"
    metadata[f"{prefix}_format_issues"] = issues
    metadata["run_status"] = f"{prefix}_complete"
    write_metadata(run_dir / "metadata.txt", metadata)
    if not answer.strip():
        raise ValueError(f"{prefix} answer is empty; preserved but cannot continue")
    return answer


def run_fixed_cell(
    root: Path,
    prepared: dict[str, Any],
    clip_id: str,
    condition: str,
    client: OllamaClient,
    digest: str,
) -> Path:
    """One fresh condition; no cross-condition answers, reviews, or coaching."""
    batch = prepared["batch"]
    cell_root = _run_root(root, condition, batch["model"], clip_id)
    if cell_root.is_dir() and any(cell_root.iterdir()):
        raise ValueError(f"Cell already attempted; will not rerun: {condition}/{clip_id}")
    run_dir = cell_root / timestamp_utc()
    run_dir.mkdir(parents=True, exist_ok=False)
    frames = prepared["frames"][clip_id]
    generation = prepared["generation"]
    recognition = prepared["recognition_path"].read_text(encoding="utf-8")
    metadata: dict[str, Any] = {
        "protocol_id": batch["protocol_id"],
        "method": condition,
        "method_revision": VARIANT,
        "dataset_b_clip_id": clip_id,
        "dataset_b_split": "train",
        "development_only": True,
        "hidden_b_action_used_for_selection": True,
        "hidden_b_action_sent_to_model": False,
        "human_intervention_inside_run": False,
        "human_authored_visible_cues_sent": condition == "P3_visible_cue_hint",
        "coaching_requested": False,
        "frame_sha256": {
            image.relative_to(root).as_posix(): sha256_file(image) for image in frames
        },
        "frame_set_sha256": frame_set_sha256(frames),
        "batch_config_sha256": sha256_file(prepared["batch_path"]),
        "selection_manifest_sha256": sha256_file(prepared["selection_path"]),
        "device_config_sha256": sha256_file(prepared["device_path"]),
        "recognition_prompt_sha256": sha256_file(prepared["recognition_path"]),
        "model": batch["model"],
        "model_digest": digest,
        "generation": generation,
        "created_at_utc": timestamp_utc(),
        "run_status": "started",
    }
    if condition == "P2_attention_hint":
        metadata["fixed_hints_sha256"] = sha256_file(prepared["hints_path"])
        metadata["hint_wrapper_sha256"] = sha256_file(prepared["p2_wrapper_path"])
    else:
        metadata["frozen_cue_sha256"] = sha256_file(prepared["cues"][clip_id])
        metadata["cue_wrapper_sha256"] = sha256_file(prepared["p3_wrapper_path"])
    write_metadata(run_dir / "metadata.txt", metadata)
    try:
        first = _save_stage(
            root, run_dir, 1, recognition_messages(recognition, frames), client,
            batch["model"], generation, digest, metadata,
        )
        if condition == "P2_attention_hint":
            wrapper = prepared["p2_wrapper_path"].read_text(encoding="utf-8").rstrip()
            answers = [first]
            sent_prompts = []
            for number, hint in enumerate(prepared["hints"], start=2):
                prompt = f"{wrapper}\n\n{hint}\n"
                messages = progressive_messages(
                    recognition, frames, answers, sent_prompts, next_prompt=prompt
                )
                answers.append(
                    _save_stage(
                        root, run_dir, number, messages, client, batch["model"],
                        generation, digest, metadata,
                    )
                )
                sent_prompts.append(prompt)
        else:
            wrapper = prepared["p3_wrapper_path"].read_text(encoding="utf-8").rstrip()
            cues = prepared["cues"][clip_id].read_text(encoding="utf-8").strip()
            messages = revision_messages(recognition, frames, first, f"{wrapper}\n\n{cues}\n")
            _save_stage(
                root, run_dir, 2, messages, client, batch["model"], generation,
                digest, metadata,
            )
        metadata["run_status"] = "awaiting_human_review_before_coaching"
        write_metadata(run_dir / "metadata.txt", metadata)
    except Exception as error:
        metadata["run_status"] = "error"
        write_json(
            run_dir / "error.json",
            {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc(),
            },
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    return run_dir


def run_p1_initial_cell(
    root: Path,
    prepared: dict[str, Any],
    clip_id: str,
    client: OllamaClient,
    digest: str,
) -> Path:
    """Create a resumable P1 Stage 1 run, with no feedback or coaching."""
    batch = prepared["batch"]
    if clip_id not in batch["p1_initial_only_clip_ids"]:
        raise ValueError("P1 first-pass clip is not approved or was already run")
    cell_root = _run_root(root, P1_METHOD, batch["model"], clip_id)
    if cell_root.is_dir() and any(cell_root.iterdir()):
        raise ValueError(f"P1 initial-only cell already attempted: {clip_id}")
    created = timestamp_utc()
    run_dir = cell_root / created
    run_dir.mkdir(parents=True, exist_ok=False)
    frames = prepared["frames"][clip_id]
    device = prepared["device"]
    generation = prepared["generation"]
    messages = recognition_messages(
        prepared["recognition_path"].read_text(encoding="utf-8"), frames
    )
    prompt_path = run_dir / "stage_1_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, root), encoding="utf-8")
    metadata: dict[str, Any] = {
        "protocol_id": batch["protocol_id"],
        "parent_protocol_id": device["parent_protocol_id"],
        "method": P1_METHOD,
        "method_revision": "remote_initial_only_v1",
        "dataset_b_clip_id": clip_id,
        "dataset_b_split": "train",
        "development_only": True,
        "hidden_b_action_sent_to_model": False,
        "hidden_b_action_used_for_selection": True,
        "selection_manifest_sha256": sha256_file(prepared["selection_path"]),
        "human_intervention_inside_run": True,
        "human_assisted": True,
        "dataset_a_material_sent_to_model": False,
        "dataset_b_frame_count": 30,
        "dataset_b_frame_indices_1_based": [
            int(image.stem.rsplit("_", 1)[1]) for image in frames
        ],
        "maximum_edge": device["sampling"]["maximum_edge"],
        "sampling_algorithm": device["sampling"]["algorithm"],
        "image_construction": device["sampling"]["image_encoding"],
        "frame_sha256": {
            image.relative_to(root).as_posix(): sha256_file(image) for image in frames
        },
        "frame_set_sha256": frame_set_sha256(frames),
        "config_sha256": sha256_file(prepared["device_path"]),
        "cohort_sha256": sha256_file(prepared["cohort_path"]),
        "human_reference_sha256": batch["p1_local_reference_sha256"][clip_id],
        "recognition_prompt_sha256": sha256_file(prepared["recognition_path"]),
        "revision_prompt_sha256": sha256_file(prepared["p1_revision_path"]),
        "coaching_prompt_sha256": sha256_file(prepared["p1_coaching_path"]),
        "batch_config_sha256": sha256_file(prepared["batch_path"]),
        "model": batch["model"],
        "model_digest": digest,
        "generation": generation,
        "run_status": "started",
        "created_at_utc": created,
    }
    write_metadata(run_dir / "metadata.txt", metadata)
    current_stage = "stage_1_gpu_preflight"
    total_started = perf_counter()
    try:
        options = dict(generation["options"])
        metadata["stage_1_gpu_preflight"] = _cpu_status(client, batch["model"], options, digest)
        write_metadata(run_dir / "metadata.txt", metadata)
        current_stage = "stage_1_recognition"
        recognition_started = perf_counter()
        raw = client.chat(batch["model"], messages, options, bool(generation["think"]))
        recognition_seconds = perf_counter() - recognition_started
        answer = response_text(raw)
        response_path = run_dir / "stage_1_response.txt"
        response_path.write_text(answer, encoding="utf-8")
        write_json(run_dir / "stage_1_raw_api_response.json", raw)
        current_stage = "stage_1_gpu_postcheck"
        metadata["stage_1_gpu_postcheck"] = _cpu_status(
            client, batch["model"], options, digest, preload=False
        )
        issues = heading_issues(answer, RECOGNITION_HEADINGS)
        metadata.update(
            run_status="awaiting_human_review",
            stage_1_elapsed_seconds=recognition_seconds,
            elapsed_seconds=perf_counter() - total_started,
            stage_1_format_status="valid" if not issues else "invalid",
            stage_1_format_issues=issues,
        )
        write_json(run_dir / "initial_review.json", pending_guided_review())
        write_metadata(run_dir / "metadata.txt", metadata)
    except Exception as error:
        metadata.update(
            run_status="crash",
            crash_stage=current_stage,
            error_type=type(error).__name__,
            error_message=str(error),
            elapsed_seconds=perf_counter() - total_started,
        )
        write_json(
            run_dir / "error.json",
            {"stage": current_stage, "type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    return run_dir


def run_fixed_batch(
    root: Path,
    prepared: dict[str, Any],
    on_cell: Callable[[Path], None] | None = None,
) -> list[Path]:
    """Run two P1 first passes, then six fixed cells; never request coaching."""
    if existing_cells(root, prepared):
        raise ValueError("Fixed batch has attempted cells; inspect them before another run")
    load_dotenv(root / ".env")
    client = OllamaClient()
    model = prepared["batch"]["model"]
    digest = client.model_metadata(model).get("digest")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("Ollama did not provide a full model digest")
    _cpu_status(client, model, prepared["generation"]["options"], digest)
    completed = []
    for clip_id in prepared["batch"]["p1_initial_only_clip_ids"]:
        run_dir = run_p1_initial_cell(root, prepared, clip_id, client, digest)
        completed.append(run_dir)
        if on_cell is not None:
            on_cell(run_dir)
    for clip_id in prepared["batch"]["clip_ids_in_order"]:
        for condition in CONDITIONS:
            run_dir = run_fixed_cell(root, prepared, clip_id, condition, client, digest)
            completed.append(run_dir)
            if on_cell is not None:
                on_cell(run_dir)
    return completed
