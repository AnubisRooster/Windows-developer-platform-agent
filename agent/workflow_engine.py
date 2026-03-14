"""
Workflow engine - runs event-driven workflows.
Uses pathlib.Path for all file operations (Windows-compatible).
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from typing import Any

from agent.orchestrator import Orchestrator


class WorkflowEngine:
    """Executes workflows from YAML/JSON definitions."""

    def __init__(
        self,
        orchestrator: Orchestrator,
        workflows_dir: Path | str,
    ) -> None:
        self.orchestrator = orchestrator
        self.workflows_dir = Path(workflows_dir)

    def _load_workflow(self, name: str) -> dict[str, Any]:
        """Load workflow definition by name."""
        for ext in (".yaml", ".yml", ".json"):
            path = self.workflows_dir / f"{name}{ext}"
            if path.exists():
                with path.open(encoding="utf-8") as f:
                    if ext == ".json":
                        return json.load(f)
                    return yaml.safe_load(f) or {}
        raise FileNotFoundError(f"Workflow '{name}' not found in {self.workflows_dir}")

    def run(
        self,
        workflow_name: str,
        event: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run a workflow with the given event."""
        wf = self._load_workflow(workflow_name)
        if dry_run:
            return {"dry_run": True, "workflow": wf}
        steps = wf.get("steps", [])
        results = []
        for step in steps:
            action = step.get("action", "chat")
            if action == "chat":
                msg = step.get("message", "") or str(event)
                out = self.orchestrator.chat(msg, context=event or {})
                results.append({"step": step.get("name", ""), "output": out})
        return {"workflow": workflow_name, "results": results}
