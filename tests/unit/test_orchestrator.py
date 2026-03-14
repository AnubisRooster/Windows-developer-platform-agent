"""Unit tests for LLMClient, Orchestrator, ToolOutput, TOOL_CALL_PATTERN."""

from __future__ import annotations

import json
import re
from unittest.mock import MagicMock, patch

import pytest

from agent.orchestrator import (
    TOOL_CALL_PATTERN,
    LLMClient,
    Orchestrator,
    ToolOutput,
    ToolRegistry,
)


class TestToolOutput:
    def test_success(self):
        out = ToolOutput(tool_name="test", success=True, result="ok")
        assert out.success
        assert out.error is None

    def test_failure(self):
        out = ToolOutput(tool_name="test", success=False, result={}, error="boom")
        assert not out.success
        assert out.error == "boom"


class TestToolCallPattern:
    def test_matches_simple(self):
        text = 'TOOL_CALL: my_tool {"key": "value"}'
        m = TOOL_CALL_PATTERN.search(text)
        assert m is not None
        assert m.group(1).strip() == "my_tool"
        assert json.loads(m.group(2)) == {"key": "value"}

    def test_matches_multiline_args(self):
        text = 'TOOL_CALL: do_thing {"a": 1,\n"b": 2}'
        m = TOOL_CALL_PATTERN.search(text)
        assert m is not None
        assert json.loads(m.group(2)) == {"a": 1, "b": 2}

    def test_no_match(self):
        text = "Just a regular message."
        assert TOOL_CALL_PATTERN.search(text) is None

    def test_multiple_matches(self):
        text = 'TOOL_CALL: a {"x":1}\nTOOL_CALL: b {"y":2}'
        matches = list(TOOL_CALL_PATTERN.finditer(text))
        assert len(matches) == 2


class TestLLMClient:
    def test_default_config(self, monkeypatch):
        monkeypatch.delenv("OPENCLAW_PROVIDER", raising=False)
        monkeypatch.delenv("OPENCLAW_API_KEY", raising=False)
        client = LLMClient()
        assert client.provider == "openrouter"

    def test_explicit_config(self):
        client = LLMClient(provider="openai", api_key="sk-test", model="gpt-4", base_url="https://api.openai.com/v1")
        assert client.provider == "openai"
        assert client.api_key == "sk-test"
        assert client.model == "gpt-4"

    def test_headers_with_key(self):
        client = LLMClient(api_key="my-key")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer my-key"

    def test_headers_without_key(self):
        client = LLMClient(api_key="")
        headers = client._headers()
        assert "Authorization" not in headers

    @patch("agent.orchestrator.httpx.Client")
    def test_chat_returns_content(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello!"}}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = LLMClient(api_key="test")
        result = client.chat([{"role": "user", "content": "Hi"}])
        assert result == "Hello!"

    @patch("agent.orchestrator.httpx.Client")
    def test_chat_empty_choices(self, mock_client_class):
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": []}
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = LLMClient(api_key="test")
        assert client.chat([{"role": "user", "content": "Hi"}]) == ""


class TestOrchestrator:
    def test_handle_message_no_tool_calls(self):
        llm = MagicMock()
        llm.chat.return_value = "Sure, I can help with that."
        registry = ToolRegistry()
        orch = Orchestrator(llm, registry)
        result = orch.handle_message("Hello")
        assert result == "Sure, I can help with that."

    def test_handle_message_with_tool_call(self):
        responses = iter([
            'TOOL_CALL: greet {"name": "World"}',
            "Done! Greeted World.",
        ])
        llm = MagicMock()
        llm.chat.side_effect = lambda *a, **kw: next(responses)
        registry = ToolRegistry()
        registry.register("greet", lambda name: f"Hello, {name}!", "Greet someone")
        orch = Orchestrator(llm, registry)
        result = orch.handle_message("Greet World")
        assert "Done" in result or "Hello" in result

    def test_handle_message_unknown_tool(self):
        responses = iter([
            'TOOL_CALL: unknown_tool {"a":1}',
            "Sorry, that tool doesn't exist.",
        ])
        llm = MagicMock()
        llm.chat.side_effect = lambda *a, **kw: next(responses)
        registry = ToolRegistry()
        orch = Orchestrator(llm, registry)
        result = orch.handle_message("Use unknown tool")
        assert "Sorry" in result or "exist" in result or "error" in result.lower()

    def test_handle_message_tool_error(self):
        def failing_tool(**kwargs):
            raise ValueError("Tool broke!")

        responses = iter([
            'TOOL_CALL: broken {"x":1}',
            "Tool had an error.",
        ])
        llm = MagicMock()
        llm.chat.side_effect = lambda *a, **kw: next(responses)
        registry = ToolRegistry()
        registry.register("broken", failing_tool, "A broken tool")
        persisted = []
        orch = Orchestrator(llm, registry, persist_tool_output=persisted.append)
        result = orch.handle_message("Run broken tool")
        assert any(not o.success for o in persisted)

    def test_handle_message_max_iterations(self):
        llm = MagicMock()
        llm.chat.return_value = 'TOOL_CALL: loop {"x":1}'
        registry = ToolRegistry()
        registry.register("loop", lambda **kw: "looping", "infinite loop tool")
        orch = Orchestrator(llm, registry)
        result = orch.handle_message("Loop forever")
        assert result == "Maximum tool call iterations reached."

    def test_persist_callback(self):
        responses = iter([
            'TOOL_CALL: echo {"msg": "hi"}',
            "Echoed.",
        ])
        llm = MagicMock()
        llm.chat.side_effect = lambda *a, **kw: next(responses)
        registry = ToolRegistry()
        registry.register("echo", lambda msg: msg, "Echo tool")
        persisted = []
        orch = Orchestrator(llm, registry, persist_tool_output=persisted.append)
        orch.handle_message("Echo hi")
        assert len(persisted) >= 1
        assert persisted[0].tool_name == "echo"
        assert persisted[0].success
