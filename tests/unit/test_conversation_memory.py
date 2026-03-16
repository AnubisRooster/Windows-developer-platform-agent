"""Unit tests for backend ConversationMemory."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    yield
    db._engine = None
    db._SessionLocal = None


@pytest.fixture
def memory():
    from backend.agent.memory import ConversationMemory
    from backend.database.models import init_db
    init_db()
    return ConversationMemory()


class TestConversationMemory:
    def test_add_and_get_messages(self, memory):
        memory.add_message("c1", "user", "Hello")
        memory.add_message("c1", "assistant", "Hi there")
        msgs = memory.get_messages("c1")
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello"
        assert msgs[1]["role"] == "assistant"

    def test_messages_isolated_by_conversation(self, memory):
        memory.add_message("c1", "user", "Message for c1")
        memory.add_message("c2", "user", "Message for c2")
        assert len(memory.get_messages("c1")) == 1
        assert len(memory.get_messages("c2")) == 1

    def test_get_messages_for_llm(self, memory):
        memory.add_message("c1", "user", "Hi")
        memory.add_message("c1", "assistant", "Hello")
        llm_msgs = memory.get_messages_for_llm("c1")
        assert llm_msgs == [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]

    def test_get_messages_limit(self, memory):
        for i in range(10):
            memory.add_message("c1", "user", f"msg {i}")
        msgs = memory.get_messages("c1", limit=3)
        assert len(msgs) == 3

    def test_empty_conversation(self, memory):
        assert memory.get_messages("nonexistent") == []
        assert memory.get_messages_for_llm("nonexistent") == []
