from pathlib import Path

import pytest

from football_coach.staged_prompting import (
    COACHING_HEADINGS,
    RECOGNITION_HEADINGS,
    build_coaching_messages,
    build_recognition_messages,
    heading_issues,
)


def test_recognition_requires_frames() -> None:
    with pytest.raises(ValueError, match="at least one"):
        build_recognition_messages("recognise", [])


def test_coaching_continues_exact_visual_conversation(tmp_path: Path) -> None:
    frame = tmp_path / "01.jpg"
    messages = build_coaching_messages(
        "recognise",
        [frame],
        "raw recognition",
        "coach",
    )
    assert [message.role for message in messages] == ["user", "assistant", "user"]
    assert messages[0].images == (frame,)
    assert messages[1].content == "raw recognition"
    assert not messages[2].images


def test_stage_heading_checks_do_not_repair_answers() -> None:
    recognition = "\n".join(RECOGNITION_HEADINGS)
    coaching = "\n".join(COACHING_HEADINGS)
    assert heading_issues(recognition, RECOGNITION_HEADINGS) == []
    assert heading_issues(coaching, COACHING_HEADINGS) == []
    assert heading_issues("VISIBLE EVIDENCE", RECOGNITION_HEADINGS) == [
        "missing heading: CHRONOLOGY",
        "missing heading: EVENT ASSESSMENT",
        "missing heading: EVIDENCE LIMITS",
    ]
