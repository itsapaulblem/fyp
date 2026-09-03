from __future__ import annotations

import csv
import json
import zipfile
from dataclasses import asdict
from pathlib import Path

from .domain import SoccerNetClip

FIELDS = [field.name for field in SoccerNetClip.__dataclass_fields__.values()]


def index_dataset_b(config: dict, project_root: Path) -> list[SoccerNetClip]:
    settings = config["dataset_b"]
    records: list[SoccerNetClip] = []
    seen: set[str] = set()
    for split, relative_path in settings["archives"].items():
        archive_path = project_root / relative_path
        if not archive_path.is_file():
            raise FileNotFoundError(archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            labels = sorted(name for name in names if name.endswith("/Labels-GameState.json"))
            frame_counts: dict[str, int] = {}
            for name in names:
                parts = name.split("/")
                if len(parts) == 3 and parts[1] == "img1" and name.lower().endswith(".jpg"):
                    frame_counts[parts[0]] = frame_counts.get(parts[0], 0) + 1
            for label_member in labels:
                with archive.open(label_member) as handle:
                    info = json.load(handle)["info"]
                clip_id = str(info["name"])
                if clip_id in seen:
                    raise ValueError(f"Duplicate Dataset B clip ID: {clip_id}")
                seen.add(clip_id)
                record = SoccerNetClip(
                    clip_id=clip_id,
                    split=split,
                    action_class=str(info["action_class"]),
                    frame_rate=int(info["frame_rate"]),
                    frame_count=frame_counts.get(clip_id, 0),
                    annotation_version=str(info["version"]),
                    archive_path=str(relative_path).replace("\\", "/"),
                    label_member=label_member,
                    frame_member_pattern=f"{clip_id}/img1/%06d.jpg",
                )
                _validate_record(record, settings)
                records.append(record)
        expected_count = int(settings["expected_split_counts"][split])
        actual_count = sum(record.split == split for record in records)
        if actual_count != expected_count:
            raise ValueError(f"{split}: expected {expected_count} clips, got {actual_count}")
    return sorted(records, key=lambda record: (record.split, record.clip_id))


def _validate_record(record: SoccerNetClip, settings: dict) -> None:
    expected = {
        "annotation version": (
            record.annotation_version,
            str(settings["expected_annotation_version"]),
        ),
        "frame count": (record.frame_count, int(settings["expected_frames"])),
        "frame rate": (record.frame_rate, int(settings["expected_fps"])),
    }
    for name, (actual, wanted) in expected.items():
        if actual != wanted:
            raise ValueError(f"{record.clip_id}: expected {name} {wanted}, got {actual}")


def write_manifest(records: list[SoccerNetClip], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def read_manifest(path: Path) -> list[SoccerNetClip]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return [
            SoccerNetClip(
                clip_id=row["clip_id"],
                split=row["split"],
                action_class=row["action_class"],
                frame_rate=int(row["frame_rate"]),
                frame_count=int(row["frame_count"]),
                annotation_version=row["annotation_version"],
                archive_path=row["archive_path"],
                label_member=row["label_member"],
                frame_member_pattern=row["frame_member_pattern"],
            )
            for row in rows
        ]
