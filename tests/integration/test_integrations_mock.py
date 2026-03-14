"""Integration tests for integrations using mocks (no real API calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestSlackIntegration:
    @patch("integrations.slack._get_client")
    def test_send_message(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "123.456", "channel": "C123"}
        mock_get_client.return_value = mock_client

        from integrations.slack import send_message
        result = send_message("#general", "Hello!")
        assert result["ts"] == "123.456"
        assert result["channel"] == "C123"
        mock_client.chat_postMessage.assert_called_once_with(channel="#general", text="Hello!")

    @patch("integrations.slack._get_client")
    def test_send_message_threaded(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "789.012", "channel": "C123"}
        mock_get_client.return_value = mock_client

        from integrations.slack import send_message
        result = send_message("#general", "Reply", thread_ts="123.456")
        mock_client.chat_postMessage.assert_called_once_with(
            channel="#general", text="Reply", thread_ts="123.456"
        )

    @patch("integrations.slack._get_client")
    def test_read_channel_history(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.conversations_history.return_value = {
            "messages": [
                {"user": "U1", "text": "hi", "ts": "1.0"},
                {"user": "U2", "text": "hello", "ts": "2.0"},
            ]
        }
        mock_get_client.return_value = mock_client

        from integrations.slack import read_channel_history
        messages = read_channel_history("C123", limit=5)
        assert len(messages) == 2
        assert messages[0]["text"] == "hi"


class TestJiraIntegration:
    @patch("integrations.jira_integration._get_client")
    def test_create_ticket(self, mock_get_client):
        mock_jira = MagicMock()
        mock_issue = MagicMock()
        mock_issue.key = "PROJ-42"
        mock_issue.id = "10042"
        mock_issue.self = "https://jira.example.com/rest/api/2/issue/10042"
        mock_jira.create_issue.return_value = mock_issue
        mock_get_client.return_value = mock_jira

        from integrations.jira_integration import create_ticket
        result = create_ticket("PROJ", "Test ticket", "A description")
        assert result["key"] == "PROJ-42"

    @patch("integrations.jira_integration._get_client")
    def test_get_ticket_details(self, mock_get_client):
        mock_jira = MagicMock()
        mock_issue = MagicMock()
        mock_issue.key = "PROJ-1"
        mock_issue.fields.summary = "Test"
        mock_issue.fields.description = "Desc"
        mock_issue.fields.status = "Open"
        mock_issue.fields.assignee = "user1"
        mock_issue.fields.created = "2025-01-01"
        mock_issue.fields.updated = "2025-01-02"
        mock_jira.issue.return_value = mock_issue
        mock_get_client.return_value = mock_jira

        from integrations.jira_integration import get_ticket_details
        result = get_ticket_details("PROJ-1")
        assert result["key"] == "PROJ-1"
        assert result["summary"] == "Test"


class TestJenkinsIntegration:
    @patch("integrations.jenkins._get_client")
    def test_trigger_build(self, mock_get_client):
        mock_server = MagicMock()
        mock_server.build_job.return_value = 42
        mock_get_client.return_value = mock_server

        from integrations.jenkins import trigger_build
        result = trigger_build("my-job")
        assert result["queue_item_number"] == 42

    @patch("integrations.jenkins._get_client")
    def test_get_build_status(self, mock_get_client):
        mock_server = MagicMock()
        mock_server.get_build_info.return_value = {
            "result": "SUCCESS",
            "duration": 5000,
            "building": False,
            "url": "http://jenkins/job/1",
        }
        mock_get_client.return_value = mock_server

        from integrations.jenkins import get_build_status
        result = get_build_status("my-job", 1)
        assert result["result"] == "SUCCESS"
        assert not result["building"]

    @patch("integrations.jenkins._get_client")
    def test_fetch_build_logs(self, mock_get_client):
        mock_server = MagicMock()
        mock_server.get_build_console_output.return_value = "BUILD SUCCESS\nDone."
        mock_get_client.return_value = mock_server

        from integrations.jenkins import fetch_build_logs
        logs = fetch_build_logs("my-job", 1)
        assert "BUILD SUCCESS" in logs


class TestConfluenceIntegration:
    @patch("integrations.confluence._get_client")
    def test_search_docs(self, mock_get_client):
        mock_confluence = MagicMock()
        mock_confluence.cql.return_value = {
            "results": [
                {"content": {"title": "Getting Started", "id": "123", "type": "page", "_links": {}}},
            ]
        }
        mock_get_client.return_value = mock_confluence

        from integrations.confluence import search_docs
        results = search_docs("getting started")
        assert len(results) == 1
        assert results[0]["title"] == "Getting Started"

    @patch("integrations.confluence._get_client")
    def test_create_page(self, mock_get_client):
        mock_confluence = MagicMock()
        mock_confluence.create_page.return_value = {"id": "456", "_links": {"webui": "/page"}}
        mock_get_client.return_value = mock_confluence

        from integrations.confluence import create_page
        result = create_page("DOC", "New Page", "<p>Body</p>")
        assert result["id"] == "456"
