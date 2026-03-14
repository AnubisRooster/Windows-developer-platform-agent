"""Integration tests for the orchestrator → tool → database pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent.orchestrator import LLMClient, Orchestrator, ToolOutput, ToolRegistry
from database.models import ToolOutputModel, get_session, persist_tool_output


@pytest.fixture(autouse=True)
def _use_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")


def _db_persist(output: ToolOutput):
    persist_tool_output(output.tool_name, output.success, output.result, output.error)


class TestOrchestratorDatabasePipeline:
    def test_tool_output_persisted_on_success(self):
        responses = iter([
            'TOOL_CALL: calculator {"expression": "2+2"}',
            "The answer is 4.",
        ])
        llm = MagicMock()
        llm.chat.side_effect = lambda *a, **kw: next(responses)
        registry = ToolRegistry()
        registry.register("calculator", lambda expression: str(eval(expression)), "Calculator")

        orch = Orchestrator(llm, registry, persist_tool_output=_db_persist)
        result = orch.handle_message("What is 2+2?")

        session = get_session()
        try:
            row = session.query(ToolOutputModel).filter_by(tool_name="calculator").first()
            assert row is not None
            assert row.success == 1
            assert "4" in row.result
        finally:
            session.close()

    def test_tool_output_persisted_on_failure(self):
        responses = iter([
            'TOOL_CALL: broken_tool {"x": 1}',
            "Sorry, that failed.",
        ])
        llm = MagicMock()
        llm.chat.side_effect = lambda *a, **kw: next(responses)
        registry = ToolRegistry()

        def broken(**kwargs):
            raise ValueError("Intentional failure")

        registry.register("broken_tool", broken, "A broken tool")

        orch = Orchestrator(llm, registry, persist_tool_output=_db_persist)
        orch.handle_message("Run broken tool")

        session = get_session()
        try:
            row = session.query(ToolOutputModel).filter_by(tool_name="broken_tool").first()
            assert row is not None
            assert row.success == 0
            assert "Intentional failure" in row.error
        finally:
            session.close()

    def test_multiple_tool_calls_all_persisted(self):
        call_count = [0]

        def counter_response(*a, **kw):
            call_count[0] += 1
            if call_count[0] <= 2:
                return f'TOOL_CALL: step_{call_count[0]} {{"n": {call_count[0]}}}'
            return "All done."

        llm = MagicMock()
        llm.chat.side_effect = counter_response
        registry = ToolRegistry()
        registry.register("step_1", lambda **kw: "step 1 done", "Step 1")
        registry.register("step_2", lambda **kw: "step 2 done", "Step 2")

        orch = Orchestrator(llm, registry, persist_tool_output=_db_persist)
        orch.handle_message("Do two steps")

        session = get_session()
        try:
            rows = session.query(ToolOutputModel).all()
            tool_names = [r.tool_name for r in rows]
            assert "step_1" in tool_names
        finally:
            session.close()
