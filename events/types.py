"""
Event types for the developer platform.
Platform-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class EventSource(str, Enum):
    """Source of an event."""

    github = "github"
    slack = "slack"
    jira = "jira"
    jenkins = "jenkins"
    gmail = "gmail"
    confluence = "confluence"
    system = "system"
    agent = "agent"


@dataclass
class AgentEvent:
    """Event propagated through the event bus."""

    id: str
    source: EventSource
    event_type: str
    payload: dict[str, Any]
    timestamp: datetime | None = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(UTC)
