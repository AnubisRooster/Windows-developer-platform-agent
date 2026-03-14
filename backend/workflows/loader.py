"""
Workflow loader - load YAML workflow definitions from disk.

Uses pathlib.Path for all file operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
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
    on_failure: str = "fail"  # fail, continue, abort


@dataclass
class WorkflowDefinition:
    """Workflow definition from YAML."""

    name: str
    trigger: str
    description: str = ""
    enabled: bool = True
    actions: list[WorkflowAction] = None

    def __post_init__(self) -> None:
        if self.actions is None:
            self.actions = []


def load_workflow(path: Path) -> WorkflowDefinition | None:
    """Load a single workflow from YAML file."""
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

    actions = []
    for a in data.get("actions", []):
        if isinstance(a, dict):
            actions.append(WorkflowAction(
                tool=a.get("tool", ""),
                description=a.get("description", ""),
                args=a.get("args"),
                on_failure=a.get("on_failure", "fail"),
            ))
    return WorkflowDefinition(
        name=data.get("name", path.stem),
        trigger=data.get("trigger", ""),
        description=data.get("description", ""),
        enabled=data.get("enabled", True),
        actions=actions,
    )


def load_all_workflows(directory: Path) -> dict[str, WorkflowDefinition]:
    """Load all YAML workflows from a directory."""
    result: dict[str, WorkflowDefinition] = {}
    if not directory.exists() or not directory.is_dir():
        return result
    for p in directory.glob("*.yaml"):
        wf = load_workflow(p)
        if wf and wf.enabled:
            result[wf.name] = wf
    for p in directory.glob("*.yml"):
        wf = load_workflow(p)
        if wf and wf.enabled:
            result[wf.name] = wf
    return result
