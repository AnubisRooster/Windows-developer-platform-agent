"""
IronClawClient - HTTP client for IronClaw Rust reasoning engine.

IronClaw runs as a separate service and provides:
  - /interpret: message interpretation with tool-calling
  - /plan: task planning (decompose a goal into steps with tool selections)
  - /select-tools: choose optimal tools for a given task from available capabilities
  - /summarize: text summarization

Falls back to OpenRouter LLM API when IronClaw is unavailable.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class IronClawClient:
    """
    HTTP client for IronClaw runtime gateway.

    Env: IRONCLAW_URL, OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL.
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
        return httpx.AsyncClient(timeout=self.timeout)

    # -------------------------------------------------------------------
    # Health
    # -------------------------------------------------------------------

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{self.ironclaw_url}/api/health")
                resp.raise_for_status()
                return resp.json() if resp.content else {"status": "ok"}
            except httpx.RequestError as e:
                logger.debug("IronClaw health check failed: %s", e)
                return {}

    # -------------------------------------------------------------------
    # IronClaw native endpoints
    # -------------------------------------------------------------------

    async def _ironclaw_post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """POST to an IronClaw endpoint. Returns None on failure."""
        async with await self._client() as client:
            try:
                resp = await client.post(f"{self.ironclaw_url}{path}", json=payload)
                resp.raise_for_status()
                return resp.json()
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.debug("IronClaw %s failed: %s", path, e)
                return None

    # -------------------------------------------------------------------
    # OpenRouter fallback
    # -------------------------------------------------------------------

    async def _openrouter_chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
    ) -> dict[str, Any]:
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

    def _extract_chat_response(self, data: dict[str, Any]) -> dict[str, Any]:
        choices = data.get("choices", [])
        if not choices:
            return {"content": "", "tool_calls": [], "raw": data}
        msg = choices[0].get("message", {})
        return {
            "content": msg.get("content", ""),
            "tool_calls": msg.get("tool_calls", []),
            "raw": data,
        }

    # -------------------------------------------------------------------
    # Core: Interpret (message → response + tool calls)
    # -------------------------------------------------------------------

    async def interpret(self, message: str, tools: list[dict] | None = None) -> dict[str, Any]:
        """
        Interpret user message. Returns:
          - content: str (assistant text)
          - tool_calls: list (tool invocations to execute)
          - raw: full response
        """
        payload: dict[str, Any] = {"message": message}
        if tools:
            payload["tools"] = tools
        result = await self._ironclaw_post("/interpret", payload)
        if result is not None:
            return result

        self._use_openrouter = True
        messages = [
            {"role": "system", "content": "You are a helpful developer platform assistant."},
            {"role": "user", "content": message},
        ]
        data = await self._openrouter_chat(messages, tools)
        return self._extract_chat_response(data)

    # -------------------------------------------------------------------
    # Task Planning
    # -------------------------------------------------------------------

    async def plan(
        self,
        goal: str,
        tools: list[dict] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Decompose a goal into an ordered list of steps with tool selections.

        Returns:
          - steps: list of { description, tool, args_template }
          - reasoning: str
        """
        payload = {"goal": goal}
        if tools:
            payload["tools"] = tools
        if context:
            payload["context"] = context
        result = await self._ironclaw_post("/plan", payload)
        if result is not None:
            return result

        self._use_openrouter = True
        tool_descriptions = ""
        if tools:
            tool_descriptions = "\n".join(
                f"- {t['name']}: {t.get('description', '')}" for t in tools
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task planner for a developer platform. "
                    "Given a goal and available tools, produce a plan as a JSON object with:\n"
                    '  "reasoning": brief explanation\n'
                    '  "steps": [{  "description": ..., "tool": tool_name, "args_template": {...} }]\n'
                    "Respond ONLY with valid JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Goal: {goal}\n\n"
                    f"Available tools:\n{tool_descriptions}\n\n"
                    f"Context: {json.dumps(context or {}, default=str)}"
                ),
            },
        ]
        data = await self._openrouter_chat(messages)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"reasoning": content, "steps": []}

    # -------------------------------------------------------------------
    # Tool Selection
    # -------------------------------------------------------------------

    async def select_tools(
        self,
        task: str,
        tools: list[dict],
    ) -> list[dict[str, Any]]:
        """
        Given a task description and available tools, select the best tools to use.

        Returns list of { name, reason, args_hint }.
        """
        payload = {"task": task, "tools": tools}
        result = await self._ironclaw_post("/select-tools", payload)
        if result is not None:
            return result if isinstance(result, list) else result.get("selected", [])

        self._use_openrouter = True
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t.get('description', '')}" for t in tools
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You select tools for developer platform tasks. "
                    "Return a JSON array of objects: "
                    '[{ "name": tool_name, "reason": why, "args_hint": {} }]. '
                    "Respond ONLY with valid JSON."
                ),
            },
            {"role": "user", "content": f"Task: {task}\n\nTools:\n{tool_descriptions}"},
        ]
        data = await self._openrouter_chat(messages)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    # -------------------------------------------------------------------
    # Summarization
    # -------------------------------------------------------------------

    async def summarize(self, text: str, max_sentences: int = 3) -> str:
        """Summarize text. Uses IronClaw or OpenRouter."""
        result = await self._ironclaw_post(
            "/summarize",
            {"text": text, "max_sentences": max_sentences},
        )
        if result and result.get("summary"):
            return result["summary"]
        if result and result.get("content"):
            return result["content"]

        self._use_openrouter = True
        messages = [
            {"role": "system", "content": f"Summarize text in at most {max_sentences} sentences. Be concise."},
            {"role": "user", "content": text},
        ]
        data = await self._openrouter_chat(messages)
        choices = data.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""

    # -------------------------------------------------------------------
    # Test & Switch
    # -------------------------------------------------------------------

    async def test_model(self) -> dict[str, Any]:
        health = await self.health()
        if health:
            return {"provider": "ironclaw", "status": "ok", "details": health}
        if self.openrouter_api_key:
            try:
                await self._openrouter_chat([{"role": "user", "content": "Say 'ok'"}])
                return {"provider": "openrouter", "status": "ok", "model": self.openrouter_model}
            except Exception as e:
                return {"provider": "openrouter", "status": "error", "error": str(e)}
        return {"provider": "none", "status": "error", "error": "No IronClaw and no OpenRouter API key"}

    async def switch_model(self, provider: str, model: str) -> None:
        if provider.lower() == "openrouter":
            self.openrouter_model = model
            self._use_openrouter = True
        logger.info("Switched model: provider=%s, model=%s", provider, model)
