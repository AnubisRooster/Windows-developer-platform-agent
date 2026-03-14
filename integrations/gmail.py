"""
Gmail integration using google-api-python-client.
Platform-agnostic. Requires OAuth2 credentials.
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.modify"]


def _get_service():
    """Get Gmail API service with OAuth credentials."""
    creds = None
    token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", "token.json"))
    creds_path = Path(os.environ.get("GMAIL_CREDS_PATH", "credentials.json"))
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif creds_path.exists():
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            raise ValueError(
                "Gmail requires credentials.json and token.json. Set GMAIL_CREDS_PATH and GMAIL_TOKEN_PATH."
            )
        if token_path:
            with open(token_path, "w") as f:
                f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def read_emails(
    query: str = "is:unread",
    max_results: int = 10,
) -> list[dict[str, Any]]:
    """
    Read emails matching query.

    Args:
        query: Gmail search query (default: unread).
        max_results: Max messages to return.

    Returns:
        List of dicts with id, threadId, snippet, subject, from.
    """
    try:
        service = _get_service()
        results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        out = []
        for m in messages:
            msg = service.users().messages().get(userId="me", id=m["id"]).execute()
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            out.append({
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "snippet": msg.get("snippet", ""),
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
            })
        return out
    except HttpError as e:
        logger.exception("Gmail read_emails failed: %s", e)
        raise


def summarize_thread(thread_id: str) -> str:
    """
    Fetch a thread and return a text summary.

    Args:
        thread_id: Gmail thread ID.

    Returns:
        Summary string with subject and message snippets.
    """
    try:
        service = _get_service()
        thread = service.users().threads().get(userId="me", id=thread_id).execute()
        messages = thread.get("messages", [])
        parts = []
        for m in messages:
            headers = {h["name"]: h["value"] for h in m.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject", "(no subject)")
            snippet = m.get("snippet", "")
            parts.append(f"From: {headers.get('From', '')}\nSubject: {subject}\n{snippet}")
        return "\n---\n".join(parts)
    except HttpError as e:
        logger.exception("Gmail summarize_thread failed: %s", e)
        raise


def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """
    Send an email.

    Args:
        to: Recipient email.
        subject: Subject line.
        body: Plain text body.

    Returns:
        Dict with id, threadId, labelIds.
    """
    try:
        service = _get_service()
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"id": sent["id"], "threadId": sent.get("threadId"), "labelIds": sent.get("labelIds", [])}
    except HttpError as e:
        logger.exception("Gmail send_email failed: %s", e)
        raise


def extract_action_items(thread_id: str) -> list[str]:
    """
    Fetch thread and extract action items (heuristic: lines with TODO, FIXME, ACTION, etc.).

    Args:
        thread_id: Gmail thread ID.

    Returns:
        List of action item strings.
    """
    try:
        summary = summarize_thread(thread_id)
        keywords = ["TODO", "FIXME", "ACTION", "PLEASE", "NEED", "MUST", "SHOULD"]
        items = []
        for line in summary.split("\n"):
            line = line.strip()
            for kw in keywords:
                if kw in line.upper():
                    items.append(line[:200])
                    break
        return items[:10]  # Limit to 10
    except HttpError as e:
        logger.exception("Gmail extract_action_items failed: %s", e)
        raise
