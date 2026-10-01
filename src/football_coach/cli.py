from __future__ import annotations

import hashlib
import json
from pathlib import Path
from shutil import copyfile
from time import perf_counter
from typing import cast

import numpy as np
import typer
from dotenv import load_dotenv

from .catalog import initialize_case, load_case, load_library, validate_library
from .domain import CaseARecord, Condition, DatasetBHumanReference, SoccerNetClip
from .embedding import ClipFrameEncoder
from .experiment import (
    claim_test_attempt,
    create_protocol_freeze,
    create_sampling_freeze,
    expected_reference_visibility_keys,
    initialize_from_template,
    initialize_text_from_template,
    prepare_comparison_grading,
    prepare_pilot_grading,
    validate_human_pair,
    validate_human_reference,
    validate_pilot_cohort,
    validate_protocol_freeze,
    validate_sampling_candidate,
    validate_sampling_freeze,
    validate_score,
    write_json_exclusive,
)
from .experiment import (
    load_json as load_experiment_json,
)
from .fixed_development import existing_cells, run_fixed_batch, validate_fixed_batch
from .media import sample_dataset_a, sample_dataset_b
from .ollama_client import OllamaClient
from .pairing import deterministic_control_case
from .prompting import build_messages, plain_text_answer_issues, readable_transcript
from .provenance import sha256_file, timestamp_utc, write_run
from .retrieval import EmbeddingIndex
from .soccernet import (
    audit_dataset_b,
    index_dataset_b,
    read_manifest,
    write_integrity_report,
    write_private_manifest,
    write_public_manifest,
)
from .staged_prompting import (
    COACHING_HEADINGS,
    P1_METHOD,
    P2_METHOD,
    P3_METHOD,
    RECOGNITION_HEADINGS,
    coaching_messages,
    feedback_text,
    heading_issues,
    pending_guided_review,
    progressive_messages,
    read_metadata,
    recognition_messages,
    response_text,
    revision_messages,
    validate_progressive_review,
    validate_review,
    validate_visible_cue_review,
    write_json,
    write_metadata,
)

app = typer.Typer(no_args_is_help=True)
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/project_v0.3.0.json"
DEFAULT_V04_CONFIG = ROOT / "config/project_v0.4.0.json"
DEFAULT_B_MANIFEST = ROOT / "data/video_b/private/soccernet_gsr_v1.3_reference.csv"
DEFAULT_B_PUBLIC_MANIFEST = ROOT / "data/video_b/manifests/soccernet_gsr_v1.3_public.csv"
DEFAULT_B_INTEGRITY_REPORT = ROOT / "data/video_b/private/integrity_v1.3.json"
P2_ATTENTION_PROMPT = ROOT / "input_prompts/v0.4/p2_attention_hint.txt"
P2_ATTENTION_CONFIG = ROOT / "config/p2_attention_hint_v0.4.0.json"
P2_PROGRESSIVE_CONFIG = ROOT / "config/p2_progressive_hints_v0.4.1.json"
P3_VISIBLE_CONFIG = ROOT / "config/p3_visible_cues_v0.4.0.json"
DEFAULT_FIXED_BATCH = ROOT / "config/fixed_unattended_development_v0.4.3.json"


@app.command("validate-fixed-development")
def validate_fixed_development(
    batch_config: Path = typer.Option(DEFAULT_FIXED_BATCH),
) -> None:
    """Check frozen train-only P2/P3 inputs; make no Ollama calls."""
    prepared = validate_fixed_batch(ROOT, batch_config)
    attempted = existing_cells(ROOT, prepared)
    typer.echo(
        f"Validated {len(prepared['batch']['clip_ids_in_order'])} clips, "
        f"{len(prepared['hints'])} fixed hints, 3 frozen cue sheets, "
        "and 2 P1 initial-only runs."
    )
    typer.echo(f"Prior fixed cells: {', '.join(attempted) if attempted else 'none'}")


@app.command("run-fixed-development")
def run_fixed_development(
    batch_config: Path = typer.Option(DEFAULT_FIXED_BATCH),
) -> None:
    """Run fixed P2/P3 plus two P1 first passes; stop before coaching."""
    prepared = validate_fixed_batch(ROOT, batch_config)
    attempted = existing_cells(ROOT, prepared)
    if attempted:
        raise typer.BadParameter(
            "Fixed cells already attempted; inspect them before any new batch: "
            + ", ".join(attempted)
        )
    typer.echo("Starting fixed P2/P3 and P1 initial-only batch; coaching is disabled.")
    run_fixed_batch(ROOT, prepared, on_cell=lambda run_dir: typer.echo(f"Preserved: {run_dir}"))
    typer.echo("Batch finished. Review recognition before any coaching.")


def pending_progressive_review() -> dict:
    return {"decision": "PENDING", "frame_numbers_1_based": [], "hint": "", "notes": ""}


def progressive_condition(config: dict) -> tuple[dict, Path]:
    condition = load_json(P2_PROGRESSIVE_CONFIG)
    prompt_path = ROOT / condition.get("hint_prompt_path", "")
    if (
        condition.get("protocol_id") != config["protocol_id"]
        or condition.get("condition") != P2_METHOD
        or condition.get("revision") != "progressive_v1"
        or condition.get("status") != "draft_train_diagnostic"
        or condition.get("starting_point") != "fresh_recognition_from_30_frames"
        or condition.get("allowed_split") != "train"
        or condition.get("output_directory") != (
            f"{config['output_root']}/{P2_METHOD}"
        )
        or condition.get("maximum_hints") != 3
        or condition.get("human_review_after_every_recognition") is not True
        or condition.get("coaching_requires_approved_recognition") is not True
        or not prompt_path.is_file()
    ):
        raise typer.BadParameter("Invalid progressive P2 condition declaration")
    return condition, prompt_path


def visible_cue_condition(config: dict) -> tuple[dict, Path, Path]:
    condition = load_json(P3_VISIBLE_CONFIG)
    output_root = (ROOT / config["output_root"] / P3_METHOD).resolve()
    cue_path = (ROOT / condition.get("cue_sheet_path", "")).resolve()
    prompt_path = ROOT / condition.get("cue_prompt_path", "")
    if (
        condition.get("protocol_id") != config["protocol_id"]
        or condition.get("condition") != P3_METHOD
        or condition.get("revision") != "frozen_cues_v1"
        or condition.get("status") != "draft_train_diagnostic"
        or condition.get("starting_point") != "fresh_recognition_from_30_frames"
        or condition.get("allowed_split") != "train"
        or condition.get("output_directory") != f"{config['output_root']}/{P3_METHOD}"
        or condition.get("maximum_cue_packets") != 1
        or condition.get("human_review_before_and_after_cues") is not True
        or condition.get("coaching_requires_approved_recognition") is not True
        or not cue_path.is_relative_to(output_root)
        or not cue_path.is_file()
        or not prompt_path.is_file()
        or sha256_file(cue_path) != condition.get("cue_sheet_sha256")
    ):
        raise typer.BadParameter("Invalid or changed frozen P3 cue declaration")
    return condition, cue_path, prompt_path


def load_prompt_development_cohort(config: dict) -> dict:
    path = ROOT / config["development"]["cohort_path"]
    cohort = load_json(path)
    if cohort.get("split") != "train":
        raise ValueError("Prompt-development cohort must use Dataset B train")
    if cohort.get("selection_used_hidden_labels") is not False:
        raise ValueError("Prompt-development selection must exclude hidden labels")
    if cohort.get("selection_used_model_answers") is not False:
        raise ValueError("Prompt-development selection must exclude model answers")
    clip_ids = cohort.get("clip_ids", [])
    if not clip_ids or len(clip_ids) != len(set(clip_ids)):
        raise ValueError("Prompt-development cohort needs unique clip IDs")
    return cohort


def label_informed_development_selection(clip_id: str, cohort: dict) -> dict:
    """Record researcher-side clip selection without sending labels to the model."""
    path = ROOT / "config/label_informed_development_order_v0.4.1.json"
    if not path.is_file():
        return {
            "hidden_b_action_used_for_selection": False,
            "selection_manifest_sha256": None,
        }
    selection = load_json(path)
    selected = selection.get("clip_ids_in_order")
    if (
        selection.get("split") != "train"
        or selection.get("selection_used_hidden_labels") is not True
        or not isinstance(selected, list)
        or not selected
        or len(selected) != len(set(selected))
        or any(not isinstance(item, str) or item not in cohort["clip_ids"] for item in selected)
    ):
        raise ValueError("Invalid label-informed B-train development selection")
    return {
        "hidden_b_action_used_for_selection": clip_id in selected,
        "selection_manifest_sha256": sha256_file(path) if clip_id in selected else None,
    }


def validate_prompt_chain_config(config: dict, config_path: Path) -> dict:
    if config.get("protocol_id") != "evidence-first-football-v0.4.0":
        raise ValueError("Prompt-chain command requires the v0.4 protocol")
    if config.get("status") != "draft_train_prompt_development":
        raise ValueError("Prompt-chain command is restricted to draft train development")
    if config["development"].get("allowed_split") != "train":
        raise ValueError("v0.4 development must remain train-only")
    if config["split_policy"].get("test") != "sealed":
        raise ValueError("v0.4 test split must remain sealed")
    if P1_METHOD not in config["methods"]["active"]:
        raise ValueError(f"{P1_METHOD} is not active in {config_path}")
    generation = config["generation"]
    require_gpu = generation.get("require_gpu")
    num_gpu = generation["options"].get("num_gpu")
    if require_gpu is True and num_gpu == 0:
        raise ValueError("GPU v0.4 configuration must not force CPU execution")
    if require_gpu is False and num_gpu != 0:
        raise ValueError("CPU v0.4 configuration must explicitly set num_gpu=0")
    if not isinstance(require_gpu, bool):
        raise ValueError("v0.4 must declare a GPU or CPU device policy")
    prompt_paths = config["prompts"][P1_METHOD]
    for name in ("recognition", "revision", "coaching"):
        path = ROOT / prompt_paths[name]
        if not path.is_file():
            raise ValueError(f"Missing {name} prompt: {path}")
    cohort = load_prompt_development_cohort(config)
    return cohort


def checked_prompt_gpu(
    client: OllamaClient,
    model: str,
    options: dict,
    expected_digest: str,
    *,
    preload: bool,
) -> dict:
    status = client.gpu_status(model, options, preload=preload)
    if status["digest"] != expected_digest:
        raise ValueError("Loaded model digest differs from the selected model")
    if options.get("num_gpu") == 0:
        if status["size_vram_bytes"] != 0:
            raise RuntimeError("CPU-only v0.4 run unexpectedly used GPU VRAM")
    elif status["size_vram_bytes"] <= 0:
        raise RuntimeError(
            "Ollama loaded the model on CPU only; this v0.4 run requires GPU offload. "
            "Check the remote GPU with ollama ps and nvidia-smi."
        )
    return status


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_private_path(path: Path, private_root: Path) -> Path:
    resolved = path.resolve()
    root = private_root.resolve()
    if not resolved.is_relative_to(root):
        raise typer.BadParameter(f"Path must remain private under {root}")
    return resolved


def find_b_clip(manifest: Path, clip_id: str) -> SoccerNetClip:
    matches = [record for record in read_manifest(manifest) if record.clip_id == clip_id]
    if len(matches) != 1:
        raise typer.BadParameter(
            f"Expected one Dataset B record for {clip_id}, found {len(matches)}"
        )
    return matches[0]


def require_allowed_split(config: dict, split: str) -> None:
    status = config["status"]
    allowed = {
        "draft_train_only": {"train"},
        "sampling_validation": {"train", "valid"},
        "frozen_validation": {"train", "valid"},
        "frozen_test": {"train", "valid", "test"},
    }
    if status not in allowed:
        raise ValueError(f"Unknown protocol status: {status}")
    if split not in allowed[status]:
        raise typer.BadParameter(
            f"Protocol status {status!r} does not permit Dataset B split {split!r}"
        )
    if status == "sampling_validation":
        validate_sampling_candidate(config, ROOT)
    if status in {"frozen_validation", "frozen_test"}:
        validate_sampling_freeze(config, ROOT)
    if status == "frozen_test":
        validate_protocol_freeze(config, ROOT)


def controlled_sampling_settings(
    config: dict, condition: Condition, count: int | None, maximum_edge: int | None
) -> tuple[int, int]:
    feasibility = config["input_feasibility"]
    if config["status"] == "draft_train_only":
        if condition != "B0_frames_only":
            raise typer.BadParameter(
                "Only B0 frame-sampling pilot runs are allowed before sampling freeze"
            )
        selected_count = count if count is not None else feasibility["frame_counts"][0]
        selected_edge = maximum_edge if maximum_edge is not None else feasibility["maximum_edge"]
        if selected_count not in feasibility["frame_counts"]:
            raise typer.BadParameter(
                f"Pilot frame count must be one of {feasibility['frame_counts']}"
            )
        if selected_edge != feasibility["maximum_edge"]:
            raise typer.BadParameter("Pilot maximum edge is fixed by the protocol")
        return int(selected_count), int(selected_edge)
    if config["status"] == "sampling_validation":
        if condition != "B0_frames_only":
            raise typer.BadParameter("Only B0 is allowed during sampling validation")
        decision = validate_sampling_candidate(config, ROOT)
        candidate_count = int(decision["selected_frame_count"])
        candidate_edge = int(decision["maximum_edge"])
        if count is not None and count != candidate_count:
            raise typer.BadParameter(f"Validation frame count candidate is {candidate_count}")
        if maximum_edge is not None and maximum_edge != candidate_edge:
            raise typer.BadParameter(f"Validation maximum edge is {candidate_edge}")
        return candidate_count, candidate_edge
    freeze = validate_sampling_freeze(config, ROOT)
    frozen_count = int(freeze["frame_count"])
    frozen_edge = int(freeze["maximum_edge"])
    if count is not None and count != frozen_count:
        raise typer.BadParameter(f"Frame count is frozen at {frozen_count}")
    if maximum_edge is not None and maximum_edge != frozen_edge:
        raise typer.BadParameter(f"Maximum edge is frozen at {frozen_edge}")
    return frozen_count, frozen_edge


def encoder_from_config(config: dict, device: str | None = None) -> ClipFrameEncoder:
    settings = config["retrieval"]["encoder"]
    return ClipFrameEncoder(settings["model_id"], settings["revision"], device=device)


