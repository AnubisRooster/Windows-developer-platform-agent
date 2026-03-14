"""
Jira integration - create_ticket, update_ticket, link_github_issue, get_ticket_details.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_config() -> tuple[str, str, str]:
    url = os.environ.get("JIRA_URL", "").rstrip("/")
    user = os.environ.get("JIRA_USER", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    return url, user, token


def _api(
    method: str,
    path: str,
    *,
    json_data: dict | None = None,
) -> dict[str, Any]:
    """Call Jira REST API."""
    base_url, user, token = _get_config()
    if not base_url or not user or not token:
        logger.warning("JIRA_URL, JIRA_USER, JIRA_API_TOKEN required")
        return {}
    url = f"{base_url}/rest/api/3{path}"
    auth = (user, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, auth=auth, headers=headers, json=json_data)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


def create_ticket(
    project: str,
    summary: str,
    description: str = "",
    issue_type: str = "Task",
) -> dict[str, Any]:
    """Create a Jira ticket."""
    payload = {
        "fields": {
            "project": {"key": project},
            "summary": summary,
            "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": description or summary}]}]},
            "issuetype": {"name": issue_type},
        }
    }
    return _api("POST", "/issue", json_data=payload)


def update_ticket(ticket_key: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Update a Jira ticket's fields."""
    return _api("PUT", f"/issue/{ticket_key}", json_data={"fields": fields})


def link_github_issue(ticket_key: str, github_url: str) -> dict[str, Any]:
    """Link a GitHub URL to a Jira ticket (as remote link)."""
    base_url = _get_config()[0]
    payload = {
        "object": {"url": github_url, "title": "GitHub"},
    }
    return _api("POST", f"/issue/{ticket_key}/remotelink", json_data=payload)


def get_ticket_details(ticket_key: str) -> dict[str, Any]:
    """Get full ticket details."""
    return _api("GET", f"/issue/{ticket_key}")
