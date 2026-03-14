"""
WorkflowEngine - loads YAML workflows, subscribes to EventBus, executes tool chains.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from events.bus import EventBus
from events.types import AgentEvent
from workflows.loader import WorkflowDefinition, load_all_workflows

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Loads workflows from YAML, subscribes to EventBus triggers, executes action chains.
    """

    def __init__(
        self,
        event_bus: EventBus,
        workflow_dir: Path | str | None = None,
        tool_resolver: Callable[[str], Callable[..., Any] | None] | None = None,
    ) -> None:
        self.bus = event_bus
        self.workflow_dir = Path(workflow_dir) if workflow_dir else Path.cwd() / "workflows"
        self._tool_resolver = tool_resolver or (lambda _: None)
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._subscribed = False

    def load_workflows(self) -> None:
        """Load all workflows from workflow_dir."""
        for wf in load_all_workflows(self.workflow_dir):
            if wf.enabled:
                self._workflows[wf.trigger] = wf
        logger.info("Loaded %d workflows", len(self._workflows))

    def subscribe(self) -> None:
        """Subscribe to EventBus for workflow triggers."""
        if self._subscribed:
            return
        self.load_workflows()
        for trigger, wf in self._workflows.items():
            self.bus.subscribe(trigger, self._handle_event)
        self._subscribed = True

    def _handle_event(self, event: AgentEvent) -> None:
        """Handle incoming event by running matching workflow."""
        topic = f"{event.source.value}.{event.event_type}" if hasattr(event.source, "value") else f"{event.source}.{event.event_type}"
        wf = self._workflows.get(topic)
        if not wf:
            return
        logger.info("Running workflow %s for event %s", wf.name, topic)
        context = {"event": event.payload}
        for action in wf.actions:
            tool_name = action.tool
            handler = self._tool_resolver(tool_name)
            if not handler:
                logger.warning("Unknown tool %s in workflow %s", tool_name, wf.name)
                if action.on_failure == "stop":
                    return
                continue
            try:
                result = handler(**{**action.args, **context})
                context["last_result"] = result
            except Exception as e:
                logger.exception("Workflow action %s failed: %s", tool_name, e)
                if action.on_failure == "stop":
                    return
