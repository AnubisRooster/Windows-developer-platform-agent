"""
ConversationMemory - Backend conversation persistence via SQLAlchemy.

Stores conversation messages in AgentConversation model.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.database.models import AgentConversation, get_session

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Persists and retrieves conversation messages from the database."""

    def __init__(self) -> None:
        self._session_factory = get_session()

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """Persist a conversation message."""
        Session = self._session_factory
        with Session() as session:
            msg = AgentConversation(
                conversation_id=conversation_id,
                role=role,
                content=content,
            )
            session.add(msg)
            session.commit()
        logger.debug("Added message to conversation %s", conversation_id)

    def get_messages(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieve recent messages for a conversation."""
        Session = self._session_factory
        with Session() as session:
            rows = (
                session.query(AgentConversation)
                .filter(AgentConversation.conversation_id == conversation_id)
                .order_by(AgentConversation.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {"role": r.role, "content": r.content, "timestamp": r.timestamp}
                for r in reversed(rows)
            ]

    def get_messages_for_llm(
        self,
        conversation_id: str,
        limit: int = 20,
    ) -> list[dict[str, str]]:
        """Get messages in format suitable for LLM chat API."""
        msgs = self.get_messages(conversation_id, limit=limit)
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
