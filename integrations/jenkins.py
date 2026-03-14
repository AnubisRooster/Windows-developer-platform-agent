"""
Jenkins integration using python-jenkins.
Platform-agnostic.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import jenkins

logger = logging.getLogger(__name__)


def _get_client() -> jenkins.Jenkins:
    """Get Jenkins client from env."""
    url = os.environ.get("JENKINS_URL", "http://localhost:8080")
    user = os.environ.get("JENKINS_USER", "")
    token = os.environ.get("JENKINS_TOKEN", "")
    return jenkins.Jenkins(url, username=user, password=token)


def trigger_build(
    job_name: str,
    params: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Trigger a Jenkins build.

    Args:
        job_name: Full job name (may include folder path).
        params: Optional build parameters.

    Returns:
        Dict with queue_item_number or build_number.
    """
    try:
        server = _get_client()
        params = params or {}
        if params:
            queue = server.build_job(job_name, params)
        else:
            queue = server.build_job(job_name)
        return {"queue_item_number": queue}
    except jenkins.JenkinsException as e:
        logger.exception("Jenkins trigger_build failed: %s", e)
        raise


def get_build_status(job_name: str, build_number: int) -> dict[str, Any]:
    """
    Get status of a Jenkins build.

    Args:
        job_name: Full job name.
        build_number: Build number.

    Returns:
        Dict with result, duration, building, url.
    """
    try:
        server = _get_client()
        info = server.get_build_info(job_name, build_number)
        return {
            "result": info.get("result"),
            "duration": info.get("duration"),
            "building": info.get("building", False),
            "url": info.get("url"),
        }
    except jenkins.JenkinsException as e:
        logger.exception("Jenkins get_build_status failed: %s", e)
        raise


def fetch_build_logs(job_name: str, build_number: int) -> str:
    """
    Fetch console output logs for a Jenkins build.

    Args:
        job_name: Full job name.
        build_number: Build number.

    Returns:
        Raw console log string.
    """
    try:
        server = _get_client()
        return server.get_build_console_output(job_name, build_number)
    except jenkins.JenkinsException as e:
        logger.exception("Jenkins fetch_build_logs failed: %s", e)
        raise