def approved_case(case_id: str) -> CaseARecord:
    path = ROOT / "data/video_a/cases" / f"{case_id}.json"
    if not path.is_file():
        raise typer.BadParameter(f"Dataset A case does not exist: {case_id}")
    case = load_case(path)
    errors = case.approval_errors(ROOT)
    if case.status != "approved" or errors:
        details = "; ".join(errors) if errors else "status is not approved"
        raise typer.BadParameter(f"Dataset A case {case_id} is not usable: {details}")
    return case


@app.command("index-b")
def index_b(
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    public_output: Path = typer.Option(DEFAULT_B_PUBLIC_MANIFEST),
    private_output: Path = typer.Option(DEFAULT_B_MANIFEST),
    report_output: Path = typer.Option(DEFAULT_B_INTEGRITY_REPORT),
) -> None:
    """Index and fully verify immutable SoccerNet Dataset B archives."""
    try:
        records = index_dataset_b(load_json(config_path), ROOT)
        report = audit_dataset_b(records, ROOT, progress=typer.echo)
    except Exception as error:
        failure_path = ROOT / "data/video_b/private/integrity_failures" / f"{timestamp_utc()}.json"
        write_integrity_report(
            {
                "status": "fail",
                "raw_data_modified": False,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "created_at_utc": timestamp_utc(),
            },
            failure_path,
        )
        typer.echo(f"Preserved failed integrity audit at {failure_path}")
        raise
    if report["status"] != "pass":
        failure_path = ROOT / "data/video_b/private/integrity_failures" / f"{timestamp_utc()}.json"
        write_integrity_report(report, failure_path)
        typer.echo(f"Preserved failed integrity audit at {failure_path}")
        raise typer.Exit(code=1)
    write_public_manifest(records, public_output)
    write_private_manifest(records, private_output)
    counts = {
        split: sum(record.split == split for record in records)
        for split in ("train", "valid", "test")
    }
    typer.echo(f"Wrote model-visible manifest to {public_output}")
    typer.echo(f"Wrote private reference crosswalk to {private_output}")
    typer.echo(f"split_counts={json.dumps(counts)}")
    typer.echo(f"public_manifest_sha256={sha256_file(public_output)}")
    typer.echo(f"private_manifest_sha256={sha256_file(private_output)}")
    write_integrity_report(report, report_output)
    typer.echo(f"Wrote integrity report to {report_output}")
    typer.echo(
        f"integrity_status={report['status']} "
        f"decoded_frames={report['decoded_frame_count']}/"
        f"{report['expected_frame_count']}"
    )


@app.command("init-case-a")
def init_case_a(case_id: str) -> None:
    """Create non-overwriting Dataset A metadata and advice templates."""
    case_path, advice_path = initialize_case(
        case_id,
        ROOT,
        ROOT / "templates/case_a.template.json",
        ROOT / "templates/advice.template.txt",
    )
    typer.echo(f"Created {case_path}")
    typer.echo(f"Created {advice_path}")
    typer.echo(f"Add private media at data/video_a/media/{case_id}.mp4")


@app.command("validate-a")
def validate_a() -> None:
    """Validate Dataset A syntax and all requirements for approved cases."""
    reports = validate_library(ROOT / "data/video_a/cases", ROOT)
    invalid = 0
    approved = 0
    for case_id, errors in reports.items():
        case_path = ROOT / "data/video_a/cases" / f"{case_id}.json"
        case = None if errors else load_case(case_path)
        if errors:
            invalid += 1
            typer.echo(f"{case_id}: INVALID")
            for error in errors:
                typer.echo(f"  - {error}")
        elif case is not None:
            approved += case.status == "approved"
            typer.echo(f"{case_id}: {case.status.upper()}")
    typer.echo(f"cases={len(reports)} approved={approved} invalid={invalid}")
    if invalid:
        raise typer.Exit(code=1)


@app.command("pilot-plan")
def pilot_plan(config_path: Path = typer.Option(DEFAULT_CONFIG)) -> None:
    """Validate and display the fixed, label-blind Dataset B pilot matrix."""
    config = load_json(config_path)
    cohort = validate_pilot_cohort(
        ROOT / config["input_feasibility"]["pilot_cohort_path"],
        ROOT / config["dataset_b"]["public_manifest"],
    )
    typer.echo(f"cohort={cohort['cohort_id']}")
    typer.echo(f"clips={','.join(cohort['clip_ids'])}")
    for clip_id in cohort["clip_ids"]:
        for count in cohort["frame_counts"]:
            typer.echo(f"B0_frames_only\t{clip_id}\tF{count}\tedge={cohort['maximum_edge']}")
    typer.echo("validation_confirmation=" + ",".join(cohort["validation_confirmation_clip_ids"]))


