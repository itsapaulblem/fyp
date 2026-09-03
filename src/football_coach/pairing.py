from __future__ import annotations

import hashlib
import re

from .domain import CaseARecord, Condition, SoccerNetClip


def normalize_action(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def deterministic_control_case(
    cases: list[CaseARecord],
    query: SoccerNetClip,
    condition: Condition,
    seed: int,
) -> CaseARecord:
    if condition not in {"B1_random_case", "B2_action_oracle"}:
        raise ValueError("Deterministic control selection is only for B1 or B2")
    query_action = normalize_action(query.action_class)
    if condition == "B1_random_case":
        candidates = [
            case
            for case in cases
            if normalize_action(case.situation.action_family) != query_action
        ]
    else:
        candidates = [
            case
            for case in cases
            if normalize_action(case.situation.action_family) == query_action
        ]
    candidates.sort(key=lambda case: case.case_id)
    if not candidates:
        raise ValueError(f"No eligible Dataset A case exists for {condition}")
    token = f"{seed}:{condition}:{query.clip_id}".encode()
    index = int.from_bytes(hashlib.sha256(token).digest()[:8], "big") % len(candidates)
    return candidates[index]

