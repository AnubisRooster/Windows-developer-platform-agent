"""Unit tests for workflow loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from workflows.loader import (
    WorkflowAction,
    WorkflowDefinition,
    load_all_workflows,
    load_workflow,
)


class TestWorkflowAction:
    def test_creation(self):
        action = WorkflowAction(tool="slack.send_message", args={"channel": "#test"}, on_failure="continue")
        assert action.tool == "slack.send_message"
        assert action.args == {"channel": "#test"}
        assert action.on_failure == "continue"


class TestWorkflowDefinition:
    def test_creation(self):
        wf = WorkflowDefinition(
            name="test",
            trigger="github.push",
            description="A test",
            enabled=True,
            actions=[],
        )
        assert wf.name == "test"
        assert wf.enabled


class TestLoadWorkflow:
    def test_load_valid_workflow(self, tmp_workflow_dir):
        wf = load_workflow(tmp_workflow_dir / "pr_opened.yaml")
        assert wf.name == "pr_opened_workflow"
        assert wf.trigger == "github.pull_request.opened"
        assert wf.enabled
        assert len(wf.actions) == 2
        assert wf.actions[0].tool == "github.summarize_pull_request"
        assert wf.actions[1].args["channel"] == "#test"
        assert wf.actions[1].on_failure == "continue"

    def test_load_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_workflow(tmp_path / "nonexistent.yaml")

    def test_load_disabled_workflow(self, tmp_workflow_dir):
        wf = load_workflow(tmp_workflow_dir / "disabled.yaml")
        assert not wf.enabled

    def test_load_workflow_defaults(self, tmp_path):
        minimal = tmp_path / "minimal.yaml"
        minimal.write_text("actions:\n  - tool: noop\n", encoding="utf-8")
        wf = load_workflow(minimal)
        assert wf.name == "minimal"
        assert wf.trigger == ""
        assert wf.enabled
        assert wf.actions[0].on_failure == "stop"


class TestLoadAllWorkflows:
    def test_loads_multiple(self, tmp_workflow_dir):
        workflows = load_all_workflows(tmp_workflow_dir)
        names = [w.name for w in workflows]
        assert "pr_opened_workflow" in names
        assert "build_failed_workflow" in names
        assert "disabled_workflow" in names

    def test_nonexistent_directory(self, tmp_path):
        result = load_all_workflows(tmp_path / "nope")
        assert result == []

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        assert load_all_workflows(empty) == []


class TestLoadProjectWorkflows:
    """Test loading the actual project workflow files."""

    def test_load_project_pr_opened(self):
        project_workflows = Path(__file__).resolve().parent.parent.parent / "workflows"
        if not (project_workflows / "pr_opened.yaml").exists():
            pytest.skip("Project workflows not found")
        wf = load_workflow(project_workflows / "pr_opened.yaml")
        assert wf.trigger == "github.pull_request.opened"

    def test_load_project_build_failed(self):
        project_workflows = Path(__file__).resolve().parent.parent.parent / "workflows"
        if not (project_workflows / "build_failed.yaml").exists():
            pytest.skip("Project workflows not found")
        wf = load_workflow(project_workflows / "build_failed.yaml")
        assert wf.trigger == "jenkins.build.failed"

    def test_load_project_jira_created(self):
        project_workflows = Path(__file__).resolve().parent.parent.parent / "workflows"
        if not (project_workflows / "jira_created.yaml").exists():
            pytest.skip("Project workflows not found")
        wf = load_workflow(project_workflows / "jira_created.yaml")
        assert wf.trigger == "jira.issue.created"
