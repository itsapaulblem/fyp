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
    action_mapping: dict[str, str | None] | None = None,
) -> CaseARecord:
    if condition not in {"B1_random_case", "B2_action_oracle"}:
        raise ValueError("Deterministic control selection is only for B1 or B2")
    if condition == "B1_random_case":
        # Selection depends only on the neutral B ID and fixed seed. Relevance is
        # assessed later by a blinded scorer; hidden B labels never filter B1.
        candidates = list(cases)
    else:
        if action_mapping is None:
            raise ValueError("B2 requires an explicit versioned action mapping")
        mapped_family = action_mapping.get(query.action_class)
        if mapped_family is None:
            raise ValueError(
                f"B2 is not evaluable for hidden action {query.action_class!r}; "
                "do not substitute an unrelated case"
            )
        candidates = [
            case
            for case in cases
            if normalize_action(case.situation.action_family) == normalize_action(mapped_family)
        ]
    candidates.sort(key=lambda case: case.case_id)
    if not candidates:
        raise ValueError(f"No eligible Dataset A case exists for {condition}")
    token = f"{seed}:{condition}:{query.clip_id}".encode()
    index = int.from_bytes(hashlib.sha256(token).digest()[:8], "big") % len(candidates)
    return candidates[index]
