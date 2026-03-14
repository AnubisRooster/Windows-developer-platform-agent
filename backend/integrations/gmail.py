"""
Gmail integration - read_emails, summarize_thread, send_email, extract_action_items.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _get_credentials_path() -> Path:
    p = os.environ.get("GMAIL_CREDENTIALS_FILE", "credentials.json")
    return Path(p) if os.path.isabs(p) else Path.cwd() / p


def _get_token_path() -> Path:
    p = os.environ.get("GMAIL_TOKEN_FILE", "token.json")
    return Path(p) if os.path.isabs(p) else Path.cwd() / p


def _get_service():
    """Get Gmail API service (lazy import)."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds_path = _get_credentials_path()
    token_path = _get_token_path()
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ]
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(f"Credentials file not found: {creds_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with token_path.open("w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def read_emails(query: str = "in:inbox", max_results: int = 10) -> list[dict[str, Any]]:
    """Read emails matching query."""
    try:
        service = _get_service()
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        out = []
        for m in messages:
            msg = service.users().messages().get(userId="me", id=m["id"]).execute()
            payload = msg.get("payload", {})
            headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
            out.append({
                "id": msg["id"],
                "subject": headers.get("subject", ""),
                "from": headers.get("from", ""),
                "snippet": msg.get("snippet", ""),
            })
        return out
    except Exception as e:
        logger.exception("read_emails failed: %s", e)
        return []


def summarize_thread(thread_id: str) -> str:
    """Fetch a thread and return a summary of messages."""
    try:
        service = _get_service()
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        msgs = thread.get("messages", [])
        parts = []
        for m in msgs:
            payload = m.get("payload", {})
            headers = {h["name"].lower(): h["value"] for h in payload.get("headers", [])}
            parts.append(f"From: {headers.get('from')} - {m.get('snippet', '')}")
        return "\n".join(parts)
    except Exception as e:
        logger.exception("summarize_thread failed: %s", e)
        return ""


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email."""
    import base64
    from email.mime.text import MIMEText

    try:
        service = _get_service()
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"id": result.get("id"), "status": "sent"}
    except Exception as e:
        logger.exception("send_email failed: %s", e)
        return {"status": "error", "error": str(e)}


def extract_action_items(text: str) -> list[str]:
    """Extract action items from email/thread text (simple heuristic)."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        lower = line.lower()
        if any(kw in lower for kw in ["action:", "todo:", "to do:", "- [ ]", "[ ]", "follow up", "follow-up"]):
            items.append(line)
        elif line.startswith("-") or line.startswith("*"):
            items.append(line.lstrip("-* ").strip())
    return items[:20]
