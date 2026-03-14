"""Integration tests for the Chat API endpoints."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from events.bus import EventBus
from webhooks.server import app, set_event_bus


@pytest.fixture(autouse=True)
def _wire_event_bus():
    bus = EventBus()
    set_event_bus(bus)
    yield
    set_event_bus(None)


@pytest.fixture
def client():
    return TestClient(app)


class TestChatNewSession:
    def test_create_new_session(self, client):
        resp = client.post("/api/chat/new")
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["title"] == "New Chat"

    def test_create_multiple_sessions(self, client):
        r1 = client.post("/api/chat/new").json()
        r2 = client.post("/api/chat/new").json()
        assert r1["session_id"] != r2["session_id"]


class TestChatSessions:
    def test_list_sessions_empty(self, client):
        resp = client.get("/api/chat/sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_sessions_includes_new(self, client):
        created = client.post("/api/chat/new").json()
        sessions = client.get("/api/chat/sessions").json()
        sids = [s["session_id"] for s in sessions]
        assert created["session_id"] in sids


class TestChatMessages:
    def test_get_messages_empty_session(self, client):
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]
        resp = client.get(f"/api/chat/{sid}/messages")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_messages_nonexistent_session(self, client):
        resp = client.get("/api/chat/nonexistent/messages")
        assert resp.status_code == 200
        assert resp.json() == []


class TestChatSend:
    @patch("webhooks.server._llm_chat", new_callable=AsyncMock)
    def test_send_message_returns_reply(self, mock_llm, client):
        mock_llm.return_value = "Hello from the assistant!"
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]

        resp = client.post(
            f"/api/chat/{sid}/send",
            json={"message": "Hello there"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "assistant"
        assert data["content"] == "Hello from the assistant!"

    @patch("webhooks.server._llm_chat", new_callable=AsyncMock)
    def test_send_message_persists_both_messages(self, mock_llm, client):
        mock_llm.return_value = "Reply"
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]

        client.post(f"/api/chat/{sid}/send", json={"message": "Hi"})
        msgs = client.get(f"/api/chat/{sid}/messages").json()
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hi"
        assert msgs[1]["role"] == "assistant"
        assert msgs[1]["content"] == "Reply"

    @patch("webhooks.server._llm_chat", new_callable=AsyncMock)
    def test_send_updates_session_title(self, mock_llm, client):
        mock_llm.return_value = "Sure!"
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]

        client.post(f"/api/chat/{sid}/send", json={"message": "What is TDD?"})
        sessions = client.get("/api/chat/sessions").json()
        match = [s for s in sessions if s["session_id"] == sid]
        assert len(match) == 1
        assert "What is TDD?" in match[0]["title"]

    def test_send_empty_message_returns_400(self, client):
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]
        resp = client.post(f"/api/chat/{sid}/send", json={"message": ""})
        assert resp.status_code == 400

    def test_send_to_nonexistent_session_returns_404(self, client):
        resp = client.post("/api/chat/nonexist/send", json={"message": "hi"})
        assert resp.status_code == 404

    @patch("webhooks.server._llm_chat", new_callable=AsyncMock)
    def test_multiple_messages_build_context(self, mock_llm, client):
        """Each send should include all prior messages in that session's context."""
        call_count = 0

        async def track_calls(messages):
            nonlocal call_count
            call_count += 1
            user_msgs = [m for m in messages if m["role"] == "user"]
            assert len(user_msgs) == call_count
            return f"Reply {call_count}"

        mock_llm.side_effect = track_calls
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]

        client.post(f"/api/chat/{sid}/send", json={"message": "First"})
        client.post(f"/api/chat/{sid}/send", json={"message": "Second"})

        msgs = client.get(f"/api/chat/{sid}/messages").json()
        assert len(msgs) == 4  # 2 user + 2 assistant

    @patch("webhooks.server._llm_chat", new_callable=AsyncMock)
    def test_new_session_has_clean_context(self, mock_llm, client):
        """A new chat session should NOT include messages from a previous session."""
        contexts_seen = []

        async def capture_context(messages):
            contexts_seen.append(messages)
            return "reply"

        mock_llm.side_effect = capture_context

        s1 = client.post("/api/chat/new").json()["session_id"]
        client.post(f"/api/chat/{s1}/send", json={"message": "Session 1 msg"})

        s2 = client.post("/api/chat/new").json()["session_id"]
        client.post(f"/api/chat/{s2}/send", json={"message": "Session 2 msg"})

        # Second call's context should only have system + "Session 2 msg"
        second_context = contexts_seen[1]
        user_msgs = [m["content"] for m in second_context if m["role"] == "user"]
        assert "Session 1 msg" not in user_msgs
        assert "Session 2 msg" in user_msgs


class TestChatDelete:
    def test_delete_session(self, client):
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]
        resp = client.delete(f"/api/chat/{sid}")
        assert resp.status_code == 200
        assert resp.json()["ok"] is True

        sessions = client.get("/api/chat/sessions").json()
        sids = [s["session_id"] for s in sessions]
        assert sid not in sids

    @patch("webhooks.server._llm_chat", new_callable=AsyncMock)
    def test_delete_removes_messages(self, mock_llm, client):
        mock_llm.return_value = "bye"
        created = client.post("/api/chat/new").json()
        sid = created["session_id"]
        client.post(f"/api/chat/{sid}/send", json={"message": "hello"})
        client.delete(f"/api/chat/{sid}")
        msgs = client.get(f"/api/chat/{sid}/messages").json()
        assert msgs == []

    def test_delete_nonexistent_session(self, client):
        resp = client.delete("/api/chat/nonexist")
        assert resp.status_code == 200
