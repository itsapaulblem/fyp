from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pydantic import ValidationError

from .domain import CaseARecord


def load_case(path: Path) -> CaseARecord:
    return CaseARecord.model_validate_json(path.read_text(encoding="utf-8"))


def load_library(case_dir: Path) -> dict[str, CaseARecord]:
    cases: dict[str, CaseARecord] = {}
    for path in sorted(case_dir.glob("A-*.json")):
        case = load_case(path)
        if case.case_id in cases:
            raise ValueError(f"Duplicate Dataset A case ID: {case.case_id}")
        cases[case.case_id] = case
    return cases


def validate_library(case_dir: Path, project_root: Path) -> dict[str, list[str]]:
    reports: dict[str, list[str]] = {}
    for path in sorted(case_dir.glob("A-*.json")):
        try:
            case = load_case(path)
        except (ValidationError, json.JSONDecodeError) as error:
            reports[path.stem] = [str(error)]
            continue
        errors = case.approval_errors(project_root) if case.status == "approved" else []
        reports[case.case_id] = errors
    return reports


def initialize_case(
    case_id: str,
    project_root: Path,
    case_template: Path,
    advice_template: Path,
) -> tuple[Path, Path]:
    if not case_id.startswith("A-") or len(case_id) != 6 or not case_id[2:].isdigit():
        raise ValueError("case_id must use the form A-0001")
    case_path = project_root / "data/video_a/cases" / f"{case_id}.json"
    advice_path = project_root / "data/video_a/advice" / f"{case_id}.txt"
    if case_path.exists() or advice_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing work for {case_id}")
    payload = deepcopy(json.loads(case_template.read_text(encoding="utf-8")))
    payload["case_id"] = case_id
    payload["source"]["local_media_path"] = f"data/video_a/media/{case_id}.mp4"
    payload["coaching"]["advice_path"] = f"data/video_a/advice/{case_id}.txt"
    case_path.parent.mkdir(parents=True, exist_ok=True)
    advice_path.parent.mkdir(parents=True, exist_ok=True)
    case_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    advice_path.write_text(advice_template.read_text(encoding="utf-8"), encoding="utf-8")
    return case_path, advice_path
