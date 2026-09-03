from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from .domain import SoccerNetClip

PRIVATE_FIELDS = [field.name for field in SoccerNetClip.__dataclass_fields__.values()]
PUBLIC_FIELDS = ["clip_id", "split", "frame_rate", "frame_count", "duration_seconds"]
SPLIT_ORDER = ("train", "valid", "test")


def index_dataset_b(config: dict, project_root: Path) -> list[SoccerNetClip]:
    """Index Dataset B with neutral IDs while keeping source identifiers private."""
    settings = config["dataset_b"]
    records: list[SoccerNetClip] = []
    seen_source_ids: set[str] = set()
    for split in (name for name in SPLIT_ORDER if name in settings["archives"]):
        relative_path = settings["archives"][split]
        archive_path = project_root / relative_path
        if not archive_path.is_file():
            raise FileNotFoundError(archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            labels = sorted(name for name in names if name.endswith("/Labels-GameState.json"))
            expected_count = int(settings["expected_split_counts"][split])
            if len(labels) != expected_count:
                raise ValueError(f"{split}: expected {expected_count} labels, got {len(labels)}")
            for ordinal, label_member in enumerate(labels, start=1):
                source_clip_id = label_member.split("/", maxsplit=1)[0]
                if source_clip_id in seen_source_ids:
                    raise ValueError(f"Duplicate SoccerNet source clip ID: {source_clip_id}")
                seen_source_ids.add(source_clip_id)
                with archive.open(label_member) as handle:
                    info = json.load(handle)["info"]
                if str(info["name"]) != source_clip_id:
                    raise ValueError(
                        f"{source_clip_id}: label info.name is {info['name']!r}"
                    )
                frame_members = sorted(
                    name
                    for name in names
                    if name.startswith(f"{source_clip_id}/img1/")
                    and name.lower().endswith(".jpg")
                )
                expected_frames = int(settings["expected_frames"])
                expected_members = [
                    f"{source_clip_id}/img1/{number:06d}.jpg"
                    for number in range(1, expected_frames + 1)
                ]
                if frame_members != expected_members:
                    missing = sorted(set(expected_members) - set(frame_members))
                    unexpected = sorted(set(frame_members) - set(expected_members))
                    raise ValueError(
                        f"{source_clip_id}: non-contiguous frame sequence; "
                        f"missing={missing[:5]} unexpected={unexpected[:5]}"
                    )
                record = SoccerNetClip(
                    clip_id=f"B-{split.upper()}-{ordinal:04d}",
                    source_clip_id=source_clip_id,
                    split=split,
                    action_class=str(info["action_class"]),
                    frame_rate=int(info["frame_rate"]),
                    frame_count=len(frame_members),
                    annotation_version=str(info["version"]),
                    archive_path=str(relative_path).replace("\\", "/"),
                    label_member=label_member,
                    frame_member_pattern=f"{source_clip_id}/img1/%06d.jpg",
                )
                _validate_record(record, info, settings)
                records.append(record)
    return records


def _validate_record(record: SoccerNetClip, info: dict, settings: dict) -> None:
    expected = {
        "annotation version": (
            record.annotation_version,
            str(settings["expected_annotation_version"]),
        ),
        "frame count": (record.frame_count, int(settings["expected_frames"])),
        "frame rate": (record.frame_rate, int(settings["expected_fps"])),
        "sequence length": (
            int(info.get("seq_length", record.frame_count)),
            int(settings["expected_frames"]),
        ),
    }
    for name, (actual, wanted) in expected.items():
        if actual != wanted:
            raise ValueError(
                f"{record.source_clip_id}: expected {name} {wanted}, got {actual}"
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def audit_dataset_b(
    records: list[SoccerNetClip],
    project_root: Path,
    progress: Callable[[str], None] | None = None,
) -> dict:
    """CRC-read and decode every Dataset B JPEG without changing raw archives."""
    issues: list[str] = []
    resolution_counts: Counter[str] = Counter()
    decoded_frames = 0
    archive_reports: list[dict] = []
    grouped: dict[str, list[SoccerNetClip]] = defaultdict(list)
    for record in records:
        grouped[record.archive_path].append(record)
    for relative_path, archive_records in grouped.items():
        archive_path = project_root / relative_path
        if progress:
            progress(f"Hashing {relative_path}")
        archive_report = {
            "archive_path": relative_path,
            "size_bytes": archive_path.stat().st_size,
            "sha256": _sha256(archive_path),
            "clips": len(archive_records),
        }
        archive_reports.append(archive_report)
        if progress:
            progress(f"Decoding {len(archive_records)} clips from {relative_path}")
        with zipfile.ZipFile(archive_path) as archive:
            for clip_number, record in enumerate(archive_records, start=1):
                for frame_number in range(1, record.frame_count + 1):
                    member = record.frame_member_pattern % frame_number
                    try:
                        payload = archive.read(member)
                        encoded = np.frombuffer(payload, dtype=np.uint8)
                        frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                        if frame is None:
                            raise ValueError("OpenCV returned no image")
                        if frame.ndim != 3 or frame.shape[2] != 3:
                            raise ValueError(f"unexpected image shape {frame.shape}")
                        height, width = frame.shape[:2]
                        resolution_counts[f"{width}x{height}"] += 1
                        decoded_frames += 1
                    except Exception as error:
                        issues.append(f"{record.clip_id} frame {frame_number}: {error}")
                if progress and (clip_number % 10 == 0 or clip_number == len(archive_records)):
                    progress(
                        f"{record.split}: decoded {clip_number}/{len(archive_records)} clips"
                    )
    expected_frames = sum(record.frame_count for record in records)
    return {
        "status": "pass" if not issues and decoded_frames == expected_frames else "fail",
        "dataset": "SoccerNet Game State Reconstruction",
        "annotation_version": "1.3",
        "raw_data_modified": False,
        "clip_count": len(records),
        "split_counts": {
            split: sum(record.split == split for record in records)
            for split in SPLIT_ORDER
        },
        "expected_frame_count": expected_frames,
        "decoded_frame_count": decoded_frames,
        "resolution_counts": dict(sorted(resolution_counts.items())),
        "archives": archive_reports,
        "issues": issues,
    }


def write_private_manifest(records: list[SoccerNetClip], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PRIVATE_FIELDS)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def write_public_manifest(records: list[SoccerNetClip], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PUBLIC_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "clip_id": record.clip_id,
                    "split": record.split,
                    "frame_rate": record.frame_rate,
                    "frame_count": record.frame_count,
                    "duration_seconds": record.frame_count / record.frame_rate,
                }
            )


def write_integrity_report(report: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def read_manifest(path: Path) -> list[SoccerNetClip]:
    """Read the private crosswalk used internally for sampling and evaluation."""
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.DictReader(handle)
        return [
            SoccerNetClip(
                clip_id=row["clip_id"],
                source_clip_id=row["source_clip_id"],
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
