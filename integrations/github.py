"""GitHub client integration."""

from __future__ import annotations


class GitHubClient:
    """GitHub API client wrapper."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or ""
