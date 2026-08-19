from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile, ZipFile


ACTION_GROUPS = {
    "Corner": "corner",
    "Direct free-kick": "direct_free_kick",
    "Indirect free-kick": "indirect_free_kick",
    "Penalty": "penalty",
    "Shots on target": "shot",
    "Shots off target": "shot",
    "Goal": "goal",
    "Foul": "foul",
    "Clearance": "clearance",
}


FIELDNAMES = [
    "clip_id",
    "split",
    "action_class",
    "scenario_group",
    "game_id",
    "game_time_start",
    "game_time_stop",
    "frame_rate",
    "frame_count",
    "duration_seconds",
    "annotation_version",
    "annotation_count",
    "player_boxes",
    "goalkeeper_boxes",
    "referee_boxes",
    "ball_boxes",
    "ball_annotated_frames",
    "ball_coverage",
    "archive_path",
    "label_member",
    "frame_member_pattern",
    "video_representation",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clip_row(split: str, archive: Path, member: str, payload: dict) -> dict:
    info = payload["info"]
    categories = {item["id"]: item["name"] for item in payload["categories"]}
    category_counts: Counter[str] = Counter()
    ball_frames: set[str] = set()

    for annotation in payload["annotations"]:
        category = categories.get(annotation["category_id"], "unknown")
        category_counts[category] += 1
        if category == "ball":
            ball_frames.add(str(annotation["image_id"]))

    frame_count = int(info["seq_length"])
    frame_rate = int(info["frame_rate"])
    clip_id = info["name"]
    archive_rel = archive.as_posix()
    return {
        "clip_id": clip_id,
        "split": split,
        "action_class": info["action_class"],
        "scenario_group": ACTION_GROUPS.get(info["action_class"], "other"),
        "game_id": info["game_id"],
        "game_time_start": info["game_time_start"],
        "game_time_stop": info["game_time_stop"],
        "frame_rate": frame_rate,
        "frame_count": frame_count,
        "duration_seconds": frame_count / frame_rate,
        "annotation_version": info["version"],
        "annotation_count": len(payload["annotations"]),
        "player_boxes": category_counts["player"],
        "goalkeeper_boxes": category_counts["goalkeeper"],
        "referee_boxes": category_counts["referee"],
        "ball_boxes": category_counts["ball"],
        "ball_annotated_frames": len(ball_frames),
        "ball_coverage": round(len(ball_frames) / frame_count, 6),
        "archive_path": archive_rel,
        "label_member": member,
        "frame_member_pattern": f"{clip_id}/img1/%06d.jpg",
        "video_representation": "jpeg_sequence",
    }


def build_manifest(project_root: Path) -> dict:
    archive_root = project_root / "data" / "raw" / "gamestate" / "gamestate-2024"
    output_root = project_root / "data" / "processed"
    output_root.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    archives: list[dict] = []

    for split in ("train", "valid", "test"):
        archive = archive_root / f"{split}.zip"
        if not archive.exists():
            raise FileNotFoundError(f"Missing official archive: {archive}")
        try:
            with ZipFile(archive) as zipped:
                members = zipped.namelist()
                label_members = sorted(
                    member
                    for member in members
                    if member.endswith("/Labels-GameState.json")
                )
                frame_members = sum(member.lower().endswith(".jpg") for member in members)
                index = json.loads(zipped.read("sequences_info.json"))
                index_key = "validation" if split == "valid" else split
                for member in label_members:
                    payload = json.loads(zipped.read(member))
                    rows.append(_clip_row(split, archive.relative_to(project_root), member, payload))
        except BadZipFile as exc:
            raise RuntimeError(f"Invalid ZIP archive: {archive}") from exc

        archives.append(
            {
                "split": split,
                "path": archive.relative_to(project_root).as_posix(),
                "size_bytes": archive.stat().st_size,
                "sha256": _sha256(archive),
                "label_files": len(label_members),
                "jpeg_frames": frame_members,
                "official_index_count": len(index[index_key]),
            }
        )

    rows.sort(key=lambda row: (row["split"], row["clip_id"]))
    manifest_path = output_root / "manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    action_counts = Counter(row["action_class"] for row in rows)
    scenario_counts = Counter(row["scenario_group"] for row in rows)
    split_counts = Counter(row["split"] for row in rows)
    summary = {
        "dataset_name": "soccernet_coaching_eval",
        "status": "verified" if len(rows) == 164 else "count_mismatch",
        "clip_count": len(rows),
        "total_duration_seconds": sum(float(row["duration_seconds"]) for row in rows),
        "split_counts": dict(sorted(split_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "scenario_counts": dict(sorted(scenario_counts.items())),
        "clips_without_ball_boxes": [row["clip_id"] for row in rows if not row["ball_boxes"]],
        "archives": archives,
        "notes": [
            "The current official v1.3 archives contain 164 public clips, not the 166 advertised on the SoccerNet task page.",
            "Ball annotations are inherited from SoccerNet-Tracking and embedded in Labels-GameState.json.",
            "Clearance clips retain SoccerNet's official Clearance anchor label.",
            "Coaching quality labels are not supplied by SoccerNet and require a later expert rubric.",
        ],
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def validate_manifest(project_root: Path) -> dict:
    manifest_path = project_root / "data" / "processed" / "manifest.csv"
    summary_path = project_root / "data" / "processed" / "summary.json"
    if not manifest_path.exists() or not summary_path.exists():
        raise FileNotFoundError("Run `soccernet-dataset manifest` first.")

    with manifest_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    errors: list[str] = []

    if len(rows) != 164:
        errors.append(f"Expected 164 verified public clips, found {len(rows)}")
    if len({row['clip_id'] for row in rows}) != len(rows):
        errors.append("Duplicate clip IDs found")
    if Counter(row["split"] for row in rows) != Counter(
        {"train": 57, "valid": 58, "test": 49}
    ):
        errors.append("Split counts differ from the v1.3 archive index")
    if any(row["annotation_version"] != "1.3" for row in rows):
        errors.append("At least one clip is not annotation version 1.3")
    if any(int(row["frame_count"]) != 750 for row in rows):
        errors.append("At least one clip does not contain the expected 750 frames")
    if any(int(row["frame_rate"]) != 25 for row in rows):
        errors.append("At least one clip does not use the expected 25 fps")
    if summary["clip_count"] != len(rows):
        errors.append("Summary and manifest clip counts differ")

    report = {
        "status": "passed" if not errors else "failed",
        "clip_count": len(rows),
        "errors": errors,
        "warnings": [
            f"{sum(not int(row['ball_boxes']) for row in rows)} clips have no visible ball boxes.",
            "Clearance is preserved as an official SoccerNet anchor action.",
        ],
    }
    output = project_root / "data" / "processed" / "validation_report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if errors:
        raise RuntimeError("Dataset validation failed: " + "; ".join(errors))
    return report
