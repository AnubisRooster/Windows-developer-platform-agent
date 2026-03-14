"""Unit tests for Planner, PlanStep, ActionPlan."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from agent.planner import ActionPlan, PlanStep, Planner


class TestPlanStep:
    def test_creation(self):
        step = PlanStep(tool="github.create_issue", args={"repo": "org/repo"}, description="Create an issue")
        assert step.tool == "github.create_issue"
        assert step.args == {"repo": "org/repo"}
        assert step.description == "Create an issue"


class TestActionPlan:
    def test_creation(self):
        plan = ActionPlan(goal="Deploy", steps=[])
        assert plan.goal == "Deploy"
        assert plan.steps == []

    def test_with_steps(self):
        steps = [PlanStep("a", {}, "do a"), PlanStep("b", {"x": 1}, "do b")]
        plan = ActionPlan(goal="multi-step", steps=steps)
        assert len(plan.steps) == 2


class TestPlanner:
    def test_create_plan_from_llm_json(self):
        llm = MagicMock()
        llm.chat.return_value = json.dumps({
            "goal": "Summarize PRs",
            "steps": [
                {"tool": "github.summarize_pull_request", "args": {"repo": "org/repo", "pr_number": 42}, "description": "Summarize PR #42"},
                {"tool": "slack.send_message", "args": {"channel": "#dev"}, "description": "Post to Slack"},
            ],
        })
        planner = Planner(llm)
        plan = planner.create_plan("Summarize PRs", ["github.summarize_pull_request", "slack.send_message"])
        assert plan.goal == "Summarize PRs"
        assert len(plan.steps) == 2
        assert plan.steps[0].tool == "github.summarize_pull_request"
        assert plan.steps[1].args == {"channel": "#dev"}

    def test_create_plan_with_markdown_fences(self):
        llm = MagicMock()
        llm.chat.return_value = '```json\n{"goal": "test", "steps": [{"tool": "noop", "args": {}, "description": "no-op"}]}\n```'
        planner = Planner(llm)
        plan = planner.create_plan("test", ["noop"])
        assert plan.goal == "test"
        assert len(plan.steps) == 1

    def test_create_plan_invalid_json(self):
        llm = MagicMock()
        llm.chat.return_value = "This is not JSON at all."
        planner = Planner(llm)
        plan = planner.create_plan("bad plan", ["tool_a"])
        assert plan.goal == "bad plan"
        assert plan.steps == []

    def test_create_plan_llm_exception(self):
        llm = MagicMock()
        llm.chat.side_effect = RuntimeError("LLM down")
        planner = Planner(llm)
        plan = planner.create_plan("fail", ["tool_a"])
        assert plan.steps == []

    def test_create_plan_missing_fields(self):
        llm = MagicMock()
        llm.chat.return_value = json.dumps({"steps": [{"tool": "x"}]})
        planner = Planner(llm)
        plan = planner.create_plan("partial", ["x"])
        assert len(plan.steps) == 1
        assert plan.steps[0].args == {}
        assert plan.steps[0].description == ""
