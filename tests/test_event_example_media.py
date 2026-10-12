import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from football_coach import event_example_media as media


class FakeCapture:
    def __init__(self, total=1000):
        self.total = total
        self.position = 0
        self.released = False

    def isOpened(self):
        return True

    def get(self, prop):
        if prop == media.cv2.CAP_PROP_FPS:
            return 25.0
        if prop == media.cv2.CAP_PROP_FRAME_COUNT:
            return self.total
        return self.position

    def set(self, prop, value):
        self.position = value
        return True

    def read(self):
        self.position += 1
        return True, np.zeros((720, 1280, 3), dtype=np.uint8)

    def release(self):
        self.released = True


def candidate():
    return {"clip_id": "E-0001", "role": "example", "class": "corner",
            "match_path": "league/season/match", "half": 1,
            "start_ms": 1000, "end_ms": 31000}


def test_extraction_records_exact_indices_and_neutral_images(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "ROOT", tmp_path)
    monkeypatch.setattr(media, "BASE", tmp_path / "artifacts")
    capture = FakeCapture()
    monkeypatch.setattr(media.cv2, "VideoCapture", lambda _: capture)
    row = candidate()
    media.extract(row, Path("unused.mkv"), "source-sha")
    images = list(media.frame_directory(row).glob("*.jpg"))
    assert len(images) == 30
    assert sorted(path.name for path in images) == [f"{i:02d}.jpg" for i in range(1, 31)]
    assert media.complete(row)
    record = json.loads((media.BASE / "media_records/clips/E-0001.json").read_bytes())
    assert record["frames"][0]["decoded_frame_index_0_based"] == 25
    assert record["frames"][-1]["decoded_frame_index_0_based"] == 774
    assert record["frames"][0]["image_dimensions"] == [672, 378]
    assert not record["model_runs_allowed"]
    assert capture.released
    images[0].write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        media.complete(row)


def amendment_fixture():
    bad = {**candidate(), "role": "held_out_test", "selection": "primary",
           "match_group": "bad", "class_rank": 1}
    reserve = {**bad, "clip_id": "E-0002", "selection": "reserve",
               "match_group": "reserve", "class_rank": 21}
    amendment = {"replacements": [{"rejected_clip_id": bad["clip_id"],
                 "replacement_clip_id": reserve["clip_id"], "reported_start_ms": 1000,
                 "reported_end_ms": 31000, "reported_source_duration_seconds": 20,
                 "reason": "window exceeds duration"}]}
    return bad, reserve, amendment


def test_amendment_preserves_candidates_and_requires_same_role():
    bad, reserve, amendment = amendment_fixture()
    assert media.amended_rows([bad, reserve], amendment) == [reserve]
    assert bad["selection"] == "primary"
    assert reserve["selection"] == "reserve"
    with pytest.raises(ValueError, match="same role"):
        media.amended_rows([bad, {**reserve, "role": "example"}], amendment)
    earlier = {**reserve, "clip_id": "E-0003", "class_rank": 20}
    with pytest.raises(ValueError, match="first eligible"):
        media.amended_rows([bad, earlier, reserve], amendment)


def test_rejection_remeasures_and_keeps_original_video(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "BASE", tmp_path)
    bad, reserve, amendment = amendment_fixture()
    key = hashlib.sha256(media.source_path(bad).encode()).hexdigest()
    video = tmp_path / "temporary_footage" / f"{key}.mkv"
    video.parent.mkdir()
    video.write_bytes(b"source-video")
    media.save(tmp_path / "media_records/sources" / f"{key}.json", {
        "sha256": media.sha(video), "revision": media.REVISION})
    capture = FakeCapture(total=500)
    monkeypatch.setattr(media.cv2, "VideoCapture", lambda _: capture)
    media.verify_rejections([bad, reserve], amendment, "amendment-sha")
    record = json.loads((tmp_path / "media_records/rejections/E-0001.json").read_bytes())
    assert record["source_duration_seconds"] == 20
    assert record["candidate"] == bad
    assert video.exists()
    assert capture.released
    with pytest.raises(ValueError, match="does not match"):
        media.verify_rejections([bad, reserve], amendment, "changed-amendment")


def test_truncated_window_is_rejected_without_frames(tmp_path, monkeypatch):
    monkeypatch.setattr(media, "BASE", tmp_path)
    capture = FakeCapture(total=500)
    monkeypatch.setattr(media.cv2, "VideoCapture", lambda _: capture)
    with pytest.raises(ValueError, match="exceeds source duration"):
        media.extract(candidate(), Path("unused.mkv"), "hash")
    assert not list(tmp_path.rglob("*.jpg"))
    assert capture.released
