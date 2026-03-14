"""
Repository Intelligence Indexer.

Ingests data from GitHub, Jira, Confluence, and Jenkins into the
Document store and Knowledge Graph.

Each indexer:
  1. Fetches data from the external API
  2. Stores artifacts as Documents
  3. Creates Knowledge Graph nodes and edges
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from backend.database.models import Document, get_session
from backend.knowledge.graph import KnowledgeGraph

logger = logging.getLogger(__name__)


def _github_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _upsert_document(
    source: str,
    doc_type: str,
    title: str,
    content: str,
    external_id: str,
    external_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Create or update a document. Returns doc_id."""
    Session = get_session()
    with Session() as session:
        existing = (
            session.query(Document)
            .filter(Document.source == source, Document.doc_type == doc_type, Document.external_id == external_id)
            .first()
        )
        if existing:
            existing.title = title
            existing.content = content
            existing.external_url = external_url
            existing.metadata_ = metadata
            session.commit()
            return existing.doc_id

        doc = Document(
            source=source,
            doc_type=doc_type,
            title=title,
            content=content,
            external_id=external_id,
            external_url=external_url,
            metadata_=metadata,
        )
        session.add(doc)
        session.commit()
        return doc.doc_id


class GitHubIndexer:
    """Index GitHub repositories, files, commits, and pull requests."""

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or KnowledgeGraph()

    def index_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Index a repository: metadata, files (tree), recent commits, open PRs."""
        stats = {"files": 0, "commits": 0, "pull_requests": 0}
        base = f"https://api.github.com/repos/{owner}/{repo}"

        with httpx.Client(timeout=30.0) as client:
            # Repo metadata
            resp = client.get(base, headers=_github_headers())
            resp.raise_for_status()
            repo_data = resp.json()

            repo_node = self.graph.upsert_node(
                "repository", f"{owner}/{repo}",
                external_id=f"{owner}/{repo}",
                source="github",
                properties={
                    "description": repo_data.get("description"),
                    "language": repo_data.get("language"),
                    "default_branch": repo_data.get("default_branch"),
                    "stars": repo_data.get("stargazers_count"),
                },
            )

            _upsert_document(
                "github", "repository", f"{owner}/{repo}",
                f"{repo_data.get('description', '')}\n\nLanguage: {repo_data.get('language')}\n"
                f"Stars: {repo_data.get('stargazers_count')}\nForks: {repo_data.get('forks_count')}",
                f"{owner}/{repo}",
                repo_data.get("html_url"),
            )

            # File tree (first level)
            try:
                branch = repo_data.get("default_branch", "main")
                tree_resp = client.get(
                    f"{base}/git/trees/{branch}?recursive=1",
                    headers=_github_headers(),
                )
                tree_resp.raise_for_status()
                tree = tree_resp.json().get("tree", [])
                for item in tree:
                    if item.get("type") != "blob":
                        continue
                    path = item["path"]
                    file_node = self.graph.upsert_node(
                        "file", path,
                        external_id=f"{owner}/{repo}/{path}",
                        source="github",
                        properties={"size": item.get("size"), "sha": item.get("sha")},
                    )
                    self.graph.add_edge("repo_contains_file", repo_node, file_node)
                    stats["files"] += 1
            except Exception as e:
                logger.warning("Failed to index file tree for %s/%s: %s", owner, repo, e)

            # Recent commits
            try:
                commits_resp = client.get(
                    f"{base}/commits?per_page=50",
                    headers=_github_headers(),
                )
                commits_resp.raise_for_status()
                for c in commits_resp.json():
                    sha = c["sha"]
                    message = c.get("commit", {}).get("message", "")
                    author = c.get("commit", {}).get("author", {}).get("name", "")

                    commit_node = self.graph.upsert_node(
                        "commit", sha[:8],
                        external_id=sha,
                        source="github",
                        properties={"message": message[:500], "author": author},
                    )

                    if author:
                        eng_node = self.graph.upsert_node("engineer", author, external_id=author, source="github")
                        self.graph.add_edge("authored_by", commit_node, eng_node)

                    _upsert_document(
                        "github", "commit", f"{sha[:8]}: {message[:80]}",
                        f"Commit {sha}\nAuthor: {author}\n\n{message}",
                        sha, f"https://github.com/{owner}/{repo}/commit/{sha}",
                    )
                    stats["commits"] += 1
            except Exception as e:
                logger.warning("Failed to index commits for %s/%s: %s", owner, repo, e)

            # Open pull requests
            try:
                prs_resp = client.get(
                    f"{base}/pulls?state=all&per_page=30",
                    headers=_github_headers(),
                )
                prs_resp.raise_for_status()
                for pr in prs_resp.json():
                    pr_num = pr["number"]
                    pr_node = self.graph.upsert_node(
                        "pull_request", f"PR #{pr_num}: {pr.get('title', '')}",
                        external_id=f"{owner}/{repo}/pull/{pr_num}",
                        source="github",
                        properties={
                            "state": pr.get("state"),
                            "author": pr.get("user", {}).get("login"),
                            "head": pr.get("head", {}).get("ref"),
                            "base": pr.get("base", {}).get("ref"),
                        },
                    )

                    body = pr.get("body") or ""
                    _upsert_document(
                        "github", "pull_request",
                        f"PR #{pr_num}: {pr.get('title', '')}",
                        f"PR #{pr_num} by {pr.get('user', {}).get('login', '')}\n"
                        f"State: {pr.get('state')}\n"
                        f"Branch: {pr.get('head', {}).get('ref', '')} → {pr.get('base', {}).get('ref', '')}\n\n"
                        f"{body[:2000]}",
                        f"{owner}/{repo}/pull/{pr_num}",
                        pr.get("html_url"),
                    )

                    author_login = pr.get("user", {}).get("login")
                    if author_login:
                        eng = self.graph.upsert_node("engineer", author_login, external_id=author_login, source="github")
                        self.graph.add_edge("authored_by", pr_node, eng)

                    stats["pull_requests"] += 1
            except Exception as e:
                logger.warning("Failed to index PRs for %s/%s: %s", owner, repo, e)

        return stats


class JiraIndexer:
    """Index Jira issues into documents and knowledge graph."""

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or KnowledgeGraph()
        self.base_url = os.environ.get("JIRA_URL", "").rstrip("/")
        self.user = os.environ.get("JIRA_USER", "")
        self.token = os.environ.get("JIRA_API_TOKEN", "")

    def index_project(self, project_key: str, max_results: int = 100) -> dict[str, int]:
        if not self.base_url:
            return {"error": "JIRA_URL not configured"}

        stats = {"issues": 0}
        with httpx.Client(timeout=30.0, auth=(self.user, self.token)) as client:
            resp = client.get(
                f"{self.base_url}/rest/api/2/search",
                params={"jql": f"project={project_key}", "maxResults": max_results, "fields": "summary,description,status,assignee,reporter,comment"},
            )
            resp.raise_for_status()
            issues = resp.json().get("issues", [])

            for issue in issues:
                key = issue["key"]
                fields = issue.get("fields", {})
                summary = fields.get("summary", "")
                description = fields.get("description", "") or ""
                status = fields.get("status", {}).get("name", "")
                assignee = (fields.get("assignee") or {}).get("displayName", "")
                reporter = (fields.get("reporter") or {}).get("displayName", "")

                comments_text = ""
                for comment in (fields.get("comment", {}).get("comments", []))[:20]:
                    comments_text += f"\n---\n{comment.get('author', {}).get('displayName', '')}: {comment.get('body', '')[:500]}"

                issue_node = self.graph.upsert_node(
                    "jira_issue", f"{key}: {summary}",
                    external_id=key,
                    source="jira",
                    properties={"status": status, "assignee": assignee, "reporter": reporter},
                )

                if assignee:
                    eng = self.graph.upsert_node("engineer", assignee, external_id=assignee, source="jira")
                    self.graph.add_edge("assigned_to", issue_node, eng)

                _upsert_document(
                    "jira", "issue", f"{key}: {summary}",
                    f"Issue: {key}\nSummary: {summary}\nStatus: {status}\n"
                    f"Assignee: {assignee}\nReporter: {reporter}\n\n"
                    f"{description[:2000]}\n\nComments:{comments_text[:3000]}",
                    key, f"{self.base_url}/browse/{key}",
                )
                stats["issues"] += 1

        return stats


class ConfluenceIndexer:
    """Index Confluence documentation pages."""

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or KnowledgeGraph()
        self.base_url = os.environ.get("CONFLUENCE_URL", "").rstrip("/")
        self.user = os.environ.get("CONFLUENCE_USER", "")
        self.token = os.environ.get("CONFLUENCE_API_TOKEN", "")

    def index_space(self, space_key: str, max_pages: int = 50) -> dict[str, int]:
        if not self.base_url:
            return {"error": "CONFLUENCE_URL not configured"}

        stats = {"pages": 0}
        with httpx.Client(timeout=30.0, auth=(self.user, self.token)) as client:
            resp = client.get(
                f"{self.base_url}/rest/api/content",
                params={
                    "spaceKey": space_key,
                    "limit": max_pages,
                    "expand": "body.storage,version",
                    "type": "page",
                },
            )
            resp.raise_for_status()
            pages = resp.json().get("results", [])

            for page in pages:
                page_id = page["id"]
                title = page.get("title", "")
                body_html = page.get("body", {}).get("storage", {}).get("value", "")

                import re
                body_text = re.sub(r"<[^>]+>", " ", body_html)
                body_text = re.sub(r"\s+", " ", body_text).strip()

                doc_node = self.graph.upsert_node(
                    "documentation", title,
                    external_id=page_id,
                    source="confluence",
                    properties={"space": space_key},
                )

                _upsert_document(
                    "confluence", "page", title,
                    body_text[:10000],
                    page_id,
                    f"{self.base_url}/pages/viewpage.action?pageId={page_id}",
                    {"space": space_key},
                )
                stats["pages"] += 1

        return stats


class JenkinsIndexer:
    """Index Jenkins pipelines and build history."""

    def __init__(self, graph: KnowledgeGraph | None = None) -> None:
        self.graph = graph or KnowledgeGraph()
        self.base_url = os.environ.get("JENKINS_URL", "").rstrip("/")
        self.user = os.environ.get("JENKINS_USER", "")
        self.token = os.environ.get("JENKINS_API_TOKEN", "")

    def index_jobs(self, max_jobs: int = 50) -> dict[str, int]:
        if not self.base_url:
            return {"error": "JENKINS_URL not configured"}

        stats = {"pipelines": 0, "builds": 0}
        with httpx.Client(timeout=30.0, auth=(self.user, self.token)) as client:
            resp = client.get(f"{self.base_url}/api/json", params={"tree": "jobs[name,url,color,lastBuild[number,result,timestamp]]"})
            resp.raise_for_status()
            jobs = resp.json().get("jobs", [])[:max_jobs]

            for job in jobs:
                name = job.get("name", "")
                url = job.get("url", "")
                last_build = job.get("lastBuild") or {}

                pipeline_node = self.graph.upsert_node(
                    "pipeline", name,
                    external_id=name,
                    source="jenkins",
                    properties={
                        "url": url,
                        "status": job.get("color"),
                        "last_build_number": last_build.get("number"),
                        "last_build_result": last_build.get("result"),
                    },
                )

                _upsert_document(
                    "jenkins", "pipeline", name,
                    f"Pipeline: {name}\nStatus: {job.get('color')}\n"
                    f"Last build: #{last_build.get('number', 'N/A')} - {last_build.get('result', 'N/A')}",
                    name, url,
                )
                stats["pipelines"] += 1

        return stats


class RepositoryIntelligenceIndexer:
    """Orchestrates all indexers for a full reindex."""

    def __init__(self) -> None:
        self.graph = KnowledgeGraph()
        self.github = GitHubIndexer(self.graph)
        self.jira = JiraIndexer(self.graph)
        self.confluence = ConfluenceIndexer(self.graph)
        self.jenkins = JenkinsIndexer(self.graph)

    def index_github_repo(self, owner: str, repo: str) -> dict[str, Any]:
        return self.github.index_repository(owner, repo)

    def index_jira_project(self, project_key: str) -> dict[str, Any]:
        return self.jira.index_project(project_key)

    def index_confluence_space(self, space_key: str) -> dict[str, Any]:
        return self.confluence.index_space(space_key)

    def index_jenkins(self) -> dict[str, Any]:
        return self.jenkins.index_jobs()

    def full_index(
        self,
        github_repos: list[str] | None = None,
        jira_projects: list[str] | None = None,
        confluence_spaces: list[str] | None = None,
        include_jenkins: bool = True,
    ) -> dict[str, Any]:
        """Run all indexers. github_repos format: ['owner/repo', ...]"""
        results: dict[str, Any] = {}

        if github_repos:
            for repo_str in github_repos:
                parts = repo_str.split("/", 1)
                if len(parts) == 2:
                    results[f"github:{repo_str}"] = self.github.index_repository(parts[0], parts[1])

        if jira_projects:
            for proj in jira_projects:
                results[f"jira:{proj}"] = self.jira.index_project(proj)

        if confluence_spaces:
            for space in confluence_spaces:
                results[f"confluence:{space}"] = self.confluence.index_space(space)

        if include_jenkins:
            results["jenkins"] = self.jenkins.index_jobs()

        results["graph_stats"] = self.graph.get_stats()
        return results
