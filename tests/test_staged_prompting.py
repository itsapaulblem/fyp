import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from football_coach import cli
from football_coach.staged_prompting import (
    coaching_messages,
    feedback_text,
    recognition_messages,
    review_template,
    revision_messages,
    validate_progressive_review,
    validate_review,
    validate_visible_cue_review,
)


def test_visible_cue_review_requires_an_explicit_stage_decision() -> None:
    with pytest.raises(ValueError, match="P3 decision"):
        validate_visible_cue_review({"decision": "PENDING", "notes": ""}, revised=False)
    assert validate_visible_cue_review(
        {"decision": "continue", "notes": "Checked frames"}, revised=False
    ) == "continue"
    assert validate_visible_cue_review(
        {"decision": "approve", "notes": "Supported"}, revised=True
    ) == "approve"
    with pytest.raises(ValueError, match="P3 decision"):
        validate_visible_cue_review({"decision": "continue", "notes": ""}, revised=True)
    with pytest.raises(ValueError, match="only decision and notes"):
        validate_visible_cue_review(
            {"decision": "stop", "notes": "", "event_label": "Corner"}, revised=True
        )


def test_human_review_uses_only_feedback_and_notes() -> None:
    review = review_template()
    assert review == {"feedback": [], "notes": ""}
    assert validate_review(review, {18, 22}) == "approve"
    review["feedback"] = [{
            "frame_numbers_1_based": [18, 22],
            "observed_evidence": "The ball moves away from goal.",
            "correction": "Do not claim a goalkeeper catch.",
        }]
    assert validate_review(review, {18, 22}) == "revise"
    assert validate_review(review, {18, 22}, revised=True) == "reject"
    review["feedback"][0]["frame_numbers_1_based"] = [99]
    with pytest.raises(ValueError, match="sampled frame"):
        validate_review(review, {18, 22})
    review["feedback"][0]["frame_numbers_1_based"] = [18]
    review["decision"] = "approve"
    with pytest.raises(ValueError, match="only feedback and notes"):
        validate_review(review, {18, 22})


def test_review_rejects_an_edited_model_answer(tmp_path: Path) -> None:
    answer = tmp_path / "stage_1_response.txt"
    answer.write_text("edited recognition", encoding="utf-8")
    (tmp_path / "stage_1_raw_api_response.json").write_text(
        json.dumps({"message": {"content": "original recognition"}}), encoding="utf-8"
    )
    (tmp_path / "initial_review.json").write_text(
        json.dumps(review_template()), encoding="utf-8"
    )
    with pytest.raises(Exception, match="differs from its raw model response"):
        cli.checked_review(tmp_path, "initial_review.json", answer, [tmp_path / "01.jpg"])


def test_coaching_history_contains_exact_feedback_and_revised_answer(tmp_path: Path) -> None:
    frames = [tmp_path / "01.jpg"]
    review = {"feedback": [{
        "frame_numbers_1_based": [1],
        "observed_evidence": "The ball is near halfway.",
        "correction": "Remove the claimed shot.",
    }]}
    correction = feedback_text(review, "Recheck the recognition.")
    assert [m.role for m in recognition_messages("recognise", frames)] == ["user"]
    assert [m.role for m in revision_messages("recognise", frames, "original", correction)] == [
        "user", "assistant", "user"
    ]
    messages = coaching_messages(
        "recognise", frames, "original", "coach", correction, "revised"
    )
    assert [m.role for m in messages] == ["user", "assistant", "user", "assistant", "user"]
    assert messages[1].content == "original"
    assert messages[2].content == correction
    assert messages[3].content == "revised"


