"""Unit tests for the enhanced IronClaw client."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.agent.ironclaw import IronClawClient


@pytest.fixture
def client():
    return IronClawClient(
        ironclaw_url="http://localhost:3000",
        openrouter_api_key="test-key",
        openrouter_model="test-model",
    )


class TestInterpret:
    @pytest.mark.asyncio
    async def test_interpret_falls_back_to_openrouter(self, client):
        mock_response = {
            "choices": [{"message": {"content": "Hello!", "tool_calls": []}}]
        }
        with patch.object(client, "_ironclaw_post", return_value=None):
            with patch.object(client, "_openrouter_chat", return_value=mock_response):
                result = await client.interpret("Hi")
                assert result["content"] == "Hello!"
                assert client._use_openrouter is True

    @pytest.mark.asyncio
    async def test_interpret_uses_ironclaw_when_available(self, client):
        ironclaw_result = {"content": "From IronClaw", "tool_calls": []}
        with patch.object(client, "_ironclaw_post", return_value=ironclaw_result):
            result = await client.interpret("Hi")
            assert result["content"] == "From IronClaw"


class TestPlan:
    @pytest.mark.asyncio
    async def test_plan_ironclaw(self, client):
        plan_result = {
            "reasoning": "Need to check repo",
            "steps": [{"description": "Search repo", "tool": "github.search_repo"}],
        }
        with patch.object(client, "_ironclaw_post", return_value=plan_result):
            result = await client.plan("Find the auth service", tools=[{"name": "github.search_repo"}])
            assert result["reasoning"] == "Need to check repo"
            assert len(result["steps"]) == 1

    @pytest.mark.asyncio
    async def test_plan_openrouter_fallback(self, client):
        plan_json = json.dumps({
            "reasoning": "Fallback plan",
            "steps": [{"description": "step1", "tool": "t1", "args_template": {}}],
        })
        mock_response = {"choices": [{"message": {"content": plan_json}}]}
        with patch.object(client, "_ironclaw_post", return_value=None):
            with patch.object(client, "_openrouter_chat", return_value=mock_response):
                result = await client.plan("Do something")
                assert result["reasoning"] == "Fallback plan"


class TestSelectTools:
    @pytest.mark.asyncio
    async def test_select_tools_ironclaw(self, client):
        selected = [{"name": "slack.send_message", "reason": "Need to notify", "args_hint": {}}]
        with patch.object(client, "_ironclaw_post", return_value=selected):
            result = await client.select_tools("Notify team", [{"name": "slack.send_message"}])
            assert len(result) == 1
            assert result[0]["name"] == "slack.send_message"


class TestSummarize:
    @pytest.mark.asyncio
    async def test_summarize_ironclaw(self, client):
        with patch.object(client, "_ironclaw_post", return_value={"summary": "Short summary"}):
            result = await client.summarize("Long text here...")
            assert result == "Short summary"

    @pytest.mark.asyncio
    async def test_summarize_openrouter_fallback(self, client):
        mock_response = {"choices": [{"message": {"content": "A brief summary."}}]}
        with patch.object(client, "_ironclaw_post", return_value=None):
            with patch.object(client, "_openrouter_chat", return_value=mock_response):
                result = await client.summarize("Long text")
                assert result == "A brief summary."


class TestHealth:
    @pytest.mark.asyncio
    async def test_health_returns_empty_on_failure(self, client):
        result = await client.health()
        assert isinstance(result, dict)
