"""
Confluence integration using atlassian-python-api.
Platform-agnostic.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from atlassian import Confluence

logger = logging.getLogger(__name__)


def _get_client() -> Confluence:
    """Get Confluence client from env."""
    url = os.environ.get("CONFLUENCE_URL", "")
    token = os.environ.get("CONFLUENCE_TOKEN", "")
    email = os.environ.get("CONFLUENCE_EMAIL", "")
    if not all([url, token, email]):
        raise ValueError("CONFLUENCE_URL, CONFLUENCE_TOKEN, CONFLUENCE_EMAIL environment variables are required")
    return Confluence(url=url, token=token, email=email)


def search_docs(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search Confluence for documents matching query.

    Args:
        query: Search query string.
        limit: Max results to return.

    Returns:
        List of dicts with title, id, type, _links.
    """
    try:
        confluence = _get_client()
        results = confluence.cql(f'text ~ "{query}"', limit=limit)
        hits = results.get("results", [])
        return [
            {
                "title": h.get("content", {}).get("title"),
                "id": h.get("content", {}).get("id"),
                "type": h.get("content", {}).get("type"),
                "_links": h.get("content", {}).get("_links", {}),
            }
            for h in hits
        ]
    except Exception as e:
        logger.exception("Confluence search_docs failed: %s", e)
        raise


def summarize_page(page_id: str) -> str:
    """
    Fetch a Confluence page and return a text summary.

    Args:
        page_id: Confluence page ID.

    Returns:
        Summary string (title + first 500 chars of body).
    """
    try:
        confluence = _get_client()
        page = confluence.get_page_by_id(page_id, expand="body.storage")
        if not page:
            return "Page not found."
        title = page.get("title", "")
        body = page.get("body", {}).get("storage", {}).get("value", "")
        # Strip HTML for plain text
        import re
        text = re.sub(r"<[^>]+>", " ", body)
        text = re.sub(r"\s+", " ", text).strip()
        excerpt = text[:500] + "..." if len(text) > 500 else text
        return f"# {title}\n\n{excerpt}"
    except Exception as e:
        logger.exception("Confluence summarize_page failed: %s", e)
        raise


def create_page(space: str, title: str, body: str) -> dict[str, Any]:
    """
    Create a new Confluence page.

    Args:
        space: Space key (e.g. DOC).
        title: Page title.
        body: Page body in storage format (HTML).

    Returns:
        Dict with id, _links.
    """
    try:
        confluence = _get_client()
        result = confluence.create_page(space=space, title=title, body=body)
        return {"id": result.get("id"), "_links": result.get("_links", {})}
    except Exception as e:
        logger.exception("Confluence create_page failed: %s", e)
        raise
