from pathlib import Path

from football_coach.annotations import blank_annotation
from football_coach.dataset import ClipRecord


def test_blank_annotation_is_intentionally_incomplete() -> None:
    record = ClipRecord(
        "SNGS-001",
        "train",
        "Goal",
        "1",
        "1 - 00:00",
        "1 - 00:30",
        25,
        750,
        30.0,
        "1.3",
        "x.zip",
        "label",
        "%06d.jpg",
    )
    payload = blank_annotation(record)
    assert payload["review_status"] == "draft"
    assert payload["clip_id"] == "SNGS-001"


def test_schema_file_exists() -> None:
    assert Path("schemas/coaching_annotation.schema.json").is_file()

