"""
Backend secrets management, webhook verification, and redaction.

Uses pydantic-settings for configuration. No secrets in logs.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppSecrets(BaseSettings):
    """Application secrets loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # IronClaw / LLM
    IRONCLAW_URL: str = Field(default="http://127.0.0.1:3000", alias="IRONCLAW_URL")
    OPENROUTER_API_KEY: str = Field(default="", alias="OPENROUTER_API_KEY")
    OPENROUTER_MODEL: str = Field(default="anthropic/claude-sonnet-4", alias="OPENROUTER_MODEL")

    # Database
    DATABASE_URL: str = Field(default="", alias="DATABASE_URL")

    # Webhooks
    GITHUB_WEBHOOK_SECRET: str = Field(default="", alias="GITHUB_WEBHOOK_SECRET")
    JIRA_WEBHOOK_SECRET: str = Field(default="", alias="JIRA_WEBHOOK_SECRET")
    JENKINS_WEBHOOK_SECRET: str = Field(default="", alias="JENKINS_WEBHOOK_SECRET")
    SLACK_SIGNING_SECRET: str = Field(default="", alias="SLACK_SIGNING_SECRET")

    # Integrations (optional)
    GITHUB_TOKEN: str = Field(default="", alias="GITHUB_TOKEN")
    SLACK_BOT_TOKEN: str = Field(default="", alias="SLACK_BOT_TOKEN")
    JIRA_URL: str = Field(default="", alias="JIRA_URL")
    JIRA_USER: str = Field(default="", alias="JIRA_USER")
    JIRA_API_TOKEN: str = Field(default="", alias="JIRA_API_TOKEN")
    CONFLUENCE_URL: str = Field(default="", alias="CONFLUENCE_URL")
    CONFLUENCE_USER: str = Field(default="", alias="CONFLUENCE_USER")
    CONFLUENCE_API_TOKEN: str = Field(default="", alias="CONFLUENCE_API_TOKEN")
    JENKINS_URL: str = Field(default="", alias="JENKINS_URL")
    JENKINS_USER: str = Field(default="", alias="JENKINS_USER")
    JENKINS_API_TOKEN: str = Field(default="", alias="JENKINS_API_TOKEN")


_SECRETS_CACHE: AppSecrets | None = None


def get_secrets() -> AppSecrets:
    """Return cached AppSecrets instance."""
    global _SECRETS_CACHE
    if _SECRETS_CACHE is None:
        _SECRETS_CACHE = AppSecrets()
    return _SECRETS_CACHE


# Common secret patterns for redaction
_SECRET_PATTERNS = [
    (re.compile(r"(?:api[_-]?key|apikey|secret|token|password)\s*[:=]\s*['\"]?([^\s'\"]+)", re.I), r"\1=***REDACTED***"),
    (re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]+)"), "Bearer ***REDACTED***"),
    (re.compile(r"(?:ghp|gho|ghu)_[A-Za-z0-9]{36}"), "***REDACTED***"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]+"), "***REDACTED***"),
]


def redact(text: str) -> str:
    """Redact known secret patterns from text."""
    if not text:
        return text
    result = text
    for pattern, replacement in _SECRET_PATTERNS:
        if isinstance(replacement, str):
            result = pattern.sub(replacement, result)
        else:
            result = pattern.sub(replacement, result)
    return result


def verify_webhook_signature(payload: bytes | str, signature: str | None, secret: str) -> bool:
    """
    Verify webhook signature (HMAC-SHA256).

    - GitHub: X-Hub-Signature-256 (sha256=...)
    - Slack: X-Slack-Signature (v0=...)
    - Generic: compare HMAC-SHA256
    """
    if not secret or not signature:
        return False
    payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload

    # GitHub format: sha256=<hex>
    if signature.lower().startswith("sha256="):
        expected = "sha256=" + hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    # Slack format: v0=<hex>
    if signature.startswith("v0="):
        expected = "v0=" + hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)

    # Generic HMAC compare
    expected = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secrets from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and record.msg:
            record.msg = redact(str(record.msg))
        if hasattr(record, "args") and record.args:
            record.args = tuple(redact(str(a)) if isinstance(a, str) else a for a in record.args)
        return True
