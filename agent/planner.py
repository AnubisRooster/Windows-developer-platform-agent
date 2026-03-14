"""
Planner - decomposes goals into tool steps via LLM.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from agent.orchestrator import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """Single step in an action plan."""

    tool: str
    args: dict[str, Any]
    description: str


@dataclass
class ActionPlan:
    """Plan with goal and ordered steps."""

    goal: str
    steps: list[PlanStep]


class Planner:
    """Creates action plans by asking LLM to decompose goals into tool steps."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    def create_plan(self, goal: str, available_tools: list[str]) -> ActionPlan:
        """
        Ask LLM to decompose goal into tool steps. Parse JSON response into ActionPlan.

        Args:
            goal: The user's goal or intent.
            available_tools: List of available tool names.

        Returns:
            ActionPlan with goal and steps. Returns empty plan on parse failure.
        """
        tools_str = ", ".join(available_tools)
        prompt = f"""You are a task planner. The user has this goal: {goal}

Available tools: {tools_str}

Respond with a JSON object only, no other text:
{{
  "goal": "<the goal>",
  "steps": [
    {{ "tool": "<tool_name>", "args": {{...}}, "description": "<what this step does>" }},
    ...
  ]
}}"""

        messages = [
            {"role": "system", "content": "You output valid JSON only. No markdown, no explanation."},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.llm.chat(messages)
            # Strip markdown code blocks if present
            text = response.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            data = json.loads(text)
            goal_str = data.get("goal", goal)
            steps_data = data.get("steps", [])
            steps = []
            for s in steps_data:
                steps.append(
                    PlanStep(
                        tool=str(s.get("tool", "")),
                        args=dict(s.get("args", {})),
                        description=str(s.get("description", "")),
                    )
                )
            return ActionPlan(goal=goal_str, steps=steps)
        except json.JSONDecodeError as e:
            logger.warning("Planner failed to parse JSON: %s", e)
            return ActionPlan(goal=goal, steps=[])
        except Exception as e:
            logger.exception("Planner failed: %s", e)
            return ActionPlan(goal=goal, steps=[])
