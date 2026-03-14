"""Unit tests for database models and utilities."""

from __future__ import annotations

import os
from datetime import datetime

import pytest

from database.models import (
    Base,
    CachedSummary,
    Event,
    ToolOutputModel,
    WorkflowRun,
    get_engine,
    get_session,
    persist_tool_output,
)


@pytest.fixture(autouse=True)
def sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")


class TestModels:
    def test_event_columns(self):
        e = Event(event_id="abc", source="github", event_type="push", payload='{}')
        assert e.event_id == "abc"
        assert e.source == "github"

    def test_workflow_run_columns(self):
        wr = WorkflowRun(workflow_name="pr_opened", trigger_event_id="e1", status="running")
        assert wr.status == "running"

    def test_cached_summary_columns(self):
        cs = CachedSummary(key="pr:42", summary="A good PR")
        assert cs.key == "pr:42"

    def test_tool_output_model_columns(self):
        to = ToolOutputModel(tool_name="slack.send", success=1, result="sent")
        assert to.tool_name == "slack.send"
        assert to.success == 1


class TestDatabaseSession:
    def test_get_engine_creates_tables(self):
        engine = get_engine()
        assert engine is not None
        table_names = Base.metadata.tables.keys()
        assert "events" in table_names
        assert "workflow_runs" in table_names
        assert "tool_outputs" in table_names

    def test_get_session(self):
        session = get_session()
        assert session is not None
        session.close()

    def test_persist_and_query_event(self):
        session = get_session()
        try:
            evt = Event(event_id="test-1", source="github", event_type="push", payload='{"ref":"main"}')
            session.add(evt)
            session.commit()
            result = session.query(Event).filter_by(event_id="test-1").first()
            assert result is not None
            assert result.source == "github"
        finally:
            session.close()

    def test_persist_and_query_workflow_run(self):
        session = get_session()
        try:
            run = WorkflowRun(workflow_name="test_wf", trigger_event_id="e1", status="success")
            session.add(run)
            session.commit()
            result = session.query(WorkflowRun).filter_by(workflow_name="test_wf").first()
            assert result.status == "success"
        finally:
            session.close()


class TestPersistToolOutput:
    def test_persist_success(self):
        persist_tool_output("slack.send", True, "message sent")
        session = get_session()
        try:
            row = session.query(ToolOutputModel).filter_by(tool_name="slack.send").first()
            assert row is not None
            assert row.success == 1
            assert row.result == "message sent"
        finally:
            session.close()

    def test_persist_failure(self):
        persist_tool_output("broken.tool", False, {}, error="it broke")
        session = get_session()
        try:
            row = session.query(ToolOutputModel).filter_by(tool_name="broken.tool").first()
            assert row is not None
            assert row.success == 0
            assert row.error == "it broke"
        finally:
            session.close()
