from __future__ import annotations

import zipfile
from pathlib import Path

import cv2
import numpy as np

from .domain import SoccerNetClip


def uniform_positions(total: int, count: int) -> list[int]:
    if total < 1 or count < 1 or count > total:
        raise ValueError("Require 1 <= count <= total")
    if count == 1:
        return [total // 2]
    return [round(index * (total - 1) / (count - 1)) for index in range(count)]


def resize_max_edge(frame: np.ndarray, maximum_edge: int) -> np.ndarray:
    height, width = frame.shape[:2]
    scale = min(1.0, maximum_edge / max(height, width))
    if scale == 1.0:
        return frame
    return cv2.resize(
        frame,
        (round(width * scale), round(height * scale)),
        interpolation=cv2.INTER_AREA,
    )


def sample_dataset_b(
    record: SoccerNetClip,
    project_root: Path,
    destination: Path,
    count: int,
    maximum_edge: int,
) -> list[Path]:
    positions = uniform_positions(record.frame_count, count)
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    with zipfile.ZipFile(project_root / record.archive_path) as archive:
        for order, position in enumerate(positions, start=1):
            frame_number = position + 1
            member = record.frame_member_pattern % frame_number
            encoded = np.frombuffer(archive.read(member), dtype=np.uint8)
            frame = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError(f"Could not decode {member}")
            frame = resize_max_edge(frame, maximum_edge)
            output = destination / f"{order:02d}_frame_{frame_number:06d}.jpg"
            if not cv2.imwrite(str(output), frame, [cv2.IMWRITE_JPEG_QUALITY, 92]):
                raise OSError(f"Could not write {output}")
            outputs.append(output)
    return outputs


def sample_dataset_a(
    video_path: Path,
    destination: Path,
    start_seconds: float,
    end_seconds: float,
    count: int,
    maximum_edge: int,
) -> list[Path]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Could not open Dataset A video: {video_path}")
    fps = capture.get(cv2.CAP_PROP_FPS)
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if fps <= 0 or total_frames <= 0:
        capture.release()
        raise ValueError(f"Invalid video metadata: {video_path}")
    first = max(0, round(start_seconds * fps))
    last = min(total_frames - 1, round(end_seconds * fps) - 1)
    if last < first:
        capture.release()
        raise ValueError("Dataset A clip boundaries contain no frames")
    relative_positions = uniform_positions(last - first + 1, count)
    destination.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    try:
        for order, relative in enumerate(relative_positions, start=1):
            frame_number = first + relative
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ok, frame = capture.read()
            if not ok or frame is None:
                raise ValueError(f"Could not read frame {frame_number} from {video_path}")
            frame = resize_max_edge(frame, maximum_edge)
            output = destination / f"{order:02d}_frame_{frame_number:06d}.jpg"
            if not cv2.imwrite(str(output), frame, [cv2.IMWRITE_JPEG_QUALITY, 92]):
                raise OSError(f"Could not write {output}")
            outputs.append(output)
    finally:
        capture.release()
    return outputs

