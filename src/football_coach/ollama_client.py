from __future__ import annotations

import base64
import os
from typing import Any

import httpx

from .prompting import PromptMessage


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ):
        configured_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://127.0.0.1:11434"
        )
        self.base_url = configured_url.rstrip("/")
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.timeout = timeout or float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "900"))

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def tags(self) -> dict[str, Any]:
        with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
            response = client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json()

    def model_metadata(self, model: str) -> dict[str, Any]:
        installed = self.tags().get("models", [])
        for item in installed:
            if item.get("name") == model or item.get("model") == model:
                return item
        raise ValueError(f"Model {model!r} was not returned by Ollama /api/tags")

    def chat(
        self,
        model: str,
        messages: list[PromptMessage],
        schema: dict[str, Any],
        options: dict[str, Any],
        think: bool,
    ) -> dict[str, Any]:
        encoded_messages = []
        for message in messages:
            encoded_messages.append(
                {
                    "role": message.role,
                    "content": message.content,
                    "images": [
                        base64.b64encode(path.read_bytes()).decode("ascii")
                        for path in message.images
                    ],
                }
            )
        payload = {
            "model": model,
            "messages": encoded_messages,
            "format": schema,
            "options": options,
            "think": think,
            "stream": False,
        }
        with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
