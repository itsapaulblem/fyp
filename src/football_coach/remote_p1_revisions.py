"""Portable P1 recognition revisions without copying private reference labels."""

from __future__ import annotations

import json
import traceback
from pathlib import Path
from time import perf_counter
from typing import Any

from dotenv import load_dotenv

from .fixed_development import validate_fixed_batch
from .ollama_client import OllamaClient
from .prompting import readable_transcript
from .provenance import sha256_file, timestamp_utc
from .staged_prompting import (
    RECOGNITION_HEADINGS,
    feedback_text,
    heading_issues,
    pending_guided_review,
    read_metadata,
    response_text,
    revision_messages,
    validate_review,
    write_json,
    write_metadata,
)

CLIP_ORDER = ("B-TRAIN-0040", "B-TRAIN-0051", "B-TRAIN-0054")
VARIANT = "portable_p1_revisions_v1"
SOURCE_FILES = (
    "metadata.txt",
    "stage_1_prompt.txt",
    "stage_1_response.txt",
    "stage_1_raw_api_response.json",
    "initial_review.json",
)


def validate_remote_p1_revisions(root: Path, manifest_path: Path) -> list[dict[str, Any]]:
    """Verify every imported first pass before permitting any model call.

    Private human references are checked against their recorded local hashes,
    not copied to or read on the workstation. This is a narrower verification
    than the ordinary local P1 command and is recorded in the revision metadata.
    """
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_relative_to(root / "artifacts/transfer"):
        raise ValueError("Portable manifest must be under artifacts/transfer")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    batch_path = root / "config/fixed_unattended_development_v0.4.3.json"
    prepared = validate_fixed_batch(root, batch_path)
    batch = prepared["batch"]
    if (
        manifest.get("variant") != VARIANT
        or manifest.get("batch_sha256") != sha256_file(batch_path)
        or manifest.get("config_sha256") != sha256_file(prepared["device_path"])
        or not isinstance(manifest.get("runs"), list)
        or [entry.get("clip_id") for entry in manifest["runs"]] != list(CLIP_ORDER)
    ):
        raise ValueError("Portable P1 manifest differs from the approved CPU development batch")

    checked: list[dict[str, Any]] = []
    for entry in manifest["runs"]:
        clip_id = entry["clip_id"]
        relative_run = entry.get("run_dir")
        if not isinstance(relative_run, str):
            raise ValueError("Portable run path is missing")
        run_dir = (root / relative_run).resolve()
        expected_prefix = root / "output/v0.4/prompt_chain/P1_human_guided"
        if not run_dir.is_relative_to(expected_prefix):
            raise ValueError("Portable P1 run is outside P1 output")
        if clip_id in batch["p1_initial_only_clip_ids"]:
            required_parent = expected_prefix / "fixed_unattended_v2/qwen3.5_27b" / clip_id
        else:
            required_parent = expected_prefix / "qwen3.5_27b" / clip_id
        if run_dir.parent != required_parent:
            raise ValueError(f"Unexpected P1 run location for {clip_id}")
        expected_files = entry.get("source_sha256")
        if not isinstance(expected_files, dict) or set(expected_files) != set(SOURCE_FILES):
            raise ValueError(f"Incomplete frozen P1 source hashes: {clip_id}")
        for filename in SOURCE_FILES:
            path = run_dir / filename
            if not path.is_file() or sha256_file(path) != expected_files[filename]:
                raise ValueError(f"P1 source file changed: {clip_id}/{filename}")
        if any((run_dir / name).exists() for name in (
            "stage_2_revision_prompt.txt", "stage_2_revision_response.txt",
            "stage_2_revision_raw_api_response.json", "stage_2_error.json",
            "initial_review_snapshot.json", "human_feedback.txt",
        )):
            raise ValueError(f"P1 revision already attempted: {clip_id}")

        metadata = read_metadata(run_dir / "metadata.txt")
        config = prepared["device"]
        if (
            metadata.get("protocol_id") != batch["protocol_id"]
            or metadata.get("method") != "P1_human_guided"
            or metadata.get("dataset_b_clip_id") != clip_id
            or metadata.get("dataset_b_split") != "train"
            or metadata.get("run_status") != "awaiting_human_review"
            or metadata.get("model") != batch["model"]
            or not isinstance(metadata.get("model_digest"), str)
            or len(metadata["model_digest"]) != 64
            or metadata.get("config_sha256") != sha256_file(prepared["device_path"])
            or metadata.get("cohort_sha256") != sha256_file(prepared["cohort_path"])
            or metadata.get("selection_manifest_sha256") != sha256_file(prepared["selection_path"])
            or metadata.get("recognition_prompt_sha256")
            != sha256_file(prepared["recognition_path"])
            or metadata.get("revision_prompt_sha256") != sha256_file(prepared["p1_revision_path"])
            or metadata.get("coaching_prompt_sha256") != sha256_file(prepared["p1_coaching_path"])
            or metadata.get("generation") != config["generation"]
            or metadata.get("human_reference_sha256") != entry.get("human_reference_sha256")
        ):
            raise ValueError(f"P1 recorded provenance changed: {clip_id}")
        if clip_id in batch["p1_local_reference_sha256"] and (
            entry["human_reference_sha256"] != batch["p1_local_reference_sha256"][clip_id]
        ):
            raise ValueError(f"P1 frozen reference hash changed: {clip_id}")
        images = prepared["frames"][clip_id]
        expected_frame_hashes = {
            image.relative_to(root).as_posix(): sha256_file(image) for image in images
        }
        if metadata.get("frame_sha256") != expected_frame_hashes:
            raise ValueError(f"P1 sampled images changed: {clip_id}")
        if response_text(json.loads((run_dir / "stage_1_raw_api_response.json").read_text(
            encoding="utf-8"
        ))) != (run_dir / "stage_1_response.txt").read_text(encoding="utf-8"):
            raise ValueError(f"P1 first answer differs from raw API response: {clip_id}")
        review = json.loads((run_dir / "initial_review.json").read_text(encoding="utf-8"))
        if validate_review(review, set(range(1, 31))) != "revise":
            raise ValueError(f"P1 review must request a revision: {clip_id}")
        checked.append({
            "clip_id": clip_id, "run_dir": run_dir, "metadata": metadata,
            "review": review, "images": images,
        })
    return checked


