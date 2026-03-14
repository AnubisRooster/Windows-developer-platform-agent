"""
FastAPI webhook server - receives GitHub, Jira, Jenkins, Slack webhooks.
Validates signatures and publishes to EventBus.
Includes dashboard API routes for the frontend.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path

from datetime import UTC, datetime

import httpx
from fastapi import FastAPI, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database.models import ChatMessage, ChatSession, Event, WorkflowRun, get_session
from events.bus import EventBus
from events.types import AgentEvent, EventSource
from security.secrets import verify_webhook_signature
from workflows.loader import load_all_workflows

logger = logging.getLogger(__name__)

# Data directory for packaged mode (set by launcher). Falls back to ./data for dev.
def _get_data_dir() -> Path:
    env_dir = os.environ.get("CLAW_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return Path(__file__).resolve().parent.parent / "data"


def _get_dashboard_dir() -> Path | None:
    """Dashboard static files (Next.js export). Set CLAW_DASHBOARD_DIR or uses frontend/out."""
    env_dir = os.environ.get("CLAW_DASHBOARD_DIR")
    if env_dir:
        return Path(env_dir)
    # Dev: frontend/out relative to project root
    default = Path(__file__).resolve().parent.parent / "frontend" / "out"
    return default if default.exists() else None


app = FastAPI(title="Windows Developer Platform Webhooks")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_event_bus: EventBus | None = None


def set_event_bus(bus: EventBus) -> None:
    """Inject EventBus for webhook handlers."""
    global _event_bus
    _event_bus = bus


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "webhooks"}


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None),
    x_github_event: str | None = Header(None),
) -> Response:
    """
    GitHub webhook. Validates X-Hub-Signature-256 and publishes to EventBus.
    """
    if not _event_bus:
        return JSONResponse({"error": "EventBus not configured"}, status_code=503)
    body = await request.body()
    secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
    if secret and x_hub_signature_256 and not verify_webhook_signature(body, x_hub_signature_256, secret):
        return JSONResponse({"error": "Invalid signature"}, status_code=401)
    event_type = (x_github_event or "ping").replace(".", "_")
    payload = json.loads(body.decode("utf-8")) if body else {}
    action = payload.get("action", "opened")
    full_type = f"{payload.get('pull_request') and 'pull_request' or payload.get('issue') and 'issue' or 'push'}.{action}"
    full_type = full_type.replace(" ", "_")
    evt = AgentEvent(
        id=str(uuid.uuid4()),
        source=EventSource.github,
        event_type=full_type,
        payload=payload,
        timestamp=datetime.now(UTC),
    )
    _event_bus.publish(evt)
    return Response(status_code=200)


@app.post("/webhooks/jira")
async def jira_webhook(
    request: Request,
    x_atlassian_webhook_id: str | None = Header(None),
) -> Response:
    """
    Jira webhook. Publishes to EventBus. Add signature verification if Jira supports it.
    """
    if not _event_bus:
        return JSONResponse({"error": "EventBus not configured"}, status_code=503)
    body = await request.body()
    payload = json.loads(body.decode("utf-8")) if body else {}
    webhook_event = payload.get("webhookEvent", "jira:issue_created")
    event_type = webhook_event.replace("jira:", "").replace(":", ".").replace("_", ".")
    evt = AgentEvent(
        id=str(uuid.uuid4()),
        source=EventSource.jira,
        event_type=event_type,
        payload=payload,
        timestamp=datetime.now(UTC),
    )
    _event_bus.publish(evt)
    return Response(status_code=200)


@app.post("/webhooks/jenkins")
async def jenkins_webhook(
    request: Request,
) -> Response:
    """
    Jenkins webhook (generic). Publishes to EventBus.
    """
    if not _event_bus:
        return JSONResponse({"error": "EventBus not configured"}, status_code=503)
    body = await request.body()
    payload = json.loads(body.decode("utf-8")) if body else {}
    build_status = payload.get("build", {}).get("status", "unknown")
    evt = AgentEvent(
        id=str(uuid.uuid4()),
        source=EventSource.jenkins,
        event_type=f"build.{build_status}",
        payload=payload,
        timestamp=datetime.now(UTC),
    )
    _event_bus.publish(evt)
    return Response(status_code=200)


@app.post("/webhooks/slack")
async def slack_webhook(
    request: Request,
) -> Response:
    """
    Slack events/commands webhook. Publishes to EventBus.
    """
    if not _event_bus:
        return JSONResponse({"error": "EventBus not configured"}, status_code=503)
    body = await request.body()
    payload = json.loads(body.decode("utf-8")) if body else {}
    event_type = payload.get("type", "event") or "event"
    evt = AgentEvent(
        id=str(uuid.uuid4()),
        source=EventSource.slack,
        event_type=event_type,
        payload=payload,
        timestamp=datetime.now(UTC),
    )
    _event_bus.publish(evt)
    return Response(status_code=200)


# --- Dashboard API ---

def _check_ironclaw() -> dict:
    """Check if IronClaw runtime is reachable. Returns {status, details}."""
    url = os.environ.get("IRONCLAW_URL", "http://127.0.0.1:3000").rstrip("/")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{url}/api/health")
            if resp.status_code == 200:
                data = resp.json() if resp.content else {}
                status = data.get("status", "ok")
                channel = data.get("channel", "")
                detail = f"Running (channel={channel})" if channel else "Running"
                return {"status": "healthy", "details": detail}
            return {"status": "error", "details": f"HTTP {resp.status_code}"}
    except httpx.ConnectError:
        if openrouter_key:
            return {
                "status": "unavailable",
                "details": "IronClaw not running. OpenRouter fallback configured—AI will use OpenRouter.",
            }
        return {
            "status": "unavailable",
            "details": "IronClaw not running. Start it with 'ironclaw run', or add OPENROUTER_API_KEY to .env for fallback.",
        }
    except Exception as e:
        return {"status": "error", "details": str(e)}


@app.get("/api/status")
def api_status() -> dict:
    """Status for IronClaw, database, and integrations."""
    db_ok = False
    session = get_session()
    try:
        list(session.query(Event).limit(1).all())
        db_ok = True
    except Exception:
        pass
    finally:
        session.close()
    ironclaw = _check_ironclaw()
    return {
        "ironclaw": ironclaw,
        "database": {"status": "ok" if db_ok else "error", "details": ""},
        "integrations": {
            "slack": {"status": "connected" if os.environ.get("SLACK_BOT_TOKEN") else "unknown", "details": ""},
            "github": {"status": "connected" if os.environ.get("GITHUB_TOKEN") else "unknown", "details": ""},
            "jira": {"status": "connected" if os.environ.get("JIRA_API_TOKEN") else "unknown", "details": ""},
            "jenkins": {"status": "connected" if os.environ.get("JENKINS_API_TOKEN") else "unknown", "details": ""},
            "confluence": {"status": "connected" if os.environ.get("CONFLUENCE_API_TOKEN") else "unknown", "details": ""},
            "gmail": {"status": "connected" if os.environ.get("GMAIL_CREDENTIALS_FILE") else "unknown", "details": ""},
            "outlook": {"status": "connected" if os.environ.get("OUTLOOK_ACCESS_TOKEN") else "unknown", "details": ""},
            "zoho_mail": {"status": "connected" if os.environ.get("ZOHO_ACCESS_TOKEN") else "unknown", "details": ""},
            "x": {"status": "connected" if os.environ.get("X_BEARER_TOKEN") else "unknown", "details": ""},
            "linkedin": {"status": "connected" if os.environ.get("LINKEDIN_ACCESS_TOKEN") else "unknown", "details": ""},
        },
    }


@app.get("/api/events")
def api_events(limit: int = 50) -> list:
    session = get_session()
    try:
        rows = session.query(Event).order_by(Event.created_at.desc()).limit(limit).all()
        return [
            {
                "id": str(r.id),
                "source": r.source or "",
                "type": r.event_type or "",
                "time": str(r.timestamp) if r.timestamp else str(r.created_at) if r.created_at else "",
                "payload": json.loads(r.payload) if r.payload and isinstance(r.payload, str) else {},
            }
            for r in rows
        ]
    finally:
        session.close()


@app.get("/api/workflows")
def api_workflows() -> list:
    wf_dir = Path(__file__).resolve().parent.parent / "workflows"
    workflows = load_all_workflows(wf_dir)
    return [
        {
            "id": w.name,
            "name": w.name,
            "trigger": w.trigger,
            "description": w.description,
            "enabled": w.enabled,
            "actions": [{"tool": a.tool, "args": a.args} for a in w.actions],
        }
        for w in workflows
    ]


@app.get("/api/workflow-runs")
def api_workflow_runs(limit: int = 20) -> list:
    session = get_session()
    try:
        rows = session.query(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(limit).all()
        return [
            {
                "id": str(r.id),
                "workflow_name": r.workflow_name,
                "workflow_id": r.workflow_name,
                "status": (r.status or "unknown").lower(),
                "started_at": str(r.started_at) if r.started_at else "",
                "duration_ms": (
                    int((r.finished_at - r.started_at).total_seconds() * 1000)
                    if r.finished_at and r.started_at else None
                ),
            }
            for r in rows
        ]
    finally:
        session.close()


@app.get("/api/tools")
def api_tools() -> list:
    return [
        {"id": "slack.send_message", "name": "slack.send_message", "description": "Send message to Slack"},
        {"id": "github.create_issue", "name": "github.create_issue", "description": "Create GitHub issue"},
        {"id": "github.summarize_pull_request", "name": "github.summarize_pull_request", "description": "Summarize a PR"},
        {"id": "jira.create_ticket", "name": "jira.create_ticket", "description": "Create Jira ticket"},
        {"id": "jenkins.trigger_build", "name": "jenkins.trigger_build", "description": "Trigger Jenkins build"},
    ]


@app.get("/api/conversations")
def api_conversations(limit: int = 50) -> list:
    return []


# --- Model configuration ---

def _get_model_config_path() -> Path:
    return _get_data_dir() / "model_config.json"

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


@app.get("/api/model/config")
def api_model_config_get() -> dict:
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


# --- Chat API ---

_SYSTEM_PROMPT = (
    "You are Claw Agent, a helpful developer platform assistant. "
    "You can discuss code, infrastructure, integrations (Slack, GitHub, Jira, Jenkins, Gmail, Confluence), "
    "workflows, events, and help with debugging. Be concise and practical."
)


async def _llm_chat(messages: list[dict]) -> str:
    """Send messages to the configured LLM (OpenRouter or Ollama). Returns assistant text."""
    cfg = _load_model_config()
    provider = cfg.get("provider", "ironclaw")
    model = cfg.get("model", "")

    if provider == "openrouter":
        api_key = cfg.get("openrouter_api_key", "") or os.environ.get("OPENROUTER_API_KEY", "")
        base_url = "https://openrouter.ai/api/v1"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json={"model": model, "messages": messages},
            )
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            return choices[0]["message"]["content"] if choices else ""

    elif provider == "ollama":
        base_url = cfg.get("ollama_base_url", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url.rstrip('/')}/api/chat",
                json={"model": model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")

    else:
        # IronClaw gateway — try /v1/chat/completions or fall back to OpenRouter
        ironclaw_url = os.environ.get("IRONCLAW_URL", "http://127.0.0.1:3000").rstrip("/")
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{ironclaw_url}/v1/chat/completions",
                    json={"model": model, "messages": messages},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    choices = data.get("choices", [])
                    return choices[0]["message"]["content"] if choices else ""
        except Exception:
            pass
        # Fall back to OpenRouter if key is configured
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
                data = resp.json()
                choices = data.get("choices", [])
                return choices[0]["message"]["content"] if choices else ""
        return "(No LLM configured. Set an OpenRouter API key or start IronClaw to enable chat.)"


@app.post("/api/chat/new")
def api_chat_new() -> dict:
    """Create a new chat session with a fresh context window."""
    sid = str(uuid.uuid4())[:8]
    session = get_session()
    try:
        cs = ChatSession(session_id=sid, title="New Chat")
        session.add(cs)
        session.commit()
        return {"session_id": sid, "title": cs.title, "created_at": str(cs.created_at)}
    finally:
        session.close()


@app.get("/api/chat/sessions")
def api_chat_sessions(limit: int = 50) -> list:
    """List recent chat sessions (long-term memory)."""
    session = get_session()
    try:
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
    finally:
        session.close()


@app.get("/api/chat/{session_id}/messages")
def api_chat_messages(session_id: str) -> list:
    """Get all messages for a chat session."""
    session = get_session()
    try:
        rows = (
            session.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        return [
            {
                "id": r.id,
                "role": r.role,
                "content": r.content,
                "timestamp": str(r.created_at) if r.created_at else "",
            }
            for r in rows
        ]
    finally:
        session.close()


@app.post("/api/chat/{session_id}/send")
async def api_chat_send(session_id: str, request: Request) -> dict:
    """Send a message in a chat session. Returns the assistant's reply.
    Only the current session's messages are in the context window."""
    body = await request.body()
    data = json.loads(body.decode("utf-8")) if body else {}
    user_message = data.get("message", "").strip()
    if not user_message:
        return JSONResponse({"error": "Empty message"}, status_code=400)

    db = get_session()
    try:
        cs = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not cs:
            return JSONResponse({"error": "Session not found"}, status_code=404)

        # Persist user message
        user_msg = ChatMessage(session_id=session_id, role="user", content=user_message)
        db.add(user_msg)
        db.commit()

        # Auto-title from first user message
        if cs.title == "New Chat":
            cs.title = user_message[:60] + ("..." if len(user_message) > 60 else "")
            db.commit()

        # Build context window: system prompt + this session's messages only
        context_msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        llm_messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        for m in context_msgs:
            llm_messages.append({"role": m.role, "content": m.content})
    finally:
        db.close()

    # Call LLM
    try:
        assistant_text = await _llm_chat(llm_messages)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        assistant_text = f"(Error calling LLM: {e})"

    # Persist assistant reply
    db = get_session()
    try:
        assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=assistant_text)
        db.add(assistant_msg)
        cs = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if cs:
            cs.updated_at = datetime.now(UTC)
        db.commit()
        return {
            "role": "assistant",
            "content": assistant_text,
            "timestamp": str(assistant_msg.created_at) if assistant_msg.created_at else "",
        }
    finally:
        db.close()


