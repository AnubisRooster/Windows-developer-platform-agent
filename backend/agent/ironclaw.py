"""
IronClawClient - HTTP client for IronClaw runtime (Rust AI engine) with OpenRouter fallback.

Uses httpx async client. Gracefully falls back to OpenRouter when IronClaw is unavailable.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class IronClawClient:
    """
    HTTP client for IronClaw runtime gateway, with OpenRouter fallback.

    Env vars: IRONCLAW_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL.
    """

    def __init__(
        self,
        ironclaw_url: str | None = None,
        openrouter_api_key: str | None = None,
        openrouter_model: str | None = None,
        openrouter_base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.ironclaw_url = (ironclaw_url or os.environ.get("IRONCLAW_URL", "http://127.0.0.1:3000")).rstrip("/")
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.openrouter_model = openrouter_model or os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4")
        self.openrouter_base_url = (
            openrouter_base_url or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ).rstrip("/")
        self.timeout = timeout
        self._use_openrouter = False

    async def _client(self) -> httpx.AsyncClient:
        """Get httpx async client."""
        return httpx.AsyncClient(timeout=self.timeout)

    async def health(self) -> dict[str, Any]:
        """Check IronClaw health. Returns status dict or empty on failure."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self.ironclaw_url}/api/health")
                resp.raise_for_status()
                return resp.json() if resp.content else {"status": "ok"}
            except httpx.RequestError as e:
                logger.debug("IronClaw health check failed: %s", e)
                return {}

    async def _try_ironclaw_interpret(self, message: str, tools: list[dict] | None = None) -> dict[str, Any] | None:
        """Try IronClaw interpret endpoint. Returns None on failure."""
        async with await self._client() as client:
            try:
                payload: dict[str, Any] = {"message": message}
                if tools:
                    payload["tools"] = tools
                resp = await client.post(f"{self.ironclaw_url}/interpret", json=payload)
                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.debug("IronClaw interpret failed: %s", e)
                return None

    async def _openrouter_chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Call OpenRouter chat completions API."""
        async with await self._client() as client:
            headers = {"Content-Type": "application/json"}
            if self.openrouter_api_key:
                headers["Authorization"] = f"Bearer {self.openrouter_api_key}"
            payload: dict[str, Any] = {
                "model": self.openrouter_model,
                "messages": messages,
            }
            if tools:
                payload["tools"] = [{"type": "function", "function": t} for t in tools]
                payload["tool_choice"] = "auto"
            resp = await client.post(
                f"{self.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def interpret(self, message: str, tools: list[dict] | None = None) -> dict[str, Any]:
        """
        Interpret user message. Returns dict with:
        - content: str (assistant text)
        - tool_calls: list (optional)
        - raw: full API response
        """
        result = await self._try_ironclaw_interpret(message, tools)
        if result is not None:
            return result

        self._use_openrouter = True
        messages = [
            {"role": "system", "content": "You are a helpful developer platform assistant."},
            {"role": "user", "content": message},
        ]
        data = await self._openrouter_chat(messages, tools)
        choices = data.get("choices", [])
        if not choices:
            return {"content": "", "tool_calls": [], "raw": data}
        msg = choices[0].get("message", {})
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls", [])
        return {"content": content, "tool_calls": tool_calls, "raw": data}

    async def summarize(self, text: str) -> str:
        """Summarize text. Uses IronClaw or OpenRouter."""
        result = await self._try_ironclaw_interpret(
            f"Summarize the following in 2-3 sentences:\n\n{text}",
            tools=None,
        )
        if result and result.get("content"):
            return result["content"]

        messages = [
            {"role": "system", "content": "You summarize text concisely."},
            {"role": "user", "content": text},
        ]
        data = await self._openrouter_chat(messages)
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""

    async def test_model(self) -> dict[str, Any]:
        """Test model connectivity. Returns status dict."""
        health = await self.health()
        if health:
            return {"provider": "ironclaw", "status": "ok", "details": health}
        if self.openrouter_api_key:
            try:
                await self._openrouter_chat([{"role": "user", "content": "Say 'ok'"}])
                return {
                    "provider": "openrouter",
                    "status": "ok",
                    "model": self.openrouter_model,
                }
            except Exception as e:
                return {"provider": "openrouter", "status": "error", "error": str(e)}
        return {"provider": "none", "status": "error", "error": "No IronClaw and no OpenRouter API key"}

    async def switch_model(self, provider: str, model: str) -> None:
        """Switch to different provider/model (for OpenRouter fallback)."""
        if provider.lower() == "openrouter":
            self.openrouter_model = model
            self._use_openrouter = True
        logger.info("Switched model: provider=%s, model=%s", provider, model)
