"""
Developer AI Platform - Backend CLI entry point.

Commands:
  run           - Full platform: IronClaw + workflows + webhooks + knowledge
  webhook-server - Webhooks only
  index         - Run repository intelligence indexers
  reindex-embeddings - Generate embeddings for all documents
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

import click
import uvicorn

_BACKEND_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _BACKEND_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.agent.ironclaw import IronClawClient
from backend.agent.memory import ConversationMemory
from backend.agent.orchestrator import Orchestrator
from backend.database.models import init_db
from backend.events.bus import EventBus
from backend.knowledge.embeddings import EmbeddingStore
from backend.knowledge.graph import KnowledgeGraph
from backend.knowledge.tools import KnowledgeTools
from backend.tools.registry import ToolRegistry, ToolSchema
from backend.webhooks.server import create_app
from backend.workflows.engine import WorkflowEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _workflows_dir() -> Path:
    return _BACKEND_DIR / "workflows"


def _build_ironclaw() -> IronClawClient:
    return IronClawClient(
        ironclaw_url=os.environ.get("IRONCLAW_URL", "http://127.0.0.1:3000"),
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
        openrouter_model=os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4"),
        openrouter_base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        timeout=float(os.environ.get("IRONCLAW_TIMEOUT", "30")),
    )


def _register_tools(registry: ToolRegistry) -> None:
    """Register all integration tools and knowledge tools."""
    from backend.integrations import (
        confluence,
        github_integration,
        gmail,
        jira_integration,
        jenkins,
        slack as slack_int,
    )

    # GitHub
    registry.register(
        "github.create_issue",
        lambda repo, title, body="", labels=None: github_integration.create_issue(repo, title, body, labels),
        ToolSchema("github.create_issue", "Create a GitHub issue", {"type": "object", "properties": {"repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "labels": {"type": "array", "items": {"type": "string"}}}, "required": ["repo", "title"]}),
    )
    registry.register(
        "github.summarize_pr",
        lambda owner, repo, pr_number: github_integration.summarize_pull_request(owner, repo, pr_number),
        ToolSchema("github.summarize_pr", "Summarize a pull request", {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}}, "required": ["owner", "repo", "pr_number"]}),
    )
    registry.register(
        "github.comment_on_pr",
        lambda owner, repo, pr_number, body: github_integration.comment_on_pr(owner, repo, pr_number, body),
        ToolSchema("github.comment_on_pr", "Comment on a PR", {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}, "body": {"type": "string"}}, "required": ["owner", "repo", "pr_number", "body"]}),
    )
    registry.register(
        "github.create_branch",
        lambda owner, repo, branch, from_ref="main": github_integration.create_branch(owner, repo, branch, from_ref),
        ToolSchema("github.create_branch", "Create a branch", {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "branch": {"type": "string"}, "from_ref": {"type": "string"}}, "required": ["owner", "repo", "branch"]}),
    )
    registry.register(
        "github.get_repo_activity",
        lambda owner, repo, limit=10: github_integration.get_repo_activity(owner, repo, limit),
        ToolSchema("github.get_repo_activity", "Get repo activity", {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["owner", "repo"]}),
    )
    registry.register(
        "github.search_repo",
        lambda query, limit=10: github_integration.search_repos(query, limit),
        ToolSchema("github.search_repo", "Search GitHub repositories", {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}),
    )

    # Slack
    registry.register(
        "slack.send_message",
        lambda channel, text, thread_ts=None: slack_int.send_message(channel, text, thread_ts),
        ToolSchema("slack.send_message", "Send Slack message", {"type": "object", "properties": {"channel": {"type": "string"}, "text": {"type": "string"}, "thread_ts": {"type": "string"}}, "required": ["channel", "text"]}),
    )
    registry.register(
        "slack.read_channel_history",
        lambda channel, limit=100: slack_int.read_channel_history(channel, limit),
        ToolSchema("slack.read_channel_history", "Read channel history", {"type": "object", "properties": {"channel": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["channel"]}),
    )
    registry.register(
        "slack.respond_to_command",
        lambda response_url, text: slack_int.respond_to_command(response_url, text),
        ToolSchema("slack.respond_to_command", "Respond to slash command", {"type": "object", "properties": {"response_url": {"type": "string"}, "text": {"type": "string"}}, "required": ["response_url", "text"]}),
    )

    # Jira
    registry.register(
        "jira.create_ticket",
        lambda project, summary, description="", issue_type="Task": jira_integration.create_ticket(project, summary, description, issue_type),
        ToolSchema("jira.create_ticket", "Create Jira ticket", {"type": "object", "properties": {"project": {"type": "string"}, "summary": {"type": "string"}, "description": {"type": "string"}, "issue_type": {"type": "string"}}, "required": ["project", "summary"]}),
    )
    registry.register(
        "jira.update_ticket",
        lambda ticket_key, fields: jira_integration.update_ticket(ticket_key, fields),
        ToolSchema("jira.update_ticket", "Update Jira ticket", {"type": "object", "properties": {"ticket_key": {"type": "string"}, "fields": {"type": "object"}}, "required": ["ticket_key", "fields"]}),
    )
    registry.register(
        "jira.link_github_issue",
        lambda ticket_key, github_url: jira_integration.link_github_issue(ticket_key, github_url),
        ToolSchema("jira.link_github_issue", "Link GitHub URL to Jira", {"type": "object", "properties": {"ticket_key": {"type": "string"}, "github_url": {"type": "string"}}, "required": ["ticket_key", "github_url"]}),
    )
    registry.register(
        "jira.get_ticket_details",
        lambda ticket_key: jira_integration.get_ticket_details(ticket_key),
        ToolSchema("jira.get_ticket_details", "Get Jira ticket details", {"type": "object", "properties": {"ticket_key": {"type": "string"}}, "required": ["ticket_key"]}),
    )

    # Confluence
    registry.register(
        "confluence.search_docs",
        lambda cql, limit=10: confluence.search_docs(cql, limit),
        ToolSchema("confluence.search_docs", "Search Confluence", {"type": "object", "properties": {"cql": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["cql"]}),
    )
    registry.register(
        "confluence.summarize_page",
        lambda page_id: confluence.summarize_page(page_id),
        ToolSchema("confluence.summarize_page", "Summarize Confluence page", {"type": "object", "properties": {"page_id": {"type": "string"}}, "required": ["page_id"]}),
    )
    registry.register(
        "confluence.create_page",
        lambda space_key, title, body, parent_id=None: confluence.create_page(space_key, title, body, parent_id),
        ToolSchema("confluence.create_page", "Create Confluence page", {"type": "object", "properties": {"space_key": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "parent_id": {"type": "string"}}, "required": ["space_key", "title", "body"]}),
    )

    # Jenkins
    registry.register(
        "jenkins.trigger_build",
        lambda job, parameters=None: jenkins.trigger_build(job, parameters),
        ToolSchema("jenkins.trigger_build", "Trigger Jenkins build", {"type": "object", "properties": {"job": {"type": "string"}, "parameters": {"type": "object"}}, "required": ["job"]}),
    )
    registry.register(
        "jenkins.get_build_status",
        lambda job, build_number: jenkins.get_build_status(job, build_number),
        ToolSchema("jenkins.get_build_status", "Get build status", {"type": "object", "properties": {"job": {"type": "string"}, "build_number": {"type": "integer"}}, "required": ["job", "build_number"]}),
    )
    registry.register(
        "jenkins.fetch_build_logs",
        lambda job, build_number: jenkins.fetch_build_logs(job, build_number),
        ToolSchema("jenkins.fetch_build_logs", "Fetch build logs", {"type": "object", "properties": {"job": {"type": "string"}, "build_number": {"type": "integer"}}, "required": ["job", "build_number"]}),
    )

    # Gmail
    registry.register(
        "gmail.read_emails",
        lambda query="in:inbox", max_results=10: gmail.read_emails(query, max_results),
        ToolSchema("gmail.read_emails", "Read emails", {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": []}),
    )
    registry.register(
        "gmail.read_thread",
        lambda thread_id: gmail.summarize_thread(thread_id),
        ToolSchema("gmail.read_thread", "Read and summarize an email thread", {"type": "object", "properties": {"thread_id": {"type": "string"}}, "required": ["thread_id"]}),
    )
    registry.register(
        "gmail.send_email",
        lambda to, subject, body: gmail.send_email(to, subject, body),
        ToolSchema("gmail.send_email", "Send email", {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}),
    )
    registry.register(
        "gmail.extract_action_items",
        lambda text: gmail.extract_action_items(text),
        ToolSchema("gmail.extract_action_items", "Extract action items from text", {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}),
    )


def _register_knowledge_tools(registry: ToolRegistry, knowledge_tools: KnowledgeTools) -> None:
    """Register knowledge query tools in the capability registry."""
    for tool_def in knowledge_tools.get_tool_definitions():
        name = tool_def["name"]
        schema = ToolSchema(name, tool_def["description"], tool_def["parameters"])

        if name == "knowledge.search":
            registry.register(name, lambda **kwargs: asyncio.get_event_loop().run_until_complete(knowledge_tools.search(**kwargs)), schema)
        elif name == "knowledge.find_repo":
            registry.register(name, lambda **kwargs: knowledge_tools.find_repo(**kwargs), schema)
        elif name == "knowledge.trace_commit":
            registry.register(name, lambda **kwargs: knowledge_tools.trace_commit(**kwargs), schema)
        elif name == "knowledge.find_related_docs":
            registry.register(name, lambda **kwargs: knowledge_tools.find_related_docs(**kwargs), schema)
        elif name == "knowledge.explain_system":
            registry.register(name, lambda **kwargs: asyncio.get_event_loop().run_until_complete(knowledge_tools.explain_system(**kwargs)), schema)


@click.group()
def cli() -> None:
    """Developer AI Platform - Backend CLI."""
    pass


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Server host")
@click.option("--port", "-p", default=8080, type=int, help="Server port")
@click.option("--reload", is_flag=True, help="Auto-reload on changes")
def run(host: str, port: int, reload: bool) -> None:
    """Full platform: IronClaw + workflows + event bus + knowledge + webhooks."""
    host = os.environ.get("WEBHOOK_HOST", host)
    port = int(os.environ.get("WEBHOOK_PORT", str(port)))

    init_db()
    ironclaw = _build_ironclaw()
    registry = ToolRegistry()
    _register_tools(registry)

    graph = KnowledgeGraph()
    embeddings = EmbeddingStore()
    knowledge_tools = KnowledgeTools(graph, embeddings)
    _register_knowledge_tools(registry, knowledge_tools)

    memory = ConversationMemory()
    orchestrator = Orchestrator(ironclaw_client=ironclaw, tool_registry=registry, memory=memory)

    redis_url = os.environ.get("REDIS_URL", "")
    event_bus = EventBus(persist=True, redis_url=redis_url)
    workflows_dir = _workflows_dir()
    workflow_engine = WorkflowEngine(event_bus=event_bus, workflows_dir=workflows_dir, tool_executor=orchestrator)
    workflow_engine.load_workflows()
    workflow_engine.subscribe_to_triggers()

    app = create_app(
        orchestrator=orchestrator,
        event_bus=event_bus,
        workflow_engine=workflow_engine,
        ironclaw_client=ironclaw,
    )

    logger.info("Starting Developer AI Platform at http://%s:%s", host, port)
    logger.info("Registered %d tools, %d workflows", len(registry.list_tools()), len(workflow_engine._workflows))
    uvicorn.run(app, host=host, port=port, reload=reload)


@cli.command("webhook-server")
@click.option("--host", "-h", default="127.0.0.1", help="Server host")
@click.option("--port", "-p", default=8080, type=int, help="Server port")
@click.option("--reload", is_flag=True, help="Auto-reload on changes")
def webhook_server(host: str, port: int, reload: bool) -> None:
    """Webhook server only: receives events, no orchestrator."""
    host = os.environ.get("WEBHOOK_HOST", host)
    port = int(os.environ.get("WEBHOOK_PORT", str(port)))

    init_db()
    app = create_app(orchestrator=None, event_bus=None, workflow_engine=None, ironclaw_client=None)

    logger.info("Starting webhook server at http://%s:%s", host, port)
    uvicorn.run(app, host=host, port=port, reload=reload)


@cli.command("index")
@click.option("--github", "-g", multiple=True, help="GitHub repos to index (owner/repo)")
@click.option("--jira", "-j", multiple=True, help="Jira projects to index")
@click.option("--confluence", "-c", multiple=True, help="Confluence spaces to index")
@click.option("--jenkins/--no-jenkins", default=True, help="Index Jenkins pipelines")
@click.option("--embeddings/--no-embeddings", default=True, help="Generate embeddings after indexing")
def index(github: tuple, jira: tuple, confluence: tuple, jenkins: bool, embeddings: bool) -> None:
    """Run repository intelligence indexers."""
    init_db()
    from backend.knowledge.indexer import RepositoryIntelligenceIndexer

    indexer = RepositoryIntelligenceIndexer()
    results = indexer.full_index(
        github_repos=list(github) if github else None,
        jira_projects=list(jira) if jira else None,
        confluence_spaces=list(confluence) if confluence else None,
        include_jenkins=jenkins,
    )
    logger.info("Indexing complete: %s", results)

    if embeddings:
        logger.info("Generating embeddings...")
        store = EmbeddingStore()
        stats = asyncio.run(store.index_all_documents())
        logger.info("Embedding complete: %s", stats)


@cli.command("reindex-embeddings")
@click.option("--source", "-s", default=None, help="Filter by source")
def reindex_embeddings(source: str | None) -> None:
    """Regenerate embeddings for all documents."""
    init_db()
    store = EmbeddingStore()
    stats = asyncio.run(store.index_all_documents(source=source))
    logger.info("Reindex complete: %s", stats)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
