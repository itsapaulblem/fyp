import json
import zipfile
from pathlib import Path

from football_coach.soccernet import (
    index_dataset_b,
    read_manifest,
    write_private_manifest,
    write_public_manifest,
)


def test_dataset_b_index_uses_official_info(tmp_path: Path) -> None:
    archive_path = tmp_path / "train.zip"
    info = {
        "info": {
            "name": "SNGS-001",
            "action_class": "Corner",
            "frame_rate": 25,
            "seq_length": 2,
            "version": "1.3",
        }
    }
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("SNGS-001/Labels-GameState.json", json.dumps(info))
        archive.writestr("SNGS-001/img1/000001.jpg", b"one")
        archive.writestr("SNGS-001/img1/000002.jpg", b"two")
    config = {
        "dataset_b": {
            "archives": {"train": "train.zip"},
            "expected_split_counts": {"train": 1},
            "expected_annotation_version": "1.3",
            "expected_frames": 2,
            "expected_fps": 25,
        }
    }
    records = index_dataset_b(config, tmp_path)
    assert records[0].clip_id == "B-TRAIN-0001"
    assert records[0].source_clip_id == "SNGS-001"
    assert records[0].action_class == "Corner"

    public_path = tmp_path / "public.csv"
    private_path = tmp_path / "private.csv"
    write_public_manifest(records, public_path)
    write_private_manifest(records, private_path)
    public_text = public_path.read_text(encoding="utf-8")
    assert "action_class" not in public_text
    assert "SNGS-001" not in public_text
    assert "archive_path" not in public_text
    assert read_manifest(private_path) == records


def test_dataset_b_index_rejects_non_contiguous_frames(tmp_path: Path) -> None:
    archive_path = tmp_path / "train.zip"
    info = {
        "info": {
            "name": "SNGS-001",
            "action_class": "Corner",
            "frame_rate": 25,
            "seq_length": 2,
            "version": "1.3",
        }
    }
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("SNGS-001/Labels-GameState.json", json.dumps(info))
        archive.writestr("SNGS-001/img1/000001.jpg", b"one")
        archive.writestr("SNGS-001/img1/000003.jpg", b"three")
    config = {
        "dataset_b": {
            "archives": {"train": "train.zip"},
            "expected_split_counts": {"train": 1},
            "expected_annotation_version": "1.3",
            "expected_frames": 2,
            "expected_fps": 25,
        }
    }
    try:
        index_dataset_b(config, tmp_path)
    except ValueError as error:
        assert "non-contiguous frame sequence" in str(error)
    else:
        raise AssertionError("Expected non-contiguous frames to be rejected")
