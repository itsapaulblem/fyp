from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .domain import CaseARecord, Condition

PLACEHOLDER = re.compile(r"{{([A-Z0-9_]+)}}")
REQUIRED_ANSWER_HEADINGS = ("RECOGNITION", "ANALOGY", "COACHING", "UNCERTAINTY")


@dataclass(frozen=True)
class PromptMessage:
    role: str
    content: str
    images: tuple[Path, ...] = ()


def render_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for name, value in values.items():
        rendered = rendered.replace("{{" + name + "}}", value)
    remaining = sorted(set(PLACEHOLDER.findall(rendered)))
    if remaining:
        raise ValueError(f"Unresolved prompt placeholders: {', '.join(remaining)}")
    return rendered


def case_a_prompt(case: CaseARecord, advice: str, template: str) -> str:
    return render_template(
        template,
        {
            "CASE_A_ID": case.case_id,
            "CASE_A_OBSERVATION": case.situation.human_observation,
            "CASE_A_PHASE": case.situation.phase,
            "CASE_A_ACTION": case.situation.action_family,
            "CASE_A_OUTCOME": case.situation.outcome,
            "CASE_A_PROBLEM": case.situation.priority_problem,
            "CASE_A_ADVICE": advice.strip(),
        },
    )


def build_messages(
    condition: Condition,
    query_prompt: str,
    frames_b: list[Path],
    case: CaseARecord | None = None,
    advice: str | None = None,
    case_template: str | None = None,
    frames_a: list[Path] | None = None,
    advice_only_template: str | None = None,
) -> list[PromptMessage]:
    if condition == "B0_frames_only":
        return [PromptMessage("user", query_prompt, tuple(frames_b))]
    if case is None or advice is None or case_template is None:
        raise ValueError(f"{condition} requires a Dataset A case and advice")
    if condition == "B5_advice_only":
        if advice_only_template is None:
            raise ValueError("B5_advice_only requires its advice-only template")
        example = render_template(advice_only_template, {"CASE_A_ADVICE": advice.strip()})
        return [
            PromptMessage("user", example),
            PromptMessage("user", query_prompt, tuple(frames_b)),
        ]
    example_images: tuple[Path, ...] = ()
    if condition != "B5_advice_only":
        if not frames_a:
            raise ValueError(f"{condition} requires Dataset A frames")
        example_images = tuple(frames_a)
    example = case_a_prompt(case, advice, case_template)
    return [
        PromptMessage("user", example, example_images),
        PromptMessage("user", query_prompt, tuple(frames_b)),
    ]


def readable_transcript(messages: list[PromptMessage], project_root: Path) -> str:
    sections: list[str] = []
    for index, message in enumerate(messages, start=1):
        sections.append(f"MESSAGE {index} — {message.role.upper()}")
        sections.append(message.content.rstrip())
        if message.images:
            sections.append("Images in chronological order:")
            sections.extend(
                f"- {path.relative_to(project_root).as_posix()}" for path in message.images
            )
        sections.append("")
    return "\n".join(sections).rstrip() + "\n"


def plain_text_answer_issues(answer: str) -> list[str]:
    """Report format omissions without changing or rejecting the model's answer."""
    if not answer.strip():
        return ["answer is empty"]
    lines = {line.strip().upper() for line in answer.splitlines()}
    return [
        f"missing heading: {heading}"
        for heading in REQUIRED_ANSWER_HEADINGS
        if heading not in lines
    ]
