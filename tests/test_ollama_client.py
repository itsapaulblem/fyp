from pathlib import Path
from typing import Any

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
