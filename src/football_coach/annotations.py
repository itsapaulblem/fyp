from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .dataset import ClipRecord


def blank_annotation(record: ClipRecord) -> dict[str, Any]:
    return {
        "clip_id": record.clip_id,
        "split": record.split,
        "reviewer": {"pseudonym": "", "qualification": "", "reviewed_at": ""},
        "observation": {
            "phase": "unclear",
            "possession_team_description": "",
            "visible_evidence": [],
        },
        "coaching_problem": {
            "team": "not_identifiable",
            "problem": "",
            "why_it_matters": "",
        },
        "intervention": {
            "objective": "",
            "coach_message": "",
            "practice_design": "",
            "success_cues": [],
        },
        "uncertainty": {"visibility_limits": [], "confidence": "low"},
        "source_references": [],
        "review_status": "draft",
    }


def initialize_annotations(records: list[ClipRecord], root: Path) -> int:
    created = 0
    for record in records:
        destination = root / record.split / f"{record.clip_id}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            continue
        destination.write_text(
            json.dumps(blank_annotation(record), indent=2) + "\n", encoding="utf-8"
        )
        created += 1
    return created


def validate_annotation(path: Path, schema: dict[str, Any]) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
        for error in sorted(
            validator.iter_errors(payload), key=lambda item: list(item.absolute_path)
        )
    ]

