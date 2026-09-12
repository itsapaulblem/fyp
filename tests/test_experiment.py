import csv
import json
from pathlib import Path

import pytest

from football_coach.experiment import (
    prepare_pilot_grading,
    validate_pilot_cohort,
    validate_score,
)
from football_coach.provenance import sha256_file


def test_pilot_cohort_uses_only_public_split_membership(tmp_path: Path) -> None:
    manifest = tmp_path / "public.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["clip_id", "split"])
        writer.writeheader()
        writer.writerows(
            [
                *({"clip_id": f"B-TRAIN-{number:04d}", "split": "train"} for number in range(1, 9)),
                *({"clip_id": f"B-VALID-{number:04d}", "split": "valid"} for number in range(1, 5)),
            ]
        )
    cohort = {
        "clip_ids": [f"B-TRAIN-{number:04d}" for number in range(1, 9)],
        "validation_confirmation_clip_ids": [f"B-VALID-{number:04d}" for number in range(1, 5)],
        "selection_used_hidden_labels": False,
    }
    cohort_path = tmp_path / "cohort.json"
    cohort_path.write_text(json.dumps(cohort), encoding="utf-8")
    assert validate_pilot_cohort(cohort_path, manifest) == cohort


def completed_score_text() -> str:
    return """\
Rubric version: 1.0
Blind run ID: blind-1
Dataset B clip ID: B-TRAIN-0001
Recognition scored before case or condition reveal: yes
Possession score: 2
Possession reason: Correct team is visibly in possession.
Temporal sequence score: 4
Temporal sequence reason: All key events are correctly ordered.
Tactical phase score: 2
Tactical phase reason: The visible phase is correctly identified.
Main event score: 2
Main event reason: The main event matches the human reference.
Outcome score: 2
Outcome reason: The final outcome is visible and correct.
Visible evidence score: 2
Visible evidence reason: Specific claims are grounded in the frames.
Analogy relevance score: N/A
Analogy relevance reason: B0 supplied no Dataset A material.
Problem identification score: 2
Problem identification reason: The priority problem follows from the frames.
Advice quality score: 3
Advice quality reason: The advice is specific and actionable.
Practice representativeness score: 2
Practice representativeness reason: The practice recreates the problem.
Coaching evidence support score: 2
Coaching evidence support reason: Coaching is tied to visible evidence.
Hallucination categories: none
Hallucination severity score: 0
Hallucination reason: No unsupported material claim was found.
Blind copying score: N/A
Blind copying reason: B0 supplied no Dataset A material.
Unsupported transfer score: N/A
Unsupported transfer reason: B0 supplied no Dataset A material.
Uncertainty calibration score: 2
Uncertainty calibration reason: Confidence matches visibility.
Critical event missed: no
Critical event missed reason: The decisive visible event was included.
Reviewer notes:
"""


def write_score_files(tmp_path: Path, score_text: str) -> tuple[Path, Path]:
    rubric_path = tmp_path / "rubric.txt"
    rubric_path.write_text("Rubric version: 1.0\n", encoding="utf-8")
    score_path = tmp_path / "score.txt"
    score_path.write_text(score_text, encoding="utf-8")
    return score_path, rubric_path


def test_valid_plain_text_score(tmp_path: Path) -> None:
    score_path, rubric_path = write_score_files(tmp_path, completed_score_text())
    score = validate_score(score_path, rubric_path)
    assert score.run_id == "blind-1"
    assert score.recognition["temporal_sequence"] == 4
    assert score.retrieval_relevance["analogy_relevance"] is None


def test_score_requires_recognition_blinding(tmp_path: Path) -> None:
    text = completed_score_text().replace(
        "Recognition scored before case or condition reveal: yes",
        "Recognition scored before case or condition reveal: no",
    )
    score_path, rubric_path = write_score_files(tmp_path, text)
    with pytest.raises(ValueError, match="Recognition must be scored"):
        validate_score(score_path, rubric_path)


