"""Integration tests for event → workflow execution pipeline."""

from __future__ import annotations

import pytest

from events.bus import EventBus
from events.types import AgentEvent, EventSource
from workflows.engine import WorkflowEngine


class TestEventWorkflowPipeline:
    """Test full flow: event published → workflow engine triggers → tools execute."""

    def test_pr_opened_triggers_workflow(self, tmp_workflow_dir):
        bus = EventBus()
        tool_calls = []

        def mock_tool_resolver(name):
            def handler(**kwargs):
                tool_calls.append(name)
                return f"{name} executed"
            return handler

        engine = WorkflowEngine(
            event_bus=bus,
            workflow_dir=tmp_workflow_dir,
            tool_resolver=mock_tool_resolver,
        )
        engine.subscribe()

        event = AgentEvent(
            id="e1",
            source=EventSource.github,
            event_type="pull_request.opened",
            payload={"title": "Test PR", "number": 42},
        )
        bus.publish(event)

        assert "github.summarize_pull_request" in tool_calls
        assert "slack.send_message" in tool_calls

    def test_build_failed_triggers_workflow(self, tmp_workflow_dir):
        bus = EventBus()
        tool_calls = []

        def mock_tool_resolver(name):
            def handler(**kwargs):
                tool_calls.append(name)
                return f"{name} executed"
            return handler

        engine = WorkflowEngine(
            event_bus=bus,
            workflow_dir=tmp_workflow_dir,
            tool_resolver=mock_tool_resolver,
        )
        engine.subscribe()

        event = AgentEvent(
            id="e2",
            source=EventSource.jenkins,
            event_type="build.failed",
            payload={"build": {"number": 99}},
        )
        bus.publish(event)

        assert "jenkins.fetch_build_logs" in tool_calls
        assert "slack.send_message" in tool_calls

    def test_unmatched_event_does_nothing(self, tmp_workflow_dir):
        bus = EventBus()
        tool_calls = []

        def mock_tool_resolver(name):
            def handler(**kwargs):
                tool_calls.append(name)
            return handler

        engine = WorkflowEngine(event_bus=bus, workflow_dir=tmp_workflow_dir, tool_resolver=mock_tool_resolver)
        engine.subscribe()

        event = AgentEvent(
            id="e3",
            source=EventSource.system,
            event_type="heartbeat",
            payload={},
        )
        bus.publish(event)
        assert tool_calls == []

    def test_workflow_stops_on_failure_when_on_failure_is_stop(self, tmp_path):
        yaml_content = (
            "name: stop_test\n"
            "trigger: system.test\n"
            "enabled: true\n"
            "actions:\n"
            "  - tool: step_one\n"
            "    on_failure: stop\n"
            "  - tool: step_two\n"
        )
        (tmp_path / "stop_test.yaml").write_text(yaml_content, encoding="utf-8")

        bus = EventBus()
        tool_calls = []

        def mock_tool_resolver(name):
            if name == "step_one":
                def handler(**kwargs):
                    raise RuntimeError("step_one failed!")
                return handler
            def handler(**kwargs):
                tool_calls.append(name)
            return handler

        engine = WorkflowEngine(event_bus=bus, workflow_dir=tmp_path, tool_resolver=mock_tool_resolver)
        engine.subscribe()

        event = AgentEvent(id="e4", source=EventSource.system, event_type="test", payload={})
        bus.publish(event)

        assert "step_two" not in tool_calls

    def test_workflow_continues_on_failure_when_on_failure_is_continue(self, tmp_path):
        yaml_content = (
            "name: continue_test\n"
            "trigger: system.test2\n"
            "enabled: true\n"
            "actions:\n"
            "  - tool: step_one\n"
            "    on_failure: continue\n"
            "  - tool: step_two\n"
        )
        (tmp_path / "continue_test.yaml").write_text(yaml_content, encoding="utf-8")

        bus = EventBus()
        tool_calls = []

        def mock_tool_resolver(name):
            if name == "step_one":
                def handler(**kwargs):
                    raise RuntimeError("step_one failed!")
                return handler
            def handler(**kwargs):
                tool_calls.append(name)
            return handler

        engine = WorkflowEngine(event_bus=bus, workflow_dir=tmp_path, tool_resolver=mock_tool_resolver)
        engine.subscribe()

        event = AgentEvent(id="e5", source=EventSource.system, event_type="test2", payload={})
        bus.publish(event)

        assert "step_two" in tool_calls

    def test_persist_callback_fires(self, tmp_workflow_dir):
        persisted_events = []
        bus = EventBus(persist=persisted_events.append)

        def noop_resolver(name):
            return lambda **kw: None

        engine = WorkflowEngine(event_bus=bus, workflow_dir=tmp_workflow_dir, tool_resolver=noop_resolver)
        engine.subscribe()

        event = AgentEvent(
            id="e6",
            source=EventSource.github,
            event_type="pull_request.opened",
            payload={},
        )
        bus.publish(event)

        assert len(persisted_events) == 1
        assert persisted_events[0].id == "e6"
