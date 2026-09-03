import json
import zipfile
from pathlib import Path

from football_coach.soccernet import index_dataset_b


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
    assert records[0].clip_id == "SNGS-001"
    assert records[0].action_class == "Corner"