def test_cli_pauses_for_human_feedback_before_coaching(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    frame = tmp_path / "frames" / "01_frame_000001.jpg"
    frame.parent.mkdir()
    frame.write_bytes(b"sampled image")
    prompts = tmp_path / "input_prompts" / "v0.4"
    prompts.mkdir(parents=True)
    for name in ("recognition", "revision", "coaching"):
        (prompts / f"{name}.txt").write_text(name, encoding="utf-8")
    config = {
        "protocol_id": "evidence-first-football-v0.4.0",
        "parent_protocol_id": "retrieval-assisted-football-v0.3.0",
        "development": {"cohort_path": "cohort.json"},
        "dataset_b": {"human_reference_directory": "data/video_b/review"},
        "sampling": {
            "frame_count": 1,
            "maximum_edge": 672,
            "algorithm": "uniform_endpoints_v1",
            "image_encoding": "JPEG",
        },
        "prompts": {
            "P1_human_guided": {
                name: f"input_prompts/v0.4/{name}.txt"
                for name in ("recognition", "revision", "coaching")
            }
        },
        "output_root": "output/v0.4/prompt_chain",
        "models": ["qwen3.5:27b"],
        "generation": {
            "options": {"temperature": 0},
            "think": False,
            "require_gpu": True,
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    cohort_path = tmp_path / "cohort.json"
    cohort_path.write_text('{"clip_ids":["B-TRAIN-0001"]}', encoding="utf-8")
    reference = tmp_path / "data/video_b/review/B-TRAIN-0001.json"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        cli, "validate_prompt_chain_config",
        lambda *_: {"clip_ids": ["B-TRAIN-0001"]},
    )
    monkeypatch.setattr(
        cli, "find_b_clip",
        lambda *_: SimpleNamespace(clip_id="B-TRAIN-0001", split="train"),
    )
    monkeypatch.setattr(cli, "validate_human_reference", lambda *_: None)
    monkeypatch.setattr(cli, "sample_dataset_b", lambda *_: [frame])
    monkeypatch.setattr(cli, "load_dotenv", lambda *_: None)
    answers = iter([
        "first recognition", "revised recognition", "final coaching",
        "correct recognition", "direct coaching",
        "wrong recognition", "still wrong recognition",
    ])
    histories: list[list[str]] = []

    class FakeOllama:
        def model_metadata(self, _model: str) -> dict[str, str]:
            return {"digest": "a" * 64}

        def gpu_status(
            self, model: str, options: dict[str, Any], *, preload: bool = True
        ) -> dict[str, Any]:
            assert options == {"temperature": 0}
            return {
                "model": model,
                "digest": "a" * 64,
                "size_bytes": 20,
                "size_vram_bytes": 10,
                "context_length": None,
            }

        def chat(
            self, model: str, messages: list[Any], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            histories.append([message.content for message in messages])
            return {"message": {"content": next(answers)}}

    monkeypatch.setattr(cli, "OllamaClient", FakeOllama)
    cli.start_prompt_review(
        "B-TRAIN-0001", "qwen3.5:27b", "P1_human_guided", config_path, tmp_path / "manifest"
    )
    run_dir = next((tmp_path / "output/v0.4/prompt_chain/P1_human_guided").glob("*/*/*"))
    assert not (run_dir / "stage_3_coaching_response.txt").exists()
    assert (run_dir / "initial_review.json").exists()
    assert not (run_dir / "initial_review.template.json").exists()
    with pytest.raises(Exception, match="pending"):
        cli.finish_prompt_coaching(run_dir, config_path, tmp_path / "manifest")

    initial = json.loads((run_dir / "initial_review.json").read_text(encoding="utf-8"))
    initial.update(
        notes="Reviewed against sampled frames.",
        feedback=[{
            "frame_numbers_1_based": [1],
            "observed_evidence": "The ball moves away.",
            "correction": "Remove the claimed catch.",
        }],
    )
    (run_dir / "initial_review.json").write_text(json.dumps(initial), encoding="utf-8")
    cli.revise_prompt_recognition(run_dir, config_path, tmp_path / "manifest")
    assert not (run_dir / "stage_3_coaching_response.txt").exists()
    assert not (run_dir / "revision_review.template.json").exists()
    revised = json.loads((run_dir / "revision_review.json").read_text(encoding="utf-8"))
    revised["notes"] = "Recognition now supported by sampled frames."
    (run_dir / "revision_review.json").write_text(json.dumps(revised), encoding="utf-8")
    cli.finish_prompt_coaching(run_dir, config_path, tmp_path / "manifest")
    assert (run_dir / "stage_3_coaching_response.txt").read_text(encoding="utf-8") == (
        "final coaching"
    )
    assert [len(history) for history in histories] == [1, 3, 5]
    assert histories[2][1] == "first recognition"
    assert histories[2][3] == "revised recognition"
    assert cli.read_metadata(run_dir / "metadata.txt")["run_status"] == "complete"
    gpu_result = cli.read_metadata(run_dir / "metadata.txt")["stage_1_gpu_postcheck"]
    assert gpu_result["size_vram_bytes"] == 10

    cli.start_prompt_review(
        "B-TRAIN-0001", "qwen3.5:27b", "P1_human_guided", config_path, tmp_path / "manifest"
    )
    second_run = sorted((tmp_path / "output/v0.4/prompt_chain/P1_human_guided").glob("*/*/*"))[-1]
    approved = json.loads(
        (second_run / "initial_review.json").read_text(encoding="utf-8")
    )
    approved["notes"] = "No material recognition correction needed."
    (second_run / "initial_review.json").write_text(
        json.dumps(approved), encoding="utf-8"
    )
    cli.finish_prompt_coaching(second_run, config_path, tmp_path / "manifest")
    assert not (second_run / "stage_2_revision_response.txt").exists()
    assert (second_run / "stage_3_coaching_response.txt").read_text(
        encoding="utf-8"
    ) == "direct coaching"
    assert [len(history) for history in histories] == [1, 3, 5, 1, 3]

    cli.start_prompt_review(
        "B-TRAIN-0001", "qwen3.5:27b", "P1_human_guided", config_path, tmp_path / "manifest"
    )
    third_run = sorted((tmp_path / "output/v0.4/prompt_chain/P1_human_guided").glob("*/*/*"))[-1]
    correction_review = json.loads(
        (third_run / "initial_review.json").read_text(encoding="utf-8")
    )
    correction_review.update(
        notes="Reviewed against sampled frames.",
        feedback=[{
            "frame_numbers_1_based": [1],
            "observed_evidence": "Ball travels away.",
            "correction": "Remove the claimed catch.",
        }],
    )
    (third_run / "initial_review.json").write_text(
        json.dumps(correction_review), encoding="utf-8"
    )
    cli.revise_prompt_recognition(third_run, config_path, tmp_path / "manifest")
    rejected = json.loads(
        (third_run / "revision_review.json").read_text(encoding="utf-8")
    )
    rejected.update(
        notes="Recognition still has errors.",
        feedback=[{
            "frame_numbers_1_based": [1],
            "observed_evidence": "The ball is not in the claimed position.",
            "correction": "The revised event sequence remains unsupported.",
        }],
    )
    (third_run / "revision_review.json").write_text(
        json.dumps(rejected), encoding="utf-8"
    )
    cli.finish_prompt_coaching(third_run, config_path, tmp_path / "manifest")
    assert not (third_run / "stage_3_coaching_response.txt").exists()
    assert cli.read_metadata(third_run / "metadata.txt")["run_status"] == (
        "recognition_rejected"
    )
    assert [len(history) for history in histories] == [1, 3, 5, 1, 3, 1, 3]


def test_attention_branch_excludes_explicit_feedback_and_pauses_for_review(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    frame = tmp_path / "frames/01_frame_000001.jpg"
    frame.parent.mkdir()
    frame.write_bytes(b"sampled image")
    prompts = tmp_path / "input_prompts/v0.4"
    prompts.mkdir(parents=True)
    for name in ("recognition", "revision", "coaching"):
        (prompts / f"{name}.txt").write_text(name, encoding="utf-8")
    hint = prompts / "attention.txt"
    hint.write_text("Recheck sampled image 1 without guessing the event.", encoding="utf-8")
    monkeypatch.setattr(cli, "P2_ATTENTION_PROMPT", hint)
    condition_path = tmp_path / "p2_condition.json"
    monkeypatch.setattr(cli, "P2_ATTENTION_CONFIG", condition_path)
    config = {
        "protocol_id": "evidence-first-football-v0.4.0",
        "parent_protocol_id": "retrieval-assisted-football-v0.3.0",
        "development": {"cohort_path": "cohort.json"},
        "dataset_b": {"human_reference_directory": "data/video_b/review"},
        "sampling": {
            "frame_count": 1,
            "maximum_edge": 672,
            "algorithm": "uniform_endpoints_v1",
            "image_encoding": "JPEG",
        },
        "prompts": {
            "P1_human_guided": {
                name: f"input_prompts/v0.4/{name}.txt"
                for name in ("recognition", "revision", "coaching")
            }
        },
        "output_root": "output/v0.4/prompt_chain",
        "models": ["qwen3.5:27b"],
        "generation": {
            "options": {"temperature": 0}, "think": False, "require_gpu": True
        },
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "cohort.json").write_text('{"clip_ids":["B-TRAIN-0001"]}', encoding="utf-8")
    reference = tmp_path / "data/video_b/review/B-TRAIN-0001.json"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        cli, "validate_prompt_chain_config", lambda *_: {"clip_ids": ["B-TRAIN-0001"]}
    )
    monkeypatch.setattr(
        cli, "find_b_clip", lambda *_: SimpleNamespace(clip_id="B-TRAIN-0001", split="train")
    )
    monkeypatch.setattr(cli, "validate_human_reference", lambda *_: None)
    monkeypatch.setattr(cli, "sample_dataset_b", lambda *_: [frame])
    monkeypatch.setattr(cli, "load_dotenv", lambda *_: None)
    answers = iter([
        "original recognition", "explicit revision", "explicit coaching",
        "attention revision", "attention coaching", "still wrong",
    ])
    histories: list[list[str]] = []

    class FakeOllama:
        def model_metadata(self, _model: str) -> dict[str, str]:
            return {"digest": "a" * 64}

        def gpu_status(
            self, model: str, options: dict[str, Any], *, preload: bool = True
        ) -> dict[str, Any]:
            return {"model": model, "digest": "a" * 64, "size_vram_bytes": 10}

        def chat(
            self, model: str, messages: list[Any], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            histories.append([message.content for message in messages])
            return {"message": {"content": next(answers)}}

    monkeypatch.setattr(cli, "OllamaClient", FakeOllama)
    manifest = tmp_path / "manifest"
    cli.start_prompt_review(
        "B-TRAIN-0001", "qwen3.5:27b", "P1_human_guided", config_path, manifest
    )
    p1 = next((tmp_path / "output/v0.4/prompt_chain/P1_human_guided").glob("*/*/*"))
    explicit = {
        "feedback": [{
            "frame_numbers_1_based": [1],
            "observed_evidence": "The corner is visible.",
            "correction": "This is a corner, not a free kick.",
        }],
        "notes": "",
    }
    (p1 / "initial_review.json").write_text(json.dumps(explicit), encoding="utf-8")
    cli.revise_prompt_recognition(p1, config_path, manifest)
    (p1 / "revision_review.json").write_text(
        json.dumps(review_template()), encoding="utf-8"
    )
    cli.finish_prompt_coaching(p1, config_path, manifest)

    condition_path.write_text(json.dumps({
        "protocol_id": config["protocol_id"],
        "condition": "P2_attention_hint",
        "source_method": "P1_human_guided",
        "source_run": p1.relative_to(tmp_path).as_posix(),
        "source_stage": "stage_1_only",
        "allowed_split": "train",
        "clip_id": "B-TRAIN-0001",
        "prompt_path": hint.relative_to(tmp_path).as_posix(),
        "output_folder": "P2_attention_hint",
        "maximum_recognition_revisions": 1,
        "coaching_requires_human_approval": True,
    }), encoding="utf-8")

    cli.start_attention_review(p1, config_path, manifest)
    p2_root = tmp_path / "output/v0.4/prompt_chain/P2_attention_hint"
    p2 = next(p2_root.glob("*/*/*"))
    assert not (p2 / "stage_3_coaching_response.txt").exists()
    assert [len(history) for history in histories] == [1, 3, 5, 3]
    assert histories[3] == ["recognition", "original recognition", hint.read_text()]
    assert "corner" not in (p2 / "stage_2_revision_prompt.txt").read_text().lower()
    with pytest.raises(Exception, match="pending"):
        cli.finish_attention_coaching(p2, config_path, manifest)
    (p2 / "revision_review.json").write_text(
        json.dumps(review_template()), encoding="utf-8"
    )
    cli.finish_attention_coaching(p2, config_path, manifest)
    assert histories[4] == [
        "recognition", "original recognition", hint.read_text(),
        "attention revision", "coaching",
    ]
    assert cli.read_metadata(p2 / "metadata.txt")["run_status"] == "complete"
    assert (p1 / "stage_3_coaching_response.txt").read_text() == "explicit coaching"

    cli.start_attention_review(p1, config_path, manifest)
    rejected_run = sorted(p2_root.glob("*/*/*"))[-1]
    rejected_review = {
        "feedback": [{
            "frame_numbers_1_based": [1],
            "observed_evidence": "The recognition is unsupported.",
            "correction": "The event is still wrong.",
        }],
        "notes": "No coaching requested.",
    }
    (rejected_run / "revision_review.json").write_text(
        json.dumps(rejected_review), encoding="utf-8"
    )
    cli.finish_attention_coaching(rejected_run, config_path, manifest)
    assert not (rejected_run / "stage_3_coaching_response.txt").exists()
    assert cli.read_metadata(rejected_run / "metadata.txt")["run_status"] == (
        "recognition_rejected"
    )
    assert len(histories) == 6


def test_progressive_review_requires_a_cited_hint_or_clean_decision() -> None:
    review = {
        "decision": "hint", "frame_numbers_1_based": [2],
        "hint": "Recheck the ball in this image.", "notes": "",
    }
    assert validate_progressive_review(review, 30) == "hint"
    review["frame_numbers_1_based"] = [31]
    with pytest.raises(ValueError, match="sampled frame"):
        validate_progressive_review(review, 30)
    review.update(decision="approve", frame_numbers_1_based=[], hint="")
    assert validate_progressive_review(review, 30) == "approve"
    review["hint"] = "A late extra correction"
    with pytest.raises(ValueError, match="must not include"):
        validate_progressive_review(review, 30)


def test_fresh_progressive_p2_allows_three_hints_then_coaching(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    frames = []
    for index in range(1, 31):
        frame = frames_dir / f"{index:02d}_frame_{index:06d}.jpg"
        frame.write_bytes(f"frame {index}".encode())
        frames.append(frame)
    prompts = tmp_path / "input_prompts/v0.4"
    prompts.mkdir(parents=True)
    for name in ("recognition", "revision", "coaching"):
        (prompts / f"{name}.txt").write_text(name, encoding="utf-8")
    hint_prompt = prompts / "progressive.txt"
    hint_prompt.write_text("Re-examine the images.\nHUMAN HINT\n", encoding="utf-8")
    condition_path = tmp_path / "condition.json"
    condition_path.write_text(json.dumps({
        "protocol_id": "evidence-first-football-v0.4.0",
        "condition": "P2_attention_hint",
        "revision": "progressive_v1",
        "status": "draft_train_diagnostic",
        "starting_point": "fresh_recognition_from_30_frames",
        "allowed_split": "train",
        "initial_diagnostic_clip_id": "B-TRAIN-0025",
        "output_directory": "output/v0.4/prompt_chain/P2_attention_hint",
        "maximum_hints": 3,
        "hint_prompt_path": "input_prompts/v0.4/progressive.txt",
        "human_review_after_every_recognition": True,
        "coaching_requires_approved_recognition": True,
    }), encoding="utf-8")
    monkeypatch.setattr(cli, "P2_PROGRESSIVE_CONFIG", condition_path)
    config = {
        "protocol_id": "evidence-first-football-v0.4.0",
        "development": {"cohort_path": "cohort.json"},
        "dataset_b": {"human_reference_directory": "data/video_b/review"},
        "sampling": {
            "frame_count": 30, "maximum_edge": 672,
            "algorithm": "uniform_endpoints_v1", "image_encoding": "JPEG",
        },
        "prompts": {"P1_human_guided": {
            name: f"input_prompts/v0.4/{name}.txt"
            for name in ("recognition", "revision", "coaching")
        }},
        "output_root": "output/v0.4/prompt_chain",
        "models": ["qwen3.5:27b"],
        "generation": {"options": {"temperature": 0}, "think": False, "require_gpu": True},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "cohort.json").write_text('{"clip_ids":["B-TRAIN-0025"]}', encoding="utf-8")
    reference = tmp_path / "data/video_b/review/B-TRAIN-0025.json"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        cli, "validate_prompt_chain_config", lambda *_: {"clip_ids": ["B-TRAIN-0025"]}
    )
    monkeypatch.setattr(
        cli, "find_b_clip", lambda *_: SimpleNamespace(clip_id="B-TRAIN-0025", split="train")
    )
    monkeypatch.setattr(cli, "validate_human_reference", lambda *_: None)
    monkeypatch.setattr(cli, "sample_dataset_b", lambda *_: frames)
    monkeypatch.setattr(cli, "load_dotenv", lambda *_: None)
    answers = iter([
        "fresh recognition", "after hint one", "after hint two",
        "after hint three", "final advice", "fresh rejected recognition",
    ])
    histories: list[list[Any]] = []

    class FakeOllama:
        def model_metadata(self, _model: str) -> dict[str, str]:
            return {"digest": "a" * 64}

        def gpu_status(
            self, model: str, options: dict[str, Any], *, preload: bool = True
        ) -> dict[str, Any]:
            return {"model": model, "digest": "a" * 64, "size_vram_bytes": 10}

        def chat(
            self, model: str, messages: list[Any], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            histories.append(messages)
            return {"message": {"content": next(answers)}}

    monkeypatch.setattr(cli, "OllamaClient", FakeOllama)
    manifest = tmp_path / "manifest"
    cli.start_progressive_review("B-TRAIN-0025", "qwen3.5:27b", config_path, manifest)
    root = tmp_path / "output/v0.4/prompt_chain/P2_attention_hint"
    run_dir = next(root.glob("*/*/*"))
    assert len(histories[0]) == 1
    assert len(histories[0][0].images) == 30
    assert (run_dir / "stage_1_response.txt").read_text() == "fresh recognition"
    assert (run_dir / "review_stage_1.json").exists()
    assert not (run_dir / "review_stage_1.template.json").exists()
    with pytest.raises(Exception, match="Decision must"):
        cli.continue_progressive_review(run_dir, config_path, manifest)
    for stage in range(1, 4):
        review = {
            "decision": "hint", "frame_numbers_1_based": [stage],
            "hint": f"Check the ball in sampled image {stage}.", "notes": "",
        }
        (run_dir / f"review_stage_{stage}.json").write_text(
            json.dumps(review), encoding="utf-8"
        )
        cli.continue_progressive_review(run_dir, config_path, manifest)
        assert (run_dir / f"stage_{stage + 1}_revision_response.txt").exists()
        assert (run_dir / f"review_stage_{stage + 1}.json").exists()
        assert not (run_dir / f"review_stage_{stage + 1}.template.json").exists()
        assert not (run_dir / "stage_5_coaching_response.txt").exists()
    assert [len(history) for history in histories] == [1, 3, 5, 7]
    assert [m.content for m in histories[3]][1::2] == [
        "fresh recognition", "after hint one", "after hint two"
    ]
    assert "P1_human_guided" not in (run_dir / "stage_4_revision_prompt.txt").read_text()
    with pytest.raises(Exception, match="Maximum hints"):
        cli.continue_progressive_review(run_dir, config_path, manifest)
    (run_dir / "review_stage_4.json").write_text(
        json.dumps({
            "decision": "approve", "frame_numbers_1_based": [], "hint": "", "notes": ""
        }), encoding="utf-8"
    )
    cli.finish_progressive_coaching(run_dir, config_path, manifest)
    assert (run_dir / "stage_5_coaching_response.txt").read_text() == "final advice"
    assert len(histories[-1]) == 9
    assert cli.read_metadata(run_dir / "metadata.txt")["run_status"] == "complete"

    cli.start_progressive_review("B-TRAIN-0025", "qwen3.5:27b", config_path, manifest)
    stopped_run = sorted(root.glob("*/*/*"))[-1]
    (stopped_run / "review_stage_1.json").write_text(json.dumps({
        "decision": "stop", "frame_numbers_1_based": [], "hint": "", "notes": "wrong"
    }), encoding="utf-8")
    cli.finish_progressive_coaching(stopped_run, config_path, manifest)
    assert not (stopped_run / "stage_2_coaching_response.txt").exists()
    assert cli.read_metadata(stopped_run / "metadata.txt")["run_status"] == (
        "recognition_rejected"
    )
    assert len(histories) == 6


def test_frozen_visible_cue_p3_is_fresh_and_requires_approval(
    tmp_path: Path, monkeypatch: Any
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    frames = []
    for index in range(1, 31):
        frame = frames_dir / f"{index:02d}_frame_{index:06d}.jpg"
        frame.write_bytes(f"frame {index}".encode())
        frames.append(frame)
    prompts = tmp_path / "input_prompts/v0.4"
    prompts.mkdir(parents=True)
    for name in ("recognition", "revision", "coaching"):
        (prompts / f"{name}.txt").write_text(name, encoding="utf-8")
    cue_prompt = prompts / "visible.txt"
    cue_prompt.write_text("Check these frame-based observations.\nFROZEN VISIBLE CUES\n")
    cue_path = (
        tmp_path / "output/v0.4/prompt_chain/P3_visible_cue_hint/B-TRAIN-0025_cues.txt"
    )
    cue_path.parent.mkdir(parents=True)
    cue_path.write_text("Images 1-6: players gather near goal.\n", encoding="utf-8")
    condition_path = tmp_path / "condition.json"
    condition_path.write_text(json.dumps({
        "protocol_id": "evidence-first-football-v0.4.0",
        "condition": "P3_visible_cue_hint",
        "revision": "frozen_cues_v1",
        "status": "draft_train_diagnostic",
        "starting_point": "fresh_recognition_from_30_frames",
        "allowed_split": "train",
        "initial_diagnostic_clip_id": "B-TRAIN-0025",
        "output_directory": "output/v0.4/prompt_chain/P3_visible_cue_hint",
        "maximum_cue_packets": 1,
        "cue_sheet_path": cue_path.relative_to(tmp_path).as_posix(),
        "cue_sheet_sha256": cli.sha256_file(cue_path),
        "cue_prompt_path": cue_prompt.relative_to(tmp_path).as_posix(),
        "human_review_before_and_after_cues": True,
        "coaching_requires_approved_recognition": True,
    }), encoding="utf-8")
    monkeypatch.setattr(cli, "P3_VISIBLE_CONFIG", condition_path)
    config = {
        "protocol_id": "evidence-first-football-v0.4.0",
        "development": {"cohort_path": "cohort.json"},
        "dataset_b": {"human_reference_directory": "data/video_b/review"},
        "sampling": {"frame_count": 30, "maximum_edge": 672},
        "prompts": {"P1_human_guided": {
            name: f"input_prompts/v0.4/{name}.txt"
            for name in ("recognition", "revision", "coaching")
        }},
        "output_root": "output/v0.4/prompt_chain",
        "models": ["qwen3.5:27b"],
        "generation": {"options": {"temperature": 0}, "think": False, "require_gpu": True},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    (tmp_path / "cohort.json").write_text('{"clip_ids":["B-TRAIN-0025"]}')
    reference = tmp_path / "data/video_b/review/B-TRAIN-0025.json"
    reference.parent.mkdir(parents=True)
    reference.write_text("{}")
    monkeypatch.setattr(
        cli, "validate_prompt_chain_config", lambda *_: {"clip_ids": ["B-TRAIN-0025"]}
    )
    monkeypatch.setattr(
        cli, "find_b_clip", lambda *_: SimpleNamespace(clip_id="B-TRAIN-0025", split="train")
    )
    monkeypatch.setattr(cli, "validate_human_reference", lambda *_: None)
    monkeypatch.setattr(cli, "sample_dataset_b", lambda *_: frames)
    monkeypatch.setattr(cli, "load_dotenv", lambda *_: None)
    answers = iter(["fresh P3 recognition", "cue-revised recognition", "P3 advice",
                    "fresh stopped recognition"])
    histories: list[list[Any]] = []

    class FakeOllama:
        def model_metadata(self, _model: str) -> dict[str, str]:
            return {"digest": "a" * 64}

        def gpu_status(
            self, model: str, options: dict[str, Any], *, preload: bool = True
        ) -> dict[str, Any]:
            return {"model": model, "digest": "a" * 64, "size_vram_bytes": 10}

        def chat(
            self, model: str, messages: list[Any], *args: Any, **kwargs: Any
        ) -> dict[str, Any]:
            histories.append(messages)
            return {"message": {"content": next(answers)}}

    monkeypatch.setattr(cli, "OllamaClient", FakeOllama)
    manifest = tmp_path / "manifest"
    cli.start_visible_cue_review("B-TRAIN-0025", "qwen3.5:27b", config_path, manifest)
    root = tmp_path / "output/v0.4/prompt_chain/P3_visible_cue_hint"
    run_dir = next(root.glob("*/*/*"))
    assert len(histories[0]) == 1
    assert len(histories[0][0].images) == 30
    assert (run_dir / "stage_1_response.txt").read_text() == "fresh P3 recognition"
    assert (run_dir / "frozen_visible_cues.txt").read_text() == cue_path.read_text()
    with pytest.raises(Exception, match="P3 decision"):
        cli.continue_visible_cue_review(run_dir, config_path, manifest)
    (run_dir / "review_stage_1.json").write_text(
        json.dumps({"decision": "continue", "notes": "initial answer checked"})
    )
    cue_path.write_text("Changed cue text.")
    with pytest.raises(Exception, match="Invalid or changed frozen P3 cue"):
        cli.continue_visible_cue_review(run_dir, config_path, manifest)
    cue_path.write_text("Images 1-6: players gather near goal.\n")
    cli.continue_visible_cue_review(run_dir, config_path, manifest)
    assert len(histories[1]) == 3
    assert histories[1][1].content == "fresh P3 recognition"
    assert "Images 1-6" in histories[1][2].content
    assert "P1_human_guided" not in histories[1][2].content
    assert "P2_attention_hint" not in histories[1][2].content
    assert (run_dir / "review_stage_2.json").exists()
    with pytest.raises(Exception, match="P3 decision"):
        cli.finish_visible_cue_coaching(run_dir, config_path, manifest)
    response = run_dir / "stage_2_revision_response.txt"
    response.write_text("altered answer")
    with pytest.raises(Exception, match="P3 revision provenance changed"):
        cli.finish_visible_cue_coaching(run_dir, config_path, manifest)
    response.write_text("cue-revised recognition")
    (run_dir / "review_stage_2.json").write_text(
        json.dumps({"decision": "approve", "notes": "supported"})
    )
    cli.finish_visible_cue_coaching(run_dir, config_path, manifest)
    assert (run_dir / "stage_3_coaching_response.txt").read_text() == "P3 advice"
    assert len(histories[2]) == 5
    assert cli.read_metadata(run_dir / "metadata.txt")["run_status"] == "complete"

    cli.start_visible_cue_review("B-TRAIN-0025", "qwen3.5:27b", config_path, manifest)
    stopped_run = sorted(root.glob("*/*/*"))[-1]
    (stopped_run / "review_stage_1.json").write_text(
        json.dumps({"decision": "stop", "notes": "recognition insufficient"})
    )
    cli.finish_visible_cue_coaching(stopped_run, config_path, manifest)
    assert cli.read_metadata(stopped_run / "metadata.txt")["run_status"] == (
        "recognition_rejected"
    )
    assert not (stopped_run / "stage_2_revision_response.txt").exists()
    assert len(histories) == 4
