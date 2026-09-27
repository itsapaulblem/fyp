import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from football_coach import cli
from football_coach.provenance import sha256_file
from football_coach.staged_prompting import (
    coaching_messages,
    feedback_text,
    recognition_messages,
    review_template,
    revision_messages,
    validate_review,
)


def test_human_review_requires_matching_answer_and_frame_evidence(tmp_path: Path) -> None:
    answer = tmp_path / "answer.txt"
    answer.write_text("initial recognition", encoding="utf-8")
    review = review_template(sha256_file(answer))
    review.update(
        decision="revise",
        reviewer_code="R1",
        reviewed_at_utc="2026-09-27T00:00:00Z",
        used_only_sampled_frames=True,
        used_hidden_labels=False,
        feedback=[{
            "frame_numbers_1_based": [18, 22],
            "observed_evidence": "The ball moves away from goal.",
            "correction": "Do not claim a goalkeeper catch.",
        }],
    )
    validate_review(review, answer, {18, 22})
    review["feedback"][0]["frame_numbers_1_based"] = [99]
    with pytest.raises(ValueError, match="sampled frame"):
        validate_review(review, answer, {18, 22})
    review["feedback"][0]["frame_numbers_1_based"] = [18]
    review["answer_sha256"] = "wrong"
    with pytest.raises(ValueError, match="hash"):
        validate_review(review, answer, {18, 22})


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
        "generation": {"options": {"temperature": 0}, "think": False},
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
    with pytest.raises(Exception, match="review file"):
        cli.finish_prompt_coaching(run_dir, config_path, tmp_path / "manifest")

    initial = json.loads((run_dir / "initial_review.template.json").read_text(encoding="utf-8"))
    initial.update(
        decision="revise",
        reviewer_code="R1",
        reviewed_at_utc="2026-09-27T00:00:00Z",
        used_only_sampled_frames=True,
        used_hidden_labels=False,
        feedback=[{
            "frame_numbers_1_based": [1],
            "observed_evidence": "The ball moves away.",
            "correction": "Remove the claimed catch.",
        }],
    )
    (run_dir / "initial_review.json").write_text(json.dumps(initial), encoding="utf-8")
    cli.revise_prompt_recognition(run_dir, config_path, tmp_path / "manifest")
    assert not (run_dir / "stage_3_coaching_response.txt").exists()
    revised = json.loads((run_dir / "revision_review.template.json").read_text(encoding="utf-8"))
    revised.update(
        decision="approve",
        reviewer_code="R1",
        reviewed_at_utc="2026-09-27T00:01:00Z",
        used_only_sampled_frames=True,
        used_hidden_labels=False,
    )
    (run_dir / "revision_review.json").write_text(json.dumps(revised), encoding="utf-8")
    cli.finish_prompt_coaching(run_dir, config_path, tmp_path / "manifest")
    assert (run_dir / "stage_3_coaching_response.txt").read_text(encoding="utf-8") == (
        "final coaching"
    )
    assert [len(history) for history in histories] == [1, 3, 5]
    assert histories[2][1] == "first recognition"
    assert histories[2][3] == "revised recognition"
    assert cli.read_metadata(run_dir / "metadata.txt")["run_status"] == "complete"

    cli.start_prompt_review(
        "B-TRAIN-0001", "qwen3.5:27b", "P1_human_guided", config_path, tmp_path / "manifest"
    )
    second_run = sorted((tmp_path / "output/v0.4/prompt_chain/P1_human_guided").glob("*/*/*"))[-1]
    approved = json.loads(
        (second_run / "initial_review.template.json").read_text(encoding="utf-8")
    )
    approved.update(
        decision="approve",
        reviewer_code="R1",
        reviewed_at_utc="2026-09-27T00:02:00Z",
        used_only_sampled_frames=True,
        used_hidden_labels=False,
        feedback=[],
    )
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
        (third_run / "initial_review.template.json").read_text(encoding="utf-8")
    )
    correction_review.update(
        decision="revise",
        reviewer_code="R1",
        reviewed_at_utc="2026-09-27T00:03:00Z",
        used_only_sampled_frames=True,
        used_hidden_labels=False,
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
        (third_run / "revision_review.template.json").read_text(encoding="utf-8")
    )
    rejected.update(
        decision="reject",
        reviewer_code="R1",
        reviewed_at_utc="2026-09-27T00:04:00Z",
        used_only_sampled_frames=True,
        used_hidden_labels=False,
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
