from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

RightsStatus = Literal["verified_redistributable", "private_research_only", "link_only", "unknown"]
CaseStatus = Literal["draft", "approved", "rejected"]
ActionFamily = Literal[
    "corner",
    "free_kick",
    "between_lines",
    "overload",
    "one_v_one_defending",
    "low_block",
    "high_press",
    "counterpress",
    "high_regain",
    "other",
]
Condition = Literal[
    "B0_frames_only",
    "B1_random_case",
    "B2_action_oracle",
    "B3_human_oracle",
    "B4_embedding_knn",
    "B5_advice_only",
]


def safe_relative_path(value: str) -> bool:
    path = PurePosixPath(value.replace("\\", "/"))
    return not path.is_absolute() and ".." not in path.parts


class SourceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = ""
    provider: str = ""
    url: HttpUrl
    accessed_on: date
    rights_status: RightsStatus
    local_media_path: str | None = None
    clip_start_seconds: float = Field(ge=0)
    clip_end_seconds: float = Field(gt=0)

    @model_validator(mode="after")
    def validate_clip(self) -> SourceInfo:
        if self.clip_end_seconds <= self.clip_start_seconds:
            raise ValueError("clip_end_seconds must be greater than clip_start_seconds")
        if self.local_media_path and not safe_relative_path(self.local_media_path):
            raise ValueError("local_media_path must be a safe project-relative path")
        if self.local_media_path and not self.local_media_path.replace("\\", "/").startswith(
            "data/video_a/media/"
        ):
            raise ValueError("local_media_path must be under data/video_a/media")
        return self


class FootballSituation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: str = "unclear"
    action_family: ActionFamily = "other"
    team_role: str = "unclear"
    pitch_area: str = "unclear"
    outcome: str = "unclear"
    human_observation: str = ""
    priority_problem: str = ""
    visible_evidence: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class CoachingReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    advice_path: str
    objective: str = ""
    practice_design: str = ""
    success_cues: list[str] = Field(default_factory=list)
    reference_author: str = ""
    reference_author_qualification: str = ""

    @model_validator(mode="after")
    def validate_path(self) -> CoachingReference:
        if not safe_relative_path(self.advice_path):
            raise ValueError("advice_path must be a safe project-relative path")
        if not self.advice_path.replace("\\", "/").startswith("data/video_a/advice/"):
            raise ValueError("advice_path must be under data/video_a/advice")
        return self


class CaseARecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^A-[0-9]{4}$")
    status: CaseStatus
    source: SourceInfo
    situation: FootballSituation
    coaching: CoachingReference
    limitations: list[str] = Field(default_factory=list)

    def approval_errors(self, project_root: Path) -> list[str]:
        errors: list[str] = []
        required_text = {
            "source.title": self.source.title,
            "source.provider": self.source.provider,
            "situation.human_observation": self.situation.human_observation,
            "situation.priority_problem": self.situation.priority_problem,
            "coaching.objective": self.coaching.objective,
            "coaching.practice_design": self.coaching.practice_design,
            "coaching.reference_author": self.coaching.reference_author,
            "coaching.reference_author_qualification": (
                self.coaching.reference_author_qualification
            ),
        }
        errors.extend(
            f"{name} is required" for name, value in required_text.items() if not value.strip()
        )
        if self.source.rights_status == "unknown":
            errors.append("source.rights_status must be resolved")
        if not self.source.local_media_path:
            errors.append("source.local_media_path is required for a visual case")
        elif not (project_root / self.source.local_media_path).is_file():
            errors.append(f"media file is missing: {self.source.local_media_path}")
        advice_path = project_root / self.coaching.advice_path
        if not advice_path.is_file() or not advice_path.read_text(encoding="utf-8").strip():
            errors.append(f"advice text is missing or empty: {self.coaching.advice_path}")
        if not self.situation.visible_evidence:
            errors.append("situation.visible_evidence requires at least one item")
        if not self.coaching.success_cues:
            errors.append("coaching.success_cues requires at least one item")
        return errors


@dataclass(frozen=True)
class SoccerNetClip:
    clip_id: str
    source_clip_id: str
    split: str
    action_class: str
    frame_rate: int
    frame_count: int
    annotation_version: str
    archive_path: str
    label_member: str
    frame_member_pattern: str


class ReviewerInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name_or_code: str
    football_qualification_or_experience: str
    reviewed_at_utc: datetime


class ReferenceReviewProtocol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    used_only_neutral_id_and_frames: Literal[True]
    blinded_to_soccernet_label_during_visual_review: Literal[True]
    blinded_to_model_answers: Literal[True]
    blinded_to_dataset_a_pairs: Literal[True]


class VisualReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chronological_visible_description: list[str] = Field(min_length=1)
    possession_by_visible_appearance: str = Field(min_length=1)
    tactical_phase: str = Field(min_length=1)
    main_visible_event: str = Field(min_length=1)
    outcome: str = Field(min_length=1)
    visibility_limitations: list[str]


class SamplingVisibility(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_visible: bool
    notes: str


class HiddenBReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    soccernet_action_label: str = Field(min_length=1)
    attached_only_after_visual_review: Literal[True]
    used_as_coaching_ground_truth: Literal[False]
    blind_snapshot_path: str = Field(min_length=1)
    blind_snapshot_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class DatasetBHumanReference(BaseModel):
    """Private scoring reference completed without seeing labels or model answers."""

    model_config = ConfigDict(extra="forbid")

    reference_version: Literal["0.3.0"]
    clip_id: str = Field(pattern=r"^B-(TRAIN|VALID|TEST)-[0-9]{4}$")
    review_status: Literal["approved"]
    reviewer: ReviewerInfo
    review_protocol: ReferenceReviewProtocol
    visual_reference: VisualReference
    sampling_visibility: dict[str, SamplingVisibility]
    hidden_reference: HiddenBReference

    @model_validator(mode="after")
    def require_split_appropriate_sampling_conditions(self) -> DatasetBHumanReference:
        keys = set(self.sampling_visibility)
        invalid = sorted(key for key in keys if not re.fullmatch(r"F[1-9][0-9]*", key))
        if invalid:
            raise ValueError(f"Invalid sampling_visibility keys: {invalid}")
        if self.clip_id.startswith("B-TRAIN-"):
            required = {"F10", "F20", "F30", "F60"}
            if keys != required:
                raise ValueError(
                    f"Training pilot sampling_visibility must contain exactly {sorted(required)}"
                )
        elif len(keys) != 1:
            raise ValueError(
                "Validation and test sampling_visibility must contain exactly one frozen candidate"
            )
        return self


class HumanScoreRecord(BaseModel):
    """Validated human-entered scores parsed from the plain-text score form."""

    model_config = ConfigDict(extra="forbid")

    score_version: Literal["1.0"]
    run_id: str = Field(min_length=1)
    clip_id: str = Field(pattern=r"^B-(TRAIN|VALID|TEST)-[0-9]{4}$")
    blinding: dict[str, bool]
    recognition: dict[str, int | str]
    retrieval_relevance: dict[str, int | str | None]
    coaching: dict[str, int | str]
    failure_modes: dict[str, int | str | None]
    uncertainty: dict[str, int | str]
    critical_event_missed: bool
    critical_event_missed_reason: str
    notes: str
