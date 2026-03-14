"""
FastAPI Event Gateway with standardized event format.

Webhook endpoints convert source-specific payloads into a normalized event envelope:
  { event_id, source, type, timestamp, actor, payload }

Events are stored in PostgreSQL and published to the event bus.
Signature verification on all webhooks that support it.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database.models import (
    AgentConversation,
    AgentLog,
    CachedSummary,
    Document,
    Embedding,
    Event,
    KnowledgeEdge,
    KnowledgeNode,
    ToolOutput,
    WorkflowRun,
    get_session,
)
from backend.security.secrets import get_secrets, verify_webhook_signature

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_event(source: str, event_type: str, actor: str | None, payload: dict) -> dict[str, Any]:
    """Build a standardized event envelope."""
    return {
        "event_id": str(uuid.uuid4()),
        "source": source,
        "type": event_type,
        "timestamp": _now_iso(),
        "actor": actor,
        "payload": payload,
    }


def _persist_event(event: dict[str, Any]) -> int:
    """Store event in the database. Returns the row id."""
    Session = get_session()
    with Session() as session:
        ev = Event(
            event_id=event["event_id"],
            source=event["source"],
            event_type=event["type"],
            actor=event.get("actor"),
            payload=event["payload"],
        )
        session.add(ev)
        session.commit()
        return ev.id


def _log_event(event: dict[str, Any], category: str = "webhook") -> None:
    """Write structured log for the event."""
    Session = get_session()
    with Session() as session:
        session.add(AgentLog(
            level="INFO",
            category=category,
            message=f"{event['source']}.{event['type']} from {event.get('actor', 'unknown')}",
            module="event_gateway",
            event_id=event["event_id"],
            meta={"source": event["source"], "type": event["type"]},
        ))
        session.commit()


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(
    orchestrator: Any | None = None,
    event_bus: Any | None = None,
    workflow_engine: Any | None = None,
    ironclaw_client: Any | None = None,
) -> FastAPI:
    """Create FastAPI application with Event Gateway and Dashboard API."""
    app = FastAPI(
        title="Developer AI Platform - Event Gateway",
        version="2.0.0",
        description="Internal developer AI platform with event-driven workflows and knowledge graph.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    secrets = get_secrets()

    # =======================================================================
    # Health
    # =======================================================================

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "platform": "developer-ai",
            "version": "2.0.0",
            "timestamp": _now_iso(),
        }

    # =======================================================================
    # Webhook Endpoints (Event Gateway)
    # =======================================================================

    @app.post("/webhooks/github")
    async def github_webhook(
        request: Request,
        x_hub_signature_256: str | None = Header(None),
        x_github_event: str | None = Header(None),
    ) -> Response:
        body = await request.body()
        if secrets.GITHUB_WEBHOOK_SECRET and x_hub_signature_256:
            if not verify_webhook_signature(body, x_hub_signature_256, secrets.GITHUB_WEBHOOK_SECRET):
                return JSONResponse({"error": "Invalid signature"}, status_code=401)

        payload = await request.json() if body else {}
        action = payload.get("action", "unknown")
        event_kind = x_github_event or "webhook"
        event_type = f"{event_kind}.{action}"
        actor = (payload.get("sender") or {}).get("login")

        event = _make_event("github", event_type, actor, payload)
        _persist_event(event)
        _log_event(event)

        if event_bus:
            await event_bus.publish(event)
        return JSONResponse({"received": True, "event_id": event["event_id"]})

    @app.post("/webhooks/slack")
    async def slack_webhook(
        request: Request,
        x_slack_signature: str | None = Header(None),
    ) -> Response:
        body = await request.body()
        if secrets.SLACK_SIGNING_SECRET and x_slack_signature:
            if not verify_webhook_signature(body, x_slack_signature, secrets.SLACK_SIGNING_SECRET):
                return JSONResponse({"error": "Invalid signature"}, status_code=401)

        payload = await request.json() if body else {}

        if payload.get("type") == "url_verification":
            return JSONResponse({"challenge": payload.get("challenge", "")})

        event_data = payload.get("event", {})
        event_type = event_data.get("type", payload.get("type", "webhook"))
        actor = event_data.get("user")

        event = _make_event("slack", event_type, actor, payload)
        _persist_event(event)
        _log_event(event)

        if event_bus:
            await event_bus.publish(event)
        return JSONResponse({"received": True, "event_id": event["event_id"]})

    @app.post("/webhooks/jira")
    async def jira_webhook(
        request: Request,
        x_atlassian_webhook_identifier: str | None = Header(None),
    ) -> Response:
        body = await request.body()
        if secrets.JIRA_WEBHOOK_SECRET:
            sig = request.headers.get("x-hub-signature")
            if sig and not verify_webhook_signature(body, sig, secrets.JIRA_WEBHOOK_SECRET):
                return JSONResponse({"error": "Invalid signature"}, status_code=401)

        payload = await request.json() if body else {}
        webhook_event = payload.get("webhookEvent", payload.get("issue_event_type_name", "webhook"))
        actor = (payload.get("user") or {}).get("displayName") or (payload.get("user") or {}).get("name")

        event = _make_event("jira", webhook_event, actor, payload)
        _persist_event(event)
        _log_event(event)

        if event_bus:
            await event_bus.publish(event)
        return JSONResponse({"received": True, "event_id": event["event_id"]})

    @app.post("/webhooks/jenkins")
    async def jenkins_webhook(request: Request) -> Response:
        body = await request.body()
        if secrets.JENKINS_WEBHOOK_SECRET:
            token = request.headers.get("x-jenkins-token") or request.query_params.get("token")
            if token and token != secrets.JENKINS_WEBHOOK_SECRET:
                return JSONResponse({"error": "Invalid token"}, status_code=401)

        payload = await request.json() if body else {}
        build = payload.get("build", {})
        phase = build.get("phase", "unknown").lower()
        status = build.get("status", "unknown").lower()
        event_type = f"build.{phase}" if status == "unknown" else f"build.{status}"
        actor = (payload.get("build", {}).get("parameters") or {}).get("BUILD_USER")

        event = _make_event("jenkins", event_type, actor, payload)
        _persist_event(event)
        _log_event(event)

        if event_bus:
            await event_bus.publish(event)
        return JSONResponse({"received": True, "event_id": event["event_id"]})

    @app.post("/webhooks/gmail")
    async def gmail_webhook(request: Request) -> Response:
        """Gmail push notification webhook (Google Cloud Pub/Sub)."""
        payload = await request.json() if await request.body() else {}
        message = payload.get("message", {})
        email_address = message.get("data")

        event = _make_event("gmail", "push_notification", email_address, payload)
        _persist_event(event)
        _log_event(event)

        if event_bus:
            await event_bus.publish(event)
        return JSONResponse({"received": True, "event_id": event["event_id"]})

    # =======================================================================
    # Dashboard API - Status
    # =======================================================================

    @app.get("/api/status")
    async def api_status() -> dict[str, Any]:
        ironclaw_health = {}
        if ironclaw_client:
            try:
                ironclaw_health = await ironclaw_client.health()
            except Exception:
                pass
        Session = get_session()
        with Session() as session:
            event_count = session.query(Event).count()
            workflow_count = session.query(WorkflowRun).count()
            doc_count = session.query(Document).count()
            node_count = session.query(KnowledgeNode).count()
        return {
            "status": "ok",
            "ironclaw": ironclaw_health,
            "counts": {
                "events": event_count,
                "workflow_runs": workflow_count,
                "documents": doc_count,
                "knowledge_nodes": node_count,
            },
        }

    # =======================================================================
    # Dashboard API - Events
    # =======================================================================

    @app.get("/api/events")
    async def api_events(
        limit: int = 50,
        source: str | None = None,
        event_type: str | None = None,
    ) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(Event).order_by(Event.timestamp.desc())
            if source:
                q = q.filter(Event.source == source)
            if event_type:
                q = q.filter(Event.event_type.contains(event_type))
            rows = q.limit(limit).all()
            return [
                {
                    "id": r.id,
                    "event_id": r.event_id,
                    "source": r.source,
                    "type": r.event_type,
                    "actor": r.actor,
                    "timestamp": str(r.timestamp),
                    "processed": r.processed,
                }
                for r in rows
            ]

    @app.get("/api/events/{event_id}")
    async def api_event_detail(event_id: str) -> dict:
        Session = get_session()
        with Session() as session:
            ev = session.query(Event).filter(Event.event_id == event_id).first()
            if not ev:
                return JSONResponse({"error": "Not found"}, status_code=404)
            return {
                "id": ev.id,
                "event_id": ev.event_id,
                "source": ev.source,
                "type": ev.event_type,
                "actor": ev.actor,
                "payload": ev.payload,
                "timestamp": str(ev.timestamp),
                "processed": ev.processed,
            }

    # =======================================================================
    # Dashboard API - Workflows
    # =======================================================================

    @app.get("/api/workflows")
    async def api_workflows() -> list[dict]:
        if workflow_engine and hasattr(workflow_engine, "_workflows"):
            return [
                {"name": n, "trigger": w.trigger, "description": w.description, "enabled": w.enabled}
                for n, w in workflow_engine._workflows.items()
            ]
        return []

    @app.get("/api/workflow-runs")
    async def api_workflow_runs(limit: int = 20, status: str | None = None) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(WorkflowRun).order_by(WorkflowRun.started_at.desc())
            if status:
                q = q.filter(WorkflowRun.status == status)
            rows = q.limit(limit).all()
            return [
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "workflow_name": r.workflow_name,
                    "trigger_event_id": r.trigger_event_id,
                    "status": r.status,
                    "started_at": str(r.started_at),
                    "finished_at": str(r.finished_at) if r.finished_at else None,
                    "actions_log": r.actions_log,
                }
                for r in rows
            ]

    # =======================================================================
    # Dashboard API - Tools
    # =======================================================================

    @app.get("/api/tools")
    async def api_tools() -> list[dict]:
        if orchestrator and hasattr(orchestrator, "tools"):
            registry = orchestrator.tools
            entries = []
            for name in registry.list_tools():
                entry = registry._tools.get(name)
                if entry:
                    entries.append({
                        "name": entry.name,
                        "description": entry.schema.description,
                        "parameters": entry.schema.parameters,
                    })
            return entries
        return []

    # =======================================================================
    # Dashboard API - Conversations
    # =======================================================================

    @app.get("/api/conversations")
    async def api_conversations(conversation_id: str | None = None, limit: int = 50) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(AgentConversation)
            if conversation_id:
                q = q.filter(AgentConversation.conversation_id == conversation_id)
            rows = q.order_by(AgentConversation.timestamp.desc()).limit(limit).all()
            return [
                {
                    "conversation_id": r.conversation_id,
                    "role": r.role,
                    "content": r.content[:200] if r.content else "",
                    "timestamp": str(r.timestamp),
                }
                for r in rows
            ]

    @app.post("/api/chat")
    async def api_chat(data: dict[str, Any]) -> dict[str, Any]:
        if not orchestrator:
            return {"error": "Orchestrator not available"}
        message = data.get("message", "")
        conversation_id = data.get("conversation_id", str(uuid.uuid4()))
        response = await orchestrator.handle_message(message, conversation_id)
        return {"conversation_id": conversation_id, "response": response}

    # =======================================================================
    # Dashboard API - Knowledge Explorer
    # =======================================================================

    @app.get("/api/knowledge/nodes")
    async def api_knowledge_nodes(
        node_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(KnowledgeNode)
            if node_type:
                q = q.filter(KnowledgeNode.node_type == node_type)
            if search:
                q = q.filter(KnowledgeNode.name.contains(search))
            rows = q.order_by(KnowledgeNode.updated_at.desc()).limit(limit).all()
            return [
                {
                    "node_id": r.node_id,
                    "node_type": r.node_type,
                    "name": r.name,
                    "external_id": r.external_id,
                    "source": r.source,
                    "properties": r.properties,
                }
                for r in rows
            ]

    @app.get("/api/knowledge/nodes/{node_id}")
    async def api_knowledge_node_detail(node_id: str) -> dict:
        Session = get_session()
        with Session() as session:
            node = session.query(KnowledgeNode).filter(KnowledgeNode.node_id == node_id).first()
            if not node:
                return JSONResponse({"error": "Not found"}, status_code=404)
            edges_out = session.query(KnowledgeEdge).filter(KnowledgeEdge.source_node_id == node_id).all()
            edges_in = session.query(KnowledgeEdge).filter(KnowledgeEdge.target_node_id == node_id).all()
            return {
                "node_id": node.node_id,
                "node_type": node.node_type,
                "name": node.name,
                "external_id": node.external_id,
                "properties": node.properties,
                "edges_out": [
                    {"edge_type": e.edge_type, "target": e.target_node_id}
                    for e in edges_out
                ],
                "edges_in": [
                    {"edge_type": e.edge_type, "source": e.source_node_id}
                    for e in edges_in
                ],
            }

    @app.get("/api/knowledge/edges")
    async def api_knowledge_edges(
        edge_type: str | None = None,
        node_id: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(KnowledgeEdge)
            if edge_type:
                q = q.filter(KnowledgeEdge.edge_type == edge_type)
            if node_id:
                q = q.filter(
                    (KnowledgeEdge.source_node_id == node_id)
                    | (KnowledgeEdge.target_node_id == node_id)
                )
            rows = q.limit(limit).all()
            return [
                {
                    "edge_type": e.edge_type,
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "properties": e.properties,
                }
                for e in rows
            ]

    # =======================================================================
    # Dashboard API - Repository Search
    # =======================================================================

    @app.get("/api/documents")
    async def api_documents(
        source: str | None = None,
        doc_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(Document)
            if source:
                q = q.filter(Document.source == source)
            if doc_type:
                q = q.filter(Document.doc_type == doc_type)
            if search:
                q = q.filter(Document.title.contains(search) | Document.content.contains(search))
            rows = q.order_by(Document.updated_at.desc()).limit(limit).all()
            return [
                {
                    "doc_id": r.doc_id,
                    "source": r.source,
                    "doc_type": r.doc_type,
                    "title": r.title,
                    "external_id": r.external_id,
                    "external_url": r.external_url,
                    "indexed_at": str(r.indexed_at),
                }
                for r in rows
            ]

    @app.get("/api/documents/{doc_id}")
    async def api_document_detail(doc_id: str) -> dict:
        Session = get_session()
        with Session() as session:
            doc = session.query(Document).filter(Document.doc_id == doc_id).first()
            if not doc:
                return JSONResponse({"error": "Not found"}, status_code=404)
            return {
                "doc_id": doc.doc_id,
                "source": doc.source,
                "doc_type": doc.doc_type,
                "title": doc.title,
                "content": doc.content[:2000] if doc.content else "",
                "external_id": doc.external_id,
                "external_url": doc.external_url,
                "metadata": doc.metadata_,
                "indexed_at": str(doc.indexed_at),
            }

    # =======================================================================
    # Dashboard API - Model Config
    # =======================================================================

    @app.get("/api/model/config")
    async def api_model_config_get() -> dict[str, Any]:
        if ironclaw_client:
            return {
                "provider": "openrouter" if getattr(ironclaw_client, "_use_openrouter", False) else "ironclaw",
                "model": getattr(ironclaw_client, "openrouter_model", ""),
            }
        return {}

    @app.post("/api/model/config")
    async def api_model_config_post(data: dict[str, Any]) -> dict[str, Any]:
        if ironclaw_client and "provider" in data and "model" in data:
            await ironclaw_client.switch_model(data["provider"], data["model"])
            return {"status": "ok"}
        return {"status": "error", "error": "Invalid config"}

    # =======================================================================
    # Dashboard API - Logs
    # =======================================================================

    @app.get("/api/logs")
    async def api_logs(
        level: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(AgentLog)
            if level:
                q = q.filter(AgentLog.level == level)
            if category:
                q = q.filter(AgentLog.category == category)
            rows = q.order_by(AgentLog.timestamp.desc()).limit(limit).all()
            return [
                {
                    "level": r.level,
                    "category": r.category,
                    "message": r.message,
                    "module": r.module,
                    "event_id": r.event_id,
                    "timestamp": str(r.timestamp),
                }
                for r in rows
            ]

    return app
