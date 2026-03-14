"""Unit tests for EventSource and AgentEvent."""

from __future__ import annotations

from datetime import datetime

import pytest

from events.types import AgentEvent, EventSource


class TestEventSource:
    def test_all_sources_exist(self):
        expected = {"github", "slack", "jira", "jenkins", "gmail", "confluence", "system", "agent"}
        actual = {e.value for e in EventSource}
        assert expected == actual

    def test_string_enum(self):
        assert EventSource.github == "github"
        assert isinstance(EventSource.slack, str)


class TestAgentEvent:
    def test_creation(self):
        evt = AgentEvent(id="e1", source=EventSource.github, event_type="push", payload={"ref": "main"})
        assert evt.id == "e1"
        assert evt.source == EventSource.github
        assert evt.event_type == "push"
        assert evt.payload == {"ref": "main"}

    def test_auto_timestamp(self):
        evt = AgentEvent(id="e2", source=EventSource.slack, event_type="message", payload={})
        assert isinstance(evt.timestamp, datetime)

    def test_explicit_timestamp(self):
        ts = datetime(2025, 1, 1, 12, 0, 0)
        evt = AgentEvent(id="e3", source=EventSource.jira, event_type="created", payload={}, timestamp=ts)
        assert evt.timestamp == ts
