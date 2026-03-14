"""
Workflow loader - load YAML workflow definitions from disk.

Supports the new trigger format:
  trigger:
    type: jenkins.build.failed

And the legacy flat trigger format:
  trigger: jenkins.build.failed
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class WorkflowAction:
    """Single action in a workflow."""

    tool: str
    description: str = ""
    args: dict[str, Any] | None = None
    on_failure: str = "fail"


@dataclass
class WorkflowDefinition:
    """Workflow definition from YAML."""

    name: str
    trigger: str
    description: str = ""
    enabled: bool = True
    actions: list[WorkflowAction] = field(default_factory=list)


def _parse_trigger(raw: Any) -> str:
    """
    Parse trigger from YAML. Supports:
      trigger: "github.pull_request.opened"
      trigger:
        type: "github.pull_request.opened"
    """
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return raw.get("type", "")
    return ""


def _parse_actions(raw_actions: list[Any]) -> list[WorkflowAction]:
    """Parse action list. Supports dict format and plain string (tool name only)."""
    actions = []
    for a in raw_actions:
        if isinstance(a, dict):
            actions.append(WorkflowAction(
                tool=a.get("tool", ""),
                description=a.get("description", ""),
                args=a.get("args"),
                on_failure=a.get("on_failure", "fail"),
            ))
        elif isinstance(a, str):
            actions.append(WorkflowAction(tool=a))
    return actions


def load_workflow(path: Path) -> WorkflowDefinition | None:
    if not path.exists():
        logger.warning("Workflow file not found: %s", path)
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.exception("Invalid YAML in %s: %s", path, e)
        return None

    if not data or not isinstance(data, dict):
        return None

    trigger = _parse_trigger(data.get("trigger", ""))
    actions = _parse_actions(data.get("actions", []))

    return WorkflowDefinition(
        name=data.get("name", path.stem),
        trigger=trigger,
        description=data.get("description", ""),
        enabled=data.get("enabled", True),
        actions=actions,
    )


def load_all_workflows(directory: Path) -> dict[str, WorkflowDefinition]:
    result: dict[str, WorkflowDefinition] = {}
    if not directory.exists() or not directory.is_dir():
        return result
    for pattern in ("*.yaml", "*.yml"):
        for p in directory.glob(pattern):
            wf = load_workflow(p)
            if wf and wf.enabled:
                result[wf.name] = wf
    return result
