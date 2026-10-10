"""Portable CPU-only P1 follow-up with isolated coaching for B-TRAIN-0040.

The workstation never receives private SoccerNet labels or human-reference content.
Every source file and sampled image is checked before any model request.
"""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from shutil import copy2
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

from .fixed_development import validate_fixed_batch
from .ollama_client import OllamaClient
from .prompting import PromptMessage, readable_transcript
from .provenance import sha256_file, timestamp_utc
from .staged_prompting import (
    COACHING_HEADINGS,
    RECOGNITION_HEADINGS,
    coaching_messages,
    feedback_text,
    heading_issues,
    pending_guided_review,
    progressive_messages,
    read_metadata,
    response_text,
    validate_review,
    write_json,
    write_metadata,
)

VARIANT = "portable_p1_followup_v2"
PLAN = (
    ("B-TRAIN-0040", "focused_coaching"),
    ("B-TRAIN-0051", "standard_coaching"),
    ("B-TRAIN-0054", "explicit_recognition_revision"),
)
COMMON_SOURCE_FILES = (
    "metadata.txt",
    "stage_1_prompt.txt",
    "stage_1_response.txt",
    "stage_1_raw_api_response.json",
    "initial_review.json",
    "initial_review_snapshot.json",
    "human_feedback.txt",
    "stage_2_revision_prompt.txt",
    "stage_2_revision_response.txt",
    "stage_2_revision_raw_api_response.json",
    "revision_review.json",
)


