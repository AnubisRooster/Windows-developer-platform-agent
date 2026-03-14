"""
Knowledge Graph - Engineering relationship graph stored in PostgreSQL.

Node types: repository, file, commit, pull_request, jira_issue, pipeline, documentation, engineer
Edge types: repo_contains_file, file_modified_by_commit, commit_part_of_pr,
            pr_links_to_issue, repo_deployed_by_pipeline, authored_by, reviewed_by
"""

from __future__ import annotations

import logging
from typing import Any

from backend.database.models import KnowledgeEdge, KnowledgeNode, get_session

logger = logging.getLogger(__name__)

NODE_TYPES = frozenset({
    "repository", "file", "commit", "pull_request",
    "jira_issue", "pipeline", "documentation", "engineer",
})

EDGE_TYPES = frozenset({
    "repo_contains_file", "file_modified_by_commit", "commit_part_of_pr",
    "pr_links_to_issue", "repo_deployed_by_pipeline",
    "authored_by", "reviewed_by", "assigned_to", "documents_repo",
})


class KnowledgeGraph:
    """Interface over the PostgreSQL-backed knowledge graph."""

    def __init__(self) -> None:
        self._session_factory = get_session()

    # -------------------------------------------------------------------
    # Node operations
    # -------------------------------------------------------------------

    def upsert_node(
        self,
        node_type: str,
        name: str,
        external_id: str | None = None,
        source: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> str:
        """Create or update a node. Returns node_id."""
        with self._session_factory() as session:
            existing = None
            if external_id:
                existing = (
                    session.query(KnowledgeNode)
                    .filter(KnowledgeNode.node_type == node_type, KnowledgeNode.external_id == external_id)
                    .first()
                )
            if existing:
                existing.name = name
                existing.source = source or existing.source
                if properties:
                    merged = dict(existing.properties or {})
                    merged.update(properties)
                    existing.properties = merged
                session.commit()
                return existing.node_id

            node = KnowledgeNode(
                node_type=node_type,
                name=name,
                external_id=external_id,
                source=source,
                properties=properties or {},
            )
            session.add(node)
            session.commit()
            return node.node_id

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        with self._session_factory() as session:
            n = session.query(KnowledgeNode).filter(KnowledgeNode.node_id == node_id).first()
            if not n:
                return None
            return {
                "node_id": n.node_id,
                "node_type": n.node_type,
                "name": n.name,
                "external_id": n.external_id,
                "source": n.source,
                "properties": n.properties,
            }

    def find_nodes(
        self,
        node_type: str | None = None,
        name_contains: str | None = None,
        external_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with self._session_factory() as session:
            q = session.query(KnowledgeNode)
            if node_type:
                q = q.filter(KnowledgeNode.node_type == node_type)
            if name_contains:
                q = q.filter(KnowledgeNode.name.contains(name_contains))
            if external_id:
                q = q.filter(KnowledgeNode.external_id == external_id)
            rows = q.order_by(KnowledgeNode.updated_at.desc()).limit(limit).all()
            return [
                {
                    "node_id": r.node_id,
                    "node_type": r.node_type,
                    "name": r.name,
                    "external_id": r.external_id,
                    "source": r.source,
                    "properties": r.properties,
                }
                for r in rows
            ]

    # -------------------------------------------------------------------
    # Edge operations
    # -------------------------------------------------------------------

    def add_edge(
        self,
        edge_type: str,
        source_node_id: str,
        target_node_id: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """Add an edge. Returns True if created, False if already exists."""
        with self._session_factory() as session:
            existing = (
                session.query(KnowledgeEdge)
                .filter(
                    KnowledgeEdge.edge_type == edge_type,
                    KnowledgeEdge.source_node_id == source_node_id,
                    KnowledgeEdge.target_node_id == target_node_id,
                )
                .first()
            )
            if existing:
                if properties:
                    merged = (existing.properties or {})
                    merged.update(properties)
                    existing.properties = merged
                    session.commit()
                return False
            edge = KnowledgeEdge(
                edge_type=edge_type,
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                properties=properties or {},
            )
            session.add(edge)
            session.commit()
            return True

    def get_neighbors(
        self,
        node_id: str,
        edge_type: str | None = None,
        direction: str = "both",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes. direction: out, in, both."""
        with self._session_factory() as session:
            results = []
            if direction in ("out", "both"):
                q = session.query(KnowledgeEdge).filter(KnowledgeEdge.source_node_id == node_id)
                if edge_type:
                    q = q.filter(KnowledgeEdge.edge_type == edge_type)
                for e in q.limit(limit).all():
                    target = session.query(KnowledgeNode).filter(KnowledgeNode.node_id == e.target_node_id).first()
                    if target:
                        results.append({
                            "edge_type": e.edge_type,
                            "direction": "out",
                            "node_id": target.node_id,
                            "node_type": target.node_type,
                            "name": target.name,
                        })
            if direction in ("in", "both"):
                q = session.query(KnowledgeEdge).filter(KnowledgeEdge.target_node_id == node_id)
                if edge_type:
                    q = q.filter(KnowledgeEdge.edge_type == edge_type)
                for e in q.limit(limit).all():
                    source = session.query(KnowledgeNode).filter(KnowledgeNode.node_id == e.source_node_id).first()
                    if source:
                        results.append({
                            "edge_type": e.edge_type,
                            "direction": "in",
                            "node_id": source.node_id,
                            "node_type": source.node_type,
                            "name": source.name,
                        })
            return results

    # -------------------------------------------------------------------
    # Query helpers
    # -------------------------------------------------------------------

    def trace_commit(self, commit_sha: str) -> dict[str, Any]:
        """Trace a commit through the graph: commit → PR → Jira issues → repo."""
        commit_nodes = self.find_nodes(node_type="commit", external_id=commit_sha)
        if not commit_nodes:
            return {"error": f"Commit {commit_sha} not found in knowledge graph"}

        commit = commit_nodes[0]
        prs = self.get_neighbors(commit["node_id"], edge_type="commit_part_of_pr", direction="out")
        issues = []
        for pr in prs:
            pr_issues = self.get_neighbors(pr["node_id"], edge_type="pr_links_to_issue", direction="out")
            issues.extend(pr_issues)

        files = self.get_neighbors(commit["node_id"], edge_type="file_modified_by_commit", direction="in")

        return {
            "commit": commit,
            "pull_requests": prs,
            "jira_issues": issues,
            "files_modified": files,
        }

    def find_related_docs(self, entity_id: str) -> list[dict[str, Any]]:
        """Find documentation nodes related to any entity."""
        node = self.get_node(entity_id)
        if not node:
            nodes = self.find_nodes(external_id=entity_id, limit=1)
            if not nodes:
                return []
            node = nodes[0]

        all_neighbors = self.get_neighbors(node["node_id"], direction="both")
        docs = [n for n in all_neighbors if n.get("node_type") == "documentation"]

        if node["node_type"] == "repository":
            repo_files = self.get_neighbors(node["node_id"], edge_type="repo_contains_file", direction="out")
            for f in repo_files:
                file_docs = self.get_neighbors(f["node_id"], direction="both")
                docs.extend(d for d in file_docs if d.get("node_type") == "documentation")

        return docs

    def find_repo(self, name_or_id: str) -> dict[str, Any] | None:
        """Find a repository node by name or external ID."""
        nodes = self.find_nodes(node_type="repository", name_contains=name_or_id, limit=1)
        if not nodes:
            nodes = self.find_nodes(node_type="repository", external_id=name_or_id, limit=1)
        if not nodes:
            return None
        repo = nodes[0]
        repo["files"] = self.get_neighbors(repo["node_id"], edge_type="repo_contains_file", direction="out")
        repo["pipelines"] = self.get_neighbors(repo["node_id"], edge_type="repo_deployed_by_pipeline", direction="out")
        return repo

    def get_stats(self) -> dict[str, int]:
        """Get graph statistics."""
        with self._session_factory() as session:
            from sqlalchemy import func
            node_counts = (
                session.query(KnowledgeNode.node_type, func.count())
                .group_by(KnowledgeNode.node_type)
                .all()
            )
            edge_counts = (
                session.query(KnowledgeEdge.edge_type, func.count())
                .group_by(KnowledgeEdge.edge_type)
                .all()
            )
            return {
                "nodes": {t: c for t, c in node_counts},
                "edges": {t: c for t, c in edge_counts},
                "total_nodes": sum(c for _, c in node_counts),
                "total_edges": sum(c for _, c in edge_counts),
            }
