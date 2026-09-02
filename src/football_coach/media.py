from __future__ import annotations

import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .dataset import ClipRecord


def uniform_indices(frame_count: int, sample_count: int) -> list[int]:
    if sample_count < 2:
        raise ValueError("sample_count must be at least 2")
    if sample_count > frame_count:
        raise ValueError("sample_count cannot exceed frame_count")
    return [
        round(index * (frame_count - 1) / (sample_count - 1)) + 1
        for index in range(sample_count)
    ]


def extract_sampled_frames(
    record: ClipRecord, project_root: Path, output_dir: Path, count: int
) -> list[Path]:
    indices = uniform_indices(record.frame_count, count)
    archive_path = project_root / record.archive_path
    clip_dir = output_dir / record.split / record.clip_id / f"uniform_{count}"
    clip_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    with zipfile.ZipFile(archive_path) as archive:
        for order, frame_index in enumerate(indices, start=1):
            member = record.frame_member_pattern % frame_index
            destination = clip_dir / f"{order:02d}_frame_{frame_index:06d}.jpg"
            destination.write_bytes(archive.read(member))
            outputs.append(destination)
    return outputs


def make_contact_sheet(frames: list[Path], destination: Path, columns: int = 4) -> Path:
    if not frames:
        raise ValueError("No frames supplied")
    thumbnails: list[Image.Image] = []
    for index, frame in enumerate(frames, start=1):
        image = Image.open(frame).convert("RGB")
        image.thumbnail((480, 270))
        canvas = Image.new("RGB", (480, 300), "black")
        canvas.paste(image, ((480 - image.width) // 2, 24))
        ImageDraw.Draw(canvas).text((8, 6), f"Frame {index:02d}", fill="white")
        thumbnails.append(canvas)
    rows = (len(thumbnails) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * 480, rows * 300), "black")
    for index, image in enumerate(thumbnails):
        sheet.paste(image, ((index % columns) * 480, (index // columns) * 300))
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, quality=92)
    return destination


def make_review_video(record: ClipRecord, project_root: Path, destination: Path) -> Path:
    """Render the complete official JPEG sequence for private human review."""
    archive_path = project_root / record.archive_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    writer: cv2.VideoWriter | None = None
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for frame_index in range(1, record.frame_count + 1):
                member = record.frame_member_pattern % frame_index
                encoded = np.frombuffer(archive.read(member), dtype=np.uint8)
                frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
                if frame is None:
                    raise ValueError(f"Could not decode {member}")
                if writer is None:
                    height, width = frame.shape[:2]
                    writer = cv2.VideoWriter(
                        str(destination),
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        record.frame_rate,
                        (width, height),
                    )
                    if not writer.isOpened():
                        raise RuntimeError(f"Could not open video writer for {destination}")
                writer.write(frame)
    finally:
        if writer is not None:
            writer.release()
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"Review video was not created: {destination}")
    return destination