def validate_remote_followup(root: Path, manifest_path: Path) -> tuple[dict, list[dict]]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_relative_to(root / "artifacts/transfer"):
        raise ValueError("Portable follow-up manifest must be in artifacts/transfer")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    batch_path = root / "config/fixed_unattended_development_v0.4.3.json"
    prepared = validate_fixed_batch(root, batch_path)
    extension_path = root / "config/p1_multi_revision_extension_v0.4.4.json"
    extension = json.loads(extension_path.read_text(encoding="utf-8"))
    if (
        manifest.get("variant") != VARIANT
        or manifest.get("batch_sha256") != sha256_file(batch_path)
        or manifest.get("config_sha256") != sha256_file(prepared["device_path"])
        or manifest.get("extension_sha256") != sha256_file(extension_path)
        or extension.get("extension_id") != "P1_multi_revision_development_v0.4.4"
        or extension.get("maximum_recognition_revisions") != 3
        or [(entry.get("clip_id"), entry.get("action")) for entry in manifest.get("runs", [])]
        != list(PLAN)
    ):
        raise ValueError("Portable P1 follow-up declaration or frozen inputs changed")

    checked: list[dict] = []
    for entry in manifest["runs"]:
        clip_id = entry["clip_id"]
        action = entry["action"]
        relative_run = entry.get("run_dir")
        if not isinstance(relative_run, str):
            raise ValueError("Missing portable run path")
        run_dir = (root / relative_run).resolve()
        p1_root = root / "output/v0.4/prompt_chain/P1_human_guided"
        if action == "focused_coaching":
            expected_run = root / "artifacts/transfer/p1_followup_b40_clean_source"
            retry_relative = entry.get("retry_run_dir")
            if not isinstance(retry_relative, str):
                raise ValueError("Missing B-TRAIN-0040 retry destination")
            retry_dir = (root / retry_relative).resolve()
            retry_parent = p1_root / "portable_followup_v2/qwen3.5_27b" / clip_id
            if retry_dir.parent != retry_parent or retry_dir.exists():
                raise ValueError("B-TRAIN-0040 retry path is not new and isolated")
        else:
            expected_run = (
                p1_root / "qwen3.5_27b" / clip_id / run_dir.name
                if clip_id == "B-TRAIN-0054"
                else p1_root / "fixed_unattended_v2/qwen3.5_27b" / clip_id / run_dir.name
            )
            retry_dir = run_dir
        if run_dir != expected_run:
            raise ValueError(f"Unexpected P1 run location: {clip_id}")
        expected_files = set(COMMON_SOURCE_FILES)
        if action == "focused_coaching":
            expected_files.add("coaching_focus.txt")
        hashes = entry.get("source_sha256")
        if not isinstance(hashes, dict) or set(hashes) != expected_files:
            raise ValueError(f"Incomplete source hashes for {clip_id}")
        for filename, expected in hashes.items():
            path = run_dir / filename
            if not path.is_file() or sha256_file(path) != expected:
                raise ValueError(f"Preserved P1 source changed: {clip_id}/{filename}")
        forbidden = (
            "stage_3_coaching_prompt.txt", "stage_3_coaching_response.txt",
            "stage_3_coaching_raw_api_response.json", "stage_3_revision_prompt.txt",
            "stage_3_revision_response.txt", "stage_3_revision_raw_api_response.json",
            "stage_3_error.json", "revision_review_snapshot.json",
            "revision_review_2.json", "human_feedback_2.txt",
        )
        if any((run_dir / name).exists() for name in forbidden):
            raise ValueError(f"P1 follow-up already attempted: {clip_id}")
        metadata = read_metadata(run_dir / "metadata.txt")
        if (
            metadata.get("protocol_id") != prepared["batch"]["protocol_id"]
            or metadata.get("method") != "P1_human_guided"
            or metadata.get("dataset_b_clip_id") != clip_id
            or metadata.get("dataset_b_split") != "train"
            or metadata.get("run_status") != "awaiting_revision_approval"
            or metadata.get("model") != prepared["batch"]["model"]
            or not isinstance(metadata.get("model_digest"), str)
            or len(metadata["model_digest"]) != 64
            or metadata.get("generation") != prepared["device"]["generation"]
            or metadata.get("config_sha256") != sha256_file(prepared["device_path"])
            or metadata.get("cohort_sha256") != sha256_file(prepared["cohort_path"])
            or metadata.get("selection_manifest_sha256")
            != sha256_file(prepared["selection_path"])
            or metadata.get("recognition_prompt_sha256")
            != sha256_file(prepared["recognition_path"])
            or metadata.get("revision_prompt_sha256")
            != sha256_file(prepared["p1_revision_path"])
            or metadata.get("coaching_prompt_sha256")
            != sha256_file(prepared["p1_coaching_path"])
            or metadata.get("human_reference_sha256") != entry.get("human_reference_sha256")
            or metadata.get("initial_review_sha256") != sha256_file(run_dir / "initial_review.json")
            or metadata.get("human_feedback_sha256") != sha256_file(run_dir / "human_feedback.txt")
        ):
            raise ValueError(f"P1 metadata or prompt provenance changed: {clip_id}")
        frozen_reference = prepared["batch"].get("p1_local_reference_sha256", {}).get(clip_id)
        if frozen_reference is not None and entry["human_reference_sha256"] != frozen_reference:
            raise ValueError(f"Frozen human reference hash changed: {clip_id}")
        images = prepared["frames"][clip_id]
        if metadata.get("frame_sha256") != {
            image.relative_to(root).as_posix(): sha256_file(image) for image in images
        }:
            raise ValueError(f"P1 sampled images changed: {clip_id}")
        for stage, name in ((1, "stage_1"), (2, "stage_2_revision")):
            answer = (run_dir / f"{name}_response.txt").read_text(encoding="utf-8")
            raw = json.loads((run_dir / f"{name}_raw_api_response.json").read_text(
                encoding="utf-8"
            ))
            if answer != response_text(raw):
                raise ValueError(f"P1 stage {stage} answer differs from raw response: {clip_id}")
        review = json.loads((run_dir / "revision_review.json").read_text(encoding="utf-8"))
        decision = validate_review(review, set(range(1, 31)), revised=True)
        expected_decision = "reject" if action == "explicit_recognition_revision" else "approve"
        if decision != expected_decision:
            raise ValueError(f"P1 review decision does not match declared action: {clip_id}")
        if action == "focused_coaching":
            focus_path = run_dir / "coaching_focus.txt"
            focus = focus_path.read_text(encoding="utf-8").strip()
            if not focus:
                raise ValueError("B-TRAIN-0040 coaching focus is empty")
        checked.append({
            "clip_id": clip_id, "action": action, "run_dir": run_dir,
            "output_dir": retry_dir, "metadata": metadata,
            "review": review, "images": images,
        })
    return prepared, checked


