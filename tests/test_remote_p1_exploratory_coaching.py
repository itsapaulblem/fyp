from pathlib import Path

import football_coach.remote_p1_exploratory_coaching as probe


def test_probe_isolated_and_preserves_unapproved_source(tmp_path: Path, monkeypatch):
    source = tmp_path / probe.SOURCE_RELATIVE
    source.mkdir(parents=True)
    for name in probe.SOURCE_FILES:
        (source / name).write_text("source", encoding="utf-8")
    for stage, prefix in ((1, "stage_1"), (2, "stage_2_revision"),
                          (3, "stage_3_revision")):
        (source / f"{prefix}_response.txt").write_text(
            f"Recognition {stage}", encoding="utf-8"
        )
    (source / "human_feedback.txt").write_text("First correction", encoding="utf-8")
    (source / "human_feedback_2.txt").write_text("Second correction", encoding="utf-8")
    manifest = tmp_path / "artifacts/transfer/probe.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}", encoding="utf-8")
    prompts = tmp_path / "input_prompts/v0.4"
    prompts.mkdir(parents=True)
    recognition = prompts / "recognition.txt"
    coaching = prompts / "coaching.txt"
    recognition.write_text("Describe 30 frames", encoding="utf-8")
    coaching.write_text("Give conditional coaching", encoding="utf-8")
    images = []
    for index in range(30):
        image = tmp_path / f"artifacts/model_inputs/{index:02d}.jpg"
        image.parent.mkdir(parents=True, exist_ok=True)
        image.write_bytes(b"image")
        images.append(image)
    output = tmp_path / probe.OUTPUT_PARENT / "isolated"
    metadata = {"model": "qwen3.5:27b", "model_digest": "a" * 64}
    prepared = {
        "recognition_path": recognition,
        "p1_coaching_path": coaching,
        "frames": {"B-TRAIN-0054": images},
        "device": {"generation": {"options": {"num_gpu": 0}, "think": False}},
    }
    checked = {"source": source, "output": output, "metadata": metadata,
               "answers": ["Recognition 1", "Recognition 2", "Recognition 3"]}
    monkeypatch.setattr(probe, "validate_probe", lambda *_: (prepared, checked))
    monkeypatch.setattr(probe, "load_dotenv", lambda *_: None)

    class FakeOllama:
        def model_metadata(self, model):
            return {"digest": "a" * 64}

        def gpu_status(self, model, options, *, preload):
            assert options["num_gpu"] == 0
            return {"digest": "a" * 64, "size_vram_bytes": 0}

        def chat(self, model, messages, options, think):
            assert len(messages) == 7
            assert len(messages[0].images) == 30
            assert messages[-1].content == "Give conditional coaching"
            assert "Second correction" in messages[-3].content
            return {"message": {"content": (
                "TACTICAL INTERPRETATION\nCOACHING\nSAFETY AND UNCERTAINTY\n"
                "Conditional advice only."
            )}}

    monkeypatch.setattr(probe, "OllamaClient", FakeOllama)
    result = probe.run_probe(tmp_path, manifest)
    assert result == output
    assert (output / "stage_4_coaching_response.txt").is_file()
    assert "exploratory_coaching_complete" in (output / "metadata.txt").read_text(
        encoding="utf-8"
    )
    assert (source / "stage_4_coaching_response.txt").exists() is False
