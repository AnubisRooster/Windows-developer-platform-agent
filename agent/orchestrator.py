"""
Orchestrator - coordinates LLM and tools for agent workflows.
Supports OpenRouter, OpenAI, and Ollama. Uses pathlib.Path for all file operations (Windows-compatible).
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

logger = logging.getLogger(__name__)

# Regex pattern for parsing TOOL_CALL blocks from LLM responses
TOOL_CALL_PATTERN = re.compile(
    r"TOOL_CALL:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(\{.*?\})",
    re.DOTALL,
)


@dataclass
class ToolOutput:
    """Result of a tool execution."""

    tool_name: str
    success: bool
    result: str | dict[str, Any]
    error: str | None = None


class LLMClient:
    """Unified LLM client for OpenRouter, OpenAI, and Ollama."""

    def __init__(
        self,
        provider: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.provider = (provider or os.environ.get("OPENCLAW_PROVIDER", "openrouter")).lower()
        self.api_key = api_key or os.environ.get("OPENCLAW_API_KEY", "")
        self.model = model or os.environ.get("OPENCLAW_MODEL", "anthropic/claude-sonnet-4")
        self.base_url = (base_url or os.environ.get("OPENCLAW_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Send chat completion request and return assistant message content.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions for function calling.
            **kwargs: Additional payload parameters.

        Returns:
            The assistant's message content as a string.
        """
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            **kwargs,
        }
        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, headers=self._headers(), json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.exception("LLM request failed: %s", e)
            raise

        choices = data.get("choices", [])
        if not choices:
            return ""
        msg = choices[0].get("message", {})
        return msg.get("content", "")


class ToolRegistry:
    """Registry for tool handlers with descriptions."""

    def __init__(self) -> None:
        self._handlers: dict[str, Callable[..., Any]] = {}
        self._descriptions: dict[str, str] = {}

    def register(self, name: str, handler: Callable[..., Any], description: str = "") -> None:
        """Register a tool by name with its handler and optional description."""
        self._handlers[name] = handler
        self._descriptions[name] = description or f"Tool: {name}"

    def get(self, name: str) -> Callable[..., Any] | None:
        """Get the handler for a tool by name."""
        return self._handlers.get(name)

    def list_tools(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._handlers.keys())

    def get_descriptions(self) -> dict[str, str]:
        """Return mapping of tool name to description."""
        return dict(self._descriptions)


class Orchestrator:
    """Coordinates LLM and registered tools, parses tool calls, executes them, returns final response."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        persist_tool_output: Callable[[ToolOutput], None] | None = None,
    ) -> None:
        self.llm = llm_client
        self.tools = tool_registry
        self._persist = persist_tool_output or (lambda _: None)

    def handle_message(self, user_msg: str, context: dict[str, Any] | None = None) -> str:
        """
        Process user message: send to LLM, parse TOOL_CALL blocks, execute tools, return final response.

        Args:
            user_msg: The user's message.
            context: Optional context dict passed to tools.

        Returns:
            Final text response to the user.
        """
        context = context or {}
        messages = [
            {"role": "system", "content": "You are a helpful developer platform assistant. Use TOOL_CALL: tool_name {args} when you need to invoke a tool."},
            {"role": "user", "content": user_msg},
        ]

        max_iterations = 10
        for _ in range(max_iterations):
            response = self.llm.chat(messages)
            matches = list(TOOL_CALL_PATTERN.finditer(response))

            if not matches:
                return response.strip()

            # Execute each tool call
            for match in matches:
                tool_name = match.group(1).strip()
                args_str = match.group(2).strip()
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError as e:
                    logger.warning("Invalid tool args JSON for %s: %s", tool_name, e)
                    args = {}

                handler = self.tools.get(tool_name)
                if not handler:
                    out = ToolOutput(tool_name, False, {}, error=f"Unknown tool: {tool_name}")
                    self._persist(out)
                    messages.append({"role": "assistant", "content": response})
                    messages.append({"role": "user", "content": f"Error: {out.error}"})
                    continue

                try:
                    result = handler(**args) if isinstance(args, dict) else handler(*args)
                    if isinstance(result, dict):
                        result_str = json.dumps(result)
                    else:
                        result_str = str(result)
                    out = ToolOutput(tool_name, True, result_str)
                except Exception as e:
                    logger.exception("Tool %s failed: %s", tool_name, e)
                    out = ToolOutput(tool_name, False, {}, error=str(e))

                self._persist(out)
                messages.append({"role": "assistant", "content": response})
                content = (json.dumps(out.result) if isinstance(out.result, dict) else str(out.result)) if out.success else f"Tool error: {out.error}"
                messages.append({"role": "user", "content": content})

        return "Maximum tool call iterations reached."
