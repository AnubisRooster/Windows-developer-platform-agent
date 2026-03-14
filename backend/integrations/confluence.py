"""
Confluence integration - search_docs, summarize_page, create_page.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_config() -> tuple[str, str, str]:
    url = os.environ.get("CONFLUENCE_URL", "").rstrip("/")
    user = os.environ.get("CONFLUENCE_USER", "")
    token = os.environ.get("CONFLUENCE_API_TOKEN", "")
    return url, user, token


def _api(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json_data: dict | None = None,
) -> dict[str, Any]:
    """Call Confluence REST API."""
    base_url, user, token = _get_config()
    if not base_url or not user or not token:
        logger.warning("CONFLUENCE_URL, CONFLUENCE_USER, CONFLUENCE_API_TOKEN required")
        return {}
    url = f"{base_url}/rest/api{path}"
    auth = (user, token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, auth=auth, headers=headers, params=params, json=json_data)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


def search_docs(cql: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search Confluence using CQL."""
    data = _api("GET", "/content/search", params={"cql": cql, "limit": limit})
    return data.get("results", [])


def summarize_page(page_id: str) -> str:
    """Fetch a page and return a text summary (title + body excerpt)."""
    data = _api("GET", f"/content/{page_id}", params={"expand": "body.storage"})
    title = data.get("title", "")
    body = data.get("body", {}).get("storage", {}).get("value", "")
    # Strip HTML for plain text summary
    import re
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()[:500]
    return f"{title}: {text}..."


def create_page(
    space_key: str,
    title: str,
    body: str,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """Create a Confluence page."""
    payload: dict[str, Any] = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": body, "representation": "storage"}},
    }
    if parent_id:
        payload["ancestors"] = [{"id": parent_id}]
    return _api("POST", "/content", json_data=payload)
