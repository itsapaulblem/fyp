from pathlib import Path
from typing import Any

import pytest

from football_coach.cli import checked_prompt_gpu
from football_coach.ollama_client import OllamaClient
from football_coach.prompting import PromptMessage


def test_chat_requests_plain_text_without_ollama_format_schema(
    monkeypatch: Any, tmp_path: Path
) -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {"message": {"content": "RECOGNITION\n..."}}

    class FakeClient:
        def __init__(self, **_: Any) -> None:
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_: Any) -> None:
            pass

        def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
            captured.update({"url": url, "payload": json})
            return FakeResponse()

    monkeypatch.setattr("football_coach.ollama_client.httpx.Client", FakeClient)
    response = OllamaClient().chat(
        model="qwen3.5:27b",
        messages=[PromptMessage("user", "Analyze")],
        options={"temperature": 0},
        think=False,
    )

    assert response["message"]["content"].startswith("RECOGNITION")
    assert "format" not in captured["payload"]


def test_gpu_status_preloads_then_reads_remote_placement(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, Any]:
            return {"models": [{
                "name": "qwen3.5:27b", "digest": "a" * 64,
                "size": 20, "size_vram": 10, "context_length": 32768,
            }]}

    class FakeClient:
        def __init__(self, **_: Any) -> None:
            pass

        def __enter__(self) -> "FakeClient":
            return self

        def __exit__(self, *_: Any) -> None:
            pass

        def post(self, url: str, json: dict[str, Any]) -> FakeResponse:
            captured["preload_url"] = url
            captured["preload_payload"] = json
            return FakeResponse()

        def get(self, url: str) -> FakeResponse:
            captured["status_url"] = url
            return FakeResponse()

    monkeypatch.setattr("football_coach.ollama_client.httpx.Client", FakeClient)
    status = OllamaClient(base_url="http://127.0.0.1:11435").gpu_status(
        "qwen3.5:27b", {"num_ctx": 32768}
    )
    assert status["size_vram_bytes"] == 10
    assert captured["preload_payload"]["messages"] == []
    assert captured["preload_payload"]["options"] == {"num_ctx": 32768}
    assert captured["status_url"] == "http://127.0.0.1:11435/api/ps"


def test_cpu_only_placement_is_rejected() -> None:
    class CpuOnlyOllama:
        def gpu_status(self, *_: Any, **__: Any) -> dict[str, Any]:
            return {"digest": "a" * 64, "size_vram_bytes": 0}

    with pytest.raises(RuntimeError, match="CPU only"):
        checked_prompt_gpu(
            CpuOnlyOllama(), "qwen3.5:27b", {}, "a" * 64, preload=True
        )