def test_score_rejects_missing_value(tmp_path: Path) -> None:
    text = completed_score_text().replace("Main event score: 2", "Main event score:")
    score_path, rubric_path = write_score_files(tmp_path, text)
    with pytest.raises(ValueError, match="Main event score is missing"):
        validate_score(score_path, rubric_path)


def test_score_rejects_out_of_range_value(tmp_path: Path) -> None:
    text = completed_score_text().replace("Advice quality score: 3", "Advice quality score: 4")
    score_path, rubric_path = write_score_files(tmp_path, text)
    with pytest.raises(ValueError, match=r"Advice quality score must be an integer in \[0, 3\]"):
        validate_score(score_path, rubric_path)


def test_score_rejects_na_for_required_dimension(tmp_path: Path) -> None:
    text = completed_score_text().replace("Outcome score: 2", "Outcome score: N/A")
    score_path, rubric_path = write_score_files(tmp_path, text)
    with pytest.raises(ValueError, match="Outcome score cannot be N/A"):
        validate_score(score_path, rubric_path)


def test_score_rejects_partial_b0_na_set(tmp_path: Path) -> None:
    text = completed_score_text().replace("Blind copying score: N/A", "Blind copying score: 0")
    score_path, rubric_path = write_score_files(tmp_path, text)
    with pytest.raises(ValueError, match="B0 requires N/A"):
        validate_score(score_path, rubric_path)


def test_score_rejects_inconsistent_hallucination_values(tmp_path: Path) -> None:
    text = completed_score_text().replace(
        "Hallucination categories: none", "Hallucination categories: temporal"
    )
    score_path, rubric_path = write_score_files(tmp_path, text)
    with pytest.raises(ValueError, match="severity 0 requires category 'none'"):
        validate_score(score_path, rubric_path)


