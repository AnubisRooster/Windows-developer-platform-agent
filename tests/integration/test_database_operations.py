"""Integration tests for database operations spanning multiple models."""

from __future__ import annotations

import json

import pytest

from database.models import (
    CachedSummary,
    Event,
    ToolOutputModel,
    WorkflowRun,
    get_session,
    persist_tool_output,
)


@pytest.fixture(autouse=True)
def _use_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")


class TestDatabaseIntegration:
    def test_full_event_lifecycle(self):
        session = get_session()
        try:
            evt = Event(event_id="int-1", source="github", event_type="push", payload='{"ref":"main"}')
            session.add(evt)
            session.commit()

            run = WorkflowRun(
                workflow_name="pr_opened",
                trigger_event_id="int-1",
                status="running",
            )
            session.add(run)
            session.commit()

            run.status = "success"
            session.commit()

            result = session.query(WorkflowRun).filter_by(trigger_event_id="int-1").first()
            assert result.status == "success"
        finally:
            session.close()

    def test_cached_summary_upsert(self):
        session = get_session()
        try:
            cs = CachedSummary(key="pr:42", summary="Initial summary")
            session.add(cs)
            session.commit()

            existing = session.query(CachedSummary).filter_by(key="pr:42").first()
            existing.summary = "Updated summary"
            session.commit()

            result = session.query(CachedSummary).filter_by(key="pr:42").first()
            assert result.summary == "Updated summary"
        finally:
            session.close()

    def test_tool_output_with_dict_result(self):
        persist_tool_output("github.create_issue", True, {"key": "PROJ-1", "id": 123})
        session = get_session()
        try:
            row = session.query(ToolOutputModel).filter_by(tool_name="github.create_issue").first()
            assert row is not None
            assert "PROJ-1" in row.result
        finally:
            session.close()

    def test_multiple_events_query(self):
        session = get_session()
        try:
            for i in range(5):
                session.add(Event(
                    event_id=f"batch-{i}",
                    source="github" if i % 2 == 0 else "slack",
                    event_type="push",
                    payload="{}",
                ))
            session.commit()

            github_events = session.query(Event).filter_by(source="github").all()
            slack_events = session.query(Event).filter_by(source="slack").all()
            assert len(github_events) == 3
            assert len(slack_events) == 2
        finally:
            session.close()

    def test_workflow_run_failure_recording(self):
        session = get_session()
        try:
            run = WorkflowRun(
                workflow_name="build_failed",
                trigger_event_id="e-fail",
                status="failed",
                error="Step 2 timed out",
            )
            session.add(run)
            session.commit()

            result = session.query(WorkflowRun).filter_by(status="failed").first()
            assert result.error == "Step 2 timed out"
        finally:
            session.close()
