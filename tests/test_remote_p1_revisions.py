from __future__ import annotations

import json
from pathlib import Path

import pytest

import football_coach.remote_p1_revisions as portable
from football_coach.provenance import sha256_file
from football_coach.staged_prompting import read_metadata, write_json, write_metadata


def _make_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, list[Path]]:
    root = tmp_path
    (root / "config").mkdir()
    (root / "artifacts/transfer").mkdir(parents=True)
    (root / "input_prompts/v0.4").mkdir(parents=True)
    files = {}
    for name in ("recognition", "revision", "coaching"):
        path = root / f"input_prompts/v0.4/{name}.txt"
        path.write_text(f"{name} prompt\n", encoding="utf-8")
        files[name] = path
    batch_path = root / "config/fixed_unattended_development_v0.4.3.json"
    batch_path.write_text("{}\n", encoding="utf-8")
    device_path = root / "config/project_v0.4.0_cpu.json"
    generation = {"options": {"num_gpu": 0}, "think": False}
    device_path.write_text(json.dumps({"generation": generation}), encoding="utf-8")
    cohort_path = root / "config/cohort.json"
    cohort_path.write_text("{}\n", encoding="utf-8")
    selection_path = root / "config/selection.json"
    selection_path.write_text("{}\n", encoding="utf-8")
    hashes = {clip: "b" * 64 for clip in portable.CLIP_ORDER}
    prepared = {
        "batch": {
            "protocol_id": "evidence-first-football-v0.4.0",
            "model": "qwen3.5:27b",
            "p1_initial_only_clip_ids": list(portable.CLIP_ORDER[:2]),
            "p1_local_reference_sha256": dict(list(hashes.items())[:2]),
        },
        "device": {"generation": generation},
        "device_path": device_path,
        "cohort_path": cohort_path,
        "selection_path": selection_path,
        "recognition_path": files["recognition"],
        "p1_revision_path": files["revision"],
        "p1_coaching_path": files["coaching"],
        "frames": {},
    }
    monkeypatch.setattr(portable, "validate_fixed_batch", lambda *_: prepared)
    entries = []
    run_dirs = []
    for clip_id in portable.CLIP_ORDER:
        image_dir = root / f"artifacts/model_inputs/dataset_b/{clip_id}/uniform_30_edge_672"
        image_dir.mkdir(parents=True)
        images = []
        for number in range(1, 31):
            image = image_dir / f"{number:02d}_frame_{number:06d}.jpg"
            image.write_bytes(f"{clip_id}-{number}".encode())
            images.append(image)
        prepared["frames"][clip_id] = images
        if clip_id == "B-TRAIN-0054":
            relative = f"output/v0.4/prompt_chain/P1_human_guided/qwen3.5_27b/{clip_id}/first"
        else:
            relative = (
                "output/v0.4/prompt_chain/P1_human_guided/fixed_unattended_v2/"
                f"qwen3.5_27b/{clip_id}/first"
            )
        run_dir = root / relative
        run_dir.mkdir(parents=True)
        metadata = {
            "protocol_id": "evidence-first-football-v0.4.0",
            "method": "P1_human_guided",
            "dataset_b_clip_id": clip_id,
            "dataset_b_split": "train",
            "run_status": "awaiting_human_review",
            "model": "qwen3.5:27b",
            "model_digest": "a" * 64,
            "config_sha256": sha256_file(device_path),
            "cohort_sha256": sha256_file(cohort_path),
            "selection_manifest_sha256": sha256_file(selection_path),
            "recognition_prompt_sha256": sha256_file(files["recognition"]),
            "revision_prompt_sha256": sha256_file(files["revision"]),
            "coaching_prompt_sha256": sha256_file(files["coaching"]),
            "generation": generation,
            "human_reference_sha256": hashes[clip_id],
            "frame_sha256": {
                image.relative_to(root).as_posix(): sha256_file(image) for image in images
            },
        }
        write_metadata(run_dir / "metadata.txt", metadata)
        (run_dir / "stage_1_prompt.txt").write_text("first prompt\n", encoding="utf-8")
        (run_dir / "stage_1_response.txt").write_text("first answer", encoding="utf-8")
        write_json(run_dir / "stage_1_raw_api_response.json", {
            "message": {"content": "first answer"}
        })
        write_json(run_dir / "initial_review.json", {
            "feedback": [{
                "frame_numbers_1_based": [25],
                "observed_evidence": "The player falls.",
                "correction": "Recheck the outcome.",
            }],
            "notes": "Reviewed frames.",
        })
        entries.append({
            "clip_id": clip_id,
            "run_dir": relative,
            "source_sha256": {
                filename: sha256_file(run_dir / filename) for filename in portable.SOURCE_FILES
            },
            "human_reference_sha256": hashes[clip_id],
        })
        run_dirs.append(run_dir)
    manifest_path = root / "artifacts/transfer/p1_remote_revisions_v1_manifest.json"
    write_json(manifest_path, {
        "variant": portable.VARIANT,
        "batch_sha256": sha256_file(batch_path),
        "config_sha256": sha256_file(device_path),
        "runs": entries,
    })
    return manifest_path, run_dirs


