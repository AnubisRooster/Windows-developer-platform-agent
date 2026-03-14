"""
Jenkins integration - trigger_build, get_build_status, fetch_build_logs.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def _get_config() -> tuple[str, str, str]:
    url = os.environ.get("JENKINS_URL", "").rstrip("/")
    user = os.environ.get("JENKINS_USER", "")
    token = os.environ.get("JENKINS_API_TOKEN", "")
    return url, user, token


def _api(
    method: str,
    path: str,
    *,
    params: dict | None = None,
) -> Any:
    """Call Jenkins API (crumb may be required)."""
    base_url, user, token = _get_config()
    if not base_url:
        logger.warning("JENKINS_URL required")
        return None
    url = f"{base_url}{path}"
    auth = (user, token) if user and token else None
    with httpx.Client(timeout=30.0) as client:
        resp = client.request(method, url, auth=auth, params=params)
        if resp.status_code in (201, 204):
            return {}
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            return resp.json()
        return resp.text


def trigger_build(job: str, parameters: dict[str, str] | None = None) -> dict[str, Any]:
    """Trigger a Jenkins build. Returns build queue info."""
    params = parameters or {}
    path = f"/job/{job}/buildWithParameters" if params else f"/job/{job}/build"
    result = _api("POST", path, params=params)
    return result or {"status": "triggered"}


def get_build_status(job: str, build_number: int) -> dict[str, Any]:
    """Get status of a specific build."""
    path = f"/job/{job}/{build_number}/api/json"
    return _api("GET", path) or {}


def fetch_build_logs(job: str, build_number: int) -> str:
    """Fetch console log output of a build."""
    path = f"/job/{job}/{build_number}/consoleText"
    result = _api("GET", path)
    return result if isinstance(result, str) else str(result)
