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

    def gpu_status(
        self, model: str, options: dict[str, Any], *, preload: bool = True
    ) -> dict[str, Any]:
        """Report Ollama's observed GPU residency, optionally loading the model first."""
        with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
            if preload:
                response = client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": [],
                        "options": options,
                        "stream": False,
                        "keep_alive": "10m",
                    },
                )
                response.raise_for_status()
            response = client.get(f"{self.base_url}/api/ps")
            response.raise_for_status()
            running = response.json().get("models", [])
        for item in running:
            if item.get("name") == model or item.get("model") == model:
                vram = item.get("size_vram")
                if not isinstance(vram, int):
                    raise ValueError("Ollama /api/ps did not report size_vram")
                return {
                    "model": model,
                    "digest": item.get("digest"),
                    "size_bytes": item.get("size"),
                    "size_vram_bytes": vram,
                    "context_length": item.get("context_length"),
                }
        raise ValueError(f"Model {model!r} was not loaded according to Ollama /api/ps")

    def chat(
        self,
        model: str,
        messages: list[PromptMessage],
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
            "options": options,
            "think": think,
            "stream": False,
        }
        with httpx.Client(headers=self.headers, timeout=self.timeout) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
