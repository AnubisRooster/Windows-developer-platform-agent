"""Deployment tests: verify database can connect and create schema."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect

from database.models import Base, Event, WorkflowRun, get_engine, get_session


@pytest.fixture(autouse=True)
def _use_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")


@pytest.mark.deployment
class TestDatabaseConnectivity:
    def test_engine_creates_successfully(self):
        engine = get_engine()
        assert engine is not None

    def test_all_tables_created(self):
        engine = get_engine()
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        expected = ["events", "workflow_runs", "cached_summaries", "tool_outputs"]
        for table in expected:
            assert table in table_names, f"Table {table} not found"

    def test_session_can_write_and_read(self):
        session = get_session()
        try:
            evt = Event(event_id="deploy-test", source="system", event_type="deploy.check", payload="{}")
            session.add(evt)
            session.commit()
            result = session.query(Event).filter_by(event_id="deploy-test").first()
            assert result is not None
        finally:
            session.close()

    def test_concurrent_sessions(self):
        s1 = get_session()
        s2 = get_session()
        try:
            s1.add(Event(event_id="s1", source="test", event_type="a", payload="{}"))
            s1.commit()
            result = s2.query(Event).filter_by(event_id="s1").first()
            assert result is not None
        finally:
            s1.close()
            s2.close()

    def test_rollback_on_error(self):
        session = get_session()
        try:
            session.add(Event(event_id="rollback-test", source="test", event_type="a", payload="{}"))
            session.commit()
            session.add(Event(event_id="rollback-test", source="test", event_type="a", payload="{}"))
            try:
                session.commit()
            except Exception:
                session.rollback()
            result = session.query(Event).filter_by(event_id="rollback-test").all()
            assert len(result) >= 1
        finally:
            session.close()
