from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .domain import DatasetBHumanReference, HumanScoreRecord
from .provenance import sha256_file, timestamp_utc


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def sha256_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        digest.update(child.relative_to(path).as_posix().encode("utf-8"))
        digest.update(bytes.fromhex(sha256_file(child)))
    return digest.hexdigest()


def initialize_from_template(
    template: Path, destination: Path, replacements: dict[str, Any]
) -> None:
    payload = load_json(template)
    payload.update(replacements)
    write_json_exclusive(destination, payload)


def validate_human_reference(
    path: Path, expected_clip_id: str | None = None
) -> DatasetBHumanReference:
    reference = DatasetBHumanReference.model_validate(load_json(path))
    if expected_clip_id and reference.clip_id != expected_clip_id:
        raise ValueError(f"Reference clip_id {reference.clip_id} does not match {expected_clip_id}")
    return reference


def _check_range(name: str, value: Any, lower: int, upper: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def validate_score(path: Path, rubric_path: Path) -> HumanScoreRecord:
    score = HumanScoreRecord.model_validate(load_json(path))
    rubric = load_json(rubric_path)
    for section, dimensions in rubric["dimensions"].items():
        values = getattr(score, section)
        for dimension, specification in dimensions.items():
            value = values.get(dimension)
            if value is None:
                if section == "retrieval_relevance" and values.get("not_applicable_reason"):
                    continue
                raise ValueError(f"{section}.{dimension} is not scored")
            lower, upper = specification["range"]
            _check_range(f"{section}.{dimension}", value, lower, upper)
    if not score.blinding.get("condition_hidden_during_recognition_scoring", False):
        raise ValueError("Recognition must be scored before the condition is revealed")
    if not score.scorer.get("name_or_code") or not score.scorer.get("scored_at_utc"):
        raise ValueError("Score requires scorer identity/code and timestamp")
    return score


def validate_human_pair(path: Path, expected_clip_id: str, expected_case_id: str) -> dict[str, Any]:
    payload = load_json(path)
    if payload.get("status") != "approved":
        raise ValueError("Human pair judgement must be approved")
    if payload.get("condition") != "B3_human_oracle":
        raise ValueError("Human pair judgement must be for B3_human_oracle")
    if payload.get("dataset_b_clip_id") != expected_clip_id:
        raise ValueError("Human pair judgement has the wrong Dataset B clip")
    if payload.get("dataset_a_case_id") != expected_case_id:
        raise ValueError("Human pair judgement has the wrong Dataset A case")
    if payload.get("selection_used_model_answer") is not False:
        raise ValueError("B3 pairing must not use a prior model answer")
    if payload.get("selection_used_soccernet_label") is not False:
        raise ValueError("B3 pairing must not use the hidden SoccerNet label")
    if not payload.get("analogy_rationale"):
        raise ValueError("Human pair judgement requires an analogy rationale")
    if not payload.get("transferable_principles"):
        raise ValueError("Human pair judgement requires a transferable principle")
    if not payload.get("important_differences"):
        raise ValueError("Human pair judgement requires important differences")
    reviewer = payload.get("reviewer", {})
    if not reviewer.get("name_or_code") or not reviewer.get("reviewed_at_utc"):
        raise ValueError("Human pair judgement requires reviewer provenance")
    return payload


def validate_pilot_cohort(cohort_path: Path, public_manifest_path: Path) -> dict[str, Any]:
    cohort = load_json(cohort_path)
    with public_manifest_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    public_train_ids = {row["clip_id"] for row in rows if row["split"] == "train"}
    public_valid_ids = {row["clip_id"] for row in rows if row["split"] == "valid"}
    clip_ids = cohort["clip_ids"]
    if len(clip_ids) != 8 or len(set(clip_ids)) != 8:
        raise ValueError("Pilot cohort must contain eight unique clips")
    unknown = sorted(set(clip_ids) - public_train_ids)
    if unknown:
        raise ValueError(f"Pilot cohort contains unknown/non-train IDs: {unknown}")
    validation_ids = cohort.get("validation_confirmation_clip_ids", [])
    if len(validation_ids) != 4 or len(set(validation_ids)) != 4:
        raise ValueError("Validation confirmation cohort must contain four unique clips")
    unknown_validation = sorted(set(validation_ids) - public_valid_ids)
    if unknown_validation:
        raise ValueError(
            f"Validation cohort contains unknown/non-validation IDs: {unknown_validation}"
        )
    if cohort.get("selection_used_hidden_labels") is not False:
        raise ValueError("Pilot selection must explicitly exclude hidden labels")
    return cohort


def validate_sampling_candidate(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    decision_path = project_root / config["freezes"]["sampling_decision_path"]
    decision = load_json(decision_path)
    if decision.get("status") != "candidate_for_validation":
        raise ValueError("Sampling decision must have status candidate_for_validation")
    if decision.get("selected_frame_count") not in config["input_feasibility"]["frame_counts"]:
        raise ValueError("Sampling candidate is not one of the preregistered frame counts")
    if not decision.get("train_pilot_evidence_paths"):
        raise ValueError("Sampling candidate requires train-pilot evidence")
    capacity = decision.get("capacity_F60", {})
    if capacity.get("status") not in {"pass", "documented_failure"}:
        raise ValueError("F60 capacity must pass or have a preserved documented failure")
    if not capacity.get("evidence_run"):
        raise ValueError("F60 capacity decision requires a preserved evidence run")
    evidence = [project_root / item for item in decision["train_pilot_evidence_paths"]]
    evidence.append(project_root / capacity["evidence_run"])
    missing = [str(path) for path in evidence if not path.exists()]
    if missing:
        raise ValueError(f"Sampling candidate evidence does not exist: {missing}")
    return decision


def create_sampling_freeze(
    config: dict[str, Any], project_root: Path, destination: Path
) -> dict[str, Any]:
    decision_path = project_root / config["freezes"]["sampling_decision_path"]
    decision = load_json(decision_path)
    if decision.get("status") != "approved":
        raise ValueError("Sampling decision status must be approved")
    selected_value = decision.get("selected_frame_count")
    candidates = config["input_feasibility"]["frame_counts"]
    if (
        not isinstance(selected_value, int)
        or isinstance(selected_value, bool)
        or selected_value not in candidates
    ):
        raise ValueError(f"selected_frame_count must be one of {candidates}")
    selected = selected_value
    if not decision.get("model_tag") or not decision.get("model_digest"):
        raise ValueError("Sampling decision requires exact model tag and digest")
    capacity = decision.get("capacity_F60", {})
    if capacity.get("status") not in {"pass", "documented_failure"}:
        raise ValueError("The real-model F60 capacity gate lacks a preserved result")
    if not capacity.get("evidence_run"):
        raise ValueError("The F60 capacity gate requires a preserved evidence run")
    if not decision.get("train_pilot_evidence_paths"):
        raise ValueError("Sampling decision requires train pilot evidence")
    if not decision.get("validation_confirmation_paths"):
        raise ValueError("Sampling decision requires validation confirmation")
    evidence_paths = [
        project_root / item
        for item in decision["train_pilot_evidence_paths"]
        + decision["validation_confirmation_paths"]
    ]
    missing = [str(path) for path in evidence_paths if not path.exists()]
    if missing:
        raise ValueError(f"Sampling evidence does not exist: {missing}")
    total = int(config["dataset_b"]["expected_frames"])
    indices = (
        [total // 2 + 1]
        if selected == 1
        else [round(i * (total - 1) / (selected - 1)) + 1 for i in range(selected)]
    )
    cohort_path = project_root / config["input_feasibility"]["pilot_cohort_path"]
    cohort = validate_pilot_cohort(
        cohort_path, project_root / config["dataset_b"]["public_manifest"]
    )
    public_manifest = project_root / config["dataset_b"]["public_manifest"]
    selected_frame_hashes: dict[str, dict[str, str]] = {}
    frozen_clip_ids = cohort["clip_ids"] + cohort["validation_confirmation_clip_ids"]
    for clip_id in frozen_clip_ids:
        directory = (
            project_root
            / "artifacts/model_inputs/dataset_b"
            / clip_id
            / f"uniform_{selected}_edge_{decision['maximum_edge']}"
        )
        paths = [
            directory / f"{order:02d}_frame_{frame_index:06d}.jpg"
            for order, frame_index in enumerate(indices, start=1)
        ]
        missing_frames = [str(path) for path in paths if not path.is_file()]
        if missing_frames:
            raise ValueError(
                f"Cannot freeze sampling before selected frames exist: {missing_frames[:3]}"
            )
        selected_frame_hashes[clip_id] = {
            path.relative_to(project_root).as_posix(): sha256_file(path) for path in paths
        }
    query_prompt = project_root / config["prompts"]["dataset_b_task"]
    payload = {
        "freeze_type": "dataset_b_sampling",
        "protocol_id": config["protocol_id"],
        "created_at_utc": timestamp_utc(),
        "frame_count": selected,
        "frame_indices_1_based": indices,
        "maximum_edge": decision["maximum_edge"],
        "sampling_algorithm": decision["sampling_algorithm"],
        "image_encoding": config["input_feasibility"]["image_encoding"],
        "model_tag": decision["model_tag"],
        "model_digest": decision["model_digest"],
        "decision_sha256": sha256_file(decision_path),
        "pilot_cohort_sha256": sha256_file(cohort_path),
        "public_manifest_sha256": sha256_file(public_manifest),
        "dataset_b_task_prompt_sha256": sha256_file(query_prompt),
        "selected_frame_sha256": selected_frame_hashes,
        "evidence_sha256": {
            path.relative_to(project_root).as_posix(): sha256_path(path) for path in evidence_paths
        },
    }
    write_json_exclusive(destination, payload)
    return payload


def validate_sampling_freeze(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    freeze_path = project_root / config["freezes"]["sampling_freeze_path"]
    freeze = load_json(freeze_path)
    checks = {
        "pilot_cohort_sha256": project_root / config["input_feasibility"]["pilot_cohort_path"],
        "public_manifest_sha256": project_root / config["dataset_b"]["public_manifest"],
        "dataset_b_task_prompt_sha256": project_root / config["prompts"]["dataset_b_task"],
    }
    for field, path in checks.items():
        if freeze.get(field) != sha256_file(path):
            raise ValueError(f"Sampling freeze is stale: {path}")
    if freeze.get("sampling_algorithm") != "uniform_endpoints_v1":
        raise ValueError("Unsupported frozen sampling algorithm")
    for relative, expected_hash in freeze.get("evidence_sha256", {}).items():
        if sha256_path(project_root / relative) != expected_hash:
            raise ValueError(f"Sampling freeze evidence changed: {relative}")
    selected_frames = freeze.get("selected_frame_sha256")
    if not selected_frames:
        raise ValueError("Sampling freeze contains no selected frame hashes")
    for clip_hashes in selected_frames.values():
        for relative, expected_hash in clip_hashes.items():
            if sha256_file(project_root / relative) != expected_hash:
                raise ValueError(f"Frozen Dataset B frame changed: {relative}")
    return freeze


def create_protocol_freeze(
    config: dict[str, Any], project_root: Path, destination: Path
) -> dict[str, Any]:
    sampling_path = project_root / config["freezes"]["sampling_freeze_path"]
    validate_sampling_freeze(config, project_root)
    decision_path = project_root / config["freezes"]["protocol_decision_path"]
    decision = load_json(decision_path)
    if decision.get("status") != "approved" or not decision.get("approved_for_single_test_run"):
        raise ValueError("Protocol decision must explicitly approve the single test run")
    if not decision.get("selected_model_tag") or not decision.get("selected_model_digest"):
        raise ValueError("Protocol decision requires exact selected model tag and digest")
    validation_paths = [project_root / item for item in decision.get("validation_result_paths", [])]
    if not validation_paths or any(not path.exists() for path in validation_paths):
        raise ValueError("Protocol decision requires existing validation result paths")
    index_path = project_root / decision["retrieval_index_path"]
    if not index_path.is_file():
        raise ValueError(f"Retrieval index does not exist: {index_path}")
    if int(decision["retrieval_k"]) != int(config["retrieval"]["k"]):
        raise ValueError("Protocol decision k does not match config")
    from .catalog import load_case
    case_paths = sorted(project_root.glob(config["dataset_a"]["case_glob"]))
    cases = [load_case(path) for path in case_paths]
    approved = [
        case
        for case in cases
        if case.status == "approved" and not case.approval_errors(project_root)
    ]
    from .retrieval import EmbeddingIndex

    index = EmbeddingIndex.load(index_path)
    expected_case_ids = sorted(case.case_id for case in approved)
    if sorted(index.case_ids) != expected_case_ids:
        raise ValueError("Retrieval index case IDs do not match approved Dataset A cases")
    current_case_hashes = {
        case.case_id: sha256_file(project_root / "data/video_a/cases" / f"{case.case_id}.json")
        for case in approved
    }
    current_advice_hashes = {
        case.case_id: sha256_file(project_root / case.coaching.advice_path) for case in approved
    }
    current_media_hashes = {
        case.case_id: sha256_file(project_root / str(case.source.local_media_path))
        for case in approved
    }
    if index.metadata.get("case_metadata_sha256") != current_case_hashes:
        raise ValueError("Retrieval index was not built from current Dataset A metadata")
    if index.metadata.get("case_advice_sha256") != current_advice_hashes:
        raise ValueError("Retrieval index provenance does not match current Dataset A advice")
    if index.metadata.get("case_media_sha256") != current_media_hashes:
        raise ValueError("Retrieval index was not built from current Dataset A media")
    prompt_paths = {name: project_root / path for name, path in config["prompts"].items()}
    rubric_path = project_root / config["scoring"]["rubric_path"]
    payload = {
        "freeze_type": "single_final_test_protocol",
        "protocol_id": config["protocol_id"],
        "created_at_utc": timestamp_utc(),
        "sampling_freeze_sha256": sha256_file(sampling_path),
        "prompt_sha256": {name: sha256_file(path) for name, path in prompt_paths.items()},
        "rubric_sha256": sha256_file(rubric_path),
        "retrieval_index_path": decision["retrieval_index_path"],
        "retrieval_index_sha256": sha256_file(index_path),
        "retrieval_encoder": config["retrieval"]["encoder"],
        "retrieval_k": config["retrieval"]["k"],
        "model_tag": decision["selected_model_tag"],
        "model_digest": decision["selected_model_digest"],
        "generation_settings": config["generation"],
        "conditions": config["conditions"],
        "model_output": config["model_output"],
        "dataset_a_case_sha256": {
            path.relative_to(project_root).as_posix(): sha256_file(path) for path in case_paths
        },
        "dataset_a_advice_sha256": {
            case.coaching.advice_path: sha256_file(project_root / case.coaching.advice_path)
            for case in approved
        },
        "dataset_a_media_sha256": {
            str(case.source.local_media_path): sha256_file(
                project_root / str(case.source.local_media_path)
            )
            for case in approved
        },
        "validation_evidence_sha256": {
            path.relative_to(project_root).as_posix(): sha256_path(path)
            for path in validation_paths
        },
        "decision_sha256": sha256_file(decision_path),
    }
    write_json_exclusive(destination, payload)
    return payload


def validate_protocol_freeze(config: dict[str, Any], project_root: Path) -> dict[str, Any]:
    from .catalog import load_case
    freeze_path = project_root / config["freezes"]["protocol_freeze_path"]
    freeze = load_json(freeze_path)
    sampling_path = project_root / config["freezes"]["sampling_freeze_path"]
    if freeze.get("sampling_freeze_sha256") != sha256_file(sampling_path):
        raise ValueError("Protocol freeze is stale: sampling freeze changed")
    for name, relative in config["prompts"].items():
        if freeze["prompt_sha256"].get(name) != sha256_file(project_root / relative):
            raise ValueError(f"Protocol freeze is stale: prompt {name} changed")
    rubric_path = project_root / config["scoring"]["rubric_path"]
    if freeze.get("rubric_sha256") != sha256_file(rubric_path):
        raise ValueError("Protocol freeze is stale: scoring rubric changed")
    index_path = project_root / freeze["retrieval_index_path"]
    if freeze.get("retrieval_index_sha256") != sha256_file(index_path):
        raise ValueError("Protocol freeze is stale: retrieval index changed")
    if freeze.get("retrieval_encoder") != config["retrieval"]["encoder"]:
        raise ValueError("Protocol freeze is stale: retrieval encoder changed")
    if freeze.get("retrieval_k") != config["retrieval"]["k"]:
        raise ValueError("Protocol freeze is stale: retrieval k changed")
    if freeze.get("generation_settings") != config["generation"]:
        raise ValueError("Protocol freeze is stale: generation settings changed")
    if freeze.get("conditions") != config["conditions"]:
        raise ValueError("Protocol freeze is stale: conditions changed")
    if freeze.get("model_output") != config["model_output"]:
        raise ValueError("Protocol freeze is stale: model output contract changed")
    current_cases = sorted(project_root.glob(config["dataset_a"]["case_glob"]))
    current_hashes = {
        path.relative_to(project_root).as_posix(): sha256_file(path) for path in current_cases
    }
    if freeze.get("dataset_a_case_sha256") != current_hashes:
        raise ValueError("Protocol freeze is stale: Dataset A eligibility files changed")
    cases = [load_case(path) for path in current_cases]
    approved = [
        case
        for case in cases
        if case.status == "approved" and not case.approval_errors(project_root)
    ]
    current_advice = {
        case.coaching.advice_path: sha256_file(project_root / case.coaching.advice_path)
        for case in approved
    }
    current_media = {
        str(case.source.local_media_path): sha256_file(
            project_root / str(case.source.local_media_path)
        )
        for case in approved
    }
    if freeze.get("dataset_a_advice_sha256") != current_advice:
        raise ValueError("Protocol freeze is stale: Dataset A advice changed")
    if freeze.get("dataset_a_media_sha256") != current_media:
        raise ValueError("Protocol freeze is stale: Dataset A media changed")
    for relative, expected_hash in freeze.get("validation_evidence_sha256", {}).items():
        if sha256_path(project_root / relative) != expected_hash:
            raise ValueError(f"Protocol validation evidence changed: {relative}")
    return freeze


def claim_test_attempt(
    config: dict[str, Any],
    project_root: Path,
    clip_id: str,
    condition: str,
    model: str,
) -> Path:
    if config["status"] != "frozen_test":
        raise ValueError("Test attempts can only be claimed in frozen_test state")
    freeze_path = project_root / config["freezes"]["protocol_freeze_path"]
    validate_protocol_freeze(config, project_root)
    safe_model = model.replace(":", "_")
    marker = (
        project_root
        / "data/video_b/private/test_attempts"
        / safe_model
        / condition
        / f"{clip_id}.json"
    )
    write_json_exclusive(
        marker,
        {
            "protocol_id": config["protocol_id"],
            "clip_id": clip_id,
            "condition": condition,
            "model": model,
            "claimed_at_utc": timestamp_utc(),
            "protocol_freeze_sha256": sha256_file(freeze_path),
            "policy": "A preserved failure counts as the single test attempt.",
        },
    )
    return marker
