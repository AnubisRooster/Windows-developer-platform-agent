"""
Integration tests for the Developer AI Platform.

Tests end-to-end flows:
  - Webhook → Event Store → Event Bus → Workflow Engine
  - Knowledge Graph + Document Store + Embeddings pipeline
  - Dashboard API reads back data written by webhooks
  - IronClaw orchestrator with tool execution
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "")
    monkeypatch.setenv("JIRA_WEBHOOK_SECRET", "")
    monkeypatch.setenv("JENKINS_WEBHOOK_SECRET", "")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    from backend.security import secrets as sec_mod
    sec_mod._SECRETS_CACHE = None
    yield
    db._engine = None
    db._SessionLocal = None
    sec_mod._SECRETS_CACHE = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def full_app():
    """Create app with event bus and workflow engine wired up."""
    from backend.database.models import init_db
    from backend.events.bus import EventBus
    from backend.webhooks.server import create_app
    from backend.workflows.engine import WorkflowEngine

    init_db()
    bus = EventBus(persist=False, redis_url="")

    class StubExecutor:
        async def execute_tool(self, name, args):
            return {"tool": name, "args": args, "result": "ok"}

    wf_dir = PROJECT_ROOT / "backend" / "workflows"
    engine = WorkflowEngine(event_bus=bus, workflows_dir=wf_dir, tool_executor=StubExecutor())
    engine.load_workflows()
    engine.subscribe_to_triggers()

    app = create_app(orchestrator=None, event_bus=bus, workflow_engine=engine, ironclaw_client=None)
    return TestClient(app)


@pytest.fixture
def client():
    """Minimal app, no orchestrator."""
    from backend.database.models import init_db
    from backend.webhooks.server import create_app
    init_db()
    app = create_app()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Webhook → Event Store
# ---------------------------------------------------------------------------

class TestWebhookToEventStore:
    def test_github_webhook_stores_standardized_event(self, client):
        from backend.database.models import Event, get_session
        resp = client.post(
            "/webhooks/github",
            json={"action": "opened", "sender": {"login": "alice"}, "pull_request": {"number": 7}},
            headers={"X-GitHub-Event": "pull_request"},
        )
        assert resp.status_code == 200
        event_id = resp.json()["event_id"]
        assert len(event_id) == 36

        Session = get_session()
        with Session() as session:
            ev = session.query(Event).filter(Event.event_id == event_id).first()
            assert ev is not None
            assert ev.source == "github"
            assert ev.event_type == "pull_request.opened"
            assert ev.actor == "alice"

    def test_jira_webhook_stores_event_with_actor(self, client):
        from backend.database.models import Event, get_session
        resp = client.post("/webhooks/jira", json={
            "webhookEvent": "jira:issue_created",
            "user": {"displayName": "Bob"},
            "issue": {"key": "PROJ-42"},
        })
        assert resp.status_code == 200
        Session = get_session()
        with Session() as session:
            ev = session.query(Event).filter(Event.source == "jira").first()
            assert ev.actor == "Bob"

    def test_gmail_webhook_stores_event(self, client):
        from backend.database.models import Event, get_session
        resp = client.post("/webhooks/gmail", json={
            "message": {"data": "user@company.com", "messageId": "m-123"},
        })
        assert resp.status_code == 200
        Session = get_session()
        with Session() as session:
            ev = session.query(Event).filter(Event.source == "gmail").first()
            assert ev is not None
            assert ev.event_type == "push_notification"

    def test_all_webhooks_produce_logs(self, client):
        from backend.database.models import AgentLog, get_session
        client.post("/webhooks/github", json={"action": "x", "sender": {}}, headers={"X-GitHub-Event": "push"})
        client.post("/webhooks/slack", json={"type": "event_callback", "event": {"type": "message"}})
        client.post("/webhooks/jira", json={"webhookEvent": "issue_updated", "user": {}})
        client.post("/webhooks/jenkins", json={"build": {"phase": "COMPLETED", "status": "SUCCESS"}})
        client.post("/webhooks/gmail", json={"message": {"data": "x"}})

        Session = get_session()
        with Session() as session:
            logs = session.query(AgentLog).filter(AgentLog.category == "webhook").all()
            assert len(logs) == 5
            sources = {log.message.split(".")[0] for log in logs}
            assert sources == {"github", "slack", "jira", "jenkins", "gmail"}


# ---------------------------------------------------------------------------
# Dashboard API reads back webhook data
# ---------------------------------------------------------------------------

class TestDashboardReadsWebhookData:
    def test_events_api_returns_stored_events(self, client):
        client.post("/webhooks/github", json={"action": "opened", "sender": {"login": "x"}}, headers={"X-GitHub-Event": "issues"})
        client.post("/webhooks/jira", json={"webhookEvent": "issue_created", "user": {"displayName": "y"}})

        resp = client.get("/api/events")
        events = resp.json()
        assert len(events) == 2
        sources = {e["source"] for e in events}
        assert sources == {"github", "jira"}

    def test_event_detail_returns_payload(self, client):
        resp = client.post("/webhooks/github", json={"action": "closed", "sender": {"login": "z"}}, headers={"X-GitHub-Event": "pull_request"})
        event_id = resp.json()["event_id"]

        detail = client.get(f"/api/events/{event_id}").json()
        assert detail["event_id"] == event_id
        assert detail["payload"]["action"] == "closed"

    def test_logs_api_returns_webhook_logs(self, client):
        client.post("/webhooks/github", json={"action": "x", "sender": {}}, headers={"X-GitHub-Event": "push"})
        resp = client.get("/api/logs?category=webhook")
        logs = resp.json()
        assert len(logs) >= 1
        assert all(l["category"] == "webhook" for l in logs)

    def test_status_api_counts(self, client):
        client.post("/webhooks/github", json={"action": "x", "sender": {}}, headers={"X-GitHub-Event": "push"})
        resp = client.get("/api/status")
        data = resp.json()
        assert data["counts"]["events"] >= 1


# ---------------------------------------------------------------------------
# Knowledge Graph + Document Store pipeline
# ---------------------------------------------------------------------------

class TestKnowledgePipeline:
    def test_index_to_graph_and_documents(self):
        from backend.database.models import Document, get_session, init_db
        from backend.knowledge.graph import KnowledgeGraph
        from backend.knowledge.indexer import _upsert_document

        init_db()
        graph = KnowledgeGraph()
        repo_node = graph.upsert_node("repository", "test/app", external_id="test/app", source="github")
        file_node = graph.upsert_node("file", "main.py", external_id="test/app/main.py", source="github")
        graph.add_edge("repo_contains_file", repo_node, file_node)

        _upsert_document("github", "repository", "test/app", "A test app", "test/app", "https://github.com/test/app")

        repo = graph.find_repo("test/app")
        assert repo is not None
        assert len(repo["files"]) == 1

        Session = get_session()
        with Session() as session:
            doc = session.query(Document).filter(Document.external_id == "test/app").first()
            assert doc is not None
            assert doc.title == "test/app"

    def test_graph_trace_through_full_chain(self):
        from backend.database.models import init_db
        from backend.knowledge.graph import KnowledgeGraph

        init_db()
        graph = KnowledgeGraph()

        repo = graph.upsert_node("repository", "acme/api", external_id="acme/api", source="github")
        file_a = graph.upsert_node("file", "auth.py", external_id="acme/api/auth.py", source="github")
        commit = graph.upsert_node("commit", "abc1234", external_id="abc1234deadbeef", source="github")
        pr = graph.upsert_node("pull_request", "PR #10", external_id="acme/api/pull/10", source="github")
        issue = graph.upsert_node("jira_issue", "AUTH-99: Fix login", external_id="AUTH-99", source="jira")
        engineer = graph.upsert_node("engineer", "alice", external_id="alice", source="github")
        pipeline = graph.upsert_node("pipeline", "deploy-prod", external_id="deploy-prod", source="jenkins")

        graph.add_edge("repo_contains_file", repo, file_a)
        graph.add_edge("file_modified_by_commit", file_a, commit)
        graph.add_edge("commit_part_of_pr", commit, pr)
        graph.add_edge("pr_links_to_issue", pr, issue)
        graph.add_edge("authored_by", pr, engineer)
        graph.add_edge("repo_deployed_by_pipeline", repo, pipeline)

        trace = graph.trace_commit("abc1234deadbeef")
        assert trace["commit"]["name"] == "abc1234"
        assert len(trace["pull_requests"]) == 1
        assert trace["pull_requests"][0]["name"] == "PR #10"
        assert len(trace["jira_issues"]) == 1
        assert "AUTH-99" in trace["jira_issues"][0]["name"]

        repo_info = graph.find_repo("acme/api")
        assert len(repo_info["files"]) == 1
        assert len(repo_info["pipelines"]) == 1

    def test_embedding_index_and_search_pipeline(self):
        from unittest.mock import patch
        from backend.database.models import Document, init_db, get_session
        from backend.knowledge.embeddings import EmbeddingStore

        init_db()
        Session = get_session()
        with Session() as session:
            session.add(Document(source="github", doc_type="code", title="auth.py", content="def authenticate(user, password): validate credentials", external_id="auth.py"))
            session.add(Document(source="github", doc_type="code", title="db.py", content="def connect_database(): open connection pool", external_id="db.py"))
            session.commit()

        with Session() as session:
            docs = session.query(Document).all()
            doc_ids = {d.title: d.doc_id for d in docs}

        store = EmbeddingStore()

        import asyncio

        async def run_pipeline():
            with patch("backend.knowledge.embeddings.get_embeddings", side_effect=[
                [[1.0, 0.0, 0.0]],  # auth.py
                [[0.0, 1.0, 0.0]],  # db.py
            ]):
                await store.index_document(doc_ids["auth.py"], "def authenticate(user, password): validate credentials")
                await store.index_document(doc_ids["db.py"], "def connect_database(): open connection pool")

            with patch("backend.knowledge.embeddings.get_embeddings", return_value=[[0.9, 0.1, 0.0]]):
                results = await store.search("authentication login")
                assert len(results) == 2
                assert results[0]["title"] == "auth.py"
                assert results[0]["score"] > results[1]["score"]

        asyncio.run(run_pipeline())


# ---------------------------------------------------------------------------
# Orchestrator + Tool Execution pipeline
# ---------------------------------------------------------------------------

class TestOrchestratorPipeline:
    @pytest.mark.asyncio
    async def test_message_to_tool_to_database(self):
        from backend.agent.orchestrator import Orchestrator
        from backend.agent.memory import ConversationMemory
        from backend.tools.registry import ToolRegistry, ToolSchema
        from backend.database.models import AgentConversation, ToolOutput, init_db, get_session

        init_db()
        ironclaw = AsyncMock()
        ironclaw.interpret.return_value = {
            "content": "Running tool...",
            "tool_calls": [
                {"function": {"name": "ping", "arguments": '{"host": "localhost"}'}}
            ],
        }

        registry = ToolRegistry()
        registry.register(
            "ping",
            lambda host: f"pong from {host}",
            ToolSchema("ping", "Ping a host", {"type": "object", "properties": {"host": {"type": "string"}}, "required": ["host"]}),
        )

        orch = Orchestrator(ironclaw_client=ironclaw, tool_registry=registry)
        result = await orch.handle_message("Ping localhost", "integ-1")

        assert "pong from localhost" in result

        Session = get_session()
        with Session() as session:
            convos = session.query(AgentConversation).filter(AgentConversation.conversation_id == "integ-1").all()
            assert len(convos) == 2  # user + assistant

            outputs = session.query(ToolOutput).filter(ToolOutput.conversation_id == "integ-1").all()
            assert len(outputs) == 1
            assert outputs[0].tool_name == "ping"


# ---------------------------------------------------------------------------
# Workflow trigger via event bus
# ---------------------------------------------------------------------------

class TestWorkflowTriggerPipeline:
    @pytest.mark.asyncio
    async def test_event_triggers_workflow(self):
        from backend.database.models import WorkflowRun, init_db, get_session
        from backend.events.bus import EventBus
        from backend.workflows.engine import WorkflowEngine

        init_db()

        import tempfile
        with tempfile.TemporaryDirectory() as td:
            wf_path = Path(td) / "alert.yaml"
            wf_path.write_text(
                "name: test_alert\n"
                "trigger:\n"
                "  type: jenkins.build.failed\n"
                "actions:\n"
                "  - tool: mock.action\n"
                "    on_failure: continue\n",
                encoding="utf-8",
            )

            executed_tools = []

            class MockExecutor:
                async def execute_tool(self, name, args):
                    executed_tools.append(name)
                    return {"ok": True}

            bus = EventBus(persist=False, redis_url="")
            engine = WorkflowEngine(event_bus=bus, workflows_dir=Path(td), tool_executor=MockExecutor())
            engine.load_workflows()
            engine.subscribe_to_triggers()

            event = {
                "event_id": "e-test-1",
                "source": "jenkins",
                "type": "build.failed",
                "actor": "ci-bot",
                "payload": {"job": "deploy", "build_number": 99},
            }
            await bus.publish(event)

            assert "mock.action" in executed_tools

            Session = get_session()
            with Session() as session:
                runs = session.query(WorkflowRun).filter(WorkflowRun.workflow_name == "test_alert").all()
                assert len(runs) == 1
                assert runs[0].status == "success"
