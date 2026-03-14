"""Integration tests for Markets, Feeds, and Email integration API endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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


class TestMarketsEndpoint:
    def test_markets_returns_assets(self, client):
        import webhooks.server as srv
        srv._MARKET_CACHE = {}
        srv._MARKET_CACHE_TS = 0.0
        resp = client.get("/api/markets")
        assert resp.status_code == 200
        data = resp.json()
        assert "assets" in data
        assert "updated_at" in data

    def test_markets_has_btc_key(self, client):
        import webhooks.server as srv
        srv._MARKET_CACHE = {}
        srv._MARKET_CACHE_TS = 0.0
        resp = client.get("/api/markets")
        data = resp.json()
        assert "btc" in data["assets"]
        btc = data["assets"]["btc"]
        assert btc["name"] == "Bitcoin"
        assert btc["symbol"] == "BTC"
        assert "price" in btc or "error" in btc

    def test_markets_has_sp500_key(self, client):
        import webhooks.server as srv
        srv._MARKET_CACHE = {}
        srv._MARKET_CACHE_TS = 0.0
        resp = client.get("/api/markets")
        data = resp.json()
        assert "sp500" in data["assets"]
        assert data["assets"]["sp500"]["name"] == "S&P 500"
        assert "price" in data["assets"]["sp500"] or "error" in data["assets"]["sp500"]

    def test_markets_has_silver_key(self, client):
        import webhooks.server as srv
        srv._MARKET_CACHE = {}
        srv._MARKET_CACHE_TS = 0.0
        resp = client.get("/api/markets")
        data = resp.json()
        assert "silver" in data["assets"]
        assert data["assets"]["silver"]["name"] == "Silver Futures"
        assert "price" in data["assets"]["silver"] or "error" in data["assets"]["silver"]

    def test_markets_caching(self, client):
        """Second call within 30s should return cached data."""
        import time
        import webhooks.server as srv
        srv._MARKET_CACHE = {"assets": {"test": True}, "updated_at": "cached"}
        srv._MARKET_CACHE_TS = time.time()
        resp = client.get("/api/markets")
        data = resp.json()
        assert data.get("updated_at") == "cached"
        srv._MARKET_CACHE = {}
        srv._MARKET_CACHE_TS = 0.0


class TestXFeedEndpoint:
    def test_x_feed_not_configured(self, client, monkeypatch):
        monkeypatch.delenv("X_BEARER_TOKEN", raising=False)
        resp = client.get("/api/feeds/x")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is False
        assert "X_BEARER_TOKEN" in data.get("error", "")

    def test_x_feed_with_token_returns_structure(self, client, monkeypatch):
        monkeypatch.setenv("X_BEARER_TOKEN", "test-token")
        resp = client.get("/api/feeds/x")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is True
        assert "posts" in data


class TestLinkedInFeedEndpoint:
    def test_linkedin_feed_not_configured(self, client, monkeypatch):
        monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
        resp = client.get("/api/feeds/linkedin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is False

    def test_linkedin_feed_with_token_returns_structure(self, client, monkeypatch):
        monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-token")
        resp = client.get("/api/feeds/linkedin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is True
        assert "posts" in data


class TestOutlookEndpoint:
    def test_outlook_not_configured(self, client, monkeypatch):
        monkeypatch.delenv("OUTLOOK_ACCESS_TOKEN", raising=False)
        resp = client.get("/api/integrations/outlook/inbox")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is False
        assert "messages" in data

    def test_outlook_with_token_returns_structure(self, client, monkeypatch):
        monkeypatch.setenv("OUTLOOK_ACCESS_TOKEN", "test-token")
        resp = client.get("/api/integrations/outlook/inbox")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is True
        assert "messages" in data


class TestZohoEndpoint:
    def test_zoho_not_configured_missing_both(self, client, monkeypatch):
        monkeypatch.delenv("ZOHO_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ZOHO_ACCOUNT_ID", raising=False)
        resp = client.get("/api/integrations/zoho/inbox")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is False

    def test_zoho_with_token_returns_structure(self, client, monkeypatch):
        monkeypatch.setenv("ZOHO_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("ZOHO_ACCOUNT_ID", "12345")
        resp = client.get("/api/integrations/zoho/inbox")
        assert resp.status_code == 200
        data = resp.json()
        assert data["configured"] is True
        assert "messages" in data


class TestIntegrationsConfigEndpoint:
    def test_returns_all_integrations(self, client):
        resp = client.get("/api/integrations/config")
        assert resp.status_code == 200
        data = resp.json()
        expected_keys = {"outlook", "zoho", "x", "linkedin", "slack", "github", "jira", "jenkins", "confluence", "gmail"}
        assert expected_keys.issubset(set(data.keys()))
        for v in data.values():
            assert "configured" in v

    def test_reflects_env_vars(self, client, monkeypatch):
        monkeypatch.setenv("X_BEARER_TOKEN", "abc")
        monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)
        resp = client.get("/api/integrations/config")
        data = resp.json()
        assert data["x"]["configured"] is True
        assert data["linkedin"]["configured"] is False


class TestStatusIncludesNewIntegrations:
    def test_status_has_new_integration_keys(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        integrations = data.get("integrations", {})
        assert "outlook" in integrations
        assert "zoho_mail" in integrations
        assert "x" in integrations
        assert "linkedin" in integrations
