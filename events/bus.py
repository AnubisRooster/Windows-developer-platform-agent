"""
EventBus - async pub/sub with wildcard support and persistence.
"""

from __future__ import annotations

import fnmatch
import logging
from typing import Callable

from events.types import AgentEvent, EventSource

logger = logging.getLogger(__name__)


class EventBus:
    """
    Pub/sub event bus with topic wildcards (e.g. github.*, *.opened).
    Handlers can be sync; persistence is via optional database callback.
    """

    def __init__(
        self,
        persist: Callable[[AgentEvent], None] | None = None,
    ) -> None:
        self._handlers: list[tuple[str, Callable[[AgentEvent], None]]] = []
        self._persist = persist or (lambda _: None)

    def subscribe(self, topic: str, handler: Callable[[AgentEvent], None]) -> None:
        """
        Subscribe to a topic. Supports glob patterns: github.*, *.opened, github.pull_request.*

        Args:
            topic: Topic pattern (e.g. github.pull_request.opened).
            handler: Callable receiving AgentEvent.
        """
        self._handlers.append((topic, handler))

    def publish(self, event: AgentEvent) -> None:
        """
        Publish event to all matching subscribers and persist.

        Args:
            event: The event to publish.
        """
        topic = f"{event.source.value}.{event.event_type}" if isinstance(event.source, EventSource) else f"{event.source}.{event.event_type}"
        self._persist(event)
        for pattern, handler in self._handlers:
            if self._matches(topic, pattern):
                try:
                    handler(event)
                except Exception as e:
                    logger.exception("Event handler failed for %s: %s", pattern, e)

    def _matches(self, topic: str, pattern: str) -> bool:
        """Check if topic matches pattern (supports * wildcard)."""
        return fnmatch.fnmatch(topic, pattern)
