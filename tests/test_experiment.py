import csv
import json
from pathlib import Path

import pytest

from football_coach.experiment import validate_pilot_cohort, validate_score


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
