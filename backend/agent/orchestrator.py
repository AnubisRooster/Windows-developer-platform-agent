"""
Backend Orchestrator - Coordinates IronClaw/LLM and tools, persists conversations.

Handles messages, parses tool calls, executes tools, stores outputs in database.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.agent.memory import ConversationMemory
from backend.database.models import ToolOutput, get_session

logger = logging.getLogger(__name__)


class Orchestrator:
    """Backend orchestrator with IronClaw client and tool registry."""

    def __init__(
        self,
        ironclaw_client: Any,
        tool_registry: Any,
        memory: ConversationMemory | None = None,
    ) -> None:
        self.ironclaw = ironclaw_client
        self.tools = tool_registry
        self.memory = memory or ConversationMemory()

    def _build_messages(
        self,
        conversation_id: str,
        user_msg: str,
    ) -> list[dict[str, Any]]:
        """Build message list from history + new user message."""
        history = self.memory.get_messages_for_llm(conversation_id)
        messages = [{"role": "system", "content": "You are a helpful developer platform assistant."}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_msg})
        return messages

    async def handle_message(self, user_msg: str, conversation_id: str) -> str:
        """
        Process user message: send to IronClaw, parse tool calls, execute, persist.

        Returns assistant response text.
        """
        self.memory.add_message(conversation_id, "user", user_msg)

        schemas = self.tools.get_all_schemas()
        messages = self._build_messages(conversation_id, user_msg)
        # For interpret, we send the last user message
        last_content = user_msg

        result = await self.ironclaw.interpret(last_content, tools=schemas)

        content = result.get("content", "")
        tool_calls = result.get("tool_calls", [])

        # Execute tool calls in a loop (simplified; real impl may support parallel)
        for tc in tool_calls:
            if isinstance(tc, dict):
                name = tc.get("function", {}).get("name") or tc.get("name")
                args_raw = tc.get("function", {}).get("arguments") or tc.get("arguments", "{}")
            else:
                name = getattr(tc, "name", None) or getattr(tc, "function", {}).get("name")
                args_raw = getattr(tc, "arguments", "{}") or getattr(tc, "function", {}).get("arguments", "{}")
            if name:
                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
                    out = await self.execute_tool(name, args)
                    self._persist_tool_output(name, args, out, conversation_id)
                    content += f"\n[Tool {name} result: {out}]"
                except Exception as e:
                    logger.exception("Tool execution failed: %s", e)
                    content += f"\n[Tool {name} error: {str(e)}]"

        self.memory.add_message(conversation_id, "assistant", content)
        return content

    def _persist_tool_output(
        self,
        tool_name: str,
        input_data: dict,
        output_data: Any,
        conversation_id: str,
    ) -> None:
        """Store tool output in database."""
        Session = get_session()
        with Session() as session:
            out = ToolOutput(
                tool_name=tool_name,
                input_data=input_data,
                output_data=output_data if isinstance(output_data, dict) else {"result": output_data},
                conversation_id=conversation_id,
            )
            session.add(out)
            session.commit()

    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Execute a registered tool and return its result."""
        handler = self.tools.get_handler(tool_name)
        if not handler:
            raise ValueError(f"Unknown tool: {tool_name}")

        # Support both sync and async handlers
        import asyncio

        if asyncio.iscoroutinefunction(handler):
            return await handler(**args)
        return handler(**args)
