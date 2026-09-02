from __future__ import annotations

import csv
import hashlib
import json
import random
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ClipRecord:
    clip_id: str
    split: str
    action_class: str
    game_id: str
    game_time_start: str
    game_time_stop: str
    frame_rate: int
    frame_count: int
    duration_seconds: float
    annotation_version: str
    archive_path: str
    label_member: str
    frame_member_pattern: str


FIELDS = list(ClipRecord.__dataclass_fields__)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _read_info(archive: zipfile.ZipFile, member: str) -> dict[str, Any]:
    with archive.open(member) as handle:
        payload = json.load(handle)
    info = payload.get("info")
    if not isinstance(info, dict):
        raise ValueError(f"Missing info object in {member}")
    return info


def index_archives(config: dict[str, Any], project_root: Path) -> list[ClipRecord]:
    expected = config["expected"]
    records: list[ClipRecord] = []
    for split, relative in config["source_archives"].items():
        archive_path = project_root / relative
        if not archive_path.is_file():
            raise FileNotFoundError(archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            labels = sorted(name for name in names if name.endswith("/Labels-GameState.json"))
            frame_counts: Counter[str] = Counter()
            for name in names:
                parts = name.split("/")
                if len(parts) == 3 and parts[1] == "img1" and name.lower().endswith(".jpg"):
                    frame_counts[parts[0]] += 1
            for label_member in labels:
                info = _read_info(archive, label_member)
                clip_id = str(info["name"])
                frame_count = frame_counts[clip_id]
                fps = int(info["frame_rate"])
                if str(info["version"]) != str(expected["annotation_version"]):
                    raise ValueError(f"{clip_id}: expected v{expected['annotation_version']}")
                if frame_count != int(expected["frames_per_clip"]):
                    raise ValueError(
                        f"{clip_id}: expected {expected['frames_per_clip']} frames, "
                        f"got {frame_count}"
                    )
                if fps != int(expected["frame_rate"]):
                    raise ValueError(f"{clip_id}: expected {expected['frame_rate']} fps, got {fps}")
                records.append(
                    ClipRecord(
                        clip_id=clip_id,
                        split=split,
                        action_class=str(info["action_class"]),
                        game_id=str(info["game_id"]),
                        game_time_start=str(info["game_time_start"]),
                        game_time_stop=str(info["game_time_stop"]),
                        frame_rate=fps,
                        frame_count=frame_count,
                        duration_seconds=frame_count / fps,
                        annotation_version=str(info["version"]),
                        archive_path=relative.replace("\\", "/"),
                        label_member=label_member,
                        frame_member_pattern=f"{clip_id}/img1/%06d.jpg",
                    )
                )
    records.sort(key=lambda row: (row.split, row.clip_id))
    if len(records) != int(expected["source_clip_count"]):
        raise ValueError(f"Expected {expected['source_clip_count']} clips, got {len(records)}")
    return records


def write_manifest(records: list[ClipRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def read_manifest(path: Path) -> list[ClipRecord]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [
        ClipRecord(
            clip_id=row["clip_id"],
            split=row["split"],
            action_class=row["action_class"],
            game_id=row["game_id"],
            game_time_start=row["game_time_start"],
            game_time_stop=row["game_time_stop"],
            frame_rate=int(row["frame_rate"]),
            frame_count=int(row["frame_count"]),
            duration_seconds=float(row["duration_seconds"]),
            annotation_version=row["annotation_version"],
            archive_path=row["archive_path"],
            label_member=row["label_member"],
            frame_member_pattern=row["frame_member_pattern"],
        )
        for row in rows
    ]


def _allocate(groups: dict[str, list[ClipRecord]], target: int) -> dict[str, int]:
    total = sum(len(items) for items in groups.values())
    if target > total:
        raise ValueError(f"Cannot select {target} from {total}")
    if target < len(groups):
        raise ValueError("Target is too small to include every action class")
    quotas = {name: target * len(items) / total for name, items in groups.items()}
    allocated = {name: min(len(groups[name]), max(1, int(quota))) for name, quota in quotas.items()}
    while sum(allocated.values()) < target:
        candidates = [name for name in groups if allocated[name] < len(groups[name])]
        name = max(
            candidates,
            key=lambda item: (quotas[item] - allocated[item], len(groups[item]), item),
        )
        allocated[name] += 1
    while sum(allocated.values()) > target:
        candidates = [name for name in groups if allocated[name] > 1]
        name = min(
            candidates,
            key=lambda item: (quotas[item] - allocated[item], -len(groups[item]), item),
        )
        allocated[name] -= 1
    return allocated


def select_records(
    records: list[ClipRecord], targets: dict[str, int], seed: int
) -> tuple[list[ClipRecord], dict[str, dict[str, int]]]:
    by_split: dict[str, dict[str, list[ClipRecord]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        by_split[record.split][record.action_class].append(record)
    selected: list[ClipRecord] = []
    allocations: dict[str, dict[str, int]] = {}
    for split, target in targets.items():
        groups = dict(by_split[split])
        allocation = _allocate(groups, target)
        allocations[split] = dict(sorted(allocation.items()))
        for action, count in allocation.items():
            candidates = sorted(groups[action], key=lambda row: row.clip_id)
            rng = random.Random(f"{seed}:{split}:{action}")
            rng.shuffle(candidates)
            selected.extend(candidates[:count])
    selected.sort(key=lambda row: (row.split, row.clip_id))
    return selected, allocations
