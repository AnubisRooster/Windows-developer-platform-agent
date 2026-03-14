"""
Conversation memory for agent context.
Platform-agnostic; uses in-memory storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """Single message in conversation."""

    role: str
    content: str


class ConversationMemory:
    """Stores conversation history for agent context."""

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self._messages.append(Message(role=role, content=content))

    def get_history(self) -> list[Message]:
        """Return all messages in order."""
        return list(self._messages)

    def get_context(self, limit: int = 10) -> list[Message]:
        """Return the last N messages (most recent context)."""
        return list(self._messages[-limit:]) if limit > 0 else []

    def clear(self) -> None:
        """Reset conversation history."""
        self._messages.clear()

    def get_summary(self) -> str:
        """Return a brief summary of the conversation (e.g., turn count)."""
        if not self._messages:
            return "No messages yet."
        roles = {}
        for m in self._messages:
            roles[m.role] = roles.get(m.role, 0) + 1
        parts = [f"{k}: {v}" for k, v in roles.items()]
        return f"Conversation: {len(self._messages)} messages ({', '.join(parts)})"

    def to_llm_messages(self) -> list[dict[str, str]]:
        """Format messages for LLM API (list of {role, content} dicts)."""
        return [{"role": m.role, "content": m.content} for m in self._messages]
