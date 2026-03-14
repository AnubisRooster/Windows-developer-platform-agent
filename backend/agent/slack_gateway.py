"""
SlackCommandGateway - Handles Slack app_mention events, routes to orchestrator.

Uses slack_bolt. Sends responses back as threaded replies.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class SlackCommandGateway:
    """Handles Slack app_mention events and routes to orchestrator."""

    def __init__(
        self,
        orchestrator: Any,
        bolt_app: Any | None = None,
    ) -> None:
        self.orchestrator = orchestrator
        self._bolt_app = bolt_app

    def register_handlers(self, app: Any) -> None:
        """
        Register app_mention handler on the Slack Bolt app.

        Expects app to have app.event("app_mention") or similar.
        """
        @app.event("app_mention")
        async def handle_mention(event: dict, say: Any, client: Any, logger: Any) -> None:
            try:
                user = event.get("user", "")
                text = event.get("text", "").strip()
                channel = event.get("channel", "")
                ts = event.get("ts", "")

                # Strip bot mention from text
                if "<@" in text:
                    parts = text.split(">", 1)
                    if len(parts) > 1:
                        text = parts[1].strip()

                if not text:
                    await say("How can I help?", thread_ts=ts)
                    return

                conversation_id = f"slack-{channel}-{ts}"
                response = await self.orchestrator.handle_message(text, conversation_id)
                await say(response, thread_ts=ts)
            except Exception as e:
                logger.exception("Slack mention handler error: %s", e)
                await say(f"Sorry, an error occurred: {str(e)}", thread_ts=event.get("ts", ""))

    async def handle_message(
        self,
        channel: str,
        text: str,
        thread_ts: str | None = None,
    ) -> str:
        """
        Process a message and return the response.
        Used when the gateway is called directly (e.g. from webhook).
        """
        conversation_id = f"slack-{channel}-{thread_ts or 'main'}"
        return await self.orchestrator.handle_message(text, conversation_id)
