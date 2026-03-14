"""Unit tests for ConversationMemory."""

from __future__ import annotations

import pytest

from agent.memory import ConversationMemory, Message


class TestMessage:
    def test_message_creation(self):
        msg = Message(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"


class TestConversationMemory:
    def test_empty_on_init(self, memory):
        assert memory.get_history() == []

    def test_add_and_get_history(self, memory):
        memory.add("user", "hello")
        memory.add("assistant", "hi there")
        history = memory.get_history()
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "hello"
        assert history[1].role == "assistant"

    def test_get_context_limit(self, memory):
        for i in range(20):
            memory.add("user", f"message {i}")
        context = memory.get_context(limit=5)
        assert len(context) == 5
        assert context[0].content == "message 15"
        assert context[-1].content == "message 19"

    def test_get_context_zero_limit(self, memory):
        memory.add("user", "hello")
        assert memory.get_context(limit=0) == []

    def test_get_context_exceeds_history(self, memory):
        memory.add("user", "only one")
        context = memory.get_context(limit=100)
        assert len(context) == 1

    def test_clear(self, memory):
        memory.add("user", "hello")
        memory.add("assistant", "hi")
        memory.clear()
        assert memory.get_history() == []

    def test_get_summary_empty(self, memory):
        assert memory.get_summary() == "No messages yet."

    def test_get_summary_with_messages(self, memory):
        memory.add("user", "q1")
        memory.add("assistant", "a1")
        memory.add("user", "q2")
        summary = memory.get_summary()
        assert "3 messages" in summary
        assert "user: 2" in summary
        assert "assistant: 1" in summary

    def test_to_llm_messages(self, memory):
        memory.add("system", "You are helpful.")
        memory.add("user", "What time is it?")
        msgs = memory.to_llm_messages()
        assert isinstance(msgs, list)
        assert len(msgs) == 2
        assert msgs[0] == {"role": "system", "content": "You are helpful."}
        assert msgs[1] == {"role": "user", "content": "What time is it?"}

    def test_history_returns_copy(self, memory):
        memory.add("user", "hello")
        history = memory.get_history()
        history.clear()
        assert len(memory.get_history()) == 1
