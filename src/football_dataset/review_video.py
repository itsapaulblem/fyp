from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

import cv2
import numpy as np


CODEC = "mp4v"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _decode_jpeg(raw: bytes, member: str) -> np.ndarray:
    frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError(f"Could not decode JPEG: {member}")
    return frame


def inspect_video(path: Path) -> dict:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open generated video: {path}")
    try:
        frame_count = round(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_rate = capture.get(cv2.CAP_PROP_FPS)
        width = round(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    finally:
        capture.release()
    return {
        "frame_count": frame_count,
        "frame_rate": round(frame_rate, 3),
        "width": width,
        "height": height,
        "duration_seconds": round(frame_count / frame_rate, 3),
    }


def _convert_clip(
    project_root: Path,
    source: dict[str, str],
    output_path: Path,
) -> dict:
    frame_count = int(source["frame_count"])
    frame_rate = int(source["frame_rate"])
    archive_path = project_root / source["archive_path"]
    temporary_path = output_path.with_name(f"{output_path.stem}.part.mp4")
    if temporary_path.exists():
        temporary_path.unlink()

    with ZipFile(archive_path) as archive:
        first_member = source["frame_member_pattern"] % 1
        first_frame = _decode_jpeg(archive.read(first_member), first_member)
        height, width = first_frame.shape[:2]
        writer = cv2.VideoWriter(
            str(temporary_path),
            cv2.VideoWriter_fourcc(*CODEC),
            frame_rate,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not initialize {CODEC} writer: {temporary_path}")
        try:
            writer.write(first_frame)
            for frame_number in range(2, frame_count + 1):
                member = source["frame_member_pattern"] % frame_number
                frame = _decode_jpeg(archive.read(member), member)
                if frame.shape[1] != width or frame.shape[0] != height:
                    raise ValueError(
                        f"Frame-size mismatch in {source['clip_id']} frame {frame_number}"
                    )
                writer.write(frame)
        finally:
            writer.release()

    metadata = inspect_video(temporary_path)
    if metadata["frame_count"] != frame_count:
        raise RuntimeError(
            f"Generated {source['clip_id']} has {metadata['frame_count']} frames; "
            f"expected {frame_count}"
        )
    if abs(metadata["frame_rate"] - frame_rate) > 0.01:
        raise RuntimeError(
            f"Generated {source['clip_id']} is {metadata['frame_rate']} fps; "
            f"expected {frame_rate}"
        )
    temporary_path.replace(output_path)
    return metadata


def build_review_videos(
    project_root: Path,
    *,
    overwrite: bool = False,
    limit: int | None = None,
) -> dict:
    selection = _read_csv(project_root / "data" / "processed" / "pilot_selection.csv")
    selected_ids = [row["clip_id"] for row in selection if row["selected"] == "true"]
    if limit is not None:
        selected_ids = selected_ids[:limit]
    manifest = {
        row["clip_id"]: row
        for row in _read_csv(project_root / "data" / "processed" / "manifest.csv")
    }
    output_root = project_root / "data" / "processed" / "review_videos"
    output_root.mkdir(parents=True, exist_ok=True)

    records = []
    for index, clip_id in enumerate(selected_ids, start=1):
        source = manifest[clip_id]
        output_path = output_root / f"{clip_id}.mp4"
        if output_path.exists() and not overwrite:
            print(f"[{index}/{len(selected_ids)}] inspect existing {clip_id}", flush=True)
            metadata = inspect_video(output_path)
        else:
            print(f"[{index}/{len(selected_ids)}] convert {clip_id}", flush=True)
            metadata = _convert_clip(project_root, source, output_path)
        if metadata["frame_count"] != int(source["frame_count"]):
            raise RuntimeError(f"Existing video frame count is invalid: {output_path}")
        records.append(
            {
                "clip_id": clip_id,
                "split": source["split"],
                "official_anchor_action": source["action_class"],
                "output_path": output_path.relative_to(project_root).as_posix(),
                "source_archive": source["archive_path"],
                "source_frame_pattern": source["frame_member_pattern"],
                "codec": CODEC,
                "has_audio": False,
                **metadata,
                "size_bytes": output_path.stat().st_size,
                "sha256": _sha256(output_path),
            }
        )
        print(
            f"[{index}/{len(selected_ids)}] ready {clip_id} "
            f"{metadata['width']}x{metadata['height']} "
            f"{metadata['duration_seconds']:.1f}s",
            flush=True,
        )

    report = {
        "status": "complete" if len(records) == len(selected_ids) else "incomplete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Full-sequence human review only; not MLLM input",
        "source": "Official SoccerNet-GSR JPEG sequences",
        "video_count": len(records),
        "expected_video_count": len(selected_ids),
        "videos": records,
    }
    report_path = output_root / "manifest.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report