@app.delete("/api/chat/{session_id}")
def api_chat_delete(session_id: str) -> dict:
    """Delete a chat session and all its messages."""
    db = get_session()
    try:
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.query(ChatSession).filter(ChatSession.session_id == session_id).delete()
        db.commit()
        return {"ok": True}
    finally:
        db.close()


@app.get("/api/logs")
def api_logs(level: str | None = None, limit: int = 100) -> list:
    return []


# --- Market Data API ---

_MARKET_CACHE: dict = {}
_MARKET_CACHE_TS: float = 0.0


@app.get("/api/markets")
async def api_markets() -> dict:
    """Real-time market prices for BTC, S&P 500, and Silver futures."""
    import time

    global _MARKET_CACHE, _MARKET_CACHE_TS
    now = time.time()
    if _MARKET_CACHE and (now - _MARKET_CACHE_TS) < 30:
        return _MARKET_CACHE

    assets: dict = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Bitcoin via CoinGecko (free, no key)
        try:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": "bitcoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_24hr_vol": "true",
                    "include_market_cap": "true",
                },
            )
            if resp.status_code == 200:
                btc = resp.json().get("bitcoin", {})
                assets["btc"] = {
                    "name": "Bitcoin",
                    "symbol": "BTC",
                    "price": btc.get("usd"),
                    "change_24h": btc.get("usd_24h_change"),
                    "volume_24h": btc.get("usd_24h_vol"),
                    "market_cap": btc.get("usd_market_cap"),
                    "source": "coingecko",
                }
            else:
                assets["btc"] = {"name": "Bitcoin", "symbol": "BTC", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            logger.warning("CoinGecko BTC fetch failed: %s", e)
            assets["btc"] = {"name": "Bitcoin", "symbol": "BTC", "error": str(e)}

        # S&P 500 via Yahoo Finance chart API
        for ticker, key, name, symbol in [
            ("^GSPC", "sp500", "S&P 500", "SPX"),
            ("SI=F", "silver", "Silver Futures", "SI"),
        ]:
            try:
                resp = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                    params={"interval": "1d", "range": "2d"},
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                    price = meta.get("regularMarketPrice")
                    prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
                    change_pct = None
                    if price and prev_close:
                        change_pct = round(((price - prev_close) / prev_close) * 100, 2)
                    assets[key] = {
                        "name": name,
                        "symbol": symbol,
                        "price": price,
                        "previous_close": prev_close,
                        "change_24h": change_pct,
                        "currency": meta.get("currency", "USD"),
                        "source": "yahoo",
                    }
                else:
                    assets[key] = {"name": name, "symbol": symbol, "error": f"HTTP {resp.status_code}"}
            except Exception as e:
                logger.warning("Yahoo %s fetch failed: %s", ticker, e)
                assets[key] = {"name": name, "symbol": symbol, "error": str(e)}

    result = {"assets": assets, "updated_at": datetime.now(UTC).isoformat()}
    _MARKET_CACHE = result
    _MARKET_CACHE_TS = now
    return result


_HISTORY_CACHE: dict = {}
_HISTORY_CACHE_TS: float = 0.0


@app.get("/api/markets/history")
async def api_markets_history() -> dict:
    """30-day daily close history for BTC, S&P 500, and Silver futures."""
    import time

    global _HISTORY_CACHE, _HISTORY_CACHE_TS
    now = time.time()
    if _HISTORY_CACHE and (now - _HISTORY_CACHE_TS) < 3600:
        return _HISTORY_CACHE

    history: dict = {}

    async with httpx.AsyncClient(timeout=15.0) as client:
        # Bitcoin 30-day history via CoinGecko
        try:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
                params={"vs_currency": "usd", "days": "30", "interval": "daily"},
            )
            if resp.status_code == 200:
                prices = resp.json().get("prices", [])
                history["btc"] = [
                    {"date": datetime.fromtimestamp(ts / 1000, tz=UTC).strftime("%Y-%m-%d"), "close": round(price, 2)}
                    for ts, price in prices
                ]
            else:
                history["btc"] = []
        except Exception as e:
            logger.warning("CoinGecko history failed: %s", e)
            history["btc"] = []

        # S&P 500 and Silver 30-day history via Yahoo Finance
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
                        {
                            "date": datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d"),
                            "close": round(c, 4) if c is not None else None,
                        }
                        for ts, c in zip(timestamps, closes)
                        if c is not None
                    ]
                else:
                    history[key] = []
            except Exception as e:
                logger.warning("Yahoo history %s failed: %s", ticker, e)
                history[key] = []

    result = {"history": history, "updated_at": datetime.now(UTC).isoformat()}
    _HISTORY_CACHE = result
    _HISTORY_CACHE_TS = now
    return result


