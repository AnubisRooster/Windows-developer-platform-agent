"""Jira client integration."""

from __future__ import annotations


class JiraClient:
    """Jira API client wrapper."""

    def __init__(
        self,
        url: str | None = None,
        user: str | None = None,
        api_token: str | None = None,
    ) -> None:
        self.url = url or ""
        self.user = user or ""
        self.api_token = api_token or ""
