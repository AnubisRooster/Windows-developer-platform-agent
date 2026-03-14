"""
LLM client supporting OpenRouter, OpenAI, and Ollama.
Platform-agnostic HTTP calls via httpx.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


class LLMClient:
    """Unified LLM client for OpenRouter, OpenAI, and Ollama."""

    def __init__(
        self,
        provider: str = "openrouter",
        api_key: str | None = None,
        model: str = "anthropic/claude-sonnet-4",
        base_url: str = "https://openrouter.ai/api/v1",
        timeout: int = 30,
    ) -> None:
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send chat completion request and return assistant message content."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            **kwargs,
        }
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, headers=self._headers(), json=payload)
            resp.raise_for_status()
            data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")
