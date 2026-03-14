"""
Slack integration - send_message, read_channel_history, respond_to_command.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_token() -> str:
    return os.environ.get("SLACK_BOT_TOKEN", "")


def _api(method: str, path: str, *, json_data: dict | None = None) -> dict[str, Any]:
    """Call Slack Web API."""
    token = _get_token()
    if not token:
        logger.warning("SLACK_BOT_TOKEN not set")
        return {}
    url = f"https://slack.com/api{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, headers=headers, json=json_data)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("error", "Unknown Slack API error"))
        return data


def send_message(channel: str, text: str, thread_ts: str | None = None) -> dict[str, Any]:
    """Send a message to a channel (optionally in a thread)."""
    payload: dict[str, Any] = {"channel": channel, "text": text}
    if thread_ts:
        payload["thread_ts"] = thread_ts
    return _api("POST", "/chat.postMessage", json_data=payload)


def read_channel_history(channel: str, limit: int = 100, oldest: str | None = None) -> list[dict[str, Any]]:
    """Read recent messages from a channel."""
    params: dict[str, Any] = {"channel": channel, "limit": limit}
    if oldest:
        params["oldest"] = oldest
    data = _api("POST", "/conversations.history", json_data=params)
    return data.get("messages", [])


def respond_to_command(
    response_url: str,
    text: str,
    response_type: str = "in_channel",
) -> None:
    """Respond to a Slack slash command using the response_url."""
    with httpx.Client(timeout=10.0) as client:
        client.post(
            response_url,
            json={"text": text, "response_type": response_type},
        )