# --- Social Feeds API ---

@app.get("/api/feeds/x")
async def api_feeds_x(limit: int = 20) -> dict:
    """Fetch X (Twitter) home timeline. Requires X_BEARER_TOKEN."""
    token = os.environ.get("X_BEARER_TOKEN", "")
    if not token:
        return {"configured": False, "posts": [], "error": "X_BEARER_TOKEN not set. Add it to .env to enable."}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Get authenticated user ID first
            me_resp = await client.get(
                "https://api.twitter.com/2/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if me_resp.status_code == 401:
                return {"configured": True, "posts": [], "error": "Invalid X_BEARER_TOKEN."}
            if me_resp.status_code != 200:
                return {"configured": True, "posts": [], "error": f"X API: HTTP {me_resp.status_code}"}
            user_id = me_resp.json().get("data", {}).get("id", "")

            resp = await client.get(
                f"https://api.twitter.com/2/users/{user_id}/timelines/reverse_chronological",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "max_results": min(limit, 100),
                    "tweet.fields": "created_at,public_metrics,author_id,text",
                    "expansions": "author_id",
                    "user.fields": "name,username,profile_image_url",
                },
            )
            if resp.status_code != 200:
                return {"configured": True, "posts": [], "error": f"X API: HTTP {resp.status_code}"}
            body = resp.json()
            users_map = {}
            for u in body.get("includes", {}).get("users", []):
                users_map[u["id"]] = u
            posts = []
            for tweet in body.get("data", []):
                author = users_map.get(tweet.get("author_id"), {})
                posts.append({
                    "id": tweet.get("id"),
                    "text": tweet.get("text", ""),
                    "created_at": tweet.get("created_at", ""),
                    "author_name": author.get("name", ""),
                    "author_username": author.get("username", ""),
                    "author_avatar": author.get("profile_image_url", ""),
                    "metrics": tweet.get("public_metrics", {}),
                })
            return {"configured": True, "posts": posts}
    except Exception as e:
        return {"configured": True, "posts": [], "error": str(e)}


