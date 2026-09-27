from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .prompting import PromptMessage

P1_METHOD = "P1_two_turn"

RECOGNITION_HEADINGS = (
    "VISIBLE EVIDENCE",
    "CHRONOLOGY",
    "EVENT ASSESSMENT",
    "EVIDENCE LIMITS",
)

COACHING_HEADINGS = (
    "TACTICAL INTERPRETATION",
    "COACHING",
    "SAFETY AND UNCERTAINTY",
)


def heading_issues(answer: str, required_headings: tuple[str, ...]) -> list[str]:
    """Report format omissions without repairing or rejecting model content."""
    if not answer.strip():
        return ["answer is empty"]
    lines = {line.strip().upper() for line in answer.splitlines()}
    return [
        f"missing heading: {heading}"
        for heading in required_headings
        if heading not in lines
    ]


def build_recognition_messages(prompt: str, frames: list[Path]) -> list[PromptMessage]:
    if not frames:
        raise ValueError("Recognition requires at least one ordered frame")
    return [PromptMessage("user", prompt, tuple(frames))]


def build_coaching_messages(
    recognition_prompt: str,
    frames: list[Path],
    recognition_answer: str,
    coaching_prompt: str,
) -> list[PromptMessage]:
    """Continue the same visual conversation without human correction."""
    if not recognition_answer.strip():
        raise ValueError("Coaching requires the preserved recognition answer")
    return [
        PromptMessage("user", recognition_prompt, tuple(frames)),
        PromptMessage("assistant", recognition_answer),
        PromptMessage("user", coaching_prompt),
    ]


def response_text(raw_response: dict[str, Any]) -> str:
    return str(raw_response.get("message", {}).get("content", ""))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_metadata(path: Path, metadata: dict[str, Any]) -> None:
    lines = [
        f"{key}: {json.dumps(value, ensure_ascii=False)}"
        for key, value in metadata.items()
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
