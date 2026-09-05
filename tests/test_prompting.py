from pathlib import Path
from typing import cast

import pytest

from football_coach.domain import CaseARecord
from football_coach.prompting import (
    PromptMessage,
    build_messages,
    plain_text_answer_issues,
    readable_transcript,
    render_template,
)


def test_template_requires_every_placeholder() -> None:
    with pytest.raises(ValueError, match="MISSING"):
        render_template("Hello {{NAME}} {{MISSING}}", {"NAME": "coach"})


def test_readable_transcript_preserves_image_order(tmp_path: Path) -> None:
    first = tmp_path / "01.jpg"
    second = tmp_path / "02.jpg"
    transcript = readable_transcript([PromptMessage("user", "Analyze", (first, second))], tmp_path)
    assert transcript.index("01.jpg") < transcript.index("02.jpg")


def test_b5_supplies_only_advice_not_case_fields(tmp_path: Path) -> None:
    frame = tmp_path / "B-TRAIN-0001" / "01_frame_000001.jpg"
    messages = build_messages(
        "B5_advice_only",
        "query",
        [frame],
        cast(CaseARecord, object()),
        "keep compact",
        "LEAKED {{CASE_A_OBSERVATION}}",
        advice_only_template="ADVICE={{CASE_A_ADVICE}}",
    )
    assert messages[0].content == "ADVICE=keep compact"
    assert "LEAKED" not in messages[0].content
    assert not messages[0].images


def test_plain_text_answer_checks_headings_without_requiring_json() -> None:
    answer = """RECOGNITION
Visible sequence.
ANALOGY
No case.
COACHING
Stay compact.
UNCERTAINTY
Medium.
"""
    assert plain_text_answer_issues(answer) == []
    assert plain_text_answer_issues("ordinary prose") == [
        "missing heading: RECOGNITION",
        "missing heading: ANALOGY",
        "missing heading: COACHING",
        "missing heading: UNCERTAINTY",
    ]
