"""Unit tests for the enhanced platform database models."""

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


class TestEventModel:
    def test_event_has_uuid_event_id(self):
        from backend.database.models import Event, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            ev = Event(source="github", event_type="push.created", actor="octocat", payload={"ref": "main"})
            session.add(ev)
            session.commit()
            assert ev.event_id is not None
            assert len(ev.event_id) == 36  # UUID format
            assert ev.source == "github"
            assert ev.actor == "octocat"

    def test_event_stores_and_queries(self):
        from backend.database.models import Event, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            ev = Event(
                event_id="test-uuid-123",
                source="jira",
                event_type="issue_created",
                actor="dev@example.com",
                payload={"key": "PROJ-1"},
            )
            session.add(ev)
            session.commit()

        with Session() as session:
            result = session.query(Event).filter(Event.event_id == "test-uuid-123").first()
            assert result is not None
            assert result.source == "jira"
            assert result.actor == "dev@example.com"


class TestWorkflowRunModel:
    def test_workflow_run_has_run_id(self):
        from backend.database.models import WorkflowRun, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            wr = WorkflowRun(workflow_name="build_failed", status="running")
            session.add(wr)
            session.commit()
            assert wr.run_id is not None
            assert len(wr.run_id) == 36

    def test_workflow_run_stores_actions_log(self):
        from backend.database.models import WorkflowRun, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            wr = WorkflowRun(
                workflow_name="test_wf",
                status="success",
                actions_log=[{"step": 0, "tool": "slack.send_message", "status": "success"}],
            )
            session.add(wr)
            session.commit()

        with Session() as session:
            result = session.query(WorkflowRun).filter(WorkflowRun.workflow_name == "test_wf").first()
            assert result.actions_log is not None
            assert result.actions_log[0]["tool"] == "slack.send_message"


class TestKnowledgeGraphModels:
    def test_knowledge_node_creation(self):
        from backend.database.models import KnowledgeNode, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            node = KnowledgeNode(
                node_type="repository",
                name="owner/repo",
                external_id="owner/repo",
                source="github",
                properties={"language": "Python"},
            )
            session.add(node)
            session.commit()
            assert node.node_id is not None
            assert node.node_type == "repository"

    def test_knowledge_edge_creation(self):
        from backend.database.models import KnowledgeEdge, KnowledgeNode, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            repo = KnowledgeNode(node_type="repository", name="test/repo", external_id="test/repo", source="github")
            file_node = KnowledgeNode(node_type="file", name="main.py", external_id="test/repo/main.py", source="github")
            session.add_all([repo, file_node])
            session.commit()

            edge = KnowledgeEdge(
                edge_type="repo_contains_file",
                source_node_id=repo.node_id,
                target_node_id=file_node.node_id,
            )
            session.add(edge)
            session.commit()
            assert edge.id is not None


class TestDocumentModel:
    def test_document_creation(self):
        from backend.database.models import Document, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            doc = Document(
                source="github",
                doc_type="pull_request",
                title="PR #42: Fix auth",
                content="This PR fixes the authentication bug...",
                external_id="owner/repo/pull/42",
                external_url="https://github.com/owner/repo/pull/42",
            )
            session.add(doc)
            session.commit()
            assert doc.doc_id is not None
            assert doc.source == "github"


class TestEmbeddingModel:
    def test_embedding_creation(self):
        from backend.database.models import Document, Embedding, get_session, init_db
        init_db()
        Session = get_session()
        with Session() as session:
            doc = Document(source="github", doc_type="code", title="test.py", content="print('hello')", external_id="test.py")
            session.add(doc)
            session.commit()
            doc_id = doc.doc_id

        with Session() as session:
            emb = Embedding(
                doc_id=doc_id,
                chunk_index=0,
                chunk_text="print('hello')",
                embedding=[0.1, 0.2, 0.3],
                model="test-model",
                dimensions=3,
            )
            session.add(emb)
            session.commit()
            assert emb.id is not None


class TestAllTablesCreated:
    def test_all_platform_tables_exist(self):
        from backend.database.models import Base, init_db
        init_db()
        tables = set(Base.metadata.tables.keys())
        expected = {
            "events", "workflow_runs", "tool_outputs",
            "agent_memory", "agent_conversations", "agent_logs",
            "cached_summaries", "knowledge_nodes", "knowledge_edges",
            "documents", "embeddings",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"
