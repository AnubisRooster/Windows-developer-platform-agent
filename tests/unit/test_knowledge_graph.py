"""Unit tests for the Knowledge Graph."""

from __future__ import annotations

import os
import sys
from pathlib import Path

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
def graph():
    from backend.database.models import init_db
    from backend.knowledge.graph import KnowledgeGraph
    init_db()
    return KnowledgeGraph()


class TestNodeOperations:
    def test_upsert_creates_node(self, graph):
        node_id = graph.upsert_node("repository", "acme/backend", external_id="acme/backend", source="github")
        assert node_id is not None

    def test_upsert_updates_existing(self, graph):
        id1 = graph.upsert_node("repository", "acme/backend", external_id="acme/backend", source="github", properties={"stars": 10})
        id2 = graph.upsert_node("repository", "acme/backend-v2", external_id="acme/backend", source="github", properties={"stars": 20})
        assert id1 == id2

        node = graph.get_node(id1)
        assert node["name"] == "acme/backend-v2"
        assert node["properties"]["stars"] == 20

    def test_find_nodes_by_type(self, graph):
        graph.upsert_node("repository", "repo1", external_id="repo1", source="github")
        graph.upsert_node("repository", "repo2", external_id="repo2", source="github")
        graph.upsert_node("engineer", "alice", external_id="alice", source="github")

        repos = graph.find_nodes(node_type="repository")
        assert len(repos) == 2

        engineers = graph.find_nodes(node_type="engineer")
        assert len(engineers) == 1

    def test_find_nodes_by_name(self, graph):
        graph.upsert_node("repository", "frontend-app", external_id="frontend-app", source="github")
        graph.upsert_node("repository", "backend-api", external_id="backend-api", source="github")

        results = graph.find_nodes(name_contains="frontend")
        assert len(results) == 1
        assert results[0]["name"] == "frontend-app"


class TestEdgeOperations:
    def test_add_edge(self, graph):
        repo = graph.upsert_node("repository", "test/repo", external_id="test/repo", source="github")
        file_node = graph.upsert_node("file", "main.py", external_id="test/repo/main.py", source="github")
        created = graph.add_edge("repo_contains_file", repo, file_node)
        assert created is True

    def test_add_duplicate_edge_returns_false(self, graph):
        repo = graph.upsert_node("repository", "test/repo", external_id="test/repo", source="github")
        file_node = graph.upsert_node("file", "main.py", external_id="test/repo/main.py", source="github")
        graph.add_edge("repo_contains_file", repo, file_node)
        created = graph.add_edge("repo_contains_file", repo, file_node)
        assert created is False

    def test_get_neighbors_out(self, graph):
        repo = graph.upsert_node("repository", "test/repo", external_id="test/repo", source="github")
        f1 = graph.upsert_node("file", "a.py", external_id="test/repo/a.py", source="github")
        f2 = graph.upsert_node("file", "b.py", external_id="test/repo/b.py", source="github")
        graph.add_edge("repo_contains_file", repo, f1)
        graph.add_edge("repo_contains_file", repo, f2)

        neighbors = graph.get_neighbors(repo, edge_type="repo_contains_file", direction="out")
        assert len(neighbors) == 2
        names = {n["name"] for n in neighbors}
        assert names == {"a.py", "b.py"}


class TestGraphQueries:
    def test_trace_commit(self, graph):
        commit = graph.upsert_node("commit", "abc12345", external_id="abc1234567890", source="github")
        pr = graph.upsert_node("pull_request", "PR #1", external_id="owner/repo/pull/1", source="github")
        issue = graph.upsert_node("jira_issue", "PROJ-1", external_id="PROJ-1", source="jira")

        graph.add_edge("commit_part_of_pr", commit, pr)
        graph.add_edge("pr_links_to_issue", pr, issue)

        result = graph.trace_commit("abc1234567890")
        assert result["commit"]["name"] == "abc12345"
        assert len(result["pull_requests"]) == 1
        assert len(result["jira_issues"]) == 1

    def test_find_repo(self, graph):
        repo = graph.upsert_node("repository", "acme/platform", external_id="acme/platform", source="github")
        f = graph.upsert_node("file", "app.py", external_id="acme/platform/app.py", source="github")
        pipe = graph.upsert_node("pipeline", "deploy-prod", external_id="deploy-prod", source="jenkins")
        graph.add_edge("repo_contains_file", repo, f)
        graph.add_edge("repo_deployed_by_pipeline", repo, pipe)

        result = graph.find_repo("platform")
        assert result is not None
        assert result["name"] == "acme/platform"
        assert len(result["files"]) == 1
        assert len(result["pipelines"]) == 1

    def test_get_stats(self, graph):
        graph.upsert_node("repository", "r1", external_id="r1", source="github")
        graph.upsert_node("engineer", "e1", external_id="e1", source="github")

        stats = graph.get_stats()
        assert stats["total_nodes"] == 2
