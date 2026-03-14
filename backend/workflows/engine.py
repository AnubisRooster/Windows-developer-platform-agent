"""
WorkflowEngine - Loads YAML workflows, subscribes to EventBus triggers, executes tool sequences.

Records WorkflowRun in database with full action logs.
Supports the new standardized event format (event_id, source, type, actor, payload).
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.database.models import AgentLog, WorkflowRun, get_session
from backend.events.bus import EventBus
from backend.workflows.loader import WorkflowDefinition, load_all_workflows

logger = logging.getLogger(__name__)


def _get_nested(d: dict, path: str) -> Any:
    for part in path.split("."):
        d = d.get(part, {}) if isinstance(d, dict) else None
        if d is None:
            return None
    return d


def _render_template(text: str, context: dict[str, Any]) -> str:
    def repl(m: re.Match) -> str:
        key = m.group(1).strip()
        val = context.get(key)
        if val is None and "." in key:
            val = _get_nested(context, key)
        return str(val if val is not None else m.group(0))
    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", repl, text)


def _resolve_args(args: dict[str, Any] | None, context: dict[str, Any]) -> dict[str, Any]:
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


def _log_to_db(level: str, message: str, workflow_run_id: str | None = None, event_id: str | None = None) -> None:
    try:
        Session = get_session()
        with Session() as session:
            session.add(AgentLog(
                level=level,
                category="workflow",
                message=message,
                module="workflow_engine",
                event_id=event_id,
                workflow_run_id=workflow_run_id,
            ))
            session.commit()
    except Exception:
        pass


class WorkflowEngine:
    """Executes YAML-defined workflows triggered by events."""

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
        self._workflows = load_all_workflows(self.workflows_dir)
        self._loaded = True
        logger.info("Loaded %d workflows", len(self._workflows))

    def subscribe_to_triggers(self) -> None:
        if not self._loaded:
            self.load_workflows()
        for wf in self._workflows.values():
            if wf.trigger:
                self.event_bus.subscribe(wf.trigger, self._make_handler(wf))
                logger.info("Workflow '%s' subscribed to trigger: %s", wf.name, wf.trigger)

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
        wf = self._workflows.get(workflow_name)
        if not wf:
            return {"status": "error", "error": f"Workflow {workflow_name} not found"}

        context = event.get("payload", event)
        trigger_event_id = event.get("event_id", event.get("id"))
        run_id = str(uuid.uuid4())

        Session = get_session()
        with Session() as session:
            wr = WorkflowRun(
                run_id=run_id,
                workflow_name=workflow_name,
                trigger_event_id=str(trigger_event_id) if trigger_event_id else None,
                status="running",
            )
            session.add(wr)
            session.commit()

        _log_to_db("INFO", f"Workflow '{workflow_name}' started (run {run_id})", run_id, str(trigger_event_id))

        actions_log: list[dict[str, Any]] = []
        try:
            for i, action in enumerate(wf.actions):
                tool = action.tool
                args = _resolve_args(action.args, context)

                if dry_run:
                    actions_log.append({"step": i, "tool": tool, "args": args, "dry_run": True})
                    continue

                try:
                    out = await self._execute_tool(tool, args, context)
                    actions_log.append({"step": i, "tool": tool, "status": "success", "output": out})
                    _log_to_db("INFO", f"Action {tool} succeeded in workflow '{workflow_name}'", run_id)
                except Exception as e:
                    logger.exception("Workflow %s action %s failed: %s", workflow_name, tool, e)
                    actions_log.append({"step": i, "tool": tool, "status": "failed", "error": str(e)})
                    _log_to_db("ERROR", f"Action {tool} failed: {e}", run_id)

                    if action.on_failure != "continue":
                        with Session() as session:
                            wr = session.query(WorkflowRun).filter(WorkflowRun.run_id == run_id).first()
                            if wr:
                                wr.status = "failed"
                                wr.finished_at = datetime.now(timezone.utc)
                                wr.result = {"error": str(e)}
                                wr.actions_log = actions_log
                                session.commit()
                        return {"status": "failed", "run_id": run_id, "error": str(e), "actions_log": actions_log}

            with Session() as session:
                wr = session.query(WorkflowRun).filter(WorkflowRun.run_id == run_id).first()
                if wr:
                    wr.status = "success"
                    wr.finished_at = datetime.now(timezone.utc)
                    wr.result = {"results": [a.get("output") for a in actions_log if a.get("status") == "success"]}
                    wr.actions_log = actions_log
                    session.commit()
            _log_to_db("INFO", f"Workflow '{workflow_name}' completed successfully", run_id)
            return {"status": "success", "run_id": run_id, "actions_log": actions_log}

        except Exception as e:
            logger.exception("Workflow %s failed: %s", workflow_name, e)
            with Session() as session:
                wr = session.query(WorkflowRun).filter(WorkflowRun.run_id == run_id).first()
                if wr:
                    wr.status = "failed"
                    wr.finished_at = datetime.now(timezone.utc)
                    wr.result = {"error": str(e)}
                    wr.actions_log = actions_log
                    session.commit()
            return {"status": "error", "run_id": run_id, "error": str(e)}

    async def _execute_tool(self, tool: str, args: dict, context: dict) -> Any:
        if hasattr(self.tool_executor, "execute_tool"):
            return await self.tool_executor.execute_tool(tool, args)
        handler = getattr(self.tool_executor, "get_handler", lambda n: None)(tool)
        if handler:
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                return await handler(**args)
            return handler(**args)
        return {"error": f"Unknown tool: {tool}"}
