"""Unit tests for EventBus."""

from __future__ import annotations

import pytest

from events.bus import EventBus
from events.types import AgentEvent, EventSource


def _make_event(source=EventSource.github, event_type="push", payload=None):
    return AgentEvent(id="test-id", source=source, event_type=event_type, payload=payload or {})


class TestEventBus:
    def test_subscribe_and_publish(self, event_bus):
        received = []
        event_bus.subscribe("github.push", received.append)
        event_bus.publish(_make_event(EventSource.github, "push"))
        assert len(received) == 1
        assert received[0].event_type == "push"

    def test_no_match(self, event_bus):
        received = []
        event_bus.subscribe("slack.message", received.append)
        event_bus.publish(_make_event(EventSource.github, "push"))
        assert len(received) == 0

    def test_wildcard_source(self, event_bus):
        received = []
        event_bus.subscribe("github.*", received.append)
        event_bus.publish(_make_event(EventSource.github, "push"))
        event_bus.publish(_make_event(EventSource.github, "pull_request.opened"))
        assert len(received) == 2

    def test_wildcard_all(self, event_bus):
        received = []
        event_bus.subscribe("*", received.append)
        event_bus.publish(_make_event(EventSource.github, "push"))
        event_bus.publish(_make_event(EventSource.slack, "message"))
        assert len(received) == 2

    def test_multiple_handlers(self, event_bus):
        results_a, results_b = [], []
        event_bus.subscribe("github.push", results_a.append)
        event_bus.subscribe("github.push", results_b.append)
        event_bus.publish(_make_event(EventSource.github, "push"))
        assert len(results_a) == 1
        assert len(results_b) == 1

    def test_handler_exception_does_not_break_others(self, event_bus):
        results = []

        def bad_handler(event):
            raise ValueError("handler broke")

        event_bus.subscribe("github.push", bad_handler)
        event_bus.subscribe("github.push", results.append)
        event_bus.publish(_make_event(EventSource.github, "push"))
        assert len(results) == 1

    def test_persist_callback(self):
        persisted = []
        bus = EventBus(persist=persisted.append)
        bus.publish(_make_event(EventSource.github, "push"))
        assert len(persisted) == 1

    def test_pattern_matching(self, event_bus):
        received = []
        event_bus.subscribe("github.pull_request.*", received.append)
        event_bus.publish(_make_event(EventSource.github, "pull_request.opened"))
        event_bus.publish(_make_event(EventSource.github, "push"))
        assert len(received) == 1
