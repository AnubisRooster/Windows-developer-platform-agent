"""Event types for the backend event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventSource(str, Enum):
    """Source of an event."""

    GITHUB = "github"
    JIRA = "jira"
    JENKINS = "jenkins"
    SLACK = "slack"
    INTERNAL = "internal"


@dataclass
class AgentEvent:
    """Event payload for the event bus."""

    source: EventSource | str
    event_type: str
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
