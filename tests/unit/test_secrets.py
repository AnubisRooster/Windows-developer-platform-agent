"""Unit tests for security/secrets module."""

from __future__ import annotations

import hashlib
import hmac
import logging

import pytest

from security.secrets import (
    AppSecrets,
    RedactingFilter,
    get_secrets,
    redact,
    verify_webhook_signature,
)


class TestAppSecrets:
    def test_defaults(self, env_secrets):
        secrets = AppSecrets()
        assert secrets.openclaw_api_key == "sk-test-key-123"
        assert secrets.github_token == "ghp_testtoken123"
        assert secrets.slack_bot_token == "xoxb-test-token"

    def test_get_secrets_cached(self, env_secrets):
        s1 = get_secrets()
        s2 = get_secrets()
        assert s1 is s2


class TestRedact:
    def test_redact_api_key(self):
        text = "api_key: sk-proj-abc123def456ghi789"
        result = redact(text)
        assert "REDACTED" in result

    def test_redact_token_assignment(self):
        text = "token=ghp_realtoken1234567890abcdef"
        result = redact(text)
        assert "REDACTED" in result

    def test_redact_empty(self):
        assert redact("") == ""
        assert redact(None) is None

    def test_redact_normal_text(self):
        text = "Hello, this is a normal message."
        result = redact(text)
        assert "Hello" in result


class TestVerifyWebhookSignature:
    def test_valid_signature(self):
        secret = "my-secret"
        payload = b'{"action": "opened"}'
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        sig = f"sha256={digest}"
        assert verify_webhook_signature(payload, sig, secret)

    def test_invalid_signature(self):
        assert not verify_webhook_signature(b"data", "sha256=bad", "secret")

    def test_empty_secret(self):
        assert not verify_webhook_signature(b"data", "sha256=abc", "")

    def test_empty_signature(self):
        assert not verify_webhook_signature(b"data", "", "secret")

    def test_signature_without_prefix(self):
        secret = "my-secret"
        payload = b"test"
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert verify_webhook_signature(payload, digest, secret)


class TestRedactingFilter:
    def test_filter_redacts_message(self):
        f = RedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="token=ghp_realtoken1234567890abcdefgh", args=(), exc_info=None,
        )
        f.filter(record)
        assert "REDACTED" in record.msg

    def test_filter_returns_true(self):
        f = RedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="safe message", args=(), exc_info=None,
        )
        assert f.filter(record) is True
