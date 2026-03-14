"""
Tool registry for the backend orchestrator.

Registers tools with JSON Schema parameters for IronClaw/LLM tool calling.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


class ToolSchema:
    """JSON Schema for a tool's parameters."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.parameters = parameters or {"type": "object", "properties": {}, "required": []}

    def to_dict(self) -> dict[str, Any]:
        """Convert to OpenAPI/JSON Schema format for tool calls."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolEntry:
    """Registered tool with handler and schema."""

    def __init__(
        self,
        name: str,
        handler: Callable[..., Any],
        schema: ToolSchema,
    ) -> None:
        self.name = name
        self.handler = handler
        self.schema = schema


class ToolRegistry:
    """Registry of tools available to the orchestrator."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}

    def register(self, name: str, handler: Callable[..., Any], schema: ToolSchema) -> None:
        """Register a tool by name."""
        self._tools[name] = ToolEntry(name=name, handler=handler, schema=schema)
        logger.debug("Registered tool: %s", name)

    def get_handler(self, name: str) -> Callable[..., Any] | None:
        """Get handler for a tool by name."""
        entry = self._tools.get(name)
        return entry.handler if entry else None

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """Get all tool schemas for LLM tool declarations."""
        return [e.schema.to_dict() for e in self._tools.values()]

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
