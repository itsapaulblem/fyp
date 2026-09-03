from football_coach.domain import CaseARecord, SoccerNetClip
from football_coach.pairing import deterministic_control_case, normalize_action


def make_case(case_id: str, action: str) -> CaseARecord:
    return CaseARecord.model_validate(
        {
            "case_id": case_id,
            "status": "draft",
            "source": {
                "title": "source",
                "provider": "provider",
                "url": "https://example.com",
                "accessed_on": "2026-09-03",
                "rights_status": "unknown",
                "local_media_path": f"data/video_a/media/{case_id}.mp4",
                "clip_start_seconds": 0,
                "clip_end_seconds": 30,
            },
            "situation": {"action_family": action},
            "coaching": {"advice_path": f"data/video_a/advice/{case_id}.txt"},
        }
    )


def test_action_normalization_handles_official_punctuation() -> None:
    assert normalize_action("Direct free-kick") == "direct_free_kick"


def test_control_pairing_is_deterministic_and_respects_action() -> None:
    cases = [make_case("A-0001", "corner"), make_case("A-0002", "free_kick")]
    query = SoccerNetClip(
        "SNGS-001", "train", "Corner", 25, 750, "1.3", "x.zip", "label", "%06d.jpg"
    )
    oracle = deterministic_control_case(cases, query, "B2_action_oracle", 42)
    unrelated = deterministic_control_case(cases, query, "B1_random_case", 42)
    assert oracle.case_id == "A-0001"
    assert unrelated.case_id == "A-0002"
