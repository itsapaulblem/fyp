from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def timestamp_utc() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


def write_run(
    run_dir: Path,
    prompt_text: str,
    raw_response: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    run_dir.mkdir(parents=True, exist_ok=False)
    model_text = str(raw_response.get("message", {}).get("content", ""))
    (run_dir / "prompt.txt").write_text(prompt_text, encoding="utf-8")
    (run_dir / "response.txt").write_text(model_text, encoding="utf-8")
    lines = [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()]
    (run_dir / "metadata.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (run_dir / "raw_api_response.json").write_text(
        json.dumps(raw_response, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
