from pathlib import Path

from football_coach.catalog import initialize_case, load_case


def test_case_template_is_created_without_overwrite(tmp_path: Path) -> None:
    templates = tmp_path / "templates"
    templates.mkdir()
    case_template = templates / "case.json"
    advice_template = templates / "advice.txt"
    case_template.write_text(
        """{
          "case_id": "A-0001", "status": "draft",
          "source": {"title": "", "provider": "", "url": "https://example.com",
            "accessed_on": "2026-09-03", "rights_status": "unknown",
            "local_media_path": "data/video_a/media/A-0001.mp4",
            "clip_start_seconds": 0, "clip_end_seconds": 30},
          "situation": {"phase": "unclear", "action_family": "other",
            "team_role": "unclear", "pitch_area": "unclear", "outcome": "unclear",
            "human_observation": "", "priority_problem": "",
            "visible_evidence": [], "tags": []},
          "coaching": {"advice_path": "data/video_a/advice/A-0001.txt",
            "objective": "", "practice_design": "", "success_cues": [],
            "reference_author": "", "reference_author_qualification": ""},
          "limitations": []
        }""",
        encoding="utf-8",
    )
    advice_template.write_text("placeholder", encoding="utf-8")
    case_path, advice_path = initialize_case(
        "A-0042", tmp_path, case_template, advice_template
    )
    case = load_case(case_path)
    assert case.case_id == "A-0042"
    assert case.coaching.advice_path.endswith("A-0042.txt")
    assert advice_path.read_text(encoding="utf-8") == "placeholder"
