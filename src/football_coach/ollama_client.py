from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import httpx


class OllamaClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.api_key = api_key or os.getenv("OLLAMA_API_KEY")
        self.timeout = timeout or float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "900"))

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    def tags(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
            response = client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json()

    def show(self, model: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
            response = client.post(f"{self.base_url}/api/show", json={"model": model})
            response.raise_for_status()
            return response.json()

    def chat(
        self,
        model: str,
        prompt: str,
        image_paths: list[Path],
        schema: dict[str, Any],
        options: dict[str, Any],
        think: bool = False,
    ) -> dict[str, Any]:
        images = [base64.b64encode(path.read_bytes()).decode("ascii") for path in image_paths]
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt, "images": images}],
            "format": schema,
            "options": options,
            "think": think,
            "stream": False,
        }
        with httpx.Client(timeout=self.timeout, headers=self.headers) as client:
            response = client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()
