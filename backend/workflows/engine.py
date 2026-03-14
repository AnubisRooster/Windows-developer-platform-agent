"""
WorkflowEngine - Loads workflows from YAML, subscribes to EventBus triggers, executes tool sequences.

Records WorkflowRun in database.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.models import WorkflowRun, get_session
from backend.events.bus import EventBus
from backend.workflows.loader import WorkflowDefinition, load_all_workflows

logger = logging.getLogger(__name__)


def _get_nested(d: dict, path: str) -> Any:
    """Get nested dict key, e.g. pull_request.title."""
    for part in path.split("."):
        d = d.get(part, {}) if isinstance(d, dict) else None
        if d is None:
            return None
    return d


def _render_template(text: str, context: dict[str, Any]) -> str:
    """Replace {{ key }} or {{ key.nested }} with context value."""
    def repl(m: re.Match) -> str:
        key = m.group(1).strip()
        val = context.get(key)
        if val is None and "." in key:
            val = _get_nested(context, key)
        return str(val if val is not None else m.group(0))
    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", repl, text)


def _resolve_args(args: dict[str, Any] | None, context: dict[str, Any]) -> dict[str, Any]:
    """Resolve template vars in args."""
    if not args:
        return {}
    out = {}
    for k, v in args.items():
        if isinstance(v, str):
            out[k] = _render_template(v, context)
        elif isinstance(v, dict):
            out[k] = _resolve_args(v, context)
        else:
            out[k] = v
    return out


class WorkflowEngine:
    """Executes workflows triggered by events."""

    def __init__(
        self,
        event_bus: EventBus,
        workflows_dir: Path,
        tool_executor: Any,
    ) -> None:
        self.event_bus = event_bus
        self.workflows_dir = Path(workflows_dir)
        self.tool_executor = tool_executor
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._loaded = False

    def load_workflows(self) -> None:
        """Load workflows from directory."""
        self._workflows = load_all_workflows(self.workflows_dir)
        self._loaded = True
        logger.info("Loaded %d workflows", len(self._workflows))

    def subscribe_to_triggers(self) -> None:
        """Subscribe to event bus for workflow triggers."""
        if not self._loaded:
            self.load_workflows()

        for wf in self._workflows.values():
            trigger = wf.trigger
            if trigger:
                self.event_bus.subscribe(trigger, self._make_handler(wf))

    def _make_handler(self, wf: WorkflowDefinition):
        async def handler(event: dict[str, Any]) -> None:
            await self.run_workflow(wf.name, event)

        return handler

    async def run_workflow(
        self,
        workflow_name: str,
        event: dict[str, Any],
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a workflow by name. Records WorkflowRun in database.
        """
        wf = self._workflows.get(workflow_name)
        if not wf:
            return {"status": "error", "error": f"Workflow {workflow_name} not found"}

        context = event.get("payload", event)
        trigger_event_id = event.get("id")
        Session = get_session()

        with Session() as session:
            wr = WorkflowRun(
                workflow_name=workflow_name,
                trigger_event_id=trigger_event_id,
                status="running",
            )
            session.add(wr)
            session.commit()
            run_id = wr.id

        result: list[Any] = []
        try:
            for action in wf.actions:
                tool = action.tool
                args = _resolve_args(action.args, context)
                if dry_run:
                    result.append({"tool": tool, "args": args, "dry_run": True})
                    continue
                try:
                    out = await self._execute_tool(tool, args, context)
                    result.append({"tool": tool, "output": out})
                except Exception as e:
                    logger.exception("Workflow %s action %s failed: %s", workflow_name, tool, e)
                    if action.on_failure == "continue":
                        result.append({"tool": tool, "error": str(e)})
                    else:
                        with Session() as session:
                            wr = session.get(WorkflowRun, run_id)
                            if wr:
                                wr.status = "failed"
                                wr.finished_at = datetime.utcnow()
                                wr.result = {"error": str(e), "results": result}
                                session.commit()
                        return {"status": "failed", "error": str(e), "results": result}

            with Session() as session:
                wr = session.get(WorkflowRun, run_id)
                if wr:
                    wr.status = "success"
                    wr.finished_at = datetime.utcnow()
                    wr.result = {"results": result}
                    session.commit()
            return {"status": "success", "results": result}
        except Exception as e:
            logger.exception("Workflow %s failed: %s", workflow_name, e)
            with Session() as session:
                wr = session.get(WorkflowRun, run_id)
                if wr:
                    wr.status = "failed"
                    wr.finished_at = datetime.utcnow()
                    wr.result = {"error": str(e)}
                    session.commit()
            return {"status": "error", "error": str(e)}

    async def _execute_tool(self, tool: str, args: dict, context: dict) -> Any:
        """Execute a tool (e.g. github.summarize_pr). May delegate to ToolRegistry."""
        if hasattr(self.tool_executor, "execute_tool"):
            return await self.tool_executor.execute_tool(tool, args)
        handler = getattr(self.tool_executor, "get_handler", lambda n: None)(tool)
        if handler:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                return await handler(**args)
            return handler(**args)
        return {"error": f"Unknown tool: {tool}"}
