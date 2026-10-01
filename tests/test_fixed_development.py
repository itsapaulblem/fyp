from pathlib import Path

import pytest

import football_coach.fixed_development as fixed_development
from football_coach.fixed_development import (
    existing_cells,
    parse_fixed_hints,
    run_fixed_batch,
    run_fixed_cell,
    run_p1_initial_cell,
)
from football_coach.staged_prompting import read_metadata


class FakeOllama:
    def __init__(self):
        self.calls = []

    def model_metadata(self, model):
        assert model == "qwen3.5:27b"
        return {"digest": "a" * 64}

    def gpu_status(self, model, options, *, preload):
        assert model == "qwen3.5:27b"
        assert options["num_gpu"] == 0
        assert isinstance(preload, bool)
        return {"digest": "a" * 64, "size_vram_bytes": 0}

    def chat(self, model, messages, options, think):
        assert model == "qwen3.5:27b"
        assert len(messages[0].images) == 30
        assert options["num_gpu"] == 0
        assert think is False
        self.calls.append(messages)
        return {
            "message": {
                "content": (
                    "VISIBLE EVIDENCE\nCHRONOLOGY\nEVENT ASSESSMENT\n"
                    f"EVIDENCE LIMITS\nAnswer {len(self.calls)}"
                )
            }
        }


@pytest.fixture
def prepared(tmp_path: Path):
    prompts = tmp_path / "input_prompts/v0.4"
    prompts.mkdir(parents=True)
    recognition = prompts / "recognition.txt"
    recognition.write_text("Describe the frames; do not coach.", encoding="utf-8")
    revision = prompts / "revision.txt"
    revision.write_text("Revise recognition; do not coach.", encoding="utf-8")
    coaching = prompts / "coaching.txt"
    coaching.write_text("Provide advice after review.", encoding="utf-8")
    p2_wrapper = prompts / "p2.txt"
    p2_wrapper.write_text("Re-examine the images; no coaching.\n", encoding="utf-8")
    p3_wrapper = prompts / "p3.txt"
    p3_wrapper.write_text("Check these observations; no coaching.\n", encoding="utf-8")
    hints = prompts / "hints.txt"
    hints.write_text("HINT 1 — A\nFirst\nHINT 2 — B\nSecond\nHINT 3 — C\nThird\n", encoding="utf-8")
    cues = tmp_path / "output/cues.txt"
    cues.parent.mkdir(parents=True)
    cues.write_text("Images 1–30: players move.", encoding="utf-8")
    config = tmp_path / "config"
    config.mkdir()
    batch_path = config / "batch.json"
    batch_path.write_text("{}", encoding="utf-8")
    selection_path = config / "selection.json"
    selection_path.write_text("{}", encoding="utf-8")
    cohort_path = config / "cohort.json"
    cohort_path.write_text("{}", encoding="utf-8")
    device_path = config / "device.json"
    device_path.write_text("{}", encoding="utf-8")
    frames = tmp_path / "artifacts/model_inputs/dataset_b/B-TRAIN-0054/uniform_30_edge_672"
    frames.mkdir(parents=True)
    images = []
    for number in range(1, 31):
        image = frames / f"{number:02d}_frame_{number:06d}.jpg"
        image.write_bytes(b"test image")
        images.append(image)
    return {
        "root": tmp_path,
        "batch": {
            "protocol_id": "evidence-first-football-v0.4.0",
            "model": "qwen3.5:27b",
            "clip_ids_in_order": ["B-TRAIN-0054"],
            "p1_initial_only_clip_ids": ["B-TRAIN-0054"],
            "p1_local_reference_sha256": {"B-TRAIN-0054": "b" * 64},
        },
        "batch_path": batch_path,
        "selection_path": selection_path,
        "device_path": device_path,
        "device": {
            "parent_protocol_id": "retrieval-assisted-football-v0.3.0",
            "sampling": {
                "maximum_edge": 672,
                "algorithm": "uniform_endpoints_v1",
                "image_encoding": "JPEG quality 92 after OpenCV INTER_AREA resize",
            },
        },
        "cohort_path": cohort_path,
        "generation": {"options": {"num_gpu": 0}, "think": False},
        "recognition_path": recognition,
        "p1_revision_path": revision,
        "p1_coaching_path": coaching,
        "p2_wrapper_path": p2_wrapper,
        "p3_wrapper_path": p3_wrapper,
        "hints_path": hints,
        "hints": ["First", "Second", "Third"],
        "cues": {"B-TRAIN-0054": cues},
        "frames": {"B-TRAIN-0054": images},
    }


