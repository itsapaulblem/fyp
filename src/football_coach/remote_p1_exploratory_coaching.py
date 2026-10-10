"""Isolated 0054 coaching diagnostic after recognition was not approved.

This is deliberately not a successful P1 coaching cell. The original P1 run
and its pending review remain untouched.
"""

from __future__ import annotations

import argparse
import json
import traceback
from pathlib import Path
from shutil import copy2
from time import perf_counter

from dotenv import load_dotenv

from .fixed_development import validate_fixed_batch
from .ollama_client import OllamaClient
from .prompting import readable_transcript
from .provenance import sha256_file
from .staged_prompting import (
    COACHING_HEADINGS,
    heading_issues,
    progressive_messages,
    read_metadata,
    response_text,
    write_json,
    write_metadata,
)

VARIANT = "p1_unapproved_recognition_coaching_probe_v1"
SOURCE_RELATIVE = (
    "output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/"
    "B-TRAIN-0054/20260930T083320329816Z"
)
OUTPUT_PARENT = (
    "output/v0.4/prompt_chain/P1_human_guided/"
    "exploratory_unapproved_recognition_v1/qwen3.5_27b/B-TRAIN-0054"
)
SOURCE_FILES = (
    "metadata.txt",
    "stage_1_prompt.txt", "stage_1_response.txt", "stage_1_raw_api_response.json",
    "initial_review.json", "initial_review_snapshot.json", "human_feedback.txt",
    "stage_2_revision_prompt.txt", "stage_2_revision_response.txt",
    "stage_2_revision_raw_api_response.json", "revision_review.json",
    "revision_review_snapshot.json", "human_feedback_2.txt",
    "stage_3_revision_prompt.txt", "stage_3_revision_response.txt",
    "stage_3_revision_raw_api_response.json", "revision_review_2.json",
)


def validate_probe(root: Path, manifest_path: Path) -> tuple[dict, dict]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_relative_to(root / "artifacts/transfer"):
        raise ValueError("Probe manifest must be in artifacts/transfer")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prepared = validate_fixed_batch(
        root, root / "config/fixed_unattended_development_v0.4.3.json"
    )
    source = (root / SOURCE_RELATIVE).resolve()
    output = (root / manifest.get("output_dir", "")).resolve()
    if (
        manifest.get("variant") != VARIANT
        or manifest.get("source_dir") != SOURCE_RELATIVE
        or manifest.get("batch_sha256") != sha256_file(prepared["batch_path"])
        or manifest.get("config_sha256") != sha256_file(prepared["device_path"])
        or manifest.get("coaching_prompt_sha256")
        != sha256_file(prepared["p1_coaching_path"])
        or output.parent != (root / OUTPUT_PARENT).resolve()
        or output.exists()
        or set(manifest.get("source_sha256", {})) != set(SOURCE_FILES)
    ):
        raise ValueError("Invalid or already attempted exploratory coaching declaration")
    for name, expected_hash in manifest["source_sha256"].items():
        path = source / name
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise ValueError(f"P1 recognition source changed: {name}")
    metadata = read_metadata(source / "metadata.txt")
    if (
        metadata.get("protocol_id") != prepared["batch"]["protocol_id"]
        or metadata.get("method") != "P1_human_guided"
        or metadata.get("dataset_b_clip_id") != "B-TRAIN-0054"
        or metadata.get("dataset_b_split") != "train"
        or metadata.get("run_status") != "awaiting_revision_approval"
        or metadata.get("p1_revision_count") != 2
        or metadata.get("model") != prepared["batch"]["model"]
        or metadata.get("generation") != prepared["device"]["generation"]
        or metadata.get("config_sha256") != sha256_file(prepared["device_path"])
        or metadata.get("coaching_prompt_sha256")
        != sha256_file(prepared["p1_coaching_path"])
        or metadata.get("frame_sha256") != {
            image.relative_to(root).as_posix(): sha256_file(image)
            for image in prepared["frames"]["B-TRAIN-0054"]
        }
    ):
        raise ValueError("0054 recognition provenance changed")
    review = json.loads((source / "revision_review_2.json").read_text(encoding="utf-8"))
    if review != {"feedback": [], "notes": "PENDING_REVIEW"}:
        raise ValueError("0054 review changed; this probe requires unapproved recognition")
    answers = []
    for stage, prefix in ((1, "stage_1"), (2, "stage_2_revision"), (3, "stage_3_revision")):
        answer = (source / f"{prefix}_response.txt").read_text(encoding="utf-8")
        raw = json.loads((source / f"{prefix}_raw_api_response.json").read_text(
            encoding="utf-8"
        ))
        if answer != response_text(raw):
            raise ValueError(f"0054 stage {stage} answer differs from raw response")
        answers.append(answer)
    if any((source / name).exists() for name in (
        "stage_4_coaching_prompt.txt", "stage_4_coaching_response.txt"
    )):
        raise ValueError("Original P1 run already attempted coaching")
    return prepared, {"source": source, "output": output, "metadata": metadata,
                      "answers": answers, "manifest": manifest}