@app.command("init-reference-b")
def init_reference_b(
    clip_id: str,
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Create a private, non-overwriting blind human-reference form."""
    config = load_json(config_path)
    record = find_b_clip(ROOT / config["dataset_b"]["private_manifest"], clip_id)
    require_allowed_split(config, record.split)
    destination = ROOT / config["human_reference"]["directory"] / f"{clip_id}.json"
    payload = load_experiment_json(ROOT / config["human_reference"]["template"])
    payload["clip_id"] = clip_id
    visibility_keys = expected_reference_visibility_keys(config, record.split, ROOT)
    payload["sampling_visibility"] = {
        key: {"event_visible": None, "notes": ""} for key in sorted(visibility_keys)
    }
    write_json_exclusive(destination, payload)
    typer.echo(f"Created blind reference form at {destination}")
    typer.echo("Complete the visual review before attaching the hidden SoccerNet label")


@app.command("finalize-reference-b")
def finalize_reference_b(
    clip_id: str,
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Attach the hidden label only after a completed blind visual review."""
    config = load_json(config_path)
    manifest = ROOT / config["dataset_b"]["private_manifest"]
    record = find_b_clip(manifest, clip_id)
    require_allowed_split(config, record.split)
    path = ROOT / config["human_reference"]["directory"] / f"{clip_id}.json"
    payload = load_experiment_json(path)
    if payload.get("review_status") != "draft":
        raise typer.BadParameter("Only a draft reference can be finalized")
    visual = payload.get("visual_reference", {})
    required_visual = [
        "chronological_visible_description",
        "possession_by_visible_appearance",
        "tactical_phase",
        "main_visible_event",
        "outcome",
    ]
    if any(not visual.get(name) for name in required_visual):
        raise typer.BadParameter("Complete every visual-reference field before finalizing")
    reviewer = payload.get("reviewer", {})
    if any(not reviewer.get(name) for name in reviewer):
        raise typer.BadParameter("Complete reviewer provenance before finalizing")
    visibility = payload.get("sampling_visibility", {})
    required_visibility = expected_reference_visibility_keys(config, record.split, ROOT)
    if set(visibility) != required_visibility or any(
        item.get("event_visible") is None for item in visibility.values()
    ):
        required_text = "/".join(sorted(required_visibility))
        raise typer.BadParameter(f"Complete visibility judgments for {required_text}")
    payload["hidden_reference"] = {
        "soccernet_action_label": record.action_class,
        "attached_only_after_visual_review": True,
        "used_as_coaching_ground_truth": False,
        "blind_snapshot_path": "",
        "blind_snapshot_sha256": "",
    }
    snapshot = json.loads(json.dumps(payload))
    snapshot["hidden_reference"] = {
        "soccernet_action_label": "",
        "attached_only_after_visual_review": False,
        "used_as_coaching_ground_truth": False,
        "blind_snapshot_path": "",
        "blind_snapshot_sha256": "",
    }
    snapshot_path = (
        ROOT
        / config["human_reference"]["directory"]
        / "blind_snapshots"
        / f"{clip_id}_{timestamp_utc()}.json"
    )
    write_json_exclusive(snapshot_path, snapshot)
    payload["hidden_reference"]["blind_snapshot_path"] = snapshot_path.relative_to(ROOT).as_posix()
    payload["hidden_reference"]["blind_snapshot_sha256"] = sha256_file(snapshot_path)
    payload["review_status"] = "approved"
    DatasetBHumanReference.model_validate(payload)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Finalized private reference at {path}")


@app.command("validate-reference-b")
def validate_reference_b(path: Path) -> None:
    """Validate one completed private Dataset B human reference."""
    reference = validate_human_reference(path)
    typer.echo(f"VALID {reference.clip_id} reference_version={reference.reference_version}")


@app.command("init-sampling-decision")
def init_sampling_decision(config_path: Path = typer.Option(DEFAULT_CONFIG)) -> None:
    """Create the private form used to justify the sampling decision."""
    config = load_json(config_path)
    destination = ROOT / config["freezes"]["sampling_decision_path"]
    initialize_from_template(ROOT / "templates/sampling_decision.template.json", destination, {})
    typer.echo(f"Created {destination}")


@app.command("freeze-sampling")
def freeze_sampling(config_path: Path = typer.Option(DEFAULT_CONFIG)) -> None:
    """Freeze sampling only after real train-pilot and validation evidence."""
    config = load_json(config_path)
    destination = ROOT / config["freezes"]["sampling_freeze_path"]
    payload = create_sampling_freeze(config, ROOT, destination)
    typer.echo(f"Created immutable sampling freeze at {destination}")
    typer.echo(f"frame_count={payload['frame_count']} edge={payload['maximum_edge']}")


@app.command("init-protocol-decision")
def init_protocol_decision(config_path: Path = typer.Option(DEFAULT_CONFIG)) -> None:
    """Create the private decision form for authorizing the one test run."""
    config = load_json(config_path)
    destination = ROOT / config["freezes"]["protocol_decision_path"]
    initialize_from_template(ROOT / "templates/protocol_decision.template.json", destination, {})
    typer.echo(f"Created {destination}")


@app.command("freeze-protocol")
def freeze_protocol(config_path: Path = typer.Option(DEFAULT_CONFIG)) -> None:
    """Hash and freeze every material choice before test access is enabled."""
    config = load_json(config_path)
    if config["status"] != "frozen_validation":
        raise typer.BadParameter("Freeze the protocol only after validation selection")
    destination = ROOT / config["freezes"]["protocol_freeze_path"]
    create_protocol_freeze(config, ROOT, destination)
    typer.echo(f"Created immutable test protocol freeze at {destination}")


@app.command("validate-score")
def validate_score_command(
    path: Path,
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Validate a completed blinded human score against the frozen rubric."""
    if path.suffix.lower() != ".txt":
        raise typer.BadParameter("Score form must be a .txt file")
    config = load_json(config_path)
    score = validate_score(path, ROOT / config["scoring"]["rubric_path"])
    typer.echo(f"VALID score run_id={score.run_id} clip_id={score.clip_id}")


@app.command("validate-human-pair")
def validate_human_pair_command(
    path: Path,
    clip_b_id: str,
    case_a_id: str,
) -> None:
    """Validate a completed B3 human-oracle pairing judgement."""
    validate_human_pair(path, clip_b_id, case_a_id)
    typer.echo(f"VALID B3 pair {clip_b_id} -> {case_a_id}")


@app.command("init-score")
def init_score(
    blind_run_id: str,
    clip_id: str,
    destination: Path,
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Create a non-overwriting score form without condition or model identity."""
    destination = require_private_path(destination, ROOT / "data/video_b/review/scores")
    if destination.suffix.lower() != ".txt":
        raise typer.BadParameter("Score form destination must end in .txt")
    config = load_json(config_path)
    initialize_text_from_template(
        ROOT / config["scoring"]["score_template"],
        destination,
        {"BLIND_RUN_ID": blind_run_id, "DATASET_B_CLIP_ID": clip_id},
    )
    typer.echo(f"Created blinded score form at {destination}")


@app.command("prepare-pilot-grading")
def prepare_pilot_grading_command(
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Build the randomized private grading package for all 32 B0 pilot runs."""
    config = load_json(config_path)
    destination = ROOT / "data/video_b/review/pilot_grading_v1"
    mapping = ROOT / "data/video_b/private/pilot_grading_mapping_v1.json"
    try:
        summary = prepare_pilot_grading(
            config, ROOT, destination, mapping, config_path=config_path
        )
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Created randomized pilot grading package at {destination}")
    typer.echo(f"items={summary['item_count']} copied_frames={summary['frame_count']}")
    typer.echo(f"package_sha256={summary['package_sha256']}")
    typer.echo("Private mapping created separately; do not inspect it until grading is complete.")


@app.command("prepare-comparison-grading")
def prepare_comparison_grading_command(
    package_id: str,
    clip_b_id: str,
    run_paths: list[Path],
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Build a randomized private package for paired-condition grading."""
    config = load_json(config_path)
    destination = ROOT / "data/video_b/review" / package_id
    mapping = ROOT / "data/video_b/private" / f"{package_id}_mapping.json"
    try:
        summary = prepare_comparison_grading(
            config,
            ROOT,
            package_id,
            clip_b_id,
            run_paths,
            destination,
            mapping,
        )
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Created blinded comparison package at {destination}")
    typer.echo(
        f"items={summary['item_count']} copied_frames={summary['copied_frame_count']}"
    )
    typer.echo(f"package_sha256={summary['package_sha256']}")
    typer.echo("Private mapping created separately; do not inspect it until grading is complete.")


@app.command("init-human-pair")
def init_human_pair(
    clip_b_id: str,
    case_a_id: str,
    destination: Path,
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Create a private B3 human-oracle pairing judgement."""
    config = load_json(config_path)
    record = find_b_clip(ROOT / config["dataset_b"]["private_manifest"], clip_b_id)
    require_allowed_split(config, record.split)
    approved_case(case_a_id)
    destination = require_private_path(destination, ROOT / "data/pairs/private")
    payload = load_experiment_json(ROOT / "templates/pair_judgement.template.json")
    payload["dataset_b_clip_id"] = clip_b_id
    payload["dataset_a_case_id"] = case_a_id
    write_json_exclusive(destination, payload)
    typer.echo(f"Created private human-pair form at {destination}")


@app.command("sample-a")
def sample_a(
    case_id: str,
    count: int = typer.Option(20, min=1, max=32),
    maximum_edge: int = typer.Option(672, min=224, max=1920),
) -> None:
    """Sample chronological frames from one approved Dataset A case."""
    case = approved_case(case_id)
    media_path = ROOT / cast(str, case.source.local_media_path)
    destination = ROOT / "data/video_a/frames" / case_id / (f"uniform_{count}_edge_{maximum_edge}")
    frames = sample_dataset_a(
        media_path,
        destination,
        case.source.clip_start_seconds,
        case.source.clip_end_seconds,
        count,
        maximum_edge,
    )
    typer.echo(f"Wrote {len(frames)} Dataset A frames to {destination}")


@app.command("sample-b")
def sample_b(
    clip_id: str,
    count: int | None = typer.Option(None, min=1, max=750),
    maximum_edge: int | None = typer.Option(None, min=224, max=1920),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
    config_path: Path = typer.Option(DEFAULT_CONFIG),
) -> None:
    """Sample Dataset B frames without using hidden event timing."""
    config = load_json(config_path)
    record = find_b_clip(manifest, clip_id)
    require_allowed_split(config, record.split)
    count, maximum_edge = controlled_sampling_settings(
        config, "B0_frames_only", count, maximum_edge
    )
    destination = (
        ROOT
        / "artifacts/model_inputs/dataset_b"
        / clip_id
        / (f"uniform_{count}_edge_{maximum_edge}")
    )
    frames = sample_dataset_b(record, ROOT, destination, count, maximum_edge)
    typer.echo(f"Wrote {len(frames)} Dataset B frames to {destination}")


@app.command("sample-pilot-frames")
def sample_pilot_frames(
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Create all neutral pilot frames before blind human review or model runs."""
    config = load_json(config_path)
    if config["status"] != "draft_train_only":
        raise typer.BadParameter("Pilot frame preparation requires draft_train_only state")
    cohort = validate_pilot_cohort(
        ROOT / config["input_feasibility"]["pilot_cohort_path"],
        ROOT / config["dataset_b"]["public_manifest"],
    )
    for clip_id in cohort["clip_ids"]:
        record = find_b_clip(manifest, clip_id)
        require_allowed_split(config, record.split)
        for count in cohort["frame_counts"]:
            destination = (
                ROOT
                / "artifacts/model_inputs/dataset_b"
                / clip_id
                / f"uniform_{count}_edge_{cohort['maximum_edge']}"
            )
            frames = sample_dataset_b(
                record,
                ROOT,
                destination,
                int(count),
                int(cohort["maximum_edge"]),
            )
            typer.echo(f"Prepared {clip_id} F{count}: {len(frames)} frames")


@app.command("build-a-index")
def build_a_index(
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    output_path: Path | None = typer.Option(None),
    device: str | None = typer.Option(None),
    batch_size: int = typer.Option(16, min=1, max=128),
) -> None:
    """Build the pinned, pixel-only Dataset A CLIP index for B4/B5."""
    config = load_json(config_path)
    if config["status"] == "frozen_test":
        raise typer.BadParameter("The retrieval index cannot be rebuilt after test freeze")
    retrieval = config["retrieval"]
    destination = output_path or ROOT / retrieval["index_path"]
    if destination.exists():
        raise typer.BadParameter(f"Refusing to overwrite existing index: {destination}")
    library = load_library(ROOT / "data/video_a/cases")
    cases = sorted(
        (
            case
            for case in library.values()
            if case.status == "approved" and not case.approval_errors(ROOT)
        ),
        key=lambda case: case.case_id,
    )
    if not cases:
        raise typer.BadParameter("No approved Dataset A cases are available")
    encoder = encoder_from_config(config, device)
    vectors: list[np.ndarray] = []
    frame_hashes: dict[str, dict[str, str]] = {}
    count = int(retrieval["dataset_a_frame_count"])
    edge = int(config["input_feasibility"]["maximum_edge"])
    for case in cases:
        frames = sample_dataset_a(
            ROOT / cast(str, case.source.local_media_path),
            ROOT
            / "artifacts/model_inputs/dataset_a"
            / case.case_id
            / (f"uniform_{count}_edge_{edge}"),
            case.source.clip_start_seconds,
            case.source.clip_end_seconds,
            count,
            edge,
        )
        typer.echo(f"Embedding {case.case_id}")
        vectors.append(encoder.encode_frames(frames, batch_size, progress=typer.echo))
        frame_hashes[case.case_id] = {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in frames
        }
    metadata = {
        **encoder.provenance(),
        "protocol_id": config["protocol_id"],
        "metric": retrieval["metric"],
        "k": retrieval["k"],
        "dataset_a_frame_count": count,
        "maximum_edge": edge,
        "case_ids": [case.case_id for case in cases],
        "case_metadata_sha256": {
            case.case_id: sha256_file(ROOT / "data/video_a/cases" / f"{case.case_id}.json")
            for case in cases
        },
        "case_advice_sha256": {
            case.case_id: sha256_file(ROOT / case.coaching.advice_path) for case in cases
        },
        "case_media_sha256": {
            case.case_id: sha256_file(ROOT / cast(str, case.source.local_media_path))
            for case in cases
        },
        "frame_sha256": frame_hashes,
        "created_at_utc": timestamp_utc(),
    }
    EmbeddingIndex([case.case_id for case in cases], np.stack(vectors), metadata).save(destination)
    typer.echo(f"Wrote {len(cases)}-case index to {destination}")
    typer.echo(f"index_sha256={sha256_file(destination)}")


@app.command("retrieve")
def retrieve(
    index_path: Path,
    query_vector_path: Path,
    k: int = typer.Option(3, min=1),
) -> None:
    """Return cosine k-nearest Dataset A cases from precomputed embeddings."""
    index = EmbeddingIndex.load(index_path)
    query = np.load(query_vector_path, allow_pickle=False)
    for hit in index.search(query, k):
        typer.echo(f"{hit.rank}\t{hit.case_id}\t{hit.similarity:.6f}")


@app.command("validate-prompt-chain")
def validate_prompt_chain(
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Validate the train-only v0.4 P1 environment without contacting Ollama."""
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    records = {record.clip_id: record for record in read_manifest(manifest)}
    for clip_id in cohort["clip_ids"]:
        record = records.get(clip_id)
        if record is None or record.split != "train":
            raise typer.BadParameter(f"Development clip is missing or not train: {clip_id}")
        reference_path = (
            ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_id}.json"
        )
        try:
            validate_human_reference(reference_path, clip_id)
        except Exception as error:
            raise typer.BadParameter(
                f"Development clip lacks a valid human reference: {clip_id}: {error}"
            ) from error
    typer.echo(f"protocol_id={config['protocol_id']}")
    typer.echo(f"status={config['status']}")
    typer.echo(f"method={P1_METHOD}")
    typer.echo(f"development_clips={len(cohort['clip_ids'])}")
    typer.echo("allowed_split=train")
    typer.echo("test_split=sealed")


@app.command("start-prompt-review")
def start_prompt_review(
    clip_b_id: str,
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    method: str = typer.Option(P1_METHOD, help="Active v0.4 prompting method"),
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Generate recognition and stop for frame-based human review."""
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    if method != P1_METHOD:
        raise typer.BadParameter(f"Only {P1_METHOD} is active")
    if model not in config["models"]:
        raise typer.BadParameter(f"Model must be one of {config['models']}")
    if clip_b_id not in cohort["clip_ids"]:
        raise typer.BadParameter("Clip is not in the declared prompt-development cohort")
    selection_provenance = label_informed_development_selection(clip_b_id, cohort)

    record = find_b_clip(manifest, clip_b_id)
    if record.split != "train":
        raise typer.BadParameter("Draft v0.4 prompting is restricted to Dataset B train")
    reference_path = (
        ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_b_id}.json"
    )
    try:
        validate_human_reference(reference_path, clip_b_id)
    except Exception as error:
        raise typer.BadParameter(
            f"Finalize the pixel-only human reference before inference: {error}"
        ) from error

    sampling = config["sampling"]
    frame_count = int(sampling["frame_count"])
    maximum_edge = int(sampling["maximum_edge"])
    frames = sample_dataset_b(
        record,
        ROOT,
        ROOT
        / "artifacts/model_inputs/dataset_b"
        / record.clip_id
        / f"uniform_{frame_count}_edge_{maximum_edge}",
        frame_count,
        maximum_edge,
    )

    prompt_paths = {
        name: ROOT / path
        for name, path in config["prompts"][P1_METHOD].items()
    }
    recognition_prompt = prompt_paths["recognition"].read_text(encoding="utf-8")
    messages = recognition_messages(recognition_prompt, frames)

    timestamp = timestamp_utc()
    run_dir = (
        ROOT
        / config["output_root"]
        / method
        / model.replace(":", "_")
        / clip_b_id
        / timestamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "stage_1_prompt.txt").write_text(
        readable_transcript(messages, ROOT),
        encoding="utf-8",
    )

    metadata = {
        "protocol_id": config["protocol_id"],
        "parent_protocol_id": config["parent_protocol_id"],
        "method": method,
        "dataset_b_clip_id": clip_b_id,
        "dataset_b_split": record.split,
        "development_only": True,
        "hidden_b_action_sent_to_model": False,
        **selection_provenance,
        "human_intervention_inside_run": True,
        "human_assisted": True,
        "dataset_a_material_sent_to_model": False,
        "dataset_b_frame_count": frame_count,
        "dataset_b_frame_indices_1_based": [
            int(path.stem.rsplit("_", 1)[1]) for path in frames
        ],
        "maximum_edge": maximum_edge,
        "sampling_algorithm": sampling["algorithm"],
        "image_construction": sampling["image_encoding"],
        "frame_sha256": {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in frames
        },
        "config_sha256": sha256_file(config_path),
        "cohort_sha256": sha256_file(ROOT / config["development"]["cohort_path"]),
        "human_reference_sha256": sha256_file(reference_path),
        "recognition_prompt_sha256": sha256_file(prompt_paths["recognition"]),
        "revision_prompt_sha256": sha256_file(prompt_paths["revision"]),
        "coaching_prompt_sha256": sha256_file(prompt_paths["coaching"]),
        "model": model,
        "model_digest": None,
        "generation": config["generation"],
        "run_status": "started",
        "created_at_utc": timestamp,
    }
    write_metadata(run_dir / "metadata.txt", metadata)

    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    options = dict(config["generation"]["options"])
    think = bool(config["generation"]["think"])
    current_stage = "model_metadata"
    total_started = perf_counter()
    try:
        model_metadata = client.model_metadata(model)
        metadata["model_digest"] = model_metadata.get("digest")
        if (
            not isinstance(metadata["model_digest"], str)
            or len(metadata["model_digest"]) != 64
            or any(character not in "0123456789abcdef" for character in metadata["model_digest"])
        ):
            raise ValueError("Ollama did not provide a full model digest")

        current_stage = "stage_1_gpu_preflight"
        metadata["stage_1_gpu_preflight"] = checked_prompt_gpu(
            client, model, options, metadata["model_digest"], preload=True
        )
        current_stage = "stage_1_recognition"
        stage_started = perf_counter()
        raw_recognition = client.chat(
            model=model,
            messages=messages,
            options=options,
            think=think,
        )
        recognition_seconds = perf_counter() - stage_started
        recognition_answer = response_text(raw_recognition)
        (run_dir / "stage_1_response.txt").write_text(
            recognition_answer, encoding="utf-8"
        )
        write_json(run_dir / "stage_1_raw_api_response.json", raw_recognition)
        current_stage = "stage_1_gpu_postcheck"
        metadata["stage_1_gpu_postcheck"] = checked_prompt_gpu(
            client, model, options, metadata["model_digest"], preload=False
        )

    except Exception as error:
        metadata.update(
            {
                "run_status": "crash",
                "crash_stage": current_stage,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "elapsed_seconds": perf_counter() - total_started,
            }
        )
        write_json(
            run_dir / "error.json",
            {"stage": current_stage, "type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved failed run at {run_dir}")
        raise

    recognition_issues = heading_issues(recognition_answer, RECOGNITION_HEADINGS)
    metadata.update(
        {
            "run_status": "awaiting_human_review",
            "stage_1_elapsed_seconds": recognition_seconds,
            "elapsed_seconds": perf_counter() - total_started,
            "stage_1_format_status": "valid" if not recognition_issues else "invalid",
            "stage_1_format_issues": recognition_issues,
        }
    )
    write_json(
        run_dir / "initial_review.json",
        pending_guided_review(),
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Review recognition at {run_dir / 'stage_1_response.txt'}")
    typer.echo("Edit initial_review.json after checking the frames.")
    typer.echo("Replace PENDING_REVIEW in notes; fill feedback if correction is needed.")
    typer.echo(f"Preserved run at {run_dir}")


def guided_run_context(
    run_dir: Path, config_path: Path, manifest: Path
) -> tuple[dict, dict, list[Path], Path]:
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    root = (ROOT / config["output_root"]).resolve()
    run_dir = run_dir.resolve()
    if not run_dir.is_relative_to(root):
        raise typer.BadParameter(f"Run must be under {root}")
    metadata = read_metadata(run_dir / "metadata.txt")
    clip_id = metadata.get("dataset_b_clip_id")
    if (
        metadata.get("protocol_id") != config["protocol_id"]
        or metadata.get("method") != P1_METHOD
        or metadata.get("dataset_b_split") != "train"
        or clip_id not in cohort["clip_ids"]
    ):
        raise typer.BadParameter("Run is not an eligible v0.4 train development run")
    if metadata.get("config_sha256") != sha256_file(config_path):
        raise typer.BadParameter("v0.4 config changed since recognition")
    if metadata.get("cohort_sha256") != sha256_file(
        ROOT / config["development"]["cohort_path"]
    ):
        raise typer.BadParameter("Development cohort changed since recognition")
    reference_path = (
        ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_id}.json"
    )
    if metadata.get("human_reference_sha256") != sha256_file(reference_path):
        raise typer.BadParameter("Human reference changed since recognition")
    record = find_b_clip(manifest, clip_id)
    if record.split != "train":
        raise typer.BadParameter("Run clip is not in Dataset B train")
    prompt_paths = {
        name: ROOT / path for name, path in config["prompts"][P1_METHOD].items()
    }
    for name in ("recognition", "revision", "coaching"):
        if metadata.get(f"{name}_prompt_sha256") != sha256_file(prompt_paths[name]):
            raise typer.BadParameter(f"{name} prompt changed since recognition")
    frames = [ROOT / path for path in metadata["frame_sha256"]]
    if any(
        not path.is_file() or sha256_file(path) != expected
        for path, expected in zip(frames, metadata["frame_sha256"].values(), strict=True)
    ):
        raise typer.BadParameter("Sampled frames changed since recognition")
    if metadata.get("model") not in config["models"] or not metadata.get("model_digest"):
        raise typer.BadParameter("Run lacks an eligible exact model digest")
    return config, metadata, frames, run_dir


def checked_review(
    run_dir: Path,
    file_name: str,
    answer_path: Path,
    frames: list[Path],
    *,
    revised: bool = False,
) -> dict:
    path = run_dir / file_name
    if not path.is_file():
        raise typer.BadParameter(f"Complete the review file first: {path}")
    review = load_json(path)
    raw_name = (
        "stage_2_revision_raw_api_response.json"
        if revised else "stage_1_raw_api_response.json"
    )
    original_answer = response_text(load_json(run_dir / raw_name))
    if answer_path.read_text(encoding="utf-8") != original_answer:
        raise typer.BadParameter("Preserved answer differs from its raw model response")
    try:
        decision = validate_review(
            review, set(range(1, len(frames) + 1)), revised=revised
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    return {**review, "decision": decision, "submitted_at_utc": timestamp_utc()}


@app.command("revise-prompt-recognition")
def revise_prompt_recognition(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Send one frame-cited human correction and preserve revised recognition."""
    config, metadata, frames, run_dir = guided_run_context(run_dir, config_path, manifest)
    if metadata["run_status"] != "awaiting_human_review":
        raise typer.BadParameter("Run is not awaiting its initial human review")
    initial_path = run_dir / "stage_1_response.txt"
    review = checked_review(run_dir, "initial_review.json", initial_path, frames)
    if review["decision"] != "revise":
        raise typer.BadParameter("Use finish-prompt-coaching for an approved initial answer")
    if not initial_path.read_text(encoding="utf-8").strip():
        raise typer.BadParameter("Cannot revise an empty recognition answer")

    paths = {
        name: ROOT / path for name, path in config["prompts"][P1_METHOD].items()
    }
    correction = feedback_text(
        review, paths["revision"].read_text(encoding="utf-8")
    )
    messages = revision_messages(
        paths["recognition"].read_text(encoding="utf-8"),
        frames,
        initial_path.read_text(encoding="utf-8"),
        correction,
    )
    write_json(run_dir / "initial_review_snapshot.json", review)
    (run_dir / "human_feedback.txt").write_text(correction, encoding="utf-8")
    (run_dir / "stage_2_revision_prompt.txt").write_text(
        readable_transcript(messages, ROOT), encoding="utf-8"
    )
    metadata["initial_review_sha256"] = sha256_file(run_dir / "initial_review.json")
    metadata["initial_review_decision"] = review["decision"]
    metadata["initial_review_submitted_at_utc"] = review["submitted_at_utc"]
    metadata["human_feedback_sha256"] = sha256_file(run_dir / "human_feedback.txt")
    metadata["run_status"] = "revision_started"
    write_metadata(run_dir / "metadata.txt", metadata)

    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from initial recognition")
        options = dict(config["generation"]["options"])
        metadata["stage_2_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        raw = client.chat(
            metadata["model"],
            messages,
            options,
            bool(config["generation"]["think"]),
        )
        answer = response_text(raw)
        (run_dir / "stage_2_revision_response.txt").write_text(answer, encoding="utf-8")
        write_json(run_dir / "stage_2_revision_raw_api_response.json", raw)
        metadata["stage_2_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash",
            crash_stage="recognition_revision",
            error_type=type(error).__name__,
            error_message=str(error),
            stage_2_elapsed_seconds=perf_counter() - started,
        )
        write_json(
            run_dir / "stage_2_error.json",
            {"type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    issues = heading_issues(answer, RECOGNITION_HEADINGS)
    metadata.update(
        run_status="awaiting_revision_approval",
        stage_2_elapsed_seconds=perf_counter() - started,
        stage_2_format_status="valid" if not issues else "invalid",
        stage_2_format_issues=issues,
    )
    write_json(
        run_dir / "revision_review.json",
        pending_guided_review(),
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Review revised recognition at {run_dir / 'stage_2_revision_response.txt'}")
    typer.echo("Edit revision_review.json after checking the frames.")
    typer.echo("Replace PENDING_REVIEW in notes; fill feedback if errors remain.")


@app.command("finish-prompt-coaching")
def finish_prompt_coaching(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Generate coaching only after human approval of recognition."""
    config, metadata, frames, run_dir = guided_run_context(run_dir, config_path, manifest)
    if metadata["run_status"] not in {
        "awaiting_human_review", "awaiting_revision_approval"
    }:
        raise typer.BadParameter("Run is not awaiting recognition approval")
    initial_path = run_dir / "stage_1_response.txt"
    initial_answer = initial_path.read_text(encoding="utf-8")
    if not initial_answer.strip():
        raise typer.BadParameter("Cannot coach from an empty recognition answer")
    paths = {
        name: ROOT / path for name, path in config["prompts"][P1_METHOD].items()
    }
    correction = None
    revised_answer = None
    if metadata["run_status"] == "awaiting_human_review":
        review = checked_review(run_dir, "initial_review.json", initial_path, frames)
        if review["decision"] != "approve":
            raise typer.BadParameter("Revise the recognition before requesting coaching")
        write_json(run_dir / "initial_review_snapshot.json", review)
        metadata["initial_review_sha256"] = sha256_file(run_dir / "initial_review.json")
        metadata["initial_review_decision"] = review["decision"]
        metadata["initial_review_submitted_at_utc"] = review["submitted_at_utc"]
    else:
        if sha256_file(run_dir / "initial_review.json") != metadata["initial_review_sha256"]:
            raise typer.BadParameter("Initial human review changed after revision")
        if sha256_file(run_dir / "human_feedback.txt") != metadata["human_feedback_sha256"]:
            raise typer.BadParameter("Human feedback changed after revision")
        revised_path = run_dir / "stage_2_revision_response.txt"
        review = checked_review(
            run_dir, "revision_review.json", revised_path, frames, revised=True
        )
        write_json(run_dir / "revision_review_snapshot.json", review)
        metadata["revision_review_sha256"] = sha256_file(run_dir / "revision_review.json")
        metadata["revision_review_decision"] = review["decision"]
        metadata["revision_review_submitted_at_utc"] = review["submitted_at_utc"]
        if review["decision"] == "reject":
            metadata["run_status"] = "recognition_rejected"
            write_metadata(run_dir / "metadata.txt", metadata)
            typer.echo(f"Preserved rejected recognition without coaching at {run_dir}")
            return
        correction = (run_dir / "human_feedback.txt").read_text(encoding="utf-8")
        revised_answer = revised_path.read_text(encoding="utf-8")
        if not revised_answer.strip():
            raise typer.BadParameter("Cannot coach from an empty revised answer")

    messages = coaching_messages(
        paths["recognition"].read_text(encoding="utf-8"),
        frames,
        initial_answer,
        paths["coaching"].read_text(encoding="utf-8"),
        correction,
        revised_answer,
    )
    (run_dir / "stage_3_coaching_prompt.txt").write_text(
        readable_transcript(messages, ROOT), encoding="utf-8"
    )
    metadata["run_status"] = "coaching_started"
    write_metadata(run_dir / "metadata.txt", metadata)

    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from initial recognition")
        options = dict(config["generation"]["options"])
        metadata["stage_3_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        raw = client.chat(
            metadata["model"],
            messages,
            options,
            bool(config["generation"]["think"]),
        )
        answer = response_text(raw)
        (run_dir / "stage_3_coaching_response.txt").write_text(answer, encoding="utf-8")
        write_json(run_dir / "stage_3_coaching_raw_api_response.json", raw)
        metadata["stage_3_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash",
            crash_stage="coaching",
            error_type=type(error).__name__,
            error_message=str(error),
            stage_3_elapsed_seconds=perf_counter() - started,
        )
        write_json(
            run_dir / "stage_3_error.json",
            {"type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    issues = heading_issues(answer, COACHING_HEADINGS)
    metadata.update(
        run_status="complete",
        stage_3_elapsed_seconds=perf_counter() - started,
        stage_3_format_status="valid" if not issues else "invalid",
        stage_3_format_issues=issues,
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Preserved human-guided coaching run at {run_dir}")


@app.command("start-progressive-review")
def start_progressive_review(
    clip_b_id: str,
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Start a fresh P2 recognition and pause for the first human hint decision."""
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    condition, hint_prompt_path = progressive_condition(config)
    if clip_b_id != condition["initial_diagnostic_clip_id"] or clip_b_id not in cohort["clip_ids"]:
        raise typer.BadParameter("Clip is not the declared P2 B-train diagnostic")
    if model not in config["models"]:
        raise typer.BadParameter(f"Model must be one of {config['models']}")
    record = find_b_clip(manifest, clip_b_id)
    if record.split != "train":
        raise typer.BadParameter("P2 is restricted to Dataset B train")
    reference_path = ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_b_id}.json"
    validate_human_reference(reference_path, clip_b_id)
    sampling = config["sampling"]
    frame_count = int(sampling["frame_count"])
    maximum_edge = int(sampling["maximum_edge"])
    if frame_count != 30:
        raise typer.BadParameter("The declared P2 diagnostic requires 30 frames")
    frames = sample_dataset_b(
        record, ROOT,
        ROOT / "artifacts/model_inputs/dataset_b" / record.clip_id
        / f"uniform_{frame_count}_edge_{maximum_edge}",
        frame_count, maximum_edge,
    )
    recognition_path = ROOT / config["prompts"][P1_METHOD]["recognition"]
    coaching_path = ROOT / config["prompts"][P1_METHOD]["coaching"]
    messages = recognition_messages(recognition_path.read_text(encoding="utf-8"), frames)
    timestamp = timestamp_utc()
    run_dir = (
        ROOT / config["output_root"] / P2_METHOD
        / model.replace(":", "_") / clip_b_id / timestamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "stage_1_prompt.txt").write_text(
        readable_transcript(messages, ROOT), encoding="utf-8"
    )
    metadata = {
        "protocol_id": config["protocol_id"],
        "method": P2_METHOD,
        "method_revision": condition["revision"],
        "dataset_b_clip_id": clip_b_id,
        "dataset_b_split": "train",
        "development_only": True,
        "human_assisted": True,
        "human_intervention_inside_run": True,
        "hidden_b_action_sent_to_model": False,
        "dataset_a_material_sent_to_model": False,
        "frame_sha256": {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in frames
        },
        "dataset_b_frame_count": frame_count,
        "dataset_b_frame_indices_1_based": [
            int(path.stem.rsplit("_", 1)[1]) for path in frames
        ],
        "model": model,
        "model_digest": None,
        "generation": config["generation"],
        "config_sha256": sha256_file(config_path),
        "condition_sha256": sha256_file(P2_PROGRESSIVE_CONFIG),
        "cohort_sha256": sha256_file(ROOT / config["development"]["cohort_path"]),
        "human_reference_sha256": sha256_file(reference_path),
        "recognition_prompt_sha256": sha256_file(recognition_path),
        "coaching_prompt_sha256": sha256_file(coaching_path),
        "hint_prompt_sha256": sha256_file(hint_prompt_path),
        "stage_1_prompt_sha256": sha256_file(run_dir / "stage_1_prompt.txt"),
        "maximum_hints": condition["maximum_hints"],
        "hints_sent": 0,
        "latest_stage": 1,
        "turns": [],
        "run_status": "started",
        "created_at_utc": timestamp,
    }
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    stage = "model_metadata"
    try:
        digest = client.model_metadata(model).get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("Ollama did not provide a full model digest")
        metadata["model_digest"] = digest
        options = dict(config["generation"]["options"])
        stage = "stage_1_gpu_preflight"
        metadata["stage_1_gpu_preflight"] = checked_prompt_gpu(
            client, model, options, digest, preload=True
        )
        stage = "stage_1_recognition"
        raw = client.chat(model, messages, options, bool(config["generation"]["think"]))
        answer = response_text(raw)
        (run_dir / "stage_1_response.txt").write_text(answer, encoding="utf-8")
        write_json(run_dir / "stage_1_raw_api_response.json", raw)
        stage = "stage_1_gpu_postcheck"
        metadata["stage_1_gpu_postcheck"] = checked_prompt_gpu(
            client, model, options, digest, preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage=stage,
            error_type=type(error).__name__, error_message=str(error),
            stage_1_elapsed_seconds=perf_counter() - started,
        )
        write_json(run_dir / "stage_1_error.json", {"stage": stage, "message": str(error)})
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved failed progressive P2 run at {run_dir}")
        raise
    issues = heading_issues(answer, RECOGNITION_HEADINGS)
    metadata.update(
        run_status="awaiting_review",
        stage_1_elapsed_seconds=perf_counter() - started,
        stage_1_response_sha256=sha256_file(run_dir / "stage_1_response.txt"),
        stage_1_raw_sha256=sha256_file(run_dir / "stage_1_raw_api_response.json"),
        stage_1_format_status="valid" if not issues else "invalid",
        stage_1_format_issues=issues,
    )
    write_json(run_dir / "review_stage_1.json", pending_progressive_review())
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Review fresh recognition at {run_dir / 'stage_1_response.txt'}")
    typer.echo("Edit review_stage_1.json after checking the frames.")
    typer.echo("Choose hint, approve, or stop; PENDING cannot advance.")
    typer.echo(f"Preserved progressive P2 run at {run_dir}")


def progressive_run_context(
    run_dir: Path, config_path: Path, manifest: Path
) -> tuple[dict, dict, list[Path], Path, list[str], list[str], Path]:
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    condition, hint_prompt_path = progressive_condition(config)
    root = (
        ROOT / config["output_root"] / P2_METHOD
    ).resolve()
    run_dir = run_dir.resolve()
    if not run_dir.is_relative_to(root):
        raise typer.BadParameter(f"Progressive P2 run must be under {root}")
    metadata = read_metadata(run_dir / "metadata.txt")
    clip_id = metadata.get("dataset_b_clip_id")
    if (
        metadata.get("protocol_id") != config["protocol_id"]
        or metadata.get("method") != P2_METHOD
        or metadata.get("method_revision") != condition["revision"]
        or metadata.get("dataset_b_split") != "train"
        or clip_id != condition["initial_diagnostic_clip_id"]
        or clip_id not in cohort["clip_ids"]
        or metadata.get("model") not in config["models"]
        or metadata.get("maximum_hints") != condition["maximum_hints"]
    ):
        raise typer.BadParameter("Not an eligible progressive P2 train run")
    if find_b_clip(manifest, clip_id).split != "train":
        raise typer.BadParameter("P2 clip is not in Dataset B train")
    expected_hashes = {
        "config_sha256": config_path,
        "condition_sha256": P2_PROGRESSIVE_CONFIG,
        "cohort_sha256": ROOT / config["development"]["cohort_path"],
        "human_reference_sha256": (
            ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_id}.json"
        ),
        "recognition_prompt_sha256": ROOT / config["prompts"][P1_METHOD]["recognition"],
        "coaching_prompt_sha256": ROOT / config["prompts"][P1_METHOD]["coaching"],
        "hint_prompt_sha256": hint_prompt_path,
        "stage_1_prompt_sha256": run_dir / "stage_1_prompt.txt",
        "stage_1_response_sha256": run_dir / "stage_1_response.txt",
        "stage_1_raw_sha256": run_dir / "stage_1_raw_api_response.json",
    }
    for field, path in expected_hashes.items():
        if metadata.get(field) != sha256_file(path):
            raise typer.BadParameter(f"Progressive P2 provenance changed: {field}")
    frames = [ROOT / path for path in metadata["frame_sha256"]]
    if len(frames) != metadata["dataset_b_frame_count"] or any(
        not frame.is_file() or sha256_file(frame) != expected
        for frame, expected in zip(frames, metadata["frame_sha256"].values(), strict=True)
    ):
        raise typer.BadParameter("Sampled frames changed since P2 recognition")
    recognition = (
        ROOT / config["prompts"][P1_METHOD]["recognition"]
    ).read_text(encoding="utf-8")
    if (run_dir / "stage_1_prompt.txt").read_text(encoding="utf-8") != readable_transcript(
        recognition_messages(recognition, frames), ROOT
    ):
        raise typer.BadParameter("Original progressive recognition prompt changed")
    initial = (run_dir / "stage_1_response.txt").read_text(encoding="utf-8")
    if initial != response_text(load_json(run_dir / "stage_1_raw_api_response.json")):
        raise typer.BadParameter("Original progressive answer differs from raw API response")
    answers = [initial]
    hints: list[str] = []
    turns = metadata.get("turns", [])
    if not isinstance(turns, list) or len(turns) > condition["maximum_hints"]:
        raise typer.BadParameter("Malformed progressive turn history")
    for index, turn in enumerate(turns, start=1):
        previous_stage = index
        current_stage = index + 1
        paths = {
            "review_sha256": run_dir / f"review_stage_{previous_stage}.json",
            "hint_sha256": run_dir / f"hint_{index}.txt",
            "prompt_sha256": run_dir / f"stage_{current_stage}_revision_prompt.txt",
            "response_sha256": run_dir / f"stage_{current_stage}_revision_response.txt",
            "raw_sha256": run_dir / f"stage_{current_stage}_revision_raw_api_response.json",
        }
        if any(turn.get(key) != sha256_file(path) for key, path in paths.items()):
            raise typer.BadParameter(f"Progressive hint turn {index} changed")
        hint = paths["hint_sha256"].read_text(encoding="utf-8")
        transcript = readable_transcript(
            progressive_messages(recognition, frames, answers, hints, hint), ROOT
        )
        if paths["prompt_sha256"].read_text(encoding="utf-8") != transcript:
            raise typer.BadParameter(f"Progressive hint turn {index} transcript changed")
        answer = paths["response_sha256"].read_text(encoding="utf-8")
        if answer != response_text(load_json(paths["raw_sha256"])):
            raise typer.BadParameter(f"Progressive hint turn {index} differs from raw API")
        hints.append(hint)
        answers.append(answer)
    if metadata.get("latest_stage") != len(answers) or metadata.get("hints_sent") != len(hints):
        raise typer.BadParameter("Progressive turn count is inconsistent")
    return config, metadata, frames, run_dir, answers, hints, hint_prompt_path


def checked_progressive_review(
    run_dir: Path, latest_stage: int, frame_count: int
) -> tuple[dict, str]:
    path = run_dir / f"review_stage_{latest_stage}.json"
    if not path.is_file():
        raise typer.BadParameter(f"Complete the review file first: {path}")
    review = load_json(path)
    try:
        decision = validate_progressive_review(review, frame_count)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    return review, decision


@app.command("continue-progressive-review")
def continue_progressive_review(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Send one researcher-authored hint and pause for the next recognition review."""
    config, metadata, frames, run_dir, answers, hints, hint_prompt_path = (
        progressive_run_context(run_dir, config_path, manifest)
    )
    if metadata["run_status"] != "awaiting_review":
        raise typer.BadParameter("P2 run is not awaiting a human review")
    if len(hints) >= metadata["maximum_hints"]:
        raise typer.BadParameter("Maximum hints reached; approve or stop the run")
    previous_stage = metadata["latest_stage"]
    review, decision = checked_progressive_review(run_dir, previous_stage, len(frames))
    if decision != "hint":
        raise typer.BadParameter("Use finish-progressive-coaching to approve or stop")
    hint_number = len(hints) + 1
    current_stage = previous_stage + 1
    numbers = ", ".join(str(number) for number in review["frame_numbers_1_based"])
    hint_text = (
        hint_prompt_path.read_text(encoding="utf-8").rstrip()
        + f"\nSampled images: {numbers}\nResearcher hint: {review['hint'].strip()}\n"
    )
    recognition = (
        ROOT / config["prompts"][P1_METHOD]["recognition"]
    ).read_text(encoding="utf-8")
    messages = progressive_messages(recognition, frames, answers, hints, hint_text)
    review_path = run_dir / f"review_stage_{previous_stage}.json"
    write_json(
        run_dir / f"review_stage_{previous_stage}_snapshot.json",
        {**review, "submitted_at_utc": timestamp_utc()},
    )
    hint_path = run_dir / f"hint_{hint_number}.txt"
    hint_path.write_text(hint_text, encoding="utf-8")
    prompt_path = run_dir / f"stage_{current_stage}_revision_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, ROOT), encoding="utf-8")
    metadata["run_status"] = "hint_started"
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from original P2 recognition")
        options = dict(config["generation"]["options"])
        metadata[f"stage_{current_stage}_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        raw = client.chat(
            metadata["model"], messages, options, bool(config["generation"]["think"])
        )
        response_path = run_dir / f"stage_{current_stage}_revision_response.txt"
        response_path.write_text(response_text(raw), encoding="utf-8")
        raw_path = run_dir / f"stage_{current_stage}_revision_raw_api_response.json"
        write_json(raw_path, raw)
        metadata[f"stage_{current_stage}_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage=f"hint_{hint_number}",
            error_type=type(error).__name__, error_message=str(error),
            **{f"stage_{current_stage}_elapsed_seconds": perf_counter() - started},
        )
        write_json(
            run_dir / f"stage_{current_stage}_error.json",
            {"type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    metadata["turns"].append({
        "review_sha256": sha256_file(review_path),
        "hint_sha256": sha256_file(hint_path),
        "prompt_sha256": sha256_file(prompt_path),
        "response_sha256": sha256_file(response_path),
        "raw_sha256": sha256_file(raw_path),
    })
    issues = heading_issues(response_path.read_text(encoding="utf-8"), RECOGNITION_HEADINGS)
    metadata.update(
        run_status="awaiting_review", latest_stage=current_stage,
        hints_sent=hint_number,
        **{
            f"stage_{current_stage}_elapsed_seconds": perf_counter() - started,
            f"stage_{current_stage}_format_status": "valid" if not issues else "invalid",
            f"stage_{current_stage}_format_issues": issues,
        },
    )
    write_json(
        run_dir / f"review_stage_{current_stage}.json",
        pending_progressive_review(),
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Review revised recognition at {response_path}")
    typer.echo(
        f"Edit review_stage_{current_stage}.json after checking the frames."
    )
    typer.echo(f"Hints used: {hint_number}/{metadata['maximum_hints']}")


@app.command("finish-progressive-coaching")
def finish_progressive_coaching(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Stop or generate coaching only after the latest P2 recognition is approved."""
    config, metadata, frames, run_dir, answers, hints, _ = progressive_run_context(
        run_dir, config_path, manifest
    )
    if metadata["run_status"] != "awaiting_review":
        raise typer.BadParameter("P2 run is not awaiting a human review")
    latest_stage = metadata["latest_stage"]
    review, decision = checked_progressive_review(run_dir, latest_stage, len(frames))
    if decision == "hint":
        raise typer.BadParameter("Use continue-progressive-review for another hint")
    review_path = run_dir / f"review_stage_{latest_stage}.json"
    write_json(
        run_dir / f"review_stage_{latest_stage}_snapshot.json",
        {**review, "submitted_at_utc": timestamp_utc()},
    )
    metadata["final_review_sha256"] = sha256_file(review_path)
    metadata["final_review_decision"] = decision
    if decision == "stop":
        metadata["run_status"] = "recognition_rejected"
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved stopped P2 run without coaching at {run_dir}")
        return
    if not answers[-1].strip():
        raise typer.BadParameter("Cannot coach from empty recognition")
    recognition = (
        ROOT / config["prompts"][P1_METHOD]["recognition"]
    ).read_text(encoding="utf-8")
    coaching = (
        ROOT / config["prompts"][P1_METHOD]["coaching"]
    ).read_text(encoding="utf-8")
    messages = progressive_messages(recognition, frames, answers, hints, coaching)
    coaching_stage = latest_stage + 1
    prompt_path = run_dir / f"stage_{coaching_stage}_coaching_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, ROOT), encoding="utf-8")
    metadata["run_status"] = "coaching_started"
    metadata["coaching_stage"] = coaching_stage
    metadata["coaching_prompt_sha256"] = sha256_file(prompt_path)
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from original P2 recognition")
        options = dict(config["generation"]["options"])
        metadata[f"stage_{coaching_stage}_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        raw = client.chat(
            metadata["model"], messages, options, bool(config["generation"]["think"])
        )
        response_path = run_dir / f"stage_{coaching_stage}_coaching_response.txt"
        response_path.write_text(response_text(raw), encoding="utf-8")
        write_json(run_dir / f"stage_{coaching_stage}_coaching_raw_api_response.json", raw)
        metadata[f"stage_{coaching_stage}_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage="progressive_coaching",
            error_type=type(error).__name__, error_message=str(error),
            **{f"stage_{coaching_stage}_elapsed_seconds": perf_counter() - started},
        )
        write_json(
            run_dir / f"stage_{coaching_stage}_error.json",
            {"type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    issues = heading_issues(response_path.read_text(encoding="utf-8"), COACHING_HEADINGS)
    metadata.update(
        run_status="complete",
        **{
            f"stage_{coaching_stage}_elapsed_seconds": perf_counter() - started,
            f"stage_{coaching_stage}_format_status": "valid" if not issues else "invalid",
            f"stage_{coaching_stage}_format_issues": issues,
        },
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Preserved progressive P2 coaching run at {run_dir}")


def pending_visible_cue_review() -> dict:
    return {"decision": "PENDING", "notes": ""}


@app.command("start-visible-cue-review")
def start_visible_cue_review(
    clip_b_id: str,
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Start a fresh P3 recognition; pause before sending frozen visible cues."""
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    condition, cue_path, cue_prompt_path = visible_cue_condition(config)
    if clip_b_id != condition["initial_diagnostic_clip_id"] or clip_b_id not in cohort["clip_ids"]:
        raise typer.BadParameter("Clip is not the declared P3 B-train diagnostic")
    if model not in config["models"]:
        raise typer.BadParameter(f"Model must be one of {config['models']}")
    record = find_b_clip(manifest, clip_b_id)
    if record.split != "train":
        raise typer.BadParameter("P3 is restricted to Dataset B train")
    reference_path = ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_b_id}.json"
    validate_human_reference(reference_path, clip_b_id)
    sampling = config["sampling"]
    frame_count = int(sampling["frame_count"])
    maximum_edge = int(sampling["maximum_edge"])
    if frame_count != 30:
        raise typer.BadParameter("The declared P3 diagnostic requires 30 frames")
    frames = sample_dataset_b(
        record, ROOT,
        ROOT / "artifacts/model_inputs/dataset_b" / record.clip_id
        / f"uniform_{frame_count}_edge_{maximum_edge}",
        frame_count, maximum_edge,
    )
    recognition_path = ROOT / config["prompts"][P1_METHOD]["recognition"]
    coaching_path = ROOT / config["prompts"][P1_METHOD]["coaching"]
    messages = recognition_messages(recognition_path.read_text(encoding="utf-8"), frames)
    timestamp = timestamp_utc()
    run_dir = (
        ROOT / config["output_root"] / P3_METHOD
        / model.replace(":", "_") / clip_b_id / timestamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    cue_snapshot = run_dir / "frozen_visible_cues.txt"
    copyfile(cue_path, cue_snapshot)
    prompt_path = run_dir / "stage_1_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, ROOT), encoding="utf-8")
    metadata = {
        "protocol_id": config["protocol_id"],
        "method": P3_METHOD,
        "method_revision": condition["revision"],
        "dataset_b_clip_id": clip_b_id,
        "dataset_b_split": "train",
        "development_only": True,
        "human_assisted": True,
        "human_intervention_inside_run": True,
        "hidden_b_action_sent_to_model": False,
        "dataset_a_material_sent_to_model": False,
        "frame_sha256": {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in frames
        },
        "dataset_b_frame_count": frame_count,
        "dataset_b_frame_indices_1_based": [
            int(path.stem.rsplit("_", 1)[1]) for path in frames
        ],
        "model": model,
        "model_digest": None,
        "generation": config["generation"],
        "config_sha256": sha256_file(config_path),
        "condition_sha256": sha256_file(P3_VISIBLE_CONFIG),
        "cohort_sha256": sha256_file(ROOT / config["development"]["cohort_path"]),
        "human_reference_sha256": sha256_file(reference_path),
        "recognition_prompt_sha256": sha256_file(recognition_path),
        "coaching_prompt_sha256": sha256_file(coaching_path),
        "cue_prompt_sha256": sha256_file(cue_prompt_path),
        "cue_sheet_sha256": sha256_file(cue_path),
        "cue_snapshot_sha256": sha256_file(cue_snapshot),
        "stage_1_prompt_sha256": sha256_file(prompt_path),
        "run_status": "started",
        "created_at_utc": timestamp,
    }
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    stage = "model_metadata"
    try:
        digest = client.model_metadata(model).get("digest")
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("Ollama did not provide a full model digest")
        metadata["model_digest"] = digest
        options = dict(config["generation"]["options"])
        stage = "stage_1_gpu_preflight"
        metadata["stage_1_gpu_preflight"] = checked_prompt_gpu(
            client, model, options, digest, preload=True
        )
        stage = "stage_1_recognition"
        raw = client.chat(model, messages, options, bool(config["generation"]["think"]))
        response_path = run_dir / "stage_1_response.txt"
        response_path.write_text(response_text(raw), encoding="utf-8")
        raw_path = run_dir / "stage_1_raw_api_response.json"
        write_json(raw_path, raw)
        stage = "stage_1_gpu_postcheck"
        metadata["stage_1_gpu_postcheck"] = checked_prompt_gpu(
            client, model, options, digest, preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage=stage,
            error_type=type(error).__name__, error_message=str(error),
            stage_1_elapsed_seconds=perf_counter() - started,
        )
        write_json(run_dir / "stage_1_error.json", {"stage": stage, "message": str(error)})
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved failed P3 run at {run_dir}")
        raise
    issues = heading_issues(response_path.read_text(encoding="utf-8"), RECOGNITION_HEADINGS)
    metadata.update(
        run_status="awaiting_initial_review",
        stage_1_elapsed_seconds=perf_counter() - started,
        stage_1_response_sha256=sha256_file(response_path),
        stage_1_raw_sha256=sha256_file(raw_path),
        stage_1_format_status="valid" if not issues else "invalid",
        stage_1_format_issues=issues,
    )
    write_json(run_dir / "review_stage_1.json", pending_visible_cue_review())
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Review fresh recognition at {response_path}")
    typer.echo("Edit review_stage_1.json: choose continue or stop.")
    typer.echo(f"Preserved separate P3 run at {run_dir}")


def visible_cue_run_context(
    run_dir: Path, config_path: Path, manifest: Path
) -> tuple[dict, dict, list[Path], Path, list[str], str | None, Path]:
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    condition, cue_path, cue_prompt_path = visible_cue_condition(config)
    root = (ROOT / config["output_root"] / P3_METHOD).resolve()
    run_dir = run_dir.resolve()
    if not run_dir.is_relative_to(root):
        raise typer.BadParameter(f"P3 run must be under {root}")
    metadata = read_metadata(run_dir / "metadata.txt")
    clip_id = metadata.get("dataset_b_clip_id")
    if (
        metadata.get("protocol_id") != config["protocol_id"]
        or metadata.get("method") != P3_METHOD
        or metadata.get("method_revision") != condition["revision"]
        or metadata.get("dataset_b_split") != "train"
        or clip_id != condition["initial_diagnostic_clip_id"]
        or clip_id not in cohort["clip_ids"]
        or metadata.get("model") not in config["models"]
        or not metadata.get("model_digest")
    ):
        raise typer.BadParameter("Not an eligible P3 train run")
    if find_b_clip(manifest, clip_id).split != "train":
        raise typer.BadParameter("P3 clip is not in Dataset B train")
    recognition_path = ROOT / config["prompts"][P1_METHOD]["recognition"]
    coaching_path = ROOT / config["prompts"][P1_METHOD]["coaching"]
    expected_hashes = {
        "config_sha256": config_path,
        "condition_sha256": P3_VISIBLE_CONFIG,
        "cohort_sha256": ROOT / config["development"]["cohort_path"],
        "human_reference_sha256": (
            ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_id}.json"
        ),
        "recognition_prompt_sha256": recognition_path,
        "coaching_prompt_sha256": coaching_path,
        "cue_prompt_sha256": cue_prompt_path,
        "cue_sheet_sha256": cue_path,
        "cue_snapshot_sha256": run_dir / "frozen_visible_cues.txt",
        "stage_1_prompt_sha256": run_dir / "stage_1_prompt.txt",
        "stage_1_response_sha256": run_dir / "stage_1_response.txt",
        "stage_1_raw_sha256": run_dir / "stage_1_raw_api_response.json",
    }
    for field, path in expected_hashes.items():
        if metadata.get(field) != sha256_file(path):
            raise typer.BadParameter(f"P3 provenance changed: {field}")
    if metadata["cue_snapshot_sha256"] != condition["cue_sheet_sha256"]:
        raise typer.BadParameter("P3 cue snapshot differs from frozen cue sheet")
    frames = [ROOT / path for path in metadata["frame_sha256"]]
    if len(frames) != metadata["dataset_b_frame_count"] or any(
        not frame.is_file() or sha256_file(frame) != expected
        for frame, expected in zip(frames, metadata["frame_sha256"].values(), strict=True)
    ):
        raise typer.BadParameter("Sampled frames changed since P3 recognition")
    recognition = recognition_path.read_text(encoding="utf-8")
    if (run_dir / "stage_1_prompt.txt").read_text(encoding="utf-8") != readable_transcript(
        recognition_messages(recognition, frames), ROOT
    ):
        raise typer.BadParameter("Original P3 recognition prompt changed")
    initial = (run_dir / "stage_1_response.txt").read_text(encoding="utf-8")
    if initial != response_text(load_json(run_dir / "stage_1_raw_api_response.json")):
        raise typer.BadParameter("Original P3 answer differs from raw API response")
    answers = [initial]
    cue_packet: str | None = None
    if metadata.get("cue_sent"):
        stage_2_hashes = {
            "initial_review_sha256": run_dir / "review_stage_1.json",
            "cue_packet_sha256": run_dir / "cue_packet.txt",
            "stage_2_prompt_sha256": run_dir / "stage_2_revision_prompt.txt",
            "stage_2_response_sha256": run_dir / "stage_2_revision_response.txt",
            "stage_2_raw_sha256": run_dir / "stage_2_revision_raw_api_response.json",
        }
        for field, path in stage_2_hashes.items():
            if metadata.get(field) != sha256_file(path):
                raise typer.BadParameter(f"P3 revision provenance changed: {field}")
        cue_packet = (run_dir / "cue_packet.txt").read_text(encoding="utf-8")
        expected_packet = (
            cue_prompt_path.read_text(encoding="utf-8").rstrip()
            + "\n" + (run_dir / "frozen_visible_cues.txt").read_text(encoding="utf-8")
        )
        if cue_packet != expected_packet:
            raise typer.BadParameter("P3 cue packet differs from frozen source")
        messages = progressive_messages(recognition, frames, answers, [], cue_packet)
        if (run_dir / "stage_2_revision_prompt.txt").read_text(
            encoding="utf-8"
        ) != readable_transcript(messages, ROOT):
            raise typer.BadParameter("P3 revision transcript changed")
        revised = (run_dir / "stage_2_revision_response.txt").read_text(encoding="utf-8")
        if revised != response_text(load_json(run_dir / "stage_2_revision_raw_api_response.json")):
            raise typer.BadParameter("P3 revision differs from raw API response")
        answers.append(revised)
    return config, metadata, frames, run_dir, answers, cue_packet, cue_prompt_path


def checked_visible_cue_review(run_dir: Path, stage: int) -> tuple[dict, str]:
    path = run_dir / f"review_stage_{stage}.json"
    if not path.is_file():
        raise typer.BadParameter(f"Complete the review file first: {path}")
    review = load_json(path)
    try:
        decision = validate_visible_cue_review(review, revised=stage == 2)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    return review, decision


@app.command("continue-visible-cue-review")
def continue_visible_cue_review(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Send the single frozen P3 cue packet after initial recognition review."""
    config, metadata, frames, run_dir, answers, cue_packet, cue_prompt_path = (
        visible_cue_run_context(run_dir, config_path, manifest)
    )
    if metadata["run_status"] != "awaiting_initial_review" or cue_packet is not None:
        raise typer.BadParameter("P3 run is not awaiting its initial review")
    review, decision = checked_visible_cue_review(run_dir, 1)
    if decision != "continue":
        raise typer.BadParameter("Use finish-visible-cue-coaching to stop this P3 run")
    review_path = run_dir / "review_stage_1.json"
    write_json(
        run_dir / "review_stage_1_snapshot.json",
        {**review, "submitted_at_utc": timestamp_utc()},
    )
    packet = (
        cue_prompt_path.read_text(encoding="utf-8").rstrip()
        + "\n" + (run_dir / "frozen_visible_cues.txt").read_text(encoding="utf-8")
    )
    packet_path = run_dir / "cue_packet.txt"
    packet_path.write_text(packet, encoding="utf-8")
    recognition = (
        ROOT / config["prompts"][P1_METHOD]["recognition"]
    ).read_text(encoding="utf-8")
    messages = progressive_messages(recognition, frames, answers, [], packet)
    prompt_path = run_dir / "stage_2_revision_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, ROOT), encoding="utf-8")
    metadata.update(
        run_status="cue_started",
        initial_review_sha256=sha256_file(review_path),
        cue_packet_sha256=sha256_file(packet_path),
        stage_2_prompt_sha256=sha256_file(prompt_path),
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    stage = "stage_2_model_metadata"
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from original P3 recognition")
        options = dict(config["generation"]["options"])
        stage = "stage_2_gpu_preflight"
        metadata["stage_2_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        stage = "stage_2_revision"
        raw = client.chat(
            metadata["model"], messages, options, bool(config["generation"]["think"])
        )
        response_path = run_dir / "stage_2_revision_response.txt"
        response_path.write_text(response_text(raw), encoding="utf-8")
        raw_path = run_dir / "stage_2_revision_raw_api_response.json"
        write_json(raw_path, raw)
        stage = "stage_2_gpu_postcheck"
        metadata["stage_2_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage=stage,
            error_type=type(error).__name__, error_message=str(error),
            stage_2_elapsed_seconds=perf_counter() - started,
        )
        write_json(run_dir / "stage_2_error.json", {"stage": stage, "message": str(error)})
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    issues = heading_issues(response_path.read_text(encoding="utf-8"), RECOGNITION_HEADINGS)
    metadata.update(
        run_status="awaiting_revision_review",
        cue_sent=True,
        stage_2_elapsed_seconds=perf_counter() - started,
        stage_2_response_sha256=sha256_file(response_path),
        stage_2_raw_sha256=sha256_file(raw_path),
        stage_2_format_status="valid" if not issues else "invalid",
        stage_2_format_issues=issues,
    )
    write_json(run_dir / "review_stage_2.json", pending_visible_cue_review())
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Review visible-cue recognition at {response_path}")
    typer.echo("Edit review_stage_2.json: choose approve or stop.")
    typer.echo(f"Preserved separate P3 run at {run_dir}")


@app.command("finish-visible-cue-coaching")
def finish_visible_cue_coaching(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Stop P3, or request coaching only after cue-revised recognition is approved."""
    config, metadata, frames, run_dir, answers, cue_packet, _ = visible_cue_run_context(
        run_dir, config_path, manifest
    )
    if metadata["run_status"] not in {"awaiting_initial_review", "awaiting_revision_review"}:
        raise typer.BadParameter("P3 run is not awaiting a human review")
    stage = 2 if metadata["run_status"] == "awaiting_revision_review" else 1
    review, decision = checked_visible_cue_review(run_dir, stage)
    if decision == "continue":
        raise typer.BadParameter("Use continue-visible-cue-review to send the frozen cues")
    review_path = run_dir / f"review_stage_{stage}.json"
    write_json(
        run_dir / f"review_stage_{stage}_snapshot.json",
        {**review, "submitted_at_utc": timestamp_utc()},
    )
    metadata["final_review_sha256"] = sha256_file(review_path)
    metadata["final_review_decision"] = decision
    if decision == "stop":
        metadata["run_status"] = "recognition_rejected"
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved stopped P3 run without coaching at {run_dir}")
        return
    if stage != 2 or cue_packet is None or not answers[-1].strip():
        raise typer.BadParameter("P3 coaching requires a nonempty approved cue revision")
    recognition = (
        ROOT / config["prompts"][P1_METHOD]["recognition"]
    ).read_text(encoding="utf-8")
    coaching = (
        ROOT / config["prompts"][P1_METHOD]["coaching"]
    ).read_text(encoding="utf-8")
    messages = progressive_messages(recognition, frames, answers, [cue_packet], coaching)
    prompt_path = run_dir / "stage_3_coaching_prompt.txt"
    prompt_path.write_text(readable_transcript(messages, ROOT), encoding="utf-8")
    metadata["run_status"] = "coaching_started"
    metadata["stage_3_prompt_sha256"] = sha256_file(prompt_path)
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    stage_name = "stage_3_model_metadata"
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from original P3 recognition")
        options = dict(config["generation"]["options"])
        stage_name = "stage_3_gpu_preflight"
        metadata["stage_3_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        stage_name = "stage_3_coaching"
        raw = client.chat(
            metadata["model"], messages, options, bool(config["generation"]["think"])
        )
        response_path = run_dir / "stage_3_coaching_response.txt"
        response_path.write_text(response_text(raw), encoding="utf-8")
        write_json(run_dir / "stage_3_coaching_raw_api_response.json", raw)
        stage_name = "stage_3_gpu_postcheck"
        metadata["stage_3_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage=stage_name,
            error_type=type(error).__name__, error_message=str(error),
            stage_3_elapsed_seconds=perf_counter() - started,
        )
        write_json(
            run_dir / "stage_3_error.json", {"stage": stage_name, "message": str(error)}
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    issues = heading_issues(response_path.read_text(encoding="utf-8"), COACHING_HEADINGS)
    metadata.update(
        run_status="complete",
        stage_3_elapsed_seconds=perf_counter() - started,
        stage_3_format_status="valid" if not issues else "invalid",
        stage_3_format_issues=issues,
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Preserved visible-cue P3 coaching run at {run_dir}")


@app.command("start-attention-review", hidden=True)
def start_attention_review(
    source_run: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Legacy one-hint P2 pilot; superseded by start-progressive-review."""
    config, source, frames, source_run = guided_run_context(
        source_run, config_path, manifest
    )
    condition = load_json(P2_ATTENTION_CONFIG)
    p1_root = (ROOT / config["output_root"] / P1_METHOD).resolve()
    if not source_run.is_relative_to(p1_root) or source.get("run_status") != "complete":
        raise typer.BadParameter("Source must be a completed P1 run")
    if (
        condition.get("protocol_id") != config["protocol_id"]
        or condition.get("condition") != P2_METHOD
        or condition.get("source_method") != P1_METHOD
        or condition.get("source_stage") != "stage_1_only"
        or condition.get("allowed_split") != "train"
        or condition.get("clip_id") != source["dataset_b_clip_id"]
        or condition.get("source_run") != source_run.relative_to(ROOT).as_posix()
        or condition.get("prompt_path") != P2_ATTENTION_PROMPT.relative_to(ROOT).as_posix()
        or condition.get("output_folder") != P2_METHOD
        or condition.get("maximum_recognition_revisions") != 1
        or condition.get("coaching_requires_human_approval") is not True
    ):
        raise typer.BadParameter("P2 condition declaration does not match this source")
    if not P2_ATTENTION_PROMPT.is_file():
        raise typer.BadParameter(f"Missing attention prompt: {P2_ATTENTION_PROMPT}")
    initial_path = source_run / "stage_1_response.txt"
    initial_raw_path = source_run / "stage_1_raw_api_response.json"
    initial_prompt_path = source_run / "stage_1_prompt.txt"
    initial_answer = initial_path.read_text(encoding="utf-8")
    if not initial_answer.strip() or response_text(load_json(initial_raw_path)) != initial_answer:
        raise typer.BadParameter("Original stage-1 answer is empty or differs from raw response")
    recognition_prompt = (
        ROOT / config["prompts"][P1_METHOD]["recognition"]
    ).read_text(encoding="utf-8")
    if initial_prompt_path.read_text(encoding="utf-8") != readable_transcript(
        recognition_messages(recognition_prompt, frames), ROOT
    ):
        raise typer.BadParameter("Original stage-1 prompt differs from the declared frames")
    attention_hint = P2_ATTENTION_PROMPT.read_text(encoding="utf-8")
    if not attention_hint.strip():
        raise typer.BadParameter("Attention prompt is empty")
    messages = revision_messages(recognition_prompt, frames, initial_answer, attention_hint)
    timestamp = timestamp_utc()
    run_dir = (
        ROOT / config["output_root"] / P2_METHOD
        / source["model"].replace(":", "_") / source["dataset_b_clip_id"] / timestamp
    )
    run_dir.mkdir(parents=True, exist_ok=False)
    source_files = (
        "stage_1_prompt.txt", "stage_1_response.txt", "stage_1_raw_api_response.json"
    )
    for name in source_files:
        copyfile(source_run / name, run_dir / name)
    (run_dir / "attention_hint.txt").write_text(attention_hint, encoding="utf-8")
    (run_dir / "stage_2_revision_prompt.txt").write_text(
        readable_transcript(messages, ROOT), encoding="utf-8"
    )
    metadata = {
        "protocol_id": config["protocol_id"],
        "method": P2_METHOD,
        "dataset_b_clip_id": source["dataset_b_clip_id"],
        "dataset_b_split": "train",
        "development_only": True,
        "human_assisted": True,
        "human_intervention_inside_run": True,
        "feedback_type": "attention_only_without_event_labels",
        "hidden_b_action_sent_to_model": False,
        "dataset_a_material_sent_to_model": False,
        "source_p1_run": source_run.relative_to(ROOT).as_posix(),
        "source_p1_metadata_sha256": sha256_file(source_run / "metadata.txt"),
        "source_stage_1_sha256": {
            name: sha256_file(source_run / name) for name in source_files
        },
        "frame_sha256": source["frame_sha256"],
        "dataset_b_frame_count": source["dataset_b_frame_count"],
        "dataset_b_frame_indices_1_based": source["dataset_b_frame_indices_1_based"],
        "model": source["model"],
        "model_digest": source["model_digest"],
        "generation": config["generation"],
        "config_sha256": sha256_file(config_path),
        "cohort_sha256": source["cohort_sha256"],
        "human_reference_sha256": source["human_reference_sha256"],
        "recognition_prompt_sha256": source["recognition_prompt_sha256"],
        "coaching_prompt_sha256": source["coaching_prompt_sha256"],
        "attention_prompt_sha256": sha256_file(P2_ATTENTION_PROMPT),
        "attention_config_sha256": sha256_file(P2_ATTENTION_CONFIG),
        "stage_2_prompt_sha256": sha256_file(run_dir / "stage_2_revision_prompt.txt"),
        "run_status": "revision_started",
        "created_at_utc": timestamp,
    }
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(source["model"]).get("digest") != source["model_digest"]:
            raise ValueError("Installed model digest differs from original stage 1")
        options = dict(config["generation"]["options"])
        metadata["stage_2_gpu_preflight"] = checked_prompt_gpu(
            client, source["model"], options, source["model_digest"], preload=True
        )
        raw = client.chat(
            source["model"], messages, options, bool(config["generation"]["think"])
        )
        answer = response_text(raw)
        (run_dir / "stage_2_revision_response.txt").write_text(answer, encoding="utf-8")
        write_json(run_dir / "stage_2_revision_raw_api_response.json", raw)
        metadata["stage_2_gpu_postcheck"] = checked_prompt_gpu(
            client, source["model"], options, source["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage="attention_revision",
            error_type=type(error).__name__, error_message=str(error),
            stage_2_elapsed_seconds=perf_counter() - started,
        )
        write_json(
            run_dir / "stage_2_error.json",
            {"type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved failed attention run at {run_dir}")
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
    typer.echo(
        f"Review attention-guided recognition at {run_dir / 'stage_2_revision_response.txt'}"
    )
    typer.echo("Edit revision_review.json after checking the frames.")
    typer.echo("Replace PENDING_REVIEW in notes; fill feedback if errors remain.")
    typer.echo(f"Preserved separate P2 run at {run_dir}")


def attention_run_context(
    run_dir: Path, config_path: Path, manifest: Path
) -> tuple[dict, dict, list[Path], Path]:
    config = load_json(config_path)
    cohort = validate_prompt_chain_config(config, config_path)
    condition = load_json(P2_ATTENTION_CONFIG)
    p2_root = (ROOT / config["output_root"] / P2_METHOD).resolve()
    run_dir = run_dir.resolve()
    if not run_dir.is_relative_to(p2_root):
        raise typer.BadParameter(f"P2 run must be under {p2_root}")
    metadata = read_metadata(run_dir / "metadata.txt")
    clip_id = metadata.get("dataset_b_clip_id")
    if (
        metadata.get("protocol_id") != config["protocol_id"]
        or metadata.get("method") != P2_METHOD
        or metadata.get("dataset_b_split") != "train"
        or clip_id not in cohort["clip_ids"]
        or metadata.get("model") not in config["models"]
    ):
        raise typer.BadParameter("Not an eligible P2 train development run")
    if metadata.get("config_sha256") != sha256_file(config_path):
        raise typer.BadParameter("v0.4 config changed since P2 revision")
    if (
        metadata.get("attention_config_sha256") != sha256_file(P2_ATTENTION_CONFIG)
        or condition.get("source_run") != metadata.get("source_p1_run")
        or condition.get("condition") != P2_METHOD
    ):
        raise typer.BadParameter("P2 condition declaration changed since revision")
    if metadata.get("cohort_sha256") != sha256_file(
        ROOT / config["development"]["cohort_path"]
    ):
        raise typer.BadParameter("Development cohort changed since P2 revision")
    reference_path = ROOT / config["dataset_b"]["human_reference_directory"] / f"{clip_id}.json"
    if metadata.get("human_reference_sha256") != sha256_file(reference_path):
        raise typer.BadParameter("Human reference changed since P2 revision")
    if find_b_clip(manifest, clip_id).split != "train":
        raise typer.BadParameter("P2 clip is not in Dataset B train")
    paths = {name: ROOT / path for name, path in config["prompts"][P1_METHOD].items()}
    for name in ("recognition", "coaching"):
        if metadata.get(f"{name}_prompt_sha256") != sha256_file(paths[name]):
            raise typer.BadParameter(f"{name} prompt changed since P2 revision")
    if metadata.get("attention_prompt_sha256") != sha256_file(P2_ATTENTION_PROMPT):
        raise typer.BadParameter("Attention prompt changed since P2 revision")
    if sha256_file(run_dir / "attention_hint.txt") != metadata["attention_prompt_sha256"]:
        raise typer.BadParameter("Preserved attention hint changed")
    if sha256_file(run_dir / "stage_2_revision_prompt.txt") != metadata["stage_2_prompt_sha256"]:
        raise typer.BadParameter("Preserved P2 revision transcript changed")
    source_run = (ROOT / metadata["source_p1_run"]).resolve()
    if not source_run.is_relative_to((ROOT / config["output_root"] / P1_METHOD).resolve()):
        raise typer.BadParameter("P2 source is not a P1 run")
    if sha256_file(source_run / "metadata.txt") != metadata["source_p1_metadata_sha256"]:
        raise typer.BadParameter("Source P1 metadata changed since branching")
    for name, expected in metadata["source_stage_1_sha256"].items():
        if sha256_file(source_run / name) != expected or sha256_file(run_dir / name) != expected:
            raise typer.BadParameter(f"Preserved stage-1 artifact changed: {name}")
    frames = [ROOT / name for name in metadata["frame_sha256"]]
    if len(frames) != metadata["dataset_b_frame_count"] or any(
        not frame.is_file() or sha256_file(frame) != expected
        for frame, expected in zip(frames, metadata["frame_sha256"].values(), strict=True)
    ):
        raise typer.BadParameter("Sampled frames changed since P2 revision")
    return config, metadata, frames, run_dir


@app.command("finish-attention-coaching", hidden=True)
def finish_attention_coaching(
    run_dir: Path,
    config_path: Path = typer.Option(DEFAULT_V04_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Close a legacy one-hint P2 pilot; not the progressive workflow."""
    config, metadata, frames, run_dir = attention_run_context(
        run_dir, config_path, manifest
    )
    if metadata["run_status"] != "awaiting_revision_approval":
        raise typer.BadParameter("P2 run is not awaiting revision review")
    revised_path = run_dir / "stage_2_revision_response.txt"
    review = checked_review(
        run_dir, "revision_review.json", revised_path, frames, revised=True
    )
    write_json(run_dir / "revision_review_snapshot.json", review)
    metadata["revision_review_sha256"] = sha256_file(run_dir / "revision_review.json")
    metadata["revision_review_decision"] = review["decision"]
    metadata["revision_review_submitted_at_utc"] = review["submitted_at_utc"]
    if review["decision"] == "reject":
        metadata["run_status"] = "recognition_rejected"
        write_metadata(run_dir / "metadata.txt", metadata)
        typer.echo(f"Preserved rejected P2 recognition without coaching at {run_dir}")
        return
    revised_answer = revised_path.read_text(encoding="utf-8")
    if not revised_answer.strip():
        raise typer.BadParameter("Cannot coach from an empty P2 recognition answer")
    paths = {name: ROOT / path for name, path in config["prompts"][P1_METHOD].items()}
    messages = coaching_messages(
        paths["recognition"].read_text(encoding="utf-8"),
        frames,
        (run_dir / "stage_1_response.txt").read_text(encoding="utf-8"),
        paths["coaching"].read_text(encoding="utf-8"),
        (run_dir / "attention_hint.txt").read_text(encoding="utf-8"),
        revised_answer,
    )
    (run_dir / "stage_3_coaching_prompt.txt").write_text(
        readable_transcript(messages, ROOT), encoding="utf-8"
    )
    metadata["run_status"] = "coaching_started"
    write_metadata(run_dir / "metadata.txt", metadata)
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    started = perf_counter()
    try:
        if client.model_metadata(metadata["model"]).get("digest") != metadata["model_digest"]:
            raise ValueError("Installed model digest differs from original stage 1")
        options = dict(config["generation"]["options"])
        metadata["stage_3_gpu_preflight"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=True
        )
        raw = client.chat(
            metadata["model"], messages, options, bool(config["generation"]["think"])
        )
        answer = response_text(raw)
        (run_dir / "stage_3_coaching_response.txt").write_text(answer, encoding="utf-8")
        write_json(run_dir / "stage_3_coaching_raw_api_response.json", raw)
        metadata["stage_3_gpu_postcheck"] = checked_prompt_gpu(
            client, metadata["model"], options, metadata["model_digest"], preload=False
        )
    except Exception as error:
        metadata.update(
            run_status="crash", crash_stage="attention_coaching",
            error_type=type(error).__name__, error_message=str(error),
            stage_3_elapsed_seconds=perf_counter() - started,
        )
        write_json(
            run_dir / "stage_3_error.json",
            {"type": type(error).__name__, "message": str(error)},
        )
        write_metadata(run_dir / "metadata.txt", metadata)
        raise
    issues = heading_issues(answer, COACHING_HEADINGS)
    metadata.update(
        run_status="complete",
        stage_3_elapsed_seconds=perf_counter() - started,
        stage_3_format_status="valid" if not issues else "invalid",
        stage_3_format_issues=issues,
    )
    write_metadata(run_dir / "metadata.txt", metadata)
    typer.echo(f"Preserved attention-guided coaching run at {run_dir}")


@app.command("ollama-check")
def ollama_check(
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    require_gpu: bool = typer.Option(False, help="Preload and verify GPU offload"),
) -> None:
    """Verify the remote endpoint, model metadata, and optionally GPU offload."""
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    metadata = client.model_metadata(model)
    if require_gpu:
        config = load_json(DEFAULT_V04_CONFIG)
        metadata["gpu_status"] = checked_prompt_gpu(
            client, model, dict(config["generation"]["options"]),
            metadata["digest"], preload=True
        )
    typer.echo(json.dumps(metadata, indent=2))


@app.command("run-pair")
def run_pair(
    clip_b_id: str,
    condition: str = typer.Option(..., help="B0 through B5 condition ID"),
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    case_a_id: str | None = typer.Option(None),
    pairing_judgement_path: Path | None = typer.Option(None),
    frame_count_b: int | None = typer.Option(None, min=1, max=750),
    maximum_edge: int | None = typer.Option(None, min=224, max=1344),
    embedding_device: str | None = typer.Option(None),
    embedding_batch_size: int = typer.Option(16, min=1, max=128),
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Run one controlled Dataset A/B comparison and preserve exact artifacts."""
    config = load_json(config_path)
    if condition not in config["conditions"]:
        raise typer.BadParameter(f"Unknown condition: {condition}")
    typed_condition = cast(Condition, condition)
    if typed_condition != "B3_human_oracle" and pairing_judgement_path:
        raise typer.BadParameter("Only B3 accepts a human pairing judgement")
    if model not in config["models"]:
        raise typer.BadParameter(f"Model must be one of {config['models']}")
    record_b = find_b_clip(manifest, clip_b_id)
    require_allowed_split(config, record_b.split)
    frame_count_b, maximum_edge = controlled_sampling_settings(
        config, typed_condition, frame_count_b, maximum_edge
    )
    if config["status"] == "draft_train_only":
        cohort = validate_pilot_cohort(
            ROOT / config["input_feasibility"]["pilot_cohort_path"],
            ROOT / config["dataset_b"]["public_manifest"],
        )
        if clip_b_id not in cohort["clip_ids"]:
            raise typer.BadParameter("Draft pilot runs are restricted to the frozen cohort")
    elif config["status"] == "sampling_validation":
        cohort = validate_pilot_cohort(
            ROOT / config["input_feasibility"]["pilot_cohort_path"],
            ROOT / config["dataset_b"]["public_manifest"],
        )
        if clip_b_id not in cohort["validation_confirmation_clip_ids"]:
            raise typer.BadParameter(
                "Sampling validation is restricted to the frozen validation cohort"
            )

    frames_b = sample_dataset_b(
        record_b,
        ROOT,
        ROOT
        / "artifacts/model_inputs/dataset_b"
        / record_b.clip_id
        / (f"uniform_{frame_count_b}_edge_{maximum_edge}"),
        frame_count_b,
        maximum_edge,
    )

    case = None
    advice = None
    frames_a: list[Path] | None = None
    retrieval_score: float | None = None
    retrieval_rank: int | None = None
    retrieval_query_sha256: str | None = None
    retrieval_provenance: dict[str, object] | None = None
    selected_index_path: Path | None = None
    pairing_note = ""
    frame_count_a = int(config["retrieval"]["dataset_a_frame_count"])
    if typed_condition != "B0_frames_only":
        library = load_library(ROOT / "data/video_a/cases")
        usable = [
            item
            for item in library.values()
            if item.status == "approved" and not item.approval_errors(ROOT)
        ]
        if typed_condition in {"B1_random_case", "B2_action_oracle"}:
            if case_a_id:
                raise typer.BadParameter(
                    f"{condition} selects Dataset A deterministically; omit --case-a-id"
                )
            try:
                case = deterministic_control_case(
                    usable,
                    record_b,
                    typed_condition,
                    int(config["seed"]),
                    config["action_oracle"]["label_to_case_family"]
                    if typed_condition == "B2_action_oracle"
                    else None,
                )
            except ValueError as error:
                raise typer.BadParameter(str(error)) from error
        elif typed_condition == "B3_human_oracle":
            if not case_a_id:
                raise typer.BadParameter("B3_human_oracle requires --case-a-id")
            case = approved_case(case_a_id)
            if not pairing_judgement_path:
                raise typer.BadParameter("B3_human_oracle requires --pairing-judgement-path")
            pairing_judgement_path = require_private_path(
                pairing_judgement_path, ROOT / "data/pairs/private"
            )
            try:
                judgement = validate_human_pair(pairing_judgement_path, clip_b_id, case_a_id)
            except ValueError as error:
                raise typer.BadParameter(str(error)) from error
            pairing_note = str(judgement["analogy_rationale"])
        elif typed_condition in {"B4_embedding_knn", "B5_advice_only"}:
            if case_a_id:
                raise typer.BadParameter(f"{condition} is automatic; omit --case-a-id")
            index_path = ROOT / config["retrieval"]["index_path"]
            if not index_path.is_file():
                raise typer.BadParameter(f"Retrieval index does not exist: {index_path}")
            index = EmbeddingIndex.load(index_path)
            expected_encoder = config["retrieval"]["encoder"]
            if index.metadata.get("protocol_id") != config["protocol_id"]:
                raise typer.BadParameter("Retrieval index protocol does not match config")
            if index.metadata.get("metric") != config["retrieval"]["metric"]:
                raise typer.BadParameter("Retrieval index metric does not match config")
            index_k = index.metadata.get("k")
            if (
                not isinstance(index_k, int)
                or isinstance(index_k, bool)
                or index_k != int(config["retrieval"]["k"])
            ):
                raise typer.BadParameter("Retrieval index k does not match config")
            if set(index.case_ids) != {item.case_id for item in usable}:
                raise typer.BadParameter(
                    "Retrieval index cases do not match the approved Dataset A library"
                )
            current_case_hashes = {
                item.case_id: sha256_file(ROOT / "data/video_a/cases" / f"{item.case_id}.json")
                for item in usable
            }
            if index.metadata.get("case_metadata_sha256") != current_case_hashes:
                raise typer.BadParameter(
                    "Retrieval index does not match current Dataset A metadata"
                )
            for key in ("model_id", "revision"):
                if index.metadata.get(key) != expected_encoder[key]:
                    raise typer.BadParameter(f"Retrieval index {key} does not match config")
            if index.metadata.get("uses_dataset_b_labels_or_text") is not False:
                raise typer.BadParameter("Retrieval index lacks a pixel-only provenance assertion")
            retrieval_started = perf_counter()
            try:
                encoder = encoder_from_config(config, embedding_device)
                query_vector = encoder.encode_frames(
                    frames_b, embedding_batch_size, progress=typer.echo
                )
            except Exception as error:
                failure_timestamp = timestamp_utc()
                failure_dir = (
                    ROOT
                    / "output"
                    / condition
                    / model.replace(":", "_")
                    / clip_b_id
                    / failure_timestamp
                )
                query_path = ROOT / config["prompts"]["dataset_b_task"]
                failure_messages = build_messages(
                    "B0_frames_only",
                    query_path.read_text(encoding="utf-8"),
                    frames_b,
                )
                write_run(
                    failure_dir,
                    readable_transcript(failure_messages, ROOT),
                    {"error": {"type": type(error).__name__, "message": str(error)}},
                    {
                        "protocol_id": config["protocol_id"],
                        "condition": condition,
                        "dataset_b_clip_id": clip_b_id,
                        "dataset_b_split": record_b.split,
                        "hidden_b_action_used_for_pairing": False,
                        "run_status": "crash",
                        "crash_stage": "automatic_pixel_embedding_retrieval",
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "elapsed_seconds": perf_counter() - retrieval_started,
                        "retrieval_index_sha256": sha256_file(index_path),
                        "frame_sha256": {
                            path.relative_to(ROOT).as_posix(): sha256_file(path)
                            for path in frames_b
                        },
                        "created_at_utc": failure_timestamp,
                    },
                )
                raise
            retrieval_query_sha256 = hashlib.sha256(query_vector.tobytes()).hexdigest()
            hits = index.search(query_vector, int(config["retrieval"]["k"]))
            if not hits:
                raise typer.BadParameter("Retrieval index returned no Dataset A case")
            hit = hits[0]
            case = approved_case(hit.case_id)
            retrieval_score = hit.similarity
            retrieval_rank = hit.rank
            selected_index_path = index_path
            retrieval_provenance = encoder.provenance()
        else:
            raise typer.BadParameter(f"Unsupported condition: {condition}")
        assert case is not None
        advice = (ROOT / case.coaching.advice_path).read_text(encoding="utf-8")
        if typed_condition != "B5_advice_only":
            frames_a = sample_dataset_a(
                ROOT / cast(str, case.source.local_media_path),
                ROOT
                / "artifacts/model_inputs/dataset_a"
                / case.case_id
                / (f"uniform_{frame_count_a}_edge_{maximum_edge}"),
                case.source.clip_start_seconds,
                case.source.clip_end_seconds,
                frame_count_a,
                maximum_edge,
            )
    elif case_a_id:
        raise typer.BadParameter("B0 does not accept Dataset A or retrieval inputs")

    case_template_path = ROOT / config["prompts"]["full_case_context"]
    advice_template_path = ROOT / config["prompts"]["advice_only_context"]
    query_template_path = ROOT / config["prompts"]["dataset_b_task"]
    messages = build_messages(
        typed_condition,
        query_template_path.read_text(encoding="utf-8"),
        frames_b,
        case,
        advice,
        case_template_path.read_text(encoding="utf-8"),
        frames_a,
        advice_template_path.read_text(encoding="utf-8"),
    )

    timestamp = timestamp_utc()
    run_dir = ROOT / "output" / condition / model.replace(":", "_") / clip_b_id / timestamp
    all_frames = (frames_a or []) + frames_b
    base_metadata = {
        "protocol_id": config["protocol_id"],
        "condition": condition,
        "dataset_a_case_id": case.case_id if case else None,
        "dataset_b_clip_id": record_b.clip_id,
        "dataset_b_split": record_b.split,
        "hidden_b_action_sent_to_model": False,
        "hidden_b_action_used_for_pairing": typed_condition == "B2_action_oracle",
        "oracle_leakage": typed_condition == "B2_action_oracle",
        "pairing_note": pairing_note,
        "pairing_judgement_sha256": (
            sha256_file(pairing_judgement_path) if pairing_judgement_path else None
        ),
        "retrieval_score": retrieval_score,
        "retrieval_rank": retrieval_rank,
        "retrieval_query_embedding_sha256": retrieval_query_sha256,
        "retrieval_encoder": retrieval_provenance,
        "retrieval_index_sha256": (
            sha256_file(selected_index_path) if selected_index_path else None
        ),
        "dataset_b_frame_count": frame_count_b,
        "dataset_b_frame_indices_1_based": [int(path.stem.rsplit("_", 1)[1]) for path in frames_b],
        "dataset_a_frame_count": frame_count_a if frames_a else None,
        "maximum_edge": maximum_edge,
        "sampling_algorithm": "uniform_endpoints_v1",
        "image_construction": config["input_feasibility"]["image_encoding"],
        "frame_sha256": {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in all_frames
        },
        "config_sha256": sha256_file(config_path),
        "full_case_context_sha256": sha256_file(case_template_path),
        "advice_only_context_sha256": sha256_file(advice_template_path),
        "dataset_b_task_sha256": sha256_file(query_template_path),
        "model_output": config["model_output"],
        "created_at_utc": timestamp,
    }
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    options = dict(config["generation"])
    think = bool(options.pop("think"))
    options.pop("stream", None)
    started = perf_counter()
    model_digest = None
    try:
        model_metadata = client.model_metadata(model)
        model_digest = model_metadata.get("digest")
        if config["status"] == "frozen_test":
            protocol_freeze = validate_protocol_freeze(config, ROOT)
            if (
                model != protocol_freeze["model_tag"]
                or model_digest != protocol_freeze["model_digest"]
            ):
                raise ValueError("Requested model tag/digest does not match protocol freeze")
            claim_test_attempt(config, ROOT, clip_b_id, condition, model)
        raw_response = client.chat(
            model=model,
            messages=messages,
            options=options,
            think=think,
        )
    except Exception as error:
        failure_metadata = {
            **base_metadata,
            "model": model,
            "model_digest": model_digest,
            "elapsed_seconds": perf_counter() - started,
            "run_status": "crash",
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        write_run(
            run_dir,
            readable_transcript(messages, ROOT),
            {"error": {"type": type(error).__name__, "message": str(error)}},
            failure_metadata,
        )
        raise
    raw_text = str(raw_response.get("message", {}).get("content", ""))
    format_issues = plain_text_answer_issues(raw_text)

    metadata = {
        **base_metadata,
        "model": model,
        "model_digest": model_digest,
        "elapsed_seconds": perf_counter() - started,
        "run_status": "complete",
        "answer_format": "plain_text",
        "answer_format_status": "valid" if not format_issues else "invalid",
        "answer_format_issues": format_issues,
    }
    write_run(run_dir, readable_transcript(messages, ROOT), raw_response, metadata)
    typer.echo(f"Preserved run at {run_dir}")


@app.command("run-sampling-pilot")
def run_sampling_pilot(
    model: str = typer.Option(..., help="One exact model tag for the full matrix"),
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Run the complete fixed B0 F10/F20/F30/F60 train matrix."""
    config = load_json(config_path)
    if config["status"] != "draft_train_only":
        raise typer.BadParameter("Sampling pilot requires draft_train_only state")
    if model not in config["models"]:
        raise typer.BadParameter(f"Model must be one of {config['models']}")
    cohort = validate_pilot_cohort(
        ROOT / config["input_feasibility"]["pilot_cohort_path"],
        ROOT / config["dataset_b"]["public_manifest"],
    )
    for clip_id in cohort["clip_ids"]:
        reference_path = (
            ROOT / config["human_reference"]["directory"] / f"{clip_id}.json"
        )
        try:
            validate_human_reference(reference_path, clip_id)
        except Exception as error:
            raise typer.BadParameter(
                f"Finalize the blind human reference for {clip_id} before model runs: {error}"
            ) from error
    failures: list[str] = []
    for clip_id in cohort["clip_ids"]:
        for count in cohort["frame_counts"]:
            typer.echo(f"RUN {clip_id} F{count} model={model}")
            try:
                run_pair(
                    clip_b_id=clip_id,
                    condition="B0_frames_only",
                    model=model,
                    case_a_id=None,
                    pairing_judgement_path=None,
                    frame_count_b=int(count),
                    maximum_edge=int(cohort["maximum_edge"]),
                    embedding_device=None,
                    embedding_batch_size=16,
                    config_path=config_path,
                    manifest=manifest,
                )
            except Exception as error:
                failure = f"{clip_id} F{count}: {type(error).__name__}: {error}"
                failures.append(failure)
                typer.echo(f"FAILED {failure}")
    typer.echo(f"pilot_cells={len(cohort['clip_ids']) * len(cohort['frame_counts'])}")
    typer.echo(f"pilot_failures={len(failures)}")
    if failures:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
