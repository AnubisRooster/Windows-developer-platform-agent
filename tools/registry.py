"""
Tool registry for backend use - ToolSchema, ToolEntry, register, get_handler, get_all_schemas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolSchema:
    """Schema descriptor for a tool (name, description, parameters)."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolEntry:
    """Registered tool with schema and handler."""

    schema: ToolSchema
    handler: Callable[..., Any]


class ToolRegistry:
    """Backend tool registry with schemas."""

    def __init__(self) -> None:
        self._entries: dict[str, ToolEntry] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> None:
        """Register a tool with schema."""
        schema = ToolSchema(name=name, description=description, parameters=parameters or {})
        self._entries[name] = ToolEntry(schema=schema, handler=handler)

    def get_handler(self, name: str) -> Callable[..., Any] | None:
        """Get handler for tool by name."""
        entry = self._entries.get(name)
        return entry.handler if entry else None

    def get_all_schemas(self) -> list[ToolSchema]:
        """Return all registered tool schemas."""
        return [e.schema for e in self._entries.values()]