def run_remote_p1_revisions(root: Path, manifest_path: Path) -> list[Path]:
    """Run the three reviewed P1 revisions sequentially; never coach or rerun."""
    checked = validate_remote_p1_revisions(root, manifest_path)
    root = root.resolve()
    manifest_sha256 = sha256_file(manifest_path)
    load_dotenv(root / ".env")
    client = OllamaClient()
    prepared = validate_fixed_batch(
        root, root / "config/fixed_unattended_development_v0.4.3.json"
    )
    config = prepared["device"]
    options = dict(config["generation"]["options"])
    recognition = prepared["recognition_path"].read_text(encoding="utf-8")
    revision = prepared["p1_revision_path"].read_text(encoding="utf-8")
    completed = []
    for item in checked:
        run_dir = item["run_dir"]
        metadata = item["metadata"]
        correction = feedback_text(item["review"], revision)
        messages = revision_messages(
            recognition, item["images"],
            (run_dir / "stage_1_response.txt").read_text(encoding="utf-8"),
            correction,
        )
        review_snapshot = dict(item["review"])
        review_snapshot.update(decision="revise", submitted_at_utc=timestamp_utc())
        write_json(run_dir / "initial_review_snapshot.json", review_snapshot)
        (run_dir / "human_feedback.txt").write_text(correction, encoding="utf-8")
        (run_dir / "stage_2_revision_prompt.txt").write_text(
            readable_transcript(messages, root), encoding="utf-8"
        )
        metadata.update(
            initial_review_sha256=sha256_file(run_dir / "initial_review.json"),
            initial_review_decision="revise",
            initial_review_submitted_at_utc=review_snapshot["submitted_at_utc"],
            human_feedback_sha256=sha256_file(run_dir / "human_feedback.txt"),
            remote_revision_variant=VARIANT,
            portable_manifest_sha256=manifest_sha256,
            private_reference_verified_remotely=False,
            run_status="revision_started",
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        started = perf_counter()
        try:
            if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
                raise ValueError("Installed model digest differs from P1 first pass")
            preflight = client.gpu_status(metadata["model"], options, preload=True)
            if (
                preflight["digest"] != metadata["model_digest"]
                or preflight["size_vram_bytes"] != 0
            ):
                raise RuntimeError("P1 CPU-only model placement or digest changed")
            metadata["stage_2_gpu_preflight"] = preflight
            write_metadata(run_dir / "metadata.txt", metadata)
            raw = client.chat(
                metadata["model"], messages, options,
                bool(config["generation"]["think"]),
            )
            answer = response_text(raw)
            (run_dir / "stage_2_revision_response.txt").write_text(answer, encoding="utf-8")
            write_json(run_dir / "stage_2_revision_raw_api_response.json", raw)
            postcheck = client.gpu_status(metadata["model"], options, preload=False)
            if (
                postcheck["digest"] != metadata["model_digest"]
                or postcheck["size_vram_bytes"] != 0
            ):
                raise RuntimeError("P1 CPU-only postcheck failed")
            metadata["stage_2_gpu_postcheck"] = postcheck
        except Exception as error:
            metadata.update(
                run_status="crash", crash_stage="recognition_revision",
                error_type=type(error).__name__, error_message=str(error),
                stage_2_elapsed_seconds=perf_counter() - started,
            )
            write_json(run_dir / "stage_2_error.json", {
                "type": type(error).__name__, "message": str(error),
                "traceback": traceback.format_exc(),
            })
            write_metadata(run_dir / "metadata.txt", metadata)
            raise
        issues = heading_issues(answer, RECOGNITION_HEADINGS)
        metadata.update(
            run_status="awaiting_revision_approval",
            stage_2_elapsed_seconds=perf_counter() - started,
            stage_2_format_status="valid" if not issues else "invalid",
            stage_2_format_issues=issues,
        )
        write_json(run_dir / "revision_review.json", pending_guided_review())
        write_metadata(run_dir / "metadata.txt", metadata)
        completed.append(run_dir)
        print(f"Preserved P1 revision: {run_dir}", flush=True)
    return completed


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Portable CPU-only P1 recognition revisions")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    checked = validate_remote_p1_revisions(root, args.manifest)
    print(f"Validated {len(checked)} P1 revision inputs; coaching is disabled.", flush=True)
    if not args.validate_only:
        run_remote_p1_revisions(root, args.manifest)
        print("P1 revisions finished. Review each answer before any coaching.", flush=True)


if __name__ == "__main__":
    main()
