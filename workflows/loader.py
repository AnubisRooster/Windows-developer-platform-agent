"""
Workflow loader - loads YAML definitions from pathlib paths.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file from path."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass
class WorkflowAction:
    """Single action in a workflow."""

    tool: str
    args: dict[str, Any]
    on_failure: str  # continue, stop, alert


@dataclass
class WorkflowDefinition:
    """Parsed workflow definition from YAML."""

    name: str
    trigger: str
    description: str
    enabled: bool
    actions: list[WorkflowAction]


def load_workflow(path: Path | str) -> WorkflowDefinition:
    """
    Load a single workflow from YAML file.

    Args:
        path: Path to YAML file.

    Returns:
        WorkflowDefinition.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Workflow file not found: {path}")
    data = _load_yaml(path)
    actions_data = data.get("actions", [])
    actions = []
    for a in actions_data:
        actions.append(
            WorkflowAction(
                tool=a.get("tool", ""),
                args=dict(a.get("args", {})),
                on_failure=str(a.get("on_failure", "stop")),
            )
        )
    return WorkflowDefinition(
        name=data.get("name", path.stem),
        trigger=data.get("trigger", ""),
        description=data.get("description", ""),
        enabled=data.get("enabled", True),
        actions=actions,
    )


def load_all_workflows(directory: Path | str) -> list[WorkflowDefinition]:
    """
    Load all YAML workflows from a directory.

    Args:
        directory: Directory containing .yaml workflow files.

    Returns:
        List of WorkflowDefinitions.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []
    workflows = []
    for path in directory.glob("*.yaml"):
        try:
            workflows.append(load_workflow(path))
        except Exception as e:
            logger.warning("Failed to load workflow %s: %s", path, e)
    return workflows
