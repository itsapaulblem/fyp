from __future__ import annotations

import hashlib
import json
from pathlib import Path
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

app = typer.Typer(no_args_is_help=True)
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/project_v0.3.0.json"
DEFAULT_B_MANIFEST = ROOT / "data/video_b/private/soccernet_gsr_v1.3_reference.csv"
DEFAULT_B_PUBLIC_MANIFEST = ROOT / "data/video_b/manifests/soccernet_gsr_v1.3_public.csv"
DEFAULT_B_INTEGRITY_REPORT = ROOT / "data/video_b/private/integrity_v1.3.json"


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


@app.command("ollama-check")
def ollama_check(model: str = typer.Option(..., help="Exact Ollama model tag")) -> None:
    """Verify the remote endpoint and return exact installed-model metadata."""
    load_dotenv(ROOT / ".env")
    metadata = OllamaClient().model_metadata(model)
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