@app.get("/api/feeds/linkedin")
async def api_feeds_linkedin(limit: int = 20) -> dict:
    """Fetch LinkedIn feed. Requires LINKEDIN_ACCESS_TOKEN (OAuth2)."""
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
    if not token:
        return {"configured": False, "posts": [], "error": "LINKEDIN_ACCESS_TOKEN not set. Add it to .env to enable."}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.linkedin.com/v2/feed",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                params={"count": min(limit, 50)},
            )
            if resp.status_code == 401:
                return {"configured": True, "posts": [], "error": "Invalid or expired LINKEDIN_ACCESS_TOKEN."}
            if resp.status_code != 200:
                return {"configured": True, "posts": [], "error": f"LinkedIn API: HTTP {resp.status_code}"}
            body = resp.json()
            posts = []
            for elem in body.get("elements", []):
                posts.append({
                    "id": elem.get("id", ""),
                    "text": elem.get("commentary", elem.get("text", {}).get("text", "")),
                    "created_at": "",
                    "author": elem.get("actor", {}).get("name", {}).get("localized", {}).get("en_US", ""),
                })
            return {"configured": True, "posts": posts}
    except Exception as e:
        return {"configured": True, "posts": [], "error": str(e)}


# --- Email Integration APIs ---

@app.get("/api/integrations/outlook/inbox")
async def api_outlook_inbox(limit: int = 20) -> dict:
    """Fetch Outlook inbox via Microsoft Graph API. Requires OUTLOOK_ACCESS_TOKEN."""
    token = os.environ.get("OUTLOOK_ACCESS_TOKEN", "")
    if not token:
        return {"configured": False, "messages": [], "error": "OUTLOOK_ACCESS_TOKEN not set. Add it to .env."}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "$top": min(limit, 50),
                    "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
                    "$orderby": "receivedDateTime desc",
                },
            )
            if resp.status_code == 401:
                return {"configured": True, "messages": [], "error": "Invalid or expired OUTLOOK_ACCESS_TOKEN."}
            if resp.status_code != 200:
                return {"configured": True, "messages": [], "error": f"Graph API: HTTP {resp.status_code}"}
            body = resp.json()
            messages = []
            for m in body.get("value", []):
                sender = m.get("from", {}).get("emailAddress", {})
                messages.append({
                    "id": m.get("id", ""),
                    "subject": m.get("subject", "(no subject)"),
                    "from_name": sender.get("name", ""),
                    "from_email": sender.get("address", ""),
                    "received_at": m.get("receivedDateTime", ""),
                    "is_read": m.get("isRead", False),
                    "preview": m.get("bodyPreview", "")[:200],
                })
            return {"configured": True, "messages": messages}
    except Exception as e:
        return {"configured": True, "messages": [], "error": str(e)}


