"""Integration tests for FastAPI webhook endpoints."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid

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


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestGitHubWebhook:
    def test_github_webhook_no_signature(self, client, monkeypatch):
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "")
        payload = {"action": "opened", "pull_request": {"title": "test PR"}}
        resp = client.post(
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert resp.status_code == 200

    def test_github_webhook_valid_signature(self, client, monkeypatch):
        secret = "test-secret"
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", secret)
        payload = json.dumps({"action": "opened", "pull_request": {"title": "test"}}).encode()
        sig = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        resp = client.post(
            "/webhooks/github",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": sig,
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 200

    def test_github_webhook_invalid_signature(self, client, monkeypatch):
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "real-secret")
        payload = json.dumps({"action": "opened"}).encode()
        resp = client.post(
            "/webhooks/github",
            content=payload,
            headers={
                "X-GitHub-Event": "push",
                "X-Hub-Signature-256": "sha256=invalid",
                "Content-Type": "application/json",
            },
        )
        assert resp.status_code == 401

    def test_github_webhook_publishes_event(self, client, monkeypatch):
        monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "")
        received = []
        bus = EventBus()
        bus.subscribe("github.*", received.append)
        set_event_bus(bus)
        payload = {"action": "opened", "pull_request": {"title": "test"}}
        client.post(
            "/webhooks/github",
            json=payload,
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert len(received) == 1
        assert received[0].source.value == "github"


class TestJiraWebhook:
    def test_jira_webhook(self, client):
        payload = {"webhookEvent": "jira:issue_created", "issue": {"key": "PROJ-1"}}
        resp = client.post("/webhooks/jira", json=payload)
        assert resp.status_code == 200

    def test_jira_webhook_publishes_event(self, client):
        received = []
        bus = EventBus()
        bus.subscribe("jira.*", received.append)
        set_event_bus(bus)
        payload = {"webhookEvent": "jira:issue_created", "issue": {"key": "PROJ-1"}}
        client.post("/webhooks/jira", json=payload)
        assert len(received) == 1


class TestJenkinsWebhook:
    def test_jenkins_webhook(self, client):
        payload = {"build": {"status": "failed", "number": 42, "url": "http://jenkins/job/1"}}
        resp = client.post("/webhooks/jenkins", json=payload)
        assert resp.status_code == 200

    def test_jenkins_webhook_publishes_event(self, client):
        received = []
        bus = EventBus()
        bus.subscribe("jenkins.*", received.append)
        set_event_bus(bus)
        payload = {"build": {"status": "failed"}}
        client.post("/webhooks/jenkins", json=payload)
        assert len(received) == 1
        assert "failed" in received[0].event_type


class TestSlackWebhook:
    def test_slack_url_verification(self, client):
        payload = {"type": "url_verification", "challenge": "abc123"}
        resp = client.post("/webhooks/slack", json=payload)
        assert resp.status_code == 200

    def test_slack_event_callback(self, client):
        received = []
        bus = EventBus()
        bus.subscribe("slack.*", received.append)
        set_event_bus(bus)
        payload = {"type": "event_callback", "event": {"type": "app_mention", "text": "hello"}}
        resp = client.post("/webhooks/slack", json=payload)
        assert resp.status_code == 200
        assert len(received) == 1


class TestModelConfigAPI:
    def test_get_model_config_returns_providers(self, client):
        resp = client.get("/api/model/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "model" in data
        assert "available_models" in data
        assert "ironclaw" in data["available_models"]
        assert "openrouter" in data["available_models"]
        assert "ollama" in data["available_models"]

    def test_get_model_config_has_ironclaw_models(self, client):
        resp = client.get("/api/model/config")
        data = resp.json()
        ironclaw_models = data["available_models"]["ironclaw"]
        model_ids = [m["id"] for m in ironclaw_models]
        assert "qwen3.5:latest" in model_ids
        assert "granite4:latest" in model_ids
        assert "deepseek-r1:latest" in model_ids

    def test_get_model_config_has_openrouter_models(self, client):
        resp = client.get("/api/model/config")
        data = resp.json()
        or_models = data["available_models"]["openrouter"]
        model_ids = [m["id"] for m in or_models]
        assert "anthropic/claude-sonnet-4" in model_ids
        assert "openai/gpt-4.1" in model_ids

    def test_get_model_config_has_ollama_models(self, client):
        resp = client.get("/api/model/config")
        data = resp.json()
        ollama_models = data["available_models"]["ollama"]
        model_ids = [m["id"] for m in ollama_models]
        assert "qwen3.5:latest" in model_ids
        assert "granite4:latest" in model_ids

    def test_post_model_config_saves_provider_and_model(self, client):
        resp = client.post(
            "/api/model/config",
            json={"provider": "openrouter", "model": "anthropic/claude-sonnet-4"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["provider"] == "openrouter"
        assert data["model"] == "anthropic/claude-sonnet-4"

    def test_post_model_config_saves_api_key_masked(self, client):
        client.post(
            "/api/model/config",
            json={"openrouter_api_key": "sk-or-v1-testkey1234abcd"},
        )
        resp = client.get("/api/model/config")
        data = resp.json()
        assert data["openrouter_api_key_set"] is True
        assert data["openrouter_api_key_masked"] == "sk-o...abcd"
        assert "sk-or-v1-testkey1234abcd" not in json.dumps(data)

    def test_get_model_config_includes_ironclaw_status(self, client):
        resp = client.get("/api/model/config")
        data = resp.json()
        assert "ironclaw_status" in data
        assert "ironclaw_details" in data

    def test_post_model_config_empty_body(self, client):
        resp = client.post("/api/model/config", content=b"")
        assert resp.status_code == 200


class TestEventBusNotConfigured:
    def test_returns_503_without_bus(self, client):
        set_event_bus(None)
        resp = client.post("/webhooks/github", json={})
        assert resp.status_code == 503
