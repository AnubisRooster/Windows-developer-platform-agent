"""
FastAPI webhook server with webhook endpoints and dashboard API.

CORS for frontend, signature verification on webhooks.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database.models import (
    AgentConversation,
    AgentLog,
    CachedSummary,
    Event,
    ToolOutput,
    WorkflowRun,
    get_session,
)
from backend.security.secrets import get_secrets, verify_webhook_signature

logger = logging.getLogger(__name__)


def create_app(
    orchestrator: Any | None = None,
    event_bus: Any | None = None,
    workflow_engine: Any | None = None,
    ironclaw_client: Any | None = None,
) -> FastAPI:
    """Create FastAPI application with all routes."""
    app = FastAPI(title="Windows Developer Platform Agent API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    secrets = get_secrets()

    # --- Health ---
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "platform": "windows", "timestamp": datetime.utcnow().isoformat()}

    # --- Webhooks ---
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
        event_type = f"{event_kind}.{action}" if event_kind else action
        Session = get_session()
        with Session() as session:
            ev = Event(
                source="github",
                event_type=event_type,
                payload=payload,
            )
            session.add(ev)
            session.commit()
            ev_id = ev.id
        if event_bus:
            await event_bus.publish({"source": "github", "event_type": event_type, "payload": payload, "id": ev_id})
        return JSONResponse({"received": True, "source": "github"})

    @app.post("/webhooks/jira")
    async def jira_webhook(request: Request) -> Response:
        payload = await request.json()
        Session = get_session()
        with Session() as session:
            ev = Event(source="jira", event_type="webhook", payload=payload)
            session.add(ev)
            session.commit()
            ev_id = ev.id
        if event_bus:
            await event_bus.publish({"source": "jira", "event_type": "webhook", "payload": payload, "id": ev_id})
        return JSONResponse({"received": True, "source": "jira"})

    @app.post("/webhooks/jenkins")
    async def jenkins_webhook(request: Request) -> Response:
        payload = await request.json()
        Session = get_session()
        with Session() as session:
            ev = Event(source="jenkins", event_type="webhook", payload=payload)
            session.add(ev)
            session.commit()
        if event_bus:
            await event_bus.publish({"source": "jenkins", "event_type": "webhook", "payload": payload})
        return JSONResponse({"received": True, "source": "jenkins"})

    @app.post("/webhooks/slack")
    async def slack_webhook(request: Request, x_slack_signature: str | None = Header(None)) -> Response:
        body = await request.body()
        if secrets.SLACK_SIGNING_SECRET and x_slack_signature:
            if not verify_webhook_signature(body, x_slack_signature, secrets.SLACK_SIGNING_SECRET):
                return JSONResponse({"error": "Invalid signature"}, status_code=401)
        payload = await request.json() if body else {}
        Session = get_session()
        with Session() as session:
            ev = Event(source="slack", event_type="webhook", payload=payload)
            session.add(ev)
            session.commit()
        if event_bus:
            await event_bus.publish({"source": "slack", "event_type": "webhook", "payload": payload})
        return JSONResponse({"received": True, "source": "slack"})

    # --- Dashboard API ---
    @app.get("/api/status")
    async def api_status() -> dict[str, Any]:
        health = {}
        if ironclaw_client:
            try:
                health = await ironclaw_client.health()
            except Exception:
                pass
        return {"status": "ok", "ironclaw": health}

    @app.get("/api/events")
    async def api_events(limit: int = 50) -> list[dict]:
        Session = get_session()
        with Session() as session:
            rows = session.query(Event).order_by(Event.timestamp.desc()).limit(limit).all()
            return [{"id": r.id, "source": r.source, "event_type": r.event_type, "timestamp": str(r.timestamp)} for r in rows]

    @app.get("/api/workflows")
    async def api_workflows() -> list[dict]:
        if workflow_engine and hasattr(workflow_engine, "_workflows"):
            return [{"name": n, "trigger": w.trigger} for n, w in workflow_engine._workflows.items()]
        return []

    @app.get("/api/workflow-runs")
    async def api_workflow_runs(limit: int = 20) -> list[dict]:
        Session = get_session()
        with Session() as session:
            rows = session.query(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(limit).all()
            return [
                {
                    "id": r.id,
                    "workflow_name": r.workflow_name,
                    "status": r.status,
                    "started_at": str(r.started_at),
                    "finished_at": str(r.finished_at) if r.finished_at else None,
                }
                for r in rows
            ]

    @app.get("/api/tools")
    async def api_tools() -> list[dict]:
        if orchestrator and hasattr(orchestrator, "tools"):
            return [{"name": n} for n in orchestrator.tools.list_tools()]
        return []

    @app.get("/api/conversations")
    async def api_conversations(conversation_id: str | None = None, limit: int = 50) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(AgentConversation)
            if conversation_id:
                q = q.filter(AgentConversation.conversation_id == conversation_id)
            rows = q.order_by(AgentConversation.timestamp.desc()).limit(limit).all()
            return [
                {"conversation_id": r.conversation_id, "role": r.role, "content": r.content[:200], "timestamp": str(r.timestamp)}
                for r in rows
            ]

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

    @app.get("/api/logs")
    async def api_logs(level: str | None = None, limit: int = 100) -> list[dict]:
        Session = get_session()
        with Session() as session:
            q = session.query(AgentLog)
            if level:
                q = q.filter(AgentLog.level == level)
            rows = q.order_by(AgentLog.timestamp.desc()).limit(limit).all()
            return [
                {"level": r.level, "message": r.message, "module": r.module, "timestamp": str(r.timestamp)}
                for r in rows
            ]

    return app
