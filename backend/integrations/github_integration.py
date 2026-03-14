"""
GitHub integration - create_issue, summarize_pull_request, comment_on_pr, create_branch, get_repo_activity.

Same API as root integrations/github but adapted for backend (config from env).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_token() -> str:
    return os.environ.get("GITHUB_TOKEN", "")


def _api(
    method: str,
    path: str,
    *,
    json_data: dict | None = None,
    params: dict | None = None,
) -> dict[str, Any]:
    """Call GitHub REST API."""
    token = _get_token()
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, headers=headers, json=json_data, params=params)
        resp.raise_for_status()
        return resp.json() if resp.content else {}


def create_issue(
    repo: str,
    title: str,
    body: str = "",
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a GitHub issue."""
    path = f"/repos/{repo}/issues"
    data: dict[str, Any] = {"title": title, "body": body}
    if labels:
        data["labels"] = labels
    return _api("POST", path, json_data=data)


def summarize_pull_request(owner: str, repo: str, pr_number: int | str) -> str:
    """Fetch PR details and return a summary string."""
    pr_num = int(pr_number) if isinstance(pr_number, str) else pr_number
    path = f"/repos/{owner}/{repo}/pulls/{pr_num}"
    pr = _api("GET", path)
    title = pr.get("title", "")
    body = pr.get("body", "")
    user = pr.get("user", {}).get("login", "unknown")
    state = pr.get("state", "open")
    head = pr.get("head", {}).get("ref", "")
    base = pr.get("base", {}).get("ref", "")

    # Fetch files changed
    files_path = f"/repos/{owner}/{repo}/pulls/{pr_num}/files"
    try:
        files = _api("GET", files_path)
        file_list = [f.get("filename", "") for f in files] if isinstance(files, list) else []
        files_summary = ", ".join(file_list[:10])
        if len(file_list) > 10:
            files_summary += f" (+{len(file_list) - 10} more)"
    except Exception:
        files_summary = "N/A"

    return (
        f"PR #{pr_num}: {title}\n"
        f"By: {user} | State: {state}\n"
        f"Branch: {head} → {base}\n"
        f"Files: {files_summary}\n"
        f"Description: {(body or '')[:200]}..."
    )


def comment_on_pr(owner: str, repo: str, pr_number: int, body: str) -> dict[str, Any]:
    """Post a comment on a pull request."""
    path = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
    return _api("POST", path, json_data={"body": body})


def create_branch(owner: str, repo: str, branch: str, from_ref: str = "HEAD") -> dict[str, Any]:
    """Create a new branch from a ref."""
    ref_path = f"/repos/{owner}/{repo}/git/refs/heads/{from_ref}"
    try:
        ref_data = _api("GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_ref}")
    except Exception:
        ref_data = _api("GET", f"/repos/{owner}/{repo}/git/refs/heads/main")
    sha = ref_data.get("object", {}).get("sha") if isinstance(ref_data.get("object"), dict) else ref_data.get("object", {}).get("sha")
    if not sha and "refs/" in str(ref_data):
        ref_data = _api("GET", f"/repos/{owner}/{repo}/git/ref/heads/{from_ref}")
        obj = ref_data.get("object") or {}
        sha = obj.get("sha") if isinstance(obj, dict) else None
    if not sha:
        # Fallback: get default branch
        repo_data = _api("GET", f"/repos/{owner}/{repo}")
        default_branch = repo_data.get("default_branch", "main")
        ref_info = _api("GET", f"/repos/{owner}/{repo}/git/ref/heads/{default_branch}")
        sha = ref_info.get("object", {}).get("sha")
    path = "/repos/{owner}/{repo}/git/refs".format(owner=owner, repo=repo)
    return _api("POST", path, json_data={"ref": f"refs/heads/{branch}", "sha": sha})


def get_repo_activity(owner: str, repo: str, limit: int = 10) -> list[dict[str, Any]]:
    """Get recent repo activity (events)."""
    path = f"/repos/{owner}/{repo}/events"
    try:
        events = _api("GET", path)
        if isinstance(events, list):
            return events[:limit]
    except Exception as e:
        logger.debug("get_repo_activity error: %s", e)
    return []


def search_repos(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search GitHub repositories."""
    try:
        result = _api("GET", "/search/repositories", params={"q": query, "per_page": limit})
        items = result.get("items", [])
        return [
            {
                "full_name": r.get("full_name"),
                "description": r.get("description"),
                "language": r.get("language"),
                "stars": r.get("stargazers_count"),
                "url": r.get("html_url"),
            }
            for r in items
        ]
    except Exception as e:
        logger.debug("search_repos error: %s", e)
        return []
