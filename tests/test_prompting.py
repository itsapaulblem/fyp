from pathlib import Path

import pytest

from football_coach.prompting import PromptMessage, readable_transcript, render_template


def test_template_requires_every_placeholder() -> None:
    with pytest.raises(ValueError, match="MISSING"):
        render_template("Hello {{NAME}} {{MISSING}}", {"NAME": "coach"})


def test_readable_transcript_preserves_image_order(tmp_path: Path) -> None:
    first = tmp_path / "01.jpg"
    second = tmp_path / "02.jpg"
    transcript = readable_transcript(
        [PromptMessage("user", "Analyze", (first, second))], tmp_path
    )
    assert transcript.index("01.jpg") < transcript.index("02.jpg")