def _cpu_check(client: OllamaClient, model: str, options: dict, digest: str, *, preload: bool) -> dict:
    status = client.gpu_status(model, options, preload=preload)
    if status.get("digest") != digest or status.get("size_vram_bytes") != 0:
        raise RuntimeError("P1 CPU-only model placement or digest changed")
    return status


def run_remote_followup(root: Path, manifest_path: Path) -> list[Path]:
    prepared, checked = validate_remote_followup(root, manifest_path)
    root = root.resolve()
    manifest_sha256 = sha256_file(manifest_path)
    extension_sha256 = sha256_file(root / "config/p1_multi_revision_extension_v0.4.4.json")
    recognition = prepared["recognition_path"].read_text(encoding="utf-8")
    revision = prepared["p1_revision_path"].read_text(encoding="utf-8")
    coaching = prepared["p1_coaching_path"].read_text(encoding="utf-8")
    config = prepared["device"]
    options = dict(config["generation"]["options"])
    load_dotenv(root / ".env")
    client = OllamaClient()
    completed = []
    for item in checked:
        clip_id = item["clip_id"]
        source_dir = item["run_dir"]
        run_dir = item["output_dir"]
        metadata = item["metadata"]
        review = dict(item["review"])
        review.update(decision=(
            "reject" if item["action"] == "explicit_recognition_revision" else "approve"
        ), submitted_at_utc=timestamp_utc())
        first = (source_dir / "stage_1_response.txt").read_text(encoding="utf-8")
        second = (source_dir / "stage_2_revision_response.txt").read_text(encoding="utf-8")
        first_feedback = (source_dir / "human_feedback.txt").read_text(encoding="utf-8")
        if item["action"] == "focused_coaching":
            run_dir.mkdir(parents=True, exist_ok=False)
            for filename in (*COMMON_SOURCE_FILES, "coaching_focus.txt"):
                copy2(source_dir / filename, run_dir / filename)
            metadata.update(
                isolated_followup_source="output/v0.4/prompt_chain/P1_human_guided/"
                "fixed_unattended_v2/qwen3.5_27b/B-TRAIN-0040/20260930T104115914624Z",
                isolated_followup_source_metadata_sha256=sha256_file(source_dir / "metadata.txt"),
            )

        if item["action"] == "explicit_recognition_revision":
            second_feedback = feedback_text(review, revision)
            messages = progressive_messages(
                recognition, item["images"], [first, second],
                [first_feedback], second_feedback,
            )
            write_json(run_dir / "revision_review_snapshot.json", review)
            (run_dir / "human_feedback_2.txt").write_text(
                second_feedback, encoding="utf-8"
            )
            metadata.update(
                p1_extension_id="P1_multi_revision_development_v0.4.4",
                p1_extension_config_sha256=extension_sha256,
                p1_prior_revision_reviews=[{
                    "review_file": "revision_review.json",
                    "review_sha256": sha256_file(run_dir / "revision_review.json"),
                    "feedback_file": "human_feedback_2.txt",
                    "feedback_sha256": sha256_file(run_dir / "human_feedback_2.txt"),
                    "submitted_at_utc": review["submitted_at_utc"],
                }],
                p1_revision_count=2,
            )
            answer_name = "stage_3_revision_response.txt"
            raw_name = "stage_3_revision_raw_api_response.json"
            headings = RECOGNITION_HEADINGS
        else:
            messages = coaching_messages(
                recognition, item["images"], first, coaching,
                first_feedback, second,
            )
            if item["action"] == "focused_coaching":
                focus = (run_dir / "coaching_focus.txt").read_text(encoding="utf-8").strip()
                if not focus:
                    raise ValueError("B-TRAIN-0040 coaching focus is empty")
                messages[-1] = PromptMessage(
                    "user", messages[-1].content + "\n\nDEVELOPMENT COACHING FOCUS\n" + focus + "\n"
                )
                metadata.update(
                    coaching_variant="P1_researcher_focused_development",
                    coaching_focus_file="coaching_focus.txt",
                    coaching_focus_sha256=sha256_file(run_dir / "coaching_focus.txt"),
                )
            write_json(run_dir / "revision_review_snapshot.json", review)
            metadata.update(
                revision_review_sha256=sha256_file(run_dir / "revision_review.json"),
                revision_review_file="revision_review.json",
                revision_review_decision="approve",
                revision_review_submitted_at_utc=review["submitted_at_utc"],
            )
            answer_name = "stage_3_coaching_response.txt"
            raw_name = "stage_3_coaching_raw_api_response.json"
            headings = COACHING_HEADINGS
        prompt_name = (
            "stage_3_revision_prompt.txt" if headings == RECOGNITION_HEADINGS
            else "stage_3_coaching_prompt.txt"
        )
        (run_dir / prompt_name).write_text(
            readable_transcript(messages, root), encoding="utf-8"
        )
        metadata.update(
            portable_followup_variant=VARIANT,
            portable_manifest_sha256=manifest_sha256,
            private_reference_verified_remotely=False,
            run_status=(
                "revision_started" if headings == RECOGNITION_HEADINGS else "coaching_started"
            ),
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        started = perf_counter()
        try:
            if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
                raise ValueError("Installed model digest differs from P1 recognition")
            metadata["stage_3_gpu_preflight"] = _cpu_check(
                client, metadata["model"], options, metadata["model_digest"], preload=True
            )
            write_metadata(run_dir / "metadata.txt", metadata)
            raw = client.chat(
                metadata["model"], messages, options,
                bool(config["generation"]["think"]),
            )
            answer = response_text(raw)
            (run_dir / answer_name).write_text(answer, encoding="utf-8")
            write_json(run_dir / raw_name, raw)
            metadata["stage_3_gpu_postcheck"] = _cpu_check(
                client, metadata["model"], options, metadata["model_digest"], preload=False
            )
        except Exception as error:
            metadata.update(
                run_status="crash", crash_stage=answer_name,
                error_type=type(error).__name__, error_message=str(error),
                stage_3_elapsed_seconds=perf_counter() - started,
            )
            write_json(run_dir / "stage_3_error.json", {
                "type": type(error).__name__, "message": str(error),
                "traceback": traceback.format_exc(),
            })
            write_metadata(run_dir / "metadata.txt", metadata)
            raise
        issues = heading_issues(answer, headings)
        metadata.update(
            run_status=(
                "awaiting_revision_approval" if headings == RECOGNITION_HEADINGS else "complete"
            ),
            stage_3_elapsed_seconds=perf_counter() - started,
            stage_3_format_status="valid" if not issues else "invalid",
            stage_3_format_issues=issues,
        )
        if headings == RECOGNITION_HEADINGS:
            write_json(run_dir / "revision_review_2.json", pending_guided_review())
        write_metadata(run_dir / "metadata.txt", metadata)
        completed.append(run_dir)
        print(f"Preserved {item['action']}: {run_dir}", flush=True)
    return completed


def main() -> None:
    parser = argparse.ArgumentParser(description="Portable CPU-only P1 follow-up")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    _, checked = validate_remote_followup(root, args.manifest)
    print(f"Validated {len(checked)} P1 follow-up cells; no model calls yet.", flush=True)
    if not args.validate_only:
        run_remote_followup(root, args.manifest)
        print("P1 follow-up finished. Review every answer before further action.", flush=True)


if __name__ == "__main__":
    main()
