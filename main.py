"""
Main entry point for Windows Developer Platform Agent.
Run: python -m main (or python main.py)
"""

from __future__ import annotations

from agent.orchestrator import LLMClient, Orchestrator, ToolOutput, ToolRegistry
from database.models import persist_tool_output


def _make_persist_callback():
    """Create callback that persists ToolOutput to database."""

    def cb(out: ToolOutput) -> None:
        persist_tool_output(out.tool_name, out.success, out.result, out.error)

    return cb


def main() -> None:
    """Start CLI chat with orchestrator."""
    llm = LLMClient()
    registry = ToolRegistry()
    orch = Orchestrator(llm, registry, persist_tool_output=_make_persist_callback())

    from cli.chat import start_chat

    start_chat(orch)


if __name__ == "__main__":
    main()
