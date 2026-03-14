"""Unit tests for ToolRegistry (root agent module)."""

from __future__ import annotations

import pytest

from agent.orchestrator import ToolRegistry


class TestToolRegistry:
    def test_register_and_get(self, tool_registry):
        handler = lambda x: x * 2
        tool_registry.register("double", handler, "Doubles input")
        assert tool_registry.get("double") is handler

    def test_get_unknown_returns_none(self, tool_registry):
        assert tool_registry.get("nonexistent") is None

    def test_list_tools(self, tool_registry):
        tool_registry.register("a", lambda: None, "tool a")
        tool_registry.register("b", lambda: None, "tool b")
        names = tool_registry.list_tools()
        assert "a" in names
        assert "b" in names

    def test_get_descriptions(self, tool_registry):
        tool_registry.register("foo", lambda: None, "Foo tool")
        tool_registry.register("bar", lambda: None)
        descs = tool_registry.get_descriptions()
        assert descs["foo"] == "Foo tool"
        assert "bar" in descs

    def test_register_overwrites(self, tool_registry):
        tool_registry.register("x", lambda: 1, "v1")
        tool_registry.register("x", lambda: 2, "v2")
        assert tool_registry.get("x")() == 2
        assert tool_registry.get_descriptions()["x"] == "v2"

    def test_empty_registry(self, tool_registry):
        assert tool_registry.list_tools() == []
        assert tool_registry.get_descriptions() == {}
