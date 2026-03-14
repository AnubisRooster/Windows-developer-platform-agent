"""Unit tests for the Redis-backed Event Bus (in-memory fallback mode)."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _no_redis(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "")


@pytest.fixture
def bus():
    from backend.events.bus import EventBus
    return EventBus(persist=False, redis_url="")


class TestEventBusFallback:
    """Test in-memory fallback when Redis is unavailable."""

    @pytest.mark.asyncio
    async def test_publish_dispatches_to_handler(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("github.push", handler)
        await bus.publish({"source": "github", "type": "push", "payload": {"ref": "main"}})
        assert len(received) == 1
        assert received[0]["source"] == "github"

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe("github.*", handler)
        await bus.publish({"source": "github", "type": "push", "payload": {}})
        await bus.publish({"source": "github", "type": "pr_opened", "payload": {}})
        await bus.publish({"source": "jira", "type": "issue_created", "payload": {}})
        assert len(received) == 2

    @pytest.mark.asyncio
    async def test_multiple_handlers(self, bus):
        results = {"a": 0, "b": 0}

        async def handler_a(event):
            results["a"] += 1

        async def handler_b(event):
            results["b"] += 1

        bus.subscribe("jenkins.build.failed", handler_a)
        bus.subscribe("jenkins.build.failed", handler_b)
        await bus.publish({"source": "jenkins", "type": "build.failed", "payload": {}})
        assert results["a"] == 1
        assert results["b"] == 1

    @pytest.mark.asyncio
    async def test_handler_error_does_not_block_others(self, bus):
        results = []

        async def bad_handler(event):
            raise ValueError("boom")

        async def good_handler(event):
            results.append(event)

        bus.subscribe("test.*", bad_handler)
        bus.subscribe("test.*", good_handler)
        await bus.publish({"source": "test", "type": "event", "payload": {}})
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_persister_called(self, bus):
        persisted = []

        async def persist(event):
            persisted.append(event)

        bus._persist = True
        bus.set_persister(persist)
        await bus.publish({"source": "x", "type": "y", "payload": {}})
        assert len(persisted) == 1

    @pytest.mark.asyncio
    async def test_build_topic(self, bus):
        assert bus._build_topic({"source": "github", "type": "push"}) == "github.push"
        assert bus._build_topic({"source": "jira", "event_type": "issue_created"}) == "jira.issue_created"