def _write_pilot_grading_fixture(root: Path) -> dict:
    (root / "config").mkdir()
    (root / "templates").mkdir()
    (root / "data/video_b/manifests").mkdir(parents=True)
    (root / "data/video_b/review").mkdir(parents=True)
    clip_ids = [f"B-TRAIN-{number:04d}" for number in range(1, 9)]
    validation_ids = [f"B-VALID-{number:04d}" for number in range(1, 5)]
    manifest = root / "data/video_b/manifests/public.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["clip_id", "split"])
        writer.writeheader()
        writer.writerows({"clip_id": value, "split": "train"} for value in clip_ids)
        writer.writerows({"clip_id": value, "split": "valid"} for value in validation_ids)
    cohort = {
        "cohort_id": "test-pilot",
        "condition": "B0_frames_only",
        "clip_ids": clip_ids,
        "validation_confirmation_clip_ids": validation_ids,
        "frame_counts": [10, 20, 30, 60],
        "selection_used_hidden_labels": False,
    }
    (root / "config/cohort.json").write_text(json.dumps(cohort), encoding="utf-8")
    (root / "config/rubric.txt").write_text("Rubric version: 1.0\n", encoding="utf-8")
    (root / "templates/score.txt").write_text(
        "Blind run ID: {{BLIND_RUN_ID}}\nDataset B clip ID: {{DATASET_B_CLIP_ID}}\n",
        encoding="utf-8",
    )
    config = {
        "seed": 7,
        "input_feasibility": {
            "pilot_cohort_path": "config/cohort.json",
            "compatible_pilot_config_sha256": [],
        },
        "dataset_b": {"public_manifest": "data/video_b/manifests/public.csv"},
        "model_output": {"answer_file": "response.txt"},
        "scoring": {
            "score_template": "templates/score.txt",
            "rubric_path": "config/rubric.txt",
            "rubric_version": "1.0",
        },
    }
    config_path = root / "config/project_v0.3.0.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    config_hash = sha256_file(config_path)
    reference_base = {
        "reference_version": "0.3.0",
        "review_status": "approved",
        "reviewer": {
            "name_or_code": "R1",
            "football_qualification_or_experience": "Researcher",
            "reviewed_at_utc": "2026-01-01T00:00:00Z",
        },
        "review_protocol": {
            "used_only_neutral_id_and_frames": True,
            "blinded_to_soccernet_label_during_visual_review": True,
            "blinded_to_model_answers": True,
            "blinded_to_dataset_a_pairs": True,
        },
        "visual_reference": {
            "chronological_visible_description": ["A pass is visible."],
            "possession_by_visible_appearance": "Red team",
            "tactical_phase": "Open play",
            "main_visible_event": "Pass",
            "outcome": "Play continues",
            "visibility_limitations": ["Wide view"],
        },
        "sampling_visibility": {
            name: {"event_visible": True, "notes": "Visible"}
            for name in ["F10", "F20", "F30", "F60"]
        },
        "hidden_reference": {
            "soccernet_action_label": "Corner",
            "attached_only_after_visual_review": True,
            "used_as_coaching_ground_truth": False,
            "blind_snapshot_path": "private/snapshot.json",
            "blind_snapshot_sha256": "a" * 64,
        },
    }
    response = (
        "RECOGNITION\nA pass occurs.\n\nANALOGY\nCase used: no\n\n"
        "COACHING\nAdvice.\n\nUNCERTAINTY\nConfidence: medium\n"
    )
    for clip_id in clip_ids:
        reference = {**reference_base, "clip_id": clip_id}
        (root / f"data/video_b/review/{clip_id}.json").write_text(
            json.dumps(reference), encoding="utf-8"
        )
        for frame_count in cohort["frame_counts"]:
            run = root / f"output/B0_frames_only/qwen3.5_27b/{clip_id}/run-{frame_count}"
            run.mkdir(parents=True)
            frame_hashes = {}
            for index in range(1, frame_count + 1):
                frame = root / f"artifacts/{clip_id}/{frame_count}/frame-{index}.jpg"
                frame.parent.mkdir(parents=True, exist_ok=True)
                frame.write_bytes(f"{clip_id}-{frame_count}-{index}".encode())
                frame_hashes[frame.relative_to(root).as_posix()] = sha256_file(frame)
            metadata = {
                "condition": "B0_frames_only",
                "dataset_b_clip_id": clip_id,
                "dataset_b_frame_count": frame_count,
                "frame_sha256": frame_hashes,
                "config_sha256": config_hash,
                "model": "qwen3.5:27b",
                "model_digest": "b" * 64,
                "run_status": "complete",
                "answer_format_status": "valid",
            }
            (run / "metadata.txt").write_text(
                "\n".join(f"{key}: {json.dumps(value)}" for key, value in metadata.items()),
                encoding="utf-8",
            )
            (run / "response.txt").write_text(response, encoding="utf-8")
    return config


def test_prepare_pilot_grading_builds_verified_non_overwriting_package(
    tmp_path: Path,
) -> None:
    config = _write_pilot_grading_fixture(tmp_path)
    destination = tmp_path / "data/video_b/review/pilot_grading_v1"
    mapping_path = tmp_path / "data/video_b/private/pilot_grading_mapping_v1.json"
    summary = prepare_pilot_grading(config, tmp_path, destination, mapping_path)

    assert summary["item_count"] == 32
    assert summary["frame_count"] == 960
    assert len(list(destination.glob("PILOT-*"))) == 32
    assert len(list(destination.glob("PILOT-*/frames/*.jpg"))) == 960
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    assert len(mapping["entries"]) == 32
    assert all(
        entry["source_response_sha256"] == entry["blind_response_sha256"]
        for entry in mapping["entries"]
    )
    with pytest.raises(FileExistsError, match="already exists"):
        prepare_pilot_grading(config, tmp_path, destination, mapping_path)
