"""
Async event bus with wildcard topics and optional persistence.

Subscribers can use wildcards (e.g. github.*, *.opened).
"""

from __future__ import annotations

import fnmatch
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventBus:
    """Async event bus with wildcard subscription support."""

    def __init__(self, persist: bool = False) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._persist = persist
        self._persist_fn: Callable[[dict[str, Any]], Awaitable[None]] | None = None

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """
        Subscribe to a topic. Supports wildcards:
        - github.* matches github.pr_opened, github.issue_created, etc.
        - *.opened matches github.pr_opened, jira.ticket_opened, etc.
        """
        self._handlers[topic].append(handler)
        logger.debug("Subscribed handler to topic: %s", topic)

    def set_persister(self, fn: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        """Set function to persist events (e.g. to PostgreSQL)."""
        self._persist_fn = fn

    def _match_topic(self, event_topic: str, pattern: str) -> bool:
        """Check if event_topic matches pattern (supports * wildcard)."""
        return fnmatch.fnmatch(event_topic, pattern)

    async def publish(self, event: dict[str, Any]) -> None:
        """
        Publish an event. Event must have 'source' and 'event_type' keys.
        Topic is constructed as {source}.{event_type}.
        """
        source = event.get("source", "internal")
        event_type = event.get("event_type", "unknown")
        if hasattr(source, "value"):
            source = source.value
        topic = f"{source}.{event_type}"

        if self._persist and self._persist_fn:
            try:
                await self._persist_fn(event)
            except Exception as e:
                logger.exception("Failed to persist event: %s", e)

        matched = 0
        for pattern, handlers in list(self._handlers.items()):
            if self._match_topic(topic, pattern):
                for handler in handlers:
                    try:
                        await handler(event)
                        matched += 1
                    except Exception as e:
                        logger.exception("Event handler failed for %s: %s", pattern, e)

        logger.debug("Published event %s, %d handlers invoked", topic, matched)
