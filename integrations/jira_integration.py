"""
Jira integration using jira library.
Platform-agnostic.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from jira import JIRA
from jira.exceptions import JIRAError

logger = logging.getLogger(__name__)


def _get_client() -> JIRA:
    """Get Jira client from env."""
    server = os.environ.get("JIRA_SERVER", "")
    token = os.environ.get("JIRA_API_TOKEN", "")
    email = os.environ.get("JIRA_EMAIL", "")
    if not all([server, token, email]):
        raise ValueError("JIRA_SERVER, JIRA_API_TOKEN, JIRA_EMAIL environment variables are required")
    return JIRA(server=server, token_auth=token)


def create_ticket(
    project: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> dict[str, Any]:
    """
    Create a Jira ticket.

    Args:
        project: Project key (e.g. PROJ).
        summary: Ticket summary/title.
        description: Ticket description.
        issue_type: Issue type (Task, Bug, Story, etc.).

    Returns:
        Dict with key, id, self.
    """
    try:
        jira = _get_client()
        issue = jira.create_issue(
            project=project,
            summary=summary,
            description=description,
            issuetype={"name": issue_type},
        )
        return {"key": issue.key, "id": issue.id, "self": issue.self}
    except JIRAError as e:
        logger.exception("Jira create_ticket failed: %s", e)
        raise


def update_ticket(ticket_key: str, fields: dict[str, Any]) -> dict[str, Any]:
    """
    Update a Jira ticket with given fields.

    Args:
        ticket_key: Issue key (e.g. PROJ-123).
        fields: Dict of field names to values (summary, description, etc.).

    Returns:
        Updated issue dict.
    """
    try:
        jira = _get_client()
        issue = jira.issue(ticket_key)
        issue.update(fields=fields)
        return {"key": issue.key, "fields": dict(issue.fields)}
    except JIRAError as e:
        logger.exception("Jira update_ticket failed: %s", e)
        raise


def link_github_issue(ticket_key: str, github_url: str) -> None:
    """
    Link a Jira ticket to a GitHub issue/PR URL.

    Args:
        ticket_key: Jira issue key.
        github_url: Full GitHub issue or PR URL.
    """
    try:
        jira = _get_client()
        jira.add_simple_link(ticket_key, {"url": github_url, "title": "GitHub"})
    except JIRAError as e:
        logger.exception("Jira link_github_issue failed: %s", e)
        raise


def get_ticket_details(ticket_key: str) -> dict[str, Any]:
    """
    Get full details of a Jira ticket.

    Args:
        ticket_key: Issue key.

    Returns:
        Dict with key, summary, description, status, assignee, etc.
    """
    try:
        jira = _get_client()
        issue = jira.issue(ticket_key)
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": getattr(issue.fields, "description") or "",
            "status": str(issue.fields.status),
            "assignee": str(issue.fields.assignee) if issue.fields.assignee else None,
            "created": str(issue.fields.created),
            "updated": str(issue.fields.updated),
        }
    except JIRAError as e:
        logger.exception("Jira get_ticket_details failed: %s", e)
        raise
