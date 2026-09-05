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


def test_score_requires_recognition_blinding(tmp_path: Path) -> None:
    rubric = {
        "dimensions": {
            "recognition": {"main_event": {"range": [0, 2]}},
            "retrieval_relevance": {"analogy_relevance": {"range": [0, 3]}},
            "coaching": {"advice_quality": {"range": [0, 3]}},
            "failure_modes": {"hallucination_severity": {"range": [0, 3]}},
            "uncertainty": {"calibration": {"range": [0, 2]}},
        }
    }
    score = {
        "score_version": "0.3.0",
        "run_id": "blind-1",
        "clip_id": "B-TRAIN-0001",
        "scorer": {},
        "blinding": {"condition_hidden_during_recognition_scoring": False},
        "recognition": {"main_event": 2},
        "retrieval_relevance": {"analogy_relevance": None, "not_applicable_reason": "B0"},
        "coaching": {"advice_quality": 2},
        "failure_modes": {"hallucination_severity": 0},
        "uncertainty": {"calibration": 2},
        "notes": "",
    }
    rubric_path = tmp_path / "rubric.json"
    score_path = tmp_path / "score.json"
    rubric_path.write_text(json.dumps(rubric), encoding="utf-8")
    score_path.write_text(json.dumps(score), encoding="utf-8")
    with pytest.raises(ValueError, match="Recognition must be scored"):
        validate_score(score_path, rubric_path)
