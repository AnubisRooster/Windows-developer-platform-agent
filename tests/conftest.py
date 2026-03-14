"""Shared fixtures for the test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///")


@pytest.fixture(autouse=True)
def _reset_secrets_cache():
    from security.secrets import get_secrets
    get_secrets.cache_clear()
    yield
    get_secrets.cache_clear()


@pytest.fixture(autouse=True)
def _reset_db_globals():
    """Ensure database globals are reset between tests."""
    import database.models as db
    db._engine = None
    db._SessionLocal = None
    yield
    db._engine = None
    db._SessionLocal = None


@pytest.fixture
def env_secrets(monkeypatch):
    vals = {
        "OPENCLAW_PROVIDER": "openai",
        "OPENCLAW_API_KEY": "sk-test-key-123",
        "OPENCLAW_MODEL": "gpt-4o",
        "OPENCLAW_BASE_URL": "",
        "SLACK_BOT_TOKEN": "xoxb-test-token",
        "SLACK_APP_TOKEN": "xapp-test-token",
        "SLACK_SIGNING_SECRET": "test-signing-secret",
        "GITHUB_TOKEN": "ghp_testtoken123",
        "GITHUB_WEBHOOK_SECRET": "gh-webhook-secret",
        "JIRA_SERVER": "https://test.atlassian.net",
        "JIRA_EMAIL": "test@example.com",
        "JIRA_API_TOKEN": "jira-test-token",
        "JIRA_WEBHOOK_SECRET": "jira-webhook-secret",
        "CONFLUENCE_URL": "https://test.atlassian.net/wiki",
        "CONFLUENCE_EMAIL": "test@example.com",
        "CONFLUENCE_TOKEN": "confluence-test-token",
        "JENKINS_URL": "https://jenkins.test.com",
        "JENKINS_USER": "admin",
        "JENKINS_TOKEN": "jenkins-test-token",
        "JENKINS_WEBHOOK_SECRET": "jenkins-webhook-secret",
        "GMAIL_CREDS_PATH": "credentials.json",
        "GMAIL_TOKEN_PATH": "token.json",
        "WEBHOOK_HOST": "127.0.0.1",
        "WEBHOOK_PORT": "8080",
        "DATABASE_URL": "sqlite:///",
    }
    for k, v in vals.items():
        monkeypatch.setenv(k, v)
    return vals


@pytest.fixture
def event_bus():
    from events.bus import EventBus
    return EventBus()


@pytest.fixture
def tool_registry():
    from agent.orchestrator import ToolRegistry
    return ToolRegistry()


@pytest.fixture
def memory():
    from agent.memory import ConversationMemory
    return ConversationMemory()


@pytest.fixture
def tmp_workflow_dir(tmp_path):
    """Create a temp directory with sample workflow YAML files."""
    pr_yaml = tmp_path / "pr_opened.yaml"
    pr_yaml.write_text(
        "name: pr_opened_workflow\n"
        "trigger: github.pull_request.opened\n"
        "description: Test PR workflow\n"
        "enabled: true\n"
        "actions:\n"
        "  - tool: github.summarize_pull_request\n"
        "  - tool: slack.send_message\n"
        "    args:\n"
        '      channel: "#test"\n'
        "    on_failure: continue\n",
        encoding="utf-8",
    )
    build_yaml = tmp_path / "build_failed.yaml"
    build_yaml.write_text(
        "name: build_failed_workflow\n"
        "trigger: jenkins.build.failed\n"
        "description: Test build workflow\n"
        "enabled: true\n"
        "actions:\n"
        "  - tool: jenkins.fetch_build_logs\n"
        "  - tool: slack.send_message\n"
        "    args:\n"
        '      channel: "#build-alerts"\n',
        encoding="utf-8",
    )
    disabled_yaml = tmp_path / "disabled.yaml"
    disabled_yaml.write_text(
        "name: disabled_workflow\n"
        "trigger: system.noop\n"
        "enabled: false\n"
        "actions:\n"
        "  - tool: noop\n",
        encoding="utf-8",
    )
    return tmp_path
