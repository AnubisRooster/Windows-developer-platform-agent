"""Unit tests for the enhanced Workflow Engine and Loader."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    yield
    db._engine = None
    db._SessionLocal = None


class TestWorkflowLoader:
    def test_load_new_trigger_format(self, tmp_path):
        from backend.workflows.loader import load_workflow
        wf_file = tmp_path / "test.yaml"
        wf_file.write_text(
            "name: test_wf\n"
            "trigger:\n"
            "  type: jenkins.build.failed\n"
            "actions:\n"
            "  - tool: jenkins.fetch_logs\n"
            "  - tool: agent.summarize_logs\n"
            "  - tool: slack.send_message\n",
            encoding="utf-8",
        )
        wf = load_workflow(wf_file)
        assert wf is not None
        assert wf.name == "test_wf"
        assert wf.trigger == "jenkins.build.failed"
        assert len(wf.actions) == 3

    def test_load_legacy_trigger_format(self, tmp_path):
        from backend.workflows.loader import load_workflow
        wf_file = tmp_path / "legacy.yaml"
        wf_file.write_text(
            "name: legacy_wf\n"
            "trigger: github.pull_request.opened\n"
            "actions:\n"
            "  - tool: github.summarize_pr\n",
            encoding="utf-8",
        )
        wf = load_workflow(wf_file)
        assert wf is not None
        assert wf.trigger == "github.pull_request.opened"

    def test_load_string_actions(self, tmp_path):
        from backend.workflows.loader import load_workflow
        wf_file = tmp_path / "string_actions.yaml"
        wf_file.write_text(
            "name: string_wf\n"
            "trigger:\n"
            "  type: test.event\n"
            "actions:\n"
            "  - jenkins.fetch_logs\n"
            "  - slack.send_message\n",
            encoding="utf-8",
        )
        wf = load_workflow(wf_file)
        assert len(wf.actions) == 2
        assert wf.actions[0].tool == "jenkins.fetch_logs"

    def test_load_all_workflows(self, tmp_path):
        from backend.workflows.loader import load_all_workflows
        (tmp_path / "a.yaml").write_text("name: a\ntrigger: x\nactions:\n  - tool: t\n", encoding="utf-8")
        (tmp_path / "b.yml").write_text("name: b\ntrigger: y\nactions:\n  - tool: t\n", encoding="utf-8")
        (tmp_path / "disabled.yaml").write_text("name: d\ntrigger: z\nenabled: false\nactions:\n  - tool: t\n", encoding="utf-8")
        wfs = load_all_workflows(tmp_path)
        assert len(wfs) == 2
        assert "a" in wfs
        assert "b" in wfs


class TestWorkflowEngine:
    @pytest.mark.asyncio
    async def test_run_workflow_records_in_db(self, tmp_path):
        from backend.database.models import WorkflowRun, get_session, init_db
        from backend.events.bus import EventBus
        from backend.workflows.engine import WorkflowEngine

        init_db()
        (tmp_path / "test.yaml").write_text(
            "name: test_wf\ntrigger: test.event\nactions:\n  - tool: noop\n    on_failure: continue\n",
            encoding="utf-8",
        )

        class FakeExecutor:
            async def execute_tool(self, name, args):
                return {"ok": True}

        bus = EventBus(persist=False)
        engine = WorkflowEngine(event_bus=bus, workflows_dir=tmp_path, tool_executor=FakeExecutor())
        engine.load_workflows()

        result = await engine.run_workflow("test_wf", {"source": "test", "type": "event", "event_id": "e-123", "payload": {}})
        assert result["status"] == "success"

        Session = get_session()
        with Session() as session:
            runs = session.query(WorkflowRun).all()
            assert len(runs) >= 1
            assert runs[-1].workflow_name == "test_wf"
            assert runs[-1].status == "success"
