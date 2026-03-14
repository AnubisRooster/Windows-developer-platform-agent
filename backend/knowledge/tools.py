"""
Knowledge Query Tools - Exposed as capabilities for IronClaw to answer engineering questions.

Tools:
  knowledge.search       - Semantic search across all indexed documents
  knowledge.find_repo    - Find repository details and relationships
  knowledge.trace_commit - Trace a commit through PRs, issues, and files
  knowledge.find_related_docs - Find documentation related to any entity
  knowledge.explain_system    - Explain a system or component using graph + docs
"""

from __future__ import annotations

import logging
from typing import Any

from backend.knowledge.embeddings import EmbeddingStore
from backend.knowledge.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class KnowledgeTools:
    """Knowledge query tools that can be registered in the capability registry."""

    def __init__(
        self,
        graph: KnowledgeGraph | None = None,
        embeddings: EmbeddingStore | None = None,
    ) -> None:
        self.graph = graph or KnowledgeGraph()
        self.embeddings = embeddings or EmbeddingStore()

    async def search(
        self,
        query: str,
        limit: int = 10,
        source: str | None = None,
        doc_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Semantic search across all indexed engineering documents."""
        return await self.embeddings.search(query, limit=limit, source=source, doc_type=doc_type)

    def find_repo(self, name: str) -> dict[str, Any]:
        """Find a repository and its relationships (files, pipelines, engineers)."""
        result = self.graph.find_repo(name)
        if not result:
            return {"error": f"Repository '{name}' not found in knowledge graph"}
        return result

    def trace_commit(self, commit_sha: str) -> dict[str, Any]:
        """Trace a commit through PRs, Jira issues, and modified files."""
        return self.graph.trace_commit(commit_sha)

    def find_related_docs(self, entity_id: str) -> list[dict[str, Any]]:
        """Find documentation related to a repository, file, or issue."""
        return self.graph.find_related_docs(entity_id)

    async def explain_system(self, name: str) -> dict[str, Any]:
        """
        Explain a system or component by combining graph data and document search.
        Gathers: graph nodes, relationships, and relevant document excerpts.
        """
        graph_results = self.graph.find_nodes(name_contains=name, limit=20)
        search_results = await self.embeddings.search(f"What is {name}? How does {name} work?", limit=5)
        related_docs = []

        for node in graph_results[:3]:
            docs = self.graph.find_related_docs(node["node_id"])
            related_docs.extend(docs)

        return {
            "query": name,
            "graph_nodes": graph_results,
            "search_results": search_results,
            "related_documentation": related_docs,
        }

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return tool schemas for registry registration."""
        return [
            {
                "name": "knowledge.search",
                "description": "Semantic search across indexed engineering documents (code, PRs, Jira, Confluence)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results", "default": 10},
                        "source": {"type": "string", "description": "Filter by source (github, jira, confluence, jenkins)"},
                        "doc_type": {"type": "string", "description": "Filter by type (repository, pull_request, issue, page, pipeline)"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "knowledge.find_repo",
                "description": "Find a repository and its relationships in the knowledge graph",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Repository name or identifier"},
                    },
                    "required": ["name"],
                },
            },
            {
                "name": "knowledge.trace_commit",
                "description": "Trace a commit through PRs, Jira issues, and modified files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commit_sha": {"type": "string", "description": "Git commit SHA"},
                    },
                    "required": ["commit_sha"],
                },
            },
            {
                "name": "knowledge.find_related_docs",
                "description": "Find documentation related to a repository, file, or issue",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_id": {"type": "string", "description": "Node ID or external ID of the entity"},
                    },
                    "required": ["entity_id"],
                },
            },
            {
                "name": "knowledge.explain_system",
                "description": "Explain a system or component using knowledge graph and document search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "System or component name to explain"},
                    },
                    "required": ["name"],
                },
            },
        ]
