"""Unit tests for KnowledgeTools (query tools for IronClaw)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    yield
    db._engine = None
    db._SessionLocal = None


@pytest.fixture
def tools():
    from backend.database.models import init_db
    from backend.knowledge.graph import KnowledgeGraph
    from backend.knowledge.embeddings import EmbeddingStore
    from backend.knowledge.tools import KnowledgeTools
    init_db()
    return KnowledgeTools(graph=KnowledgeGraph(), embeddings=EmbeddingStore())


class TestKnowledgeToolDefinitions:
    def test_returns_five_tools(self, tools):
        defs = tools.get_tool_definitions()
        assert len(defs) == 5

    def test_all_tools_have_required_fields(self, tools):
        for d in tools.get_tool_definitions():
            assert "name" in d
            assert "description" in d
            assert "parameters" in d
            assert d["name"].startswith("knowledge.")

    def test_tool_names(self, tools):
        names = {d["name"] for d in tools.get_tool_definitions()}
        assert names == {
            "knowledge.search",
            "knowledge.find_repo",
            "knowledge.trace_commit",
            "knowledge.find_related_docs",
            "knowledge.explain_system",
        }


class TestFindRepo:
    def test_find_repo_returns_result(self, tools):
        tools.graph.upsert_node("repository", "acme/api", external_id="acme/api", source="github")
        result = tools.find_repo("acme/api")
        assert result is not None
        assert result["name"] == "acme/api"

    def test_find_repo_not_found(self, tools):
        result = tools.find_repo("nonexistent")
        assert "error" in result


class TestTraceCommit:
    def test_trace_commit_with_graph_data(self, tools):
        commit = tools.graph.upsert_node("commit", "abc", external_id="abc123", source="github")
        pr = tools.graph.upsert_node("pull_request", "PR #1", external_id="pr/1", source="github")
        tools.graph.add_edge("commit_part_of_pr", commit, pr)
        result = tools.trace_commit("abc123")
        assert result["commit"]["name"] == "abc"
        assert len(result["pull_requests"]) == 1

    def test_trace_commit_not_found(self, tools):
        result = tools.trace_commit("nonexistent_sha")
        assert "error" in result


class TestFindRelatedDocs:
    def test_find_docs_for_repo(self, tools):
        repo = tools.graph.upsert_node("repository", "my/repo", external_id="my/repo", source="github")
        doc = tools.graph.upsert_node("documentation", "Setup Guide", external_id="doc-1", source="confluence")
        tools.graph.add_edge("documents_repo", doc, repo)
        result = tools.find_related_docs(repo)
        assert len(result) >= 1

    def test_find_docs_no_results(self, tools):
        result = tools.find_related_docs("nonexistent-id")
        assert result == []


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_delegates_to_embeddings(self, tools):
        mock_results = [{"score": 0.9, "chunk_text": "auth code", "doc_id": "d1"}]
        with patch.object(tools.embeddings, "search", return_value=mock_results) as mock_search:
            results = await tools.search("authentication")
            mock_search.assert_called_once_with("authentication", limit=10, source=None, doc_type=None)
            assert results == mock_results


class TestExplainSystem:
    @pytest.mark.asyncio
    async def test_explain_combines_graph_and_search(self, tools):
        tools.graph.upsert_node("repository", "auth-service", external_id="auth-service", source="github")
        mock_search = [{"score": 0.8, "chunk_text": "Auth handles login"}]
        with patch.object(tools.embeddings, "search", return_value=mock_search):
            result = await tools.explain_system("auth-service")
            assert result["query"] == "auth-service"
            assert len(result["graph_nodes"]) >= 1
            assert len(result["search_results"]) == 1