@app.get("/api/integrations/zoho/inbox")
async def api_zoho_inbox(limit: int = 20) -> dict:
    """Fetch Zoho Mail inbox. Requires ZOHO_ACCESS_TOKEN and ZOHO_ACCOUNT_ID."""
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
            if resp.status_code == 401:
                return {"configured": True, "messages": [], "error": "Invalid or expired ZOHO_ACCESS_TOKEN."}
            if resp.status_code != 200:
                return {"configured": True, "messages": [], "error": f"Zoho API: HTTP {resp.status_code}"}
            body = resp.json()
            messages = []
            for m in body.get("data", []):
                messages.append({
                    "id": m.get("messageId", ""),
                    "subject": m.get("subject", "(no subject)"),
                    "from_name": m.get("fromAddress", ""),
                    "from_email": m.get("sender", ""),
                    "received_at": m.get("receivedTime", ""),
                    "is_read": m.get("status2", "") != "1",
                    "preview": m.get("summary", "")[:200],
                })
            return {"configured": True, "messages": messages}
    except Exception as e:
        return {"configured": True, "messages": [], "error": str(e)}


# --- Integration config endpoint ---

@app.get("/api/integrations/config")
def api_integrations_config() -> dict:
    """Returns which integrations have API keys configured."""
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


# --- Static dashboard (when frontend/out or CLAW_DASHBOARD_DIR exists) ---
_dashboard_dir = _get_dashboard_dir()
if _dashboard_dir and (_dashboard_dir / "index.html").exists():
    _next_dir = _dashboard_dir / "_next"
    if _next_dir.exists():
        app.mount("/_next", StaticFiles(directory=_next_dir), name="next_static")

    @app.get("/{full_path:path}")
    def _serve_dashboard(full_path: str):
        from fastapi import HTTPException
        if full_path.startswith("api/") or full_path.startswith("webhooks/") or full_path == "health" or full_path.startswith("_next/"):
            raise HTTPException(404)
        safe = full_path.strip("/").replace("..", "").replace("\\", "")
        if not safe:
            return FileResponse(_dashboard_dir / "index.html")
        base = _dashboard_dir / safe
        if base.exists() and base.is_file():
            return FileResponse(base)
        html_path = base.with_suffix(".html") if not base.suffix else base
        if html_path.exists() and html_path.is_file():
            return FileResponse(html_path)
        index_path = _dashboard_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise HTTPException(404)
