"""Unit tests for the backend Orchestrator (IronClaw + tool registry)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    yield
    db._engine = None
    db._SessionLocal = None


@pytest.fixture
def registry():
    from backend.tools.registry import ToolRegistry, ToolSchema
    reg = ToolRegistry()
    reg.register(
        "echo",
        lambda text: f"Echo: {text}",
        ToolSchema("echo", "Echo text back", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
    )
    reg.register(
        "add",
        lambda a, b: a + b,
        ToolSchema("add", "Add two numbers", {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}),
    )
    return reg


@pytest.fixture
def ironclaw_mock():
    mock = AsyncMock()
    mock.interpret.return_value = {"content": "Hello!", "tool_calls": []}
    mock.health.return_value = {"status": "ok"}
    return mock


@pytest.fixture
def orchestrator(ironclaw_mock, registry):
    from backend.agent.orchestrator import Orchestrator
    from backend.database.models import init_db
    init_db()
    return Orchestrator(ironclaw_client=ironclaw_mock, tool_registry=registry)


class TestOrchestratorHandleMessage:
    @pytest.mark.asyncio
    async def test_simple_message_no_tools(self, orchestrator, ironclaw_mock):
        ironclaw_mock.interpret.return_value = {"content": "I can help with that.", "tool_calls": []}
        result = await orchestrator.handle_message("Hello", "conv-1")
        assert "I can help" in result

    @pytest.mark.asyncio
    async def test_message_with_tool_call(self, orchestrator, ironclaw_mock):
        ironclaw_mock.interpret.return_value = {
            "content": "Let me echo that.",
            "tool_calls": [
                {"function": {"name": "echo", "arguments": '{"text": "hello world"}'}}
            ],
        }
        result = await orchestrator.handle_message("Echo hello world", "conv-2")
        assert "Echo: hello world" in result

    @pytest.mark.asyncio
    async def test_unknown_tool_reports_error(self, orchestrator, ironclaw_mock):
        ironclaw_mock.interpret.return_value = {
            "content": "",
            "tool_calls": [
                {"function": {"name": "nonexistent_tool", "arguments": "{}"}}
            ],
        }
        result = await orchestrator.handle_message("Do something", "conv-3")
        assert "error" in result.lower() or "Unknown" in result

    @pytest.mark.asyncio
    async def test_tool_output_persisted(self, orchestrator, ironclaw_mock):
        from backend.database.models import ToolOutput, get_session
        ironclaw_mock.interpret.return_value = {
            "content": "",
            "tool_calls": [
                {"function": {"name": "add", "arguments": '{"a": 3, "b": 4}'}}
            ],
        }
        await orchestrator.handle_message("Add 3 and 4", "conv-4")
        Session = get_session()
        with Session() as session:
            outputs = session.query(ToolOutput).filter(ToolOutput.conversation_id == "conv-4").all()
            assert len(outputs) == 1
            assert outputs[0].tool_name == "add"


class TestOrchestratorExecuteTool:
    @pytest.mark.asyncio
    async def test_sync_handler(self, orchestrator):
        result = await orchestrator.execute_tool("echo", {"text": "test"})
        assert result == "Echo: test"

    @pytest.mark.asyncio
    async def test_async_handler(self, orchestrator):
        async def async_tool(msg="hi"):
            return f"async: {msg}"

        from backend.tools.registry import ToolSchema
        orchestrator.tools.register("async_tool", async_tool, ToolSchema("async_tool", "Async tool"))
        result = await orchestrator.execute_tool("async_tool", {"msg": "world"})
        assert result == "async: world"

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self, orchestrator):
        with pytest.raises(ValueError, match="Unknown tool"):
            await orchestrator.execute_tool("nope", {})


class TestOrchestratorMemory:
    @pytest.mark.asyncio
    async def test_messages_persisted_to_memory(self, orchestrator, ironclaw_mock):
        ironclaw_mock.interpret.return_value = {"content": "Reply", "tool_calls": []}
        await orchestrator.handle_message("First message", "mem-1")
        await orchestrator.handle_message("Second message", "mem-1")
        messages = orchestrator.memory.get_messages("mem-1")
        assert len(messages) == 4  # user, assistant, user, assistant
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
