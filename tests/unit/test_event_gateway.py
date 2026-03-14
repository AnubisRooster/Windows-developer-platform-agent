"""Unit tests for the Event Gateway (webhook server)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "")
    monkeypatch.setenv("JIRA_WEBHOOK_SECRET", "")
    monkeypatch.setenv("JENKINS_WEBHOOK_SECRET", "")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    from backend.security import secrets as sec_mod
    sec_mod._SECRETS_CACHE = None
    yield
    db._engine = None
    db._SessionLocal = None
    sec_mod._SECRETS_CACHE = None


@pytest.fixture
def client():
    from backend.database.models import init_db
    from backend.webhooks.server import create_app
    init_db()
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"


class TestGitHubWebhook:
    def test_github_webhook_creates_event(self, client):
        payload = {
            "action": "opened",
            "sender": {"login": "octocat"},
            "pull_request": {"number": 42, "title": "Test PR"},
        }
        resp = client.post(
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["received"] is True
        assert "event_id" in data

    def test_github_event_stored_in_db(self, client):
        from backend.database.models import Event, get_session
        payload = {"action": "closed", "sender": {"login": "dev"}}
        client.post("/webhooks/github", json=payload, headers={"X-GitHub-Event": "issues"})
        Session = get_session()
        with Session() as session:
            events = session.query(Event).filter(Event.source == "github").all()
            assert len(events) >= 1
            assert events[-1].actor == "dev"


class TestSlackWebhook:
    def test_slack_url_verification(self, client):
        resp = client.post("/webhooks/slack", json={"type": "url_verification", "challenge": "abc123"})
        assert resp.status_code == 200
        assert resp.json()["challenge"] == "abc123"

    def test_slack_event(self, client):
        payload = {"type": "event_callback", "event": {"type": "message", "user": "U123"}}
        resp = client.post("/webhooks/slack", json=payload)
        assert resp.status_code == 200
        assert resp.json()["received"] is True


class TestJiraWebhook:
    def test_jira_webhook(self, client):
        payload = {"webhookEvent": "jira:issue_created", "user": {"displayName": "Alice"}}
        resp = client.post("/webhooks/jira", json=payload)
        assert resp.status_code == 200
        assert resp.json()["received"] is True


class TestJenkinsWebhook:
    def test_jenkins_webhook(self, client):
        payload = {"build": {"phase": "COMPLETED", "status": "FAILURE", "parameters": {}}}
        resp = client.post("/webhooks/jenkins", json=payload)
        assert resp.status_code == 200
        assert resp.json()["received"] is True


class TestGmailWebhook:
    def test_gmail_push_notification(self, client):
        payload = {"message": {"data": "user@example.com", "messageId": "123"}}
        resp = client.post("/webhooks/gmail", json=payload)
        assert resp.status_code == 200
        assert resp.json()["received"] is True


class TestDashboardAPI:
    def test_api_events(self, client):
        client.post("/webhooks/github", json={"action": "opened", "sender": {"login": "x"}}, headers={"X-GitHub-Event": "push"})
        resp = client.get("/api/events")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 1

    def test_api_events_filter_by_source(self, client):
        client.post("/webhooks/github", json={"action": "x", "sender": {}}, headers={"X-GitHub-Event": "push"})
        client.post("/webhooks/jira", json={"webhookEvent": "issue_created", "user": {}})
        resp = client.get("/api/events?source=github")
        assert resp.status_code == 200
        for ev in resp.json():
            assert ev["source"] == "github"

    def test_api_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "counts" in data

    def test_api_knowledge_nodes_empty(self, client):
        resp = client.get("/api/knowledge/nodes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_documents_empty(self, client):
        resp = client.get("/api/documents")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_logs(self, client):
        client.post("/webhooks/github", json={"action": "x", "sender": {}}, headers={"X-GitHub-Event": "push"})
        resp = client.get("/api/logs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1
