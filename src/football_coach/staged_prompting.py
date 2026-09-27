from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .prompting import PromptMessage
from .provenance import sha256_file

P1_METHOD = "P1_human_guided"
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


def review_template(answer_sha256: str, *, revised: bool = False) -> dict[str, Any]:
    return {
        "decision": "PENDING",
        "reviewer_code": "REPLACE_ME",
        "reviewed_at_utc": "REPLACE_ME",
        "used_only_sampled_frames": None,
        "used_hidden_labels": None,
        "answer_sha256": answer_sha256,
        "feedback": [] if revised else [
            {
                "frame_numbers_1_based": [],
                "observed_evidence": "REPLACE_ME",
                "correction": "REPLACE_ME",
            }
        ],
        "notes": "",
    }


def validate_review(
    review: dict[str, Any],
    answer_path: Path,
    allowed_frame_numbers: set[int],
    *,
    revised: bool = False,
) -> None:
    allowed_decisions = {"approve", "reject"} if revised else {"approve", "revise"}
    if review.get("decision") not in allowed_decisions:
        raise ValueError(f"Review decision must be one of {sorted(allowed_decisions)}")
    if review.get("answer_sha256") != sha256_file(answer_path):
        raise ValueError("Review answer hash does not match the preserved response")
    if review.get("used_only_sampled_frames") is not True:
        raise ValueError("Reviewer must confirm use of sampled frames only")
    if review.get("used_hidden_labels") is not False:
        raise ValueError("Reviewer must confirm hidden labels were not used")
    for field in ("reviewer_code", "reviewed_at_utc"):
        value = review.get(field)
        if not isinstance(value, str) or not value.strip() or value == "REPLACE_ME":
            raise ValueError(f"Review requires {field}")
    feedback = review.get("feedback")
    if not isinstance(feedback, list):
        raise ValueError("Review feedback must be a list")
    if review["decision"] in {"approve", "reject"} and feedback:
        raise ValueError("Approval or rejection must not include correction feedback")
    if review["decision"] == "revise" and not feedback:
        raise ValueError("Revision requires frame-cited feedback")
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