def run_probe(root: Path, manifest_path: Path) -> Path:
    prepared, checked = validate_probe(root, manifest_path)
    root = root.resolve()
    source: Path = checked["source"]
    output: Path = checked["output"]
    metadata = checked["metadata"]
    output.mkdir(parents=True, exist_ok=False)
    for name in SOURCE_FILES:
        copy2(source / name, output / name)
    messages = progressive_messages(
        prepared["recognition_path"].read_text(encoding="utf-8"),
        prepared["frames"]["B-TRAIN-0054"],
        checked["answers"],
        [(source / "human_feedback.txt").read_text(encoding="utf-8"),
         (source / "human_feedback_2.txt").read_text(encoding="utf-8")],
        prepared["p1_coaching_path"].read_text(encoding="utf-8"),
    )
    (output / "stage_4_coaching_prompt.txt").write_text(
        readable_transcript(messages, root), encoding="utf-8"
    )
    metadata.update(
        method_variant=VARIANT,
        source_p1_run=SOURCE_RELATIVE,
        source_metadata_sha256=sha256_file(source / "metadata.txt"),
        probe_manifest_sha256=sha256_file(manifest_path),
        recognition_approved=False,
        coaching_gate_override="Researcher-requested exploratory output; not a P1 success",
        run_status="exploratory_coaching_started",
    )
    write_metadata(output / "metadata.txt", metadata)
    options = dict(prepared["device"]["generation"]["options"])
    load_dotenv(root / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from recognition run")
        preflight = client.gpu_status(metadata["model"], options, preload=True)
        if preflight.get("digest") != metadata["model_digest"] or preflight.get("size_vram_bytes") != 0:
            raise RuntimeError("CPU-only model placement or digest changed")
        metadata["stage_4_gpu_preflight"] = preflight
        write_metadata(output / "metadata.txt", metadata)
        raw = client.chat(
            metadata["model"], messages, options,
            bool(prepared["device"]["generation"]["think"]),
        )
        answer = response_text(raw)
        (output / "stage_4_coaching_response.txt").write_text(answer, encoding="utf-8")
        write_json(output / "stage_4_coaching_raw_api_response.json", raw)
        postcheck = client.gpu_status(metadata["model"], options, preload=False)
        if postcheck.get("digest") != metadata["model_digest"] or postcheck.get("size_vram_bytes") != 0:
            raise RuntimeError("CPU-only postcheck or model digest changed")
        metadata["stage_4_gpu_postcheck"] = postcheck
    except Exception as error:
        metadata.update(run_status="crash", stage_4_elapsed_seconds=perf_counter() - started,
                        error_type=type(error).__name__, error_message=str(error))
        write_json(output / "stage_4_error.json", {
            "type": type(error).__name__, "message": str(error),
            "traceback": traceback.format_exc(),
        })
        write_metadata(output / "metadata.txt", metadata)
        raise
    issues = heading_issues(answer, COACHING_HEADINGS)
    metadata.update(
        run_status="exploratory_coaching_complete",
        stage_4_elapsed_seconds=perf_counter() - started,
        stage_4_format_status="valid" if not issues else "invalid",
        stage_4_format_issues=issues,
    )
    write_metadata(output / "metadata.txt", metadata)
    print(f"Preserved unapproved-recognition coaching probe: {output}", flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="0054 exploratory coaching after unapproved recognition")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    validate_probe(root, args.manifest)
    print("Validated 0054 exploratory coaching probe; no model call yet.", flush=True)
    if not args.validate_only:
        run_probe(root, args.manifest)
        print("0054 exploratory coaching probe finished; review before use.", flush=True)


if __name__ == "__main__":
    main()
