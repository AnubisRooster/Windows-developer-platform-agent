"""Deployment tests: verify services can start and respond to health checks."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from events.bus import EventBus
from webhooks.server import app, set_event_bus


@pytest.mark.deployment
class TestServiceHealth:
    @pytest.fixture(autouse=True)
    def _setup_bus(self):
        set_event_bus(EventBus())
        yield
        set_event_bus(None)

    def test_webhook_server_health(self):
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_webhook_server_accepts_post(self):
        client = TestClient(app)
        resp = client.post("/webhooks/github", json={"action": "ping"}, headers={"X-GitHub-Event": "ping"})
        assert resp.status_code == 200

    def test_webhook_server_returns_503_without_bus(self):
        set_event_bus(None)
        client = TestClient(app)
        resp = client.post("/webhooks/github", json={})
        assert resp.status_code == 503

    def test_all_webhook_endpoints_exist(self):
        client = TestClient(app)
        endpoints = ["/webhooks/github", "/webhooks/jira", "/webhooks/jenkins", "/webhooks/slack"]
        for ep in endpoints:
            resp = client.post(ep, json={})
            assert resp.status_code in (200, 503), f"{ep} returned {resp.status_code}"
