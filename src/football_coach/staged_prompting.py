from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .prompting import PromptMessage

P1_METHOD = "P1_human_guided"
P2_METHOD = "P2_attention_hint"
P3_METHOD = "P3_visible_cue_hint"
RECOGNITION_HEADINGS = (
    "VISIBLE EVIDENCE",
    "CHRONOLOGY",
    "EVENT ASSESSMENT",
    "EVIDENCE LIMITS",
)
COACHING_HEADINGS = ("TACTICAL INTERPRETATION", "COACHING", "SAFETY AND UNCERTAINTY")


def heading_issues(answer: str, required_headings: tuple[str, ...]) -> list[str]:
    if not answer.strip():
        return ["answer is empty"]
    lines = {line.strip().upper() for line in answer.splitlines()}
    return [f"missing heading: {heading}" for heading in required_headings if heading not in lines]


def response_text(raw_response: dict[str, Any]) -> str:
    return str(raw_response.get("message", {}).get("content", ""))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_metadata(path: Path, metadata: dict[str, Any]) -> None:
    lines = [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_metadata(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Malformed metadata line in {path}")
        values[key.strip()] = json.loads(value.strip())
    return values


def review_template() -> dict[str, Any]:
    return {"feedback": [], "notes": ""}


def pending_guided_review() -> dict[str, Any]:
    return {"feedback": [], "notes": "PENDING_REVIEW"}


def validate_review(
    review: dict[str, Any],
    allowed_frame_numbers: set[int],
    *,
    revised: bool = False,
) -> str:
    if set(review) != {"feedback", "notes"}:
        raise ValueError("Review must contain only feedback and notes")
    feedback = review.get("feedback")
    if not isinstance(feedback, list):
        raise ValueError("Review feedback must be a list")
    if not isinstance(review.get("notes"), str):
        raise ValueError("Review notes must be text")
    if review["notes"] == "PENDING_REVIEW":
        raise ValueError("Review is pending; edit notes after checking the frames")
    for item in feedback:
        if not isinstance(item, dict):
            raise ValueError("Each feedback item must be an object")
        numbers = item.get("frame_numbers_1_based")
        if (
            not isinstance(numbers, list)
            or not numbers
            or any(
                not isinstance(number, int)
                or isinstance(number, bool)
                or number not in allowed_frame_numbers
                for number in numbers
            )
        ):
            raise ValueError("Each correction must cite sampled frame numbers")
        for field in ("observed_evidence", "correction"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip() or value == "REPLACE_ME":
                raise ValueError(f"Each correction requires {field}")
    return ("reject" if revised else "revise") if feedback else "approve"


def feedback_text(review: dict[str, Any], prompt: str) -> str:
    lines = [prompt.rstrip(), "", "HUMAN FRAME-BASED FEEDBACK"]
    for index, item in enumerate(review["feedback"], 1):
        numbers = ", ".join(str(number) for number in item["frame_numbers_1_based"])
        lines.extend(
            [
                f"{index}. Sampled frames: {numbers}",
                f"Visible evidence: {item['observed_evidence']}",
                f"Correction requested: {item['correction']}",
            ]
        )
    return "\n".join(lines) + "\n"


def recognition_messages(prompt: str, frames: list[Path]) -> list[PromptMessage]:
    if not frames:
        raise ValueError("Recognition requires ordered frames")
    return [PromptMessage("user", prompt, tuple(frames))]


def revision_messages(
    recognition_prompt: str,
    frames: list[Path],
    initial_answer: str,
    correction_text: str,
) -> list[PromptMessage]:
    return [
        *recognition_messages(recognition_prompt, frames),
        PromptMessage("assistant", initial_answer),
        PromptMessage("user", correction_text),
    ]


def validate_progressive_review(review: dict[str, Any], frame_count: int) -> str:
    if set(review) != {"decision", "frame_numbers_1_based", "hint", "notes"}:
        raise ValueError("Progressive review needs decision, frame numbers, hint, and notes")
    decision = review["decision"]
    if not isinstance(decision, str) or decision not in {"hint", "approve", "stop"}:
        raise ValueError("Decision must be hint, approve, or stop")
    numbers = review["frame_numbers_1_based"]
    if not isinstance(numbers, list) or any(
        not isinstance(n, int) or isinstance(n, bool) or n < 1 or n > frame_count
        for n in numbers
    ) or len(set(numbers)) != len(numbers):
        raise ValueError("Hint must cite valid, unique sampled frame numbers")
    if not isinstance(review["hint"], str) or not isinstance(review["notes"], str):
        raise ValueError("Hint and notes must be text")
    if decision == "hint" and (not numbers or not review["hint"].strip()):
        raise ValueError("A hint requires frame citations and nonempty hint text")
    if decision != "hint" and (numbers or review["hint"].strip()):
        raise ValueError("Approval or stopping must not include a new hint")
    return decision


def validate_visible_cue_review(review: dict[str, Any], *, revised: bool) -> str:
    if set(review) != {"decision", "notes"}:
        raise ValueError("P3 review needs only decision and notes")
    allowed = {"approve", "stop"} if revised else {"continue", "stop"}
    decision = review["decision"]
    if not isinstance(decision, str) or decision not in allowed:
        raise ValueError(f"P3 decision must be one of: {', '.join(sorted(allowed))}")
    if not isinstance(review["notes"], str):
        raise ValueError("P3 review notes must be text")
    return decision


def progressive_messages(
    recognition_prompt: str,
    frames: list[Path],
    answers: list[str],
    hints: list[str],
    next_prompt: str | None = None,
) -> list[PromptMessage]:
    if len(answers) != len(hints) + 1:
        raise ValueError("Each completed hint needs one subsequent recognition answer")
    messages = recognition_messages(recognition_prompt, frames)
    for index, answer in enumerate(answers):
        messages.append(PromptMessage("assistant", answer))
        if index < len(hints):
            messages.append(PromptMessage("user", hints[index]))
    if next_prompt is not None:
        messages.append(PromptMessage("user", next_prompt))
    return messages


def coaching_messages(
    recognition_prompt: str,
    frames: list[Path],
    initial_answer: str,
    coaching_prompt: str,
    correction_text: str | None = None,
    revised_answer: str | None = None,
) -> list[PromptMessage]:
    messages = [
        *recognition_messages(recognition_prompt, frames),
        PromptMessage("assistant", initial_answer),
    ]
    if correction_text is not None:
        if not revised_answer:
            raise ValueError("Coaching after feedback requires the preserved revision")
        messages.extend(
            [PromptMessage("user", correction_text), PromptMessage("assistant", revised_answer)]
        )
    messages.append(PromptMessage("user", coaching_prompt))
    return messages
