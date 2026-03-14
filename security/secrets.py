"""
AppSecrets, redaction, webhook signature verification, and logging filter.
Platform-agnostic.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
from functools import lru_cache
from typing import Any

from pydantic_settings import BaseSettings


class AppSecrets(BaseSettings):
    """Pydantic BaseSettings for secrets. Loads from env."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    openclaw_api_key: str = ""
    github_token: str = ""
    slack_bot_token: str = ""
    jira_server: str = ""
    jira_api_token: str = ""
    jira_email: str = ""
    confluence_url: str = ""
    confluence_token: str = ""
    confluence_email: str = ""
    jenkins_url: str = "http://localhost:8080"
    jenkins_user: str = ""
    jenkins_token: str = ""
    github_webhook_secret: str = ""
    database_url: str = ""


@lru_cache(maxsize=1)
def get_secrets() -> AppSecrets:
    """Get AppSecrets singleton (cached)."""
    return AppSecrets()


def redact(text: str) -> str:
    """
    Scrub tokens, keys, and secrets from text for safe logging.

    Args:
        text: Raw text that may contain secrets.

    Returns:
        Text with secrets replaced by [REDACTED].
    """
    if not text:
        return text
    patterns = [
        (r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[\w\-\.]+", r"\1=[REDACTED]"),
        (r"[\w\-]+@[\w\-\.]+\.[a-z]{2,}", "[EMAIL_REDACTED]"),
        (r"\b[A-Za-z0-9\-]{20,}\b", lambda m: "[REDACTED]" if len(m.group()) > 30 else m.group()),
    ]
    result = text
    for pat, repl in patterns[:-1]:
        result = re.sub(pat, repl, result)
    # Be conservative with the last pattern to avoid over-redacting
    return result


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256 webhook signature (e.g. GitHub X-Hub-Signature-256).

    Args:
        payload: Raw request body.
        signature: Header value (e.g. sha256=hexdigest).
        secret: Webhook secret.

    Returns:
        True if signature is valid.
    """
    if not secret or not signature:
        return False
    if signature.startswith("sha256="):
        signature = signature[7:]
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and record.msg:
            record.msg = redact(str(record.msg))
        if hasattr(record, "args") and record.args:
            record.args = tuple(redact(str(a)) for a in record.args)
        return True