def test_fixed_hints_require_exact_order():
    assert parse_fixed_hints("HINT 1 — A\nA\nHINT 2 — B\nB\nHINT 3 — C\nC") == [
        "A", "B", "C"
    ]
    with pytest.raises(ValueError):
        parse_fixed_hints("HINT 1 — A\nA\nHINT 3 — C\nC")


def test_p2_and_p3_are_fresh_and_stop_before_coaching(prepared):
    root = prepared["root"]
    client = FakeOllama()
    p2 = run_fixed_cell(root, prepared, "B-TRAIN-0054", "P2_attention_hint", client, "a" * 64)
    p3 = run_fixed_cell(root, prepared, "B-TRAIN-0054", "P3_visible_cue_hint", client, "a" * 64)
    assert [len(messages) for messages in client.calls] == [1, 3, 5, 7, 1, 3]
    assert "First" in client.calls[1][-1].content
    assert "Second" in client.calls[2][-1].content
    assert "Third" in client.calls[3][-1].content
    assert "First" not in client.calls[4][0].content
    assert "players move" in client.calls[5][-1].content
    expected_status = "awaiting_human_review_before_coaching"
    assert read_metadata(p2 / "metadata.txt")["run_status"] == expected_status
    assert read_metadata(p3 / "metadata.txt")["run_status"] == expected_status
    assert not list(p2.glob("*coaching*"))
    assert not list(p3.glob("*coaching*"))
    assert existing_cells(root, prepared) == [
        "P2_attention_hint/B-TRAIN-0054", "P3_visible_cue_hint/B-TRAIN-0054"
    ]
    with pytest.raises(ValueError, match="already attempted"):
        run_fixed_cell(root, prepared, "B-TRAIN-0054", "P2_attention_hint", client, "a" * 64)


def test_failed_cell_is_preserved_and_not_retried(prepared):
    class FailingOllama(FakeOllama):
        def chat(self, model, messages, options, think):
            if self.calls:
                raise RuntimeError("simulated Ollama failure")
            return super().chat(model, messages, options, think)

    root = prepared["root"]
    client = FailingOllama()
    with pytest.raises(RuntimeError, match="simulated Ollama failure"):
        run_fixed_cell(root, prepared, "B-TRAIN-0054", "P2_attention_hint", client, "a" * 64)
    cell_root = (
        root / "output/v0.4/prompt_chain/P2_attention_hint/fixed_unattended_v2"
        / "qwen3.5_27b/B-TRAIN-0054"
    )
    run_dir = next(cell_root.iterdir())
    assert (run_dir / "stage_1_response.txt").is_file()
    assert (run_dir / "error.json").is_file()
    assert read_metadata(run_dir / "metadata.txt")["run_status"] == "error"
    with pytest.raises(ValueError, match="already attempted"):
        run_fixed_cell(root, prepared, "B-TRAIN-0054", "P2_attention_hint", client, "a" * 64)


def test_p1_first_pass_is_resumable_and_does_not_coach(prepared):
    root = prepared["root"]
    client = FakeOllama()
    run_dir = run_p1_initial_cell(root, prepared, "B-TRAIN-0054", client, "a" * 64)
    assert [len(messages) for messages in client.calls] == [1]
    metadata = read_metadata(run_dir / "metadata.txt")
    assert metadata["run_status"] == "awaiting_human_review"
    assert metadata["human_reference_sha256"] == "b" * 64
    assert metadata["method"] == "P1_human_guided"
    assert (run_dir / "initial_review.json").read_text(encoding="utf-8").find(
        "PENDING_REVIEW"
    ) >= 0
    assert not list(run_dir.glob("*coaching*"))
    assert existing_cells(root, prepared) == ["P1_human_guided/B-TRAIN-0054"]


def test_batch_saves_p1_first_pass_before_longer_conditions(prepared, monkeypatch):
    monkeypatch.setattr(fixed_development, "OllamaClient", FakeOllama)
    completed = run_fixed_batch(prepared["root"], prepared)
    assert "P1_human_guided" in str(completed[0])
    assert "P2_attention_hint" in str(completed[1])
    assert "P3_visible_cue_hint" in str(completed[2])
