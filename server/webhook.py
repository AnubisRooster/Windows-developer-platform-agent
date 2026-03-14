"""
Webhook server - receives events from Slack, GitHub, Jira, Jenkins.
Uses pathlib.Path for all file paths (Windows-compatible).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(
    orchestrator: Any,
    config: dict[str, Any] | None = None,
) -> FastAPI:
    """Create FastAPI webhook application."""
    config = config or {}
    app = FastAPI(title="Windows Developer Platform Agent Webhooks")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "platform": "windows"}

    @app.post("/webhooks/github")
    async def github_webhook(request: Request) -> Response:
        secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
        body = await request.body()
        payload = await request.json()
        return JSONResponse({"received": True, "source": "github"})

    @app.post("/webhooks/jira")
    async def jira_webhook(request: Request) -> Response:
        payload = await request.json()
        return JSONResponse({"received": True, "source": "jira"})

    @app.post("/webhooks/jenkins")
    async def jenkins_webhook(request: Request) -> Response:
        payload = await request.json()
        return JSONResponse({"received": True, "source": "jenkins"})

    @app.post("/webhooks/slack")
    async def slack_webhook(request: Request) -> Response:
        payload = await request.json()
        return JSONResponse({"received": True, "source": "slack"})

    return app
