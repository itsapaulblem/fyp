import json
from pathlib import Path

from football_coach.provenance import write_run


def test_run_writer_keeps_readable_and_raw_outputs(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    raw = {"message": {"content": "exact answer"}, "done": True}
    write_run(run_dir, "exact prompt", raw, {"condition": "B0_frames_only"})
    assert (run_dir / "prompt.txt").read_text(encoding="utf-8") == "exact prompt"
    assert (run_dir / "response.txt").read_text(encoding="utf-8") == "exact answer"
    assert json.loads((run_dir / "raw_api_response.json").read_text())["done"] is True

