"""
Slack integration using slack_sdk.
Platform-agnostic.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


def _get_client() -> WebClient:
    """Get Slack WebClient from env token."""
    token = os.environ.get("SLACK_BOT_TOKEN", "")
    if not token:
        raise ValueError("SLACK_BOT_TOKEN environment variable is required")
    return WebClient(token=token)


def send_message(
    channel: str,
    text: str,
    thread_ts: str | None = None,
) -> dict[str, Any]:
    """
    Send a message to a Slack channel.

    Args:
        channel: Channel ID or name (e.g. #general).
        text: Message text.
        thread_ts: Optional thread timestamp for replies.

    Returns:
        Dict with ts, channel.
    """
    try:
        client = _get_client()
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if thread_ts:
            payload["thread_ts"] = thread_ts
        resp = client.chat_postMessage(**payload)
        return {"ts": resp["ts"], "channel": resp["channel"]}
    except SlackApiError as e:
        logger.exception("Slack send_message failed: %s", e)
        raise


def read_channel_history(
    channel: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Read recent messages from a Slack channel.

    Args:
        channel: Channel ID or name.
        limit: Max messages to return.

    Returns:
        List of message dicts with user, text, ts.
    """
    try:
        client = _get_client()
        resp = client.conversations_history(channel=channel, limit=limit)
        messages = resp.get("messages", [])
        return [
            {"user": m.get("user"), "text": m.get("text"), "ts": m.get("ts")}
            for m in messages
        ]
    except SlackApiError as e:
        logger.exception("Slack read_channel_history failed: %s", e)
        raise


def respond_to_command(response_url: str, text: str) -> None:
    """
    Respond to a Slack slash command via response_url.

    Args:
        response_url: URL provided in slash command payload.
        text: Response text to post.
    """
    import httpx

    try:
        with httpx.Client() as client:
            resp = client.post(
                response_url,
                json={"text": text},
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
    except Exception as e:
        logger.exception("Slack respond_to_command failed: %s", e)
        raise