def test_portable_p1_validates_all_sources_before_inference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, runs = _make_package(tmp_path, monkeypatch)
    assert len(portable.validate_remote_p1_revisions(tmp_path, manifest)) == 3
    (runs[1] / "stage_1_response.txt").write_text("changed answer", encoding="utf-8")
    with pytest.raises(ValueError, match="source file changed"):
        portable.validate_remote_p1_revisions(tmp_path, manifest)


def test_portable_p1_rejects_changed_sampled_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, _ = _make_package(tmp_path, monkeypatch)
    image = (
        tmp_path / "artifacts/model_inputs/dataset_b/B-TRAIN-0040/"
        "uniform_30_edge_672/01_frame_000001.jpg"
    )
    image.write_bytes(b"different pixels")
    with pytest.raises(ValueError, match="sampled images changed"):
        portable.validate_remote_p1_revisions(tmp_path, manifest)


def test_portable_p1_revises_only_recognition_and_never_reruns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, runs = _make_package(tmp_path, monkeypatch)
    calls = []

    class FakeOllama:
        def model_metadata(self, _model: str) -> dict:
            return {"digest": "a" * 64}

        def gpu_status(self, _model: str, options: dict, *, preload: bool) -> dict:
            assert options == {"num_gpu": 0}
            return {"digest": "a" * 64, "size_vram_bytes": 0}

        def chat(self, _model: str, messages: list, _options: dict, think: bool) -> dict:
            assert think is False
            assert len(messages) == 3
            assert len(messages[0].images) == 30
            assert messages[1].content == "first answer"
            assert "Recheck the outcome" in messages[2].content
            calls.append(messages)
            return {"message": {"content": (
                "VISIBLE EVIDENCE\nCHRONOLOGY\nEVENT ASSESSMENT\nEVIDENCE LIMITS"
            )}}

    monkeypatch.setattr(portable, "OllamaClient", FakeOllama)
    monkeypatch.setattr(portable, "load_dotenv", lambda *_: None)
    assert len(portable.run_remote_p1_revisions(tmp_path, manifest)) == 3
    assert len(calls) == 3
    for run_dir in runs:
        assert (run_dir / "stage_2_revision_response.txt").is_file()
        assert not (run_dir / "stage_3_coaching_response.txt").exists()
        metadata = read_metadata(run_dir / "metadata.txt")
        assert metadata["run_status"] == "awaiting_revision_approval"
        assert metadata["private_reference_verified_remotely"] is False
    with pytest.raises(ValueError, match="source file changed"):
        portable.run_remote_p1_revisions(tmp_path, manifest)
