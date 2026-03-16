"""
FastAPI Event Gateway with standardized event format.

Webhook endpoints convert source-specific payloads into a normalized event envelope:
  { event_id, source, type, timestamp, actor, payload }

Events are stored in PostgreSQL and published to the event bus.
Signature verification on all webhooks that support it.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Header, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.database.models import (
    AgentConversation,
    AgentLog,
    CachedSummary,
    ChatMessage,
    ChatSession,
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

    # =======================================================================
    # Model Config (persisted to data/model_config.json)
    # =======================================================================

    _IRONCLAW_MODELS = [
        {"id": "zai-org/GLM-latest", "name": "GLM Latest (default)", "provider": "nearai"},
        {"id": "qwen3.5:latest", "name": "Qwen 3.5", "provider": "nearai"},
        {"id": "granite4:latest", "name": "Granite 4", "provider": "nearai"},
        {"id": "deepseek-r1:latest", "name": "DeepSeek R1", "provider": "nearai"},
        {"id": "llama4:latest", "name": "Llama 4", "provider": "nearai"},
        {"id": "mistral-large:latest", "name": "Mistral Large", "provider": "nearai"},
        {"id": "phi-4:latest", "name": "Phi 4", "provider": "nearai"},
        {"id": "gemma3:latest", "name": "Gemma 3", "provider": "nearai"},
    ]
    _OPENROUTER_MODELS = [
        {"id": "anthropic/claude-sonnet-4", "name": "Claude Sonnet 4 (Anthropic)"},
        {"id": "anthropic/claude-opus-4", "name": "Claude Opus 4 (Anthropic)"},
        {"id": "openai/gpt-4.1", "name": "GPT-4.1 (OpenAI)"},
        {"id": "openai/o3-mini", "name": "o3-mini (OpenAI)"},
        {"id": "google/gemini-2.5-pro", "name": "Gemini 2.5 Pro (Google)"},
        {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1"},
        {"id": "meta-llama/llama-4-maverick", "name": "Llama 4 Maverick (Meta)"},
        {"id": "mistralai/mistral-large-2", "name": "Mistral Large 2"},
        {"id": "qwen/qwen3.5-coder", "name": "Qwen 3.5 Coder"},
        {"id": "openrouter/hunter-alpha", "name": "Hunter Alpha (OpenRouter)"},
    ]
    _OLLAMA_MODELS = [
        {"id": "qwen3.5:latest", "name": "Qwen 3.5"},
        {"id": "granite4:latest", "name": "Granite 4"},
        {"id": "llama4:latest", "name": "Llama 4"},
        {"id": "deepseek-r1:14b", "name": "DeepSeek R1 14B"},
        {"id": "mistral:latest", "name": "Mistral"},
        {"id": "phi4:latest", "name": "Phi 4"},
        {"id": "gemma3:latest", "name": "Gemma 3"},
        {"id": "codellama:latest", "name": "Code Llama"},
    ]

    def _get_model_config_path() -> Path:
        base = Path(__file__).resolve().parent.parent.parent
        return base / "data" / "model_config.json"

    def _load_model_config() -> dict:
        path = _get_model_config_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "provider": "ironclaw",
            "model": "zai-org/GLM-latest",
            "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY", ""),
            "ollama_base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        }

    def _save_model_config(cfg: dict) -> None:
        path = _get_model_config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    def _mask_key(key: str) -> str:
        if not key or len(key) < 8:
            return ""
        return key[:4] + "..." + key[-4:]

    def _check_ironclaw() -> dict:
        ironclaw_url = os.environ.get("IRONCLAW_URL", "http://127.0.0.1:3000").rstrip("/")
        try:
            import httpx as _hx
            for path in ("/api/health", "/health"):
                try:
                    resp = _hx.get(f"{ironclaw_url}{path}", timeout=3.0)
                    if resp.status_code == 200:
                        return {"status": "connected", "details": f"Running at {ironclaw_url}"}
                except Exception:
                    continue
        except Exception:
            pass
        return {"status": "disconnected", "details": f"Not reachable at {ironclaw_url}"}

    @app.get("/api/model/config")
    async def api_model_config_get() -> dict:
        cfg = _load_model_config()
        ironclaw_info = _check_ironclaw()
        return {
            "provider": cfg.get("provider", "ironclaw"),
            "model": cfg.get("model", ""),
            "openrouter_api_key_set": bool(cfg.get("openrouter_api_key", "")),
            "openrouter_api_key_masked": _mask_key(cfg.get("openrouter_api_key", "")),
            "ollama_base_url": cfg.get("ollama_base_url", "http://localhost:11434"),
            "ironclaw_status": ironclaw_info.get("status", "unknown"),
            "ironclaw_details": ironclaw_info.get("details", ""),
            "available_models": {
                "ironclaw": _IRONCLAW_MODELS,
                "openrouter": _OPENROUTER_MODELS,
                "ollama": _OLLAMA_MODELS,
            },
        }

    @app.post("/api/model/config")
    async def api_model_config_post(request: Request) -> dict:
        body = await request.body()
        data = json.loads(body.decode("utf-8")) if body else {}
        cfg = _load_model_config()
        if "provider" in data:
            cfg["provider"] = data["provider"]
        if "model" in data:
            cfg["model"] = data["model"]
        if "openrouter_api_key" in data:
            cfg["openrouter_api_key"] = data["openrouter_api_key"]
        if "ollama_base_url" in data:
            cfg["ollama_base_url"] = data["ollama_base_url"]
        _save_model_config(cfg)
        if cfg.get("openrouter_api_key"):
            os.environ["OPENROUTER_API_KEY"] = cfg["openrouter_api_key"]
        if cfg.get("model"):
            os.environ["OPENROUTER_MODEL"] = cfg["model"]
        return {"ok": True, "provider": cfg["provider"], "model": cfg["model"]}

    # =======================================================================
    # Chat Sessions API
    # =======================================================================

    _SYSTEM_PROMPT = (
        "You are Claw Agent, a helpful developer platform assistant. "
        "You can discuss code, infrastructure, integrations (Slack, GitHub, Jira, Jenkins, Gmail, Confluence), "
        "workflows, events, and help with debugging. Be concise and practical."
    )

    async def _llm_chat(messages: list[dict]) -> str:
        cfg = _load_model_config()
        provider = cfg.get("provider", "ironclaw")
        model = cfg.get("model", "")

        if provider == "openrouter":
            api_key = cfg.get("openrouter_api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json={"model": model, "messages": messages},
                )
                resp.raise_for_status()
                choices = resp.json().get("choices", [])
                return choices[0]["message"]["content"] if choices else ""

        elif provider == "ollama":
            base_url = cfg.get("ollama_base_url", "http://localhost:11434")
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    f"{base_url.rstrip('/')}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                )
                resp.raise_for_status()
                return resp.json().get("message", {}).get("content", "")

        else:
            ironclaw_url = os.environ.get("IRONCLAW_URL", "http://127.0.0.1:3000").rstrip("/")
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{ironclaw_url}/v1/chat/completions",
                        json={"model": model, "messages": messages},
                    )
                    if resp.status_code == 200:
                        choices = resp.json().get("choices", [])
                        return choices[0]["message"]["content"] if choices else ""
            except Exception:
                pass
            api_key = cfg.get("openrouter_api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
            if api_key:
                fallback_model = cfg.get("model", "anthropic/claude-sonnet-4")
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": fallback_model, "messages": messages},
                    )
                    resp.raise_for_status()
                    choices = resp.json().get("choices", [])
                    return choices[0]["message"]["content"] if choices else ""
            return "(No LLM configured. Set an OpenRouter API key or start IronClaw to enable chat.)"

    @app.post("/api/chat/new")
    async def api_chat_new() -> dict:
        sid = str(uuid.uuid4())[:8]
        Session = get_session()
        with Session() as session:
            cs = ChatSession(session_id=sid, title="New Chat")
            session.add(cs)
            session.commit()
            return {"session_id": sid, "title": cs.title, "created_at": str(cs.created_at)}

    @app.get("/api/chat/sessions")
    async def api_chat_sessions(limit: int = 50) -> list:
        Session = get_session()
        with Session() as session:
            rows = session.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(limit).all()
            return [
                {
                    "session_id": r.session_id,
                    "title": r.title or "Untitled",
                    "created_at": str(r.created_at) if r.created_at else "",
                    "updated_at": str(r.updated_at) if r.updated_at else "",
                    "message_count": len(r.messages),
                }
                for r in rows
            ]

    @app.get("/api/chat/{session_id}/messages")
    async def api_chat_messages(session_id: str) -> list:
        Session = get_session()
        with Session() as session:
            rows = (
                session.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            return [
                {"id": r.id, "role": r.role, "content": r.content, "timestamp": str(r.created_at) if r.created_at else ""}
                for r in rows
            ]

    @app.post("/api/chat/{session_id}/send")
    async def api_chat_send(session_id: str, request: Request) -> dict:
        body = await request.body()
        data = json.loads(body.decode("utf-8")) if body else {}
        user_message = data.get("message", "").strip()
        if not user_message:
            return JSONResponse({"error": "Empty message"}, status_code=400)

        Session = get_session()
        with Session() as db:
            cs = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not cs:
                return JSONResponse({"error": "Session not found"}, status_code=404)
            db.add(ChatMessage(session_id=session_id, role="user", content=user_message))
            db.commit()
            if cs.title == "New Chat":
                cs.title = user_message[:60] + ("..." if len(user_message) > 60 else "")
                db.commit()
            context_msgs = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            )
            llm_messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
            for m in context_msgs:
                llm_messages.append({"role": m.role, "content": m.content})

        try:
            assistant_text = await _llm_chat(llm_messages)
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            assistant_text = f"(Error calling LLM: {e})"

        with Session() as db:
            assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=assistant_text)
            db.add(assistant_msg)
            cs = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if cs:
                cs.updated_at = datetime.now(timezone.utc)
            db.commit()
            return {"role": "assistant", "content": assistant_text, "timestamp": str(assistant_msg.created_at) if assistant_msg.created_at else ""}

    @app.delete("/api/chat/{session_id}")
    async def api_chat_delete(session_id: str) -> dict:
        Session = get_session()
        with Session() as db:
            db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            db.query(ChatSession).filter(ChatSession.session_id == session_id).delete()
            db.commit()
        return {"ok": True}

    # =======================================================================
    # Markets API
    # =======================================================================

    _market_cache: dict = {}
    _market_cache_ts: float = 0.0
    _history_cache: dict = {}
    _history_cache_ts: float = 0.0

    @app.get("/api/markets")
    async def api_markets() -> dict:
        nonlocal _market_cache, _market_cache_ts
        now = time.time()
        if _market_cache and (now - _market_cache_ts) < 30:
            return _market_cache

        assets: dict = {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true", "include_24hr_vol": "true", "include_market_cap": "true"},
                )
                if resp.status_code == 200:
                    btc = resp.json().get("bitcoin", {})
                    assets["btc"] = {"name": "Bitcoin", "symbol": "BTC", "price": btc.get("usd"), "change_24h": btc.get("usd_24h_change"), "volume_24h": btc.get("usd_24h_vol"), "market_cap": btc.get("usd_market_cap"), "source": "coingecko"}
                else:
                    assets["btc"] = {"name": "Bitcoin", "symbol": "BTC", "error": f"HTTP {resp.status_code}"}
            except Exception as e:
                assets["btc"] = {"name": "Bitcoin", "symbol": "BTC", "error": str(e)}

            for ticker, key, name, symbol in [("^GSPC", "sp500", "S&P 500", "SPX"), ("SI=F", "silver", "Silver Futures", "SI")]:
                try:
                    resp = await client.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                        params={"interval": "1d", "range": "2d"},
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    if resp.status_code == 200:
                        meta = resp.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
                        price = meta.get("regularMarketPrice")
                        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
                        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if price and prev_close else None
                        assets[key] = {"name": name, "symbol": symbol, "price": price, "previous_close": prev_close, "change_24h": change_pct, "currency": meta.get("currency", "USD"), "source": "yahoo"}
                    else:
                        assets[key] = {"name": name, "symbol": symbol, "error": f"HTTP {resp.status_code}"}
                except Exception as e:
                    assets[key] = {"name": name, "symbol": symbol, "error": str(e)}

        result = {"assets": assets, "updated_at": datetime.now(timezone.utc).isoformat()}
        _market_cache = result
        _market_cache_ts = now
        return result

    @app.get("/api/markets/history")
    async def api_markets_history() -> dict:
        nonlocal _history_cache, _history_cache_ts
        now = time.time()
        if _history_cache and (now - _history_cache_ts) < 3600:
            return _history_cache

        history: dict = {}
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
                    params={"vs_currency": "usd", "days": "30", "interval": "daily"},
                )
                if resp.status_code == 200:
                    prices = resp.json().get("prices", [])
                    history["btc"] = [
                        {"date": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d"), "close": round(price, 2)}
                        for ts, price in prices
                    ]
                else:
                    history["btc"] = []
            except Exception:
                history["btc"] = []

            for ticker, key in [("^GSPC", "sp500"), ("SI=F", "silver")]:
                try:
                    resp = await client.get(
                        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                        params={"interval": "1d", "range": "1mo"},
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    if resp.status_code == 200:
                        result_data = resp.json().get("chart", {}).get("result", [{}])[0]
                        timestamps = result_data.get("timestamp", [])
                        closes = result_data.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                        history[key] = [
                            {"date": datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d"), "close": round(c, 4) if c is not None else None}
                            for ts, c in zip(timestamps, closes)
                            if c is not None
                        ]
                    else:
                        history[key] = []
                except Exception:
                    history[key] = []

        result = {"history": history, "updated_at": datetime.now(timezone.utc).isoformat()}
        _history_cache = result
        _history_cache_ts = now
        return result

    # =======================================================================
    # Social Feeds API
    # =======================================================================

    @app.get("/api/feeds/x")
    async def api_feeds_x(limit: int = 20) -> dict:
        token = os.environ.get("X_BEARER_TOKEN", "")
        if not token:
            return {"configured": False, "posts": [], "error": "X_BEARER_TOKEN not set. Add it to .env to enable."}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                me_resp = await client.get("https://api.twitter.com/2/users/me", headers={"Authorization": f"Bearer {token}"})
                if me_resp.status_code != 200:
                    return {"configured": True, "posts": [], "error": f"X API: HTTP {me_resp.status_code}"}
                user_id = me_resp.json().get("data", {}).get("id", "")
                resp = await client.get(
                    f"https://api.twitter.com/2/users/{user_id}/timelines/reverse_chronological",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"max_results": min(limit, 100), "tweet.fields": "created_at,public_metrics,author_id,text", "expansions": "author_id", "user.fields": "name,username,profile_image_url"},
                )
                if resp.status_code != 200:
                    return {"configured": True, "posts": [], "error": f"X API: HTTP {resp.status_code}"}
                body = resp.json()
                users_map = {u["id"]: u for u in body.get("includes", {}).get("users", [])}
                posts = []
                for tweet in body.get("data", []):
                    author = users_map.get(tweet.get("author_id"), {})
                    posts.append({"id": tweet.get("id"), "text": tweet.get("text", ""), "created_at": tweet.get("created_at", ""), "author_name": author.get("name", ""), "author_username": author.get("username", ""), "author_avatar": author.get("profile_image_url", ""), "metrics": tweet.get("public_metrics", {})})
                return {"configured": True, "posts": posts}
        except Exception as e:
            return {"configured": True, "posts": [], "error": str(e)}

    @app.get("/api/feeds/linkedin")
    async def api_feeds_linkedin(limit: int = 20) -> dict:
        token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        if not token:
            return {"configured": False, "posts": [], "error": "LINKEDIN_ACCESS_TOKEN not set. Add it to .env to enable."}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get("https://api.linkedin.com/v2/feed", headers={"Authorization": f"Bearer {token}", "X-Restli-Protocol-Version": "2.0.0"}, params={"count": min(limit, 50)})
                if resp.status_code != 200:
                    return {"configured": True, "posts": [], "error": f"LinkedIn API: HTTP {resp.status_code}"}
                posts = []
                for elem in resp.json().get("elements", []):
                    posts.append({"id": elem.get("id", ""), "text": elem.get("commentary", elem.get("text", {}).get("text", "")), "created_at": "", "author": elem.get("actor", {}).get("name", {}).get("localized", {}).get("en_US", "")})
                return {"configured": True, "posts": posts}
        except Exception as e:
            return {"configured": True, "posts": [], "error": str(e)}

    # =======================================================================
    # Email Integration APIs
    # =======================================================================

    @app.get("/api/integrations/outlook/inbox")
    async def api_outlook_inbox(limit: int = 20) -> dict:
        token = os.environ.get("OUTLOOK_ACCESS_TOKEN", "")
        if not token:
            return {"configured": False, "messages": [], "error": "OUTLOOK_ACCESS_TOKEN not set. Add it to .env."}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"$top": min(limit, 50), "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview", "$orderby": "receivedDateTime desc"},
                )
                if resp.status_code != 200:
                    return {"configured": True, "messages": [], "error": f"Graph API: HTTP {resp.status_code}"}
                messages = []
                for m in resp.json().get("value", []):
                    sender = m.get("from", {}).get("emailAddress", {})
                    messages.append({"id": m.get("id", ""), "subject": m.get("subject", "(no subject)"), "from_name": sender.get("name", ""), "from_email": sender.get("address", ""), "received_at": m.get("receivedDateTime", ""), "is_read": m.get("isRead", False), "preview": m.get("bodyPreview", "")[:200]})
                return {"configured": True, "messages": messages}
        except Exception as e:
            return {"configured": True, "messages": [], "error": str(e)}

    @app.get("/api/integrations/zoho/inbox")
    async def api_zoho_inbox(limit: int = 20) -> dict:
        token = os.environ.get("ZOHO_ACCESS_TOKEN", "")
        account_id = os.environ.get("ZOHO_ACCOUNT_ID", "")
        if not token or not account_id:
            return {"configured": False, "messages": [], "error": "ZOHO_ACCESS_TOKEN and ZOHO_ACCOUNT_ID not set. Add to .env."}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"https://mail.zoho.com/api/accounts/{account_id}/messages/view",
                    headers={"Authorization": f"Zoho-oauthtoken {token}"},
                    params={"limit": min(limit, 50), "folderId": "inbox"},
                )
                if resp.status_code != 200:
                    return {"configured": True, "messages": [], "error": f"Zoho API: HTTP {resp.status_code}"}
                messages = []
                for m in resp.json().get("data", []):
                    messages.append({"id": m.get("messageId", ""), "subject": m.get("subject", "(no subject)"), "from_name": m.get("fromAddress", ""), "from_email": m.get("sender", ""), "received_at": m.get("receivedTime", ""), "is_read": m.get("status2", "") != "1", "preview": m.get("summary", "")[:200]})
                return {"configured": True, "messages": messages}
        except Exception as e:
            return {"configured": True, "messages": [], "error": str(e)}

    @app.get("/api/integrations/config")
    async def api_integrations_config() -> dict:
        return {
            "outlook": {"configured": bool(os.environ.get("OUTLOOK_ACCESS_TOKEN", ""))},
            "zoho": {"configured": bool(os.environ.get("ZOHO_ACCESS_TOKEN", "") and os.environ.get("ZOHO_ACCOUNT_ID", ""))},
            "x": {"configured": bool(os.environ.get("X_BEARER_TOKEN", ""))},
            "linkedin": {"configured": bool(os.environ.get("LINKEDIN_ACCESS_TOKEN", ""))},
            "slack": {"configured": bool(os.environ.get("SLACK_BOT_TOKEN", ""))},
            "github": {"configured": bool(os.environ.get("GITHUB_TOKEN", ""))},
            "jira": {"configured": bool(os.environ.get("JIRA_API_TOKEN", ""))},
            "jenkins": {"configured": bool(os.environ.get("JENKINS_API_TOKEN", ""))},
            "confluence": {"configured": bool(os.environ.get("CONFLUENCE_API_TOKEN", ""))},
            "gmail": {"configured": bool(os.environ.get("GMAIL_CREDENTIALS_FILE", ""))},
        }

    return app
