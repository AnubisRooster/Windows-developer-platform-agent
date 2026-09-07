# Graph Report - Windows-developer-platform-agent  (2026-09-07)

## Corpus Check
- 158 files · ~264,308 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1539 nodes · 2707 edges · 125 communities (86 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 166 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- ConversationMemory
- webhooks/server.py
- IronClawClient
- frontend/package.json
- load_workflow()
- test_secrets.py
- set_event_bus()
- test_platform_e2e.py
- test_chat_api.py
- test_markets_feeds_api.py
- ToolRegistry
- EventBus
- backend/main.py
- ToolRegistry
- ToolSchema
- test_workflow_engine.py
- test_event_gateway.py
- test_knowledge_tools.py
- WorkflowRun
- EventBus
- backend/webhooks/server.py
- AgentEvent
- get_session()
- EmbeddingStore
- EventSource
- TestEnvironment
- backend/database/models.py
- github_integration.py
- compilerOptions
- test_integrations_mock.py
- test_embeddings.py
- get_session()
- api.ts
- fetchApi()
- KnowledgeGraph
- KnowledgeTools
- Event
- send_message()
- test_backend_orchestrator.py
- agent/orchestrator.py
- PlanStep
- Base
- Any
- markets/page.tsx
- LLMClient
- integrations/jira_integration.py
- TestWindowsPaths
- test_knowledge_graph.py
- TestEventBusFallback
- Planner
- backend/workflows/engine.py
- backend/integrations/gmail.py
- backend/integrations/jira_integration.py
- embeddings.py
- backend/security/secrets.py
- WorkflowEngine
- integrations/gmail.py
- init_db()
- backend/integrations/confluence.py
- backend/integrations/jenkins.py
- create_page()
- app/page.tsx
- main()
- WorkflowEngine
- backend/integrations/slack.py
- indexer.py
- test_conversation_memory.py
- SlackCommandGateway
- chat/page.tsx
- TestServiceHealth
- _make_event()
- LLMClient
- RepositoryIntelligenceIndexer
- database/models.py
- TestModelConfigAPI
- TestToolRegistry
- .handle_message()
- react
- ModelSelector.tsx
- package.json
- patch
- logs/page.tsx
- workflow-runs/page.tsx
- create_app()
- .get_messages()
- GitHubClient
- JiraClient
- TestDashboardReadsWebhookData
- TestToolCallPattern
- agent/tools.py
- _register_tools()
- TestEdgeOperations
- next.config.js
- graphify_pipeline.py
- backend/agent/__init__.py
- backend/database/__init__.py
- backend/events/__init__.py
- backend/__init__.py
- backend/integrations/__init__.py
- knowledge/__init__.py
- backend/security/__init__.py
- backend/tools/__init__.py
- backend/webhooks/__init__.py
- backend/workflows/__init__.py
- cli/__init__.py
- database/__init__.py
- events/__init__.py
- next-env.d.ts
- integrations/__init__.py
- security/__init__.py
- server/__init__.py
- tools/__init__.py
- webhooks/__init__.py
- workflows/__init__.py

## God Nodes (most connected - your core abstractions)
1. `get_session()` - 48 edges
2. `EventBus` - 42 edges
3. `init_db()` - 40 edges
4. `KnowledgeGraph` - 38 edges
5. `get_session()` - 35 edges
6. `EventBus` - 35 edges
7. `_register_tools()` - 28 edges
8. `ToolRegistry` - 27 edges
9. `Orchestrator` - 24 edges
10. `Base` - 24 edges

## Surprising Connections (you probably didn't know these)
- `_db_persist()` --uses--> `ToolOutput`  [INFERRED]
  tests/integration/test_orchestrator_pipeline.py → agent/orchestrator.py
- `tool_registry()` --uses--> `ToolRegistry`  [INFERRED]
  tests/conftest.py → agent/orchestrator.py
- `memory()` --uses--> `ConversationMemory`  [INFERRED]
  tests/unit/test_conversation_memory.py → backend/agent/memory.py
- `orchestrator()` --uses--> `Orchestrator`  [INFERRED]
  tests/unit/test_backend_orchestrator.py → backend/agent/orchestrator.py
- `TestDatabaseSession` --uses--> `Base`  [INFERRED]
  tests/unit/test_database.py → backend/database/models.py

## Import Cycles
- None detected.

## Communities (125 total, 28 thin omitted)

### Community 0 - "ConversationMemory"
Cohesion: 0.06
Nodes (25): ConversationMemory, Message, Conversation memory for agent context. Platform-agnostic; uses in-memory…, Single message in conversation., Stores conversation history for agent context., Add a message to the conversation history., Return all messages in order., Return the last N messages (most recent context). (+17 more)

### Community 1 - "webhooks/server.py"
Cohesion: 0.08
Nodes (43): get, api_chat_sessions(), api_conversations(), api_events(), api_feeds_linkedin(), api_feeds_x(), api_integrations_config(), api_logs() (+35 more)

### Community 2 - "IronClawClient"
Cohesion: 0.08
Nodes (19): AsyncClient, IronClawClient, Any, IronClawClient - HTTP client for IronClaw Rust reasoning engine. IronClaw runs…, Interpret user message. Returns: - content: str (assistant text) - tool_calls:…, Decompose a goal into an ordered list of steps with tool selections. Returns: -…, Given a task description and available tools, select the best tools to use.…, Summarize text. Uses IronClaw or OpenRouter. (+11 more)

### Community 3 - "frontend/package.json"
Cohesion: 0.05
Nodes (36): dependencies, next, react, react-dom, recharts, devDependencies, autoprefixer, postcss (+28 more)

### Community 4 - "load_workflow()"
Cohesion: 0.10
Nodes (21): Unit tests for workflow loader., Test loading the actual project workflow files., TestLoadAllWorkflows, TestLoadProjectWorkflows, TestLoadWorkflow, TestWorkflowAction, TestWorkflowDefinition, WorkflowEngine - loads YAML workflows, subscribes to EventBus, executes tool… (+13 more)

### Community 5 - "test_secrets.py"
Cohesion: 0.09
Nodes (18): AppSecrets, get_secrets(), BaseSettings, LogRecord, AppSecrets, redaction, webhook signature verification, and logging filter.…, Pydantic BaseSettings for secrets. Loads from env., Get AppSecrets singleton (cached)., Scrub tokens, keys, and secrets from text for safe logging. Args: text: Raw… (+10 more)

### Community 6 - "set_event_bus()"
Cohesion: 0.09
Nodes (16): main(), Claw Agent launcher - entry point for packaged executable. Sets up data paths…, Configure environment for packaged or portable run., _setup_packaged_env(), client(), fixture, Integration tests for FastAPI webhook endpoints., TestEventBusNotConfigured (+8 more)

### Community 7 - "test_platform_e2e.py"
Cohesion: 0.12
Nodes (19): ConversationMemory, ConversationMemory - Backend conversation persistence via SQLAlchemy. Stores…, Persists and retrieves conversation messages from the database., Persist a conversation message., Orchestrator, Any, Backend Orchestrator - Coordinates IronClaw/LLM and tools, persists…, Execute a registered tool and return its result. (+11 more)

### Community 8 - "test_chat_api.py"
Cohesion: 0.08
Nodes (12): client(), fixture, patch, Integration tests for the Chat API endpoints., Each send should include all prior messages in that session's context., A new chat session should NOT include messages from a previous session., TestChatDelete, TestChatMessages (+4 more)

### Community 9 - "test_markets_feeds_api.py"
Cohesion: 0.07
Nodes (12): client(), fixture, Integration tests for Markets, Feeds, and Email integration API endpoints., Second call within 30s should return cached data., TestIntegrationsConfigEndpoint, TestLinkedInFeedEndpoint, TestMarketsEndpoint, TestOutlookEndpoint (+4 more)

### Community 10 - "ToolRegistry"
Cohesion: 0.11
Nodes (15): Unit tests for backend tools/registry module., TestBackendToolRegistry, TestToolEntry, TestToolSchema, Any, Tool registry for backend use - ToolSchema, ToolEntry, register, get_handler,…, Schema descriptor for a tool (name, description, parameters)., Registered tool with schema and handler. (+7 more)

### Community 11 - "EventBus"
Cohesion: 0.13
Nodes (14): AgentEvent, Event payload for the event bus., EventBus, Pub/sub event bus with topic wildcards (e.g. github.*, *.opened). Handlers can…, Subscribe to a topic. Supports glob patterns: github.*, *.opened,…, Publish event to all matching subscribers and persist. Args: event: The event…, Check if topic matches pattern (supports * wildcard)., Test full flow: event published → workflow engine triggers → tools execute. (+6 more)

### Community 12 - "backend/main.py"
Cohesion: 0.11
Nodes (26): _build_ironclaw(), cli(), main(), Path, Developer AI Platform - Backend CLI entry point. Commands: run - Full platform:…, Register knowledge query tools in the capability registry., Launch IronClaw as a child process and wait until its health endpoint responds., Launch cloudflared tunnel as a child process. The tunnel connects to Cloudflare… (+18 more)

### Community 13 - "ToolRegistry"
Cohesion: 0.15
Nodes (12): Orchestrator, Registry for tool handlers with descriptions., Return list of registered tool names., Return mapping of tool name to description., Coordinates LLM and registered tools, parses tool calls, executes them, returns…, ToolRegistry, _db_persist(), fixture (+4 more)

### Community 14 - "ToolSchema"
Cohesion: 0.11
Nodes (14): Any, Tool registry for the backend orchestrator. Registers tools with JSON Schema…, JSON Schema for a tool's parameters., Convert to OpenAPI/JSON Schema format for tool calls., Registered tool with handler and schema., Registry of tools available to the orchestrator., Register a tool by name., Get handler for a tool by name. (+6 more)

### Community 15 - "test_workflow_engine.py"
Cohesion: 0.14
Nodes (17): load_all_workflows(), load_workflow(), _parse_actions(), _parse_trigger(), Any, Path, Workflow loader - load YAML workflow definitions from disk. Supports the new…, Single action in a workflow. (+9 more)

### Community 16 - "test_event_gateway.py"
Cohesion: 0.09
Nodes (10): client(), fixture, Unit tests for the Event Gateway (webhook server)., _sqlite_in_memory(), TestDashboardAPI, TestGmailWebhook, TestHealthEndpoint, TestJenkinsWebhook (+2 more)

### Community 17 - "test_knowledge_tools.py"
Cohesion: 0.09
Nodes (11): asyncio, fixture, Unit tests for KnowledgeTools (query tools for IronClaw)., _sqlite_in_memory(), TestExplainSystem, TestFindRelatedDocs, TestFindRepo, TestKnowledgeToolDefinitions (+3 more)

### Community 18 - "WorkflowRun"
Cohesion: 0.12
Nodes (13): CachedSummary, Cache for summarized content., CachedSummary, Record of a workflow execution., Cached summary (e.g. PR summary, page summary)., Persisted tool output from Orchestrator (DB model; avoids conflict with…, ToolOutputModel, WorkflowRun (+5 more)

### Community 19 - "EventBus"
Cohesion: 0.13
Nodes (10): EventBus, Any, Dispatch event to all matching local handlers., Start consuming events from Redis stream in background., Async event bus with Redis stream backing and wildcard subscription support.…, Lazily connect to Redis., Publish an event to Redis stream and invoke local handlers. Event must have…, EventHandler (+2 more)

### Community 20 - "backend/webhooks/server.py"
Cohesion: 0.13
Nodes (20): Verify webhook signature (HMAC-SHA256). - GitHub: X-Hub-Signature-256…, verify_webhook_signature(), create_app(), _log_event(), _make_event(), _now_iso(), _persist_event(), Any (+12 more)

### Community 21 - "AgentEvent"
Cohesion: 0.17
Nodes (11): EventBus - async pub/sub with wildcard support and persistence., AgentEvent, EventSource, Enum, str, Event types for the developer platform. Platform-agnostic., Event propagated through the event bus., Integration tests for event → workflow execution pipeline. (+3 more)

### Community 22 - "get_session()"
Cohesion: 0.15
Nodes (8): Event, get_session(), Session, Standardized event from any webhook or internal source., sessionmaker, TestWebhookToEventStore, TestGitHubWebhook, TestEventModel

### Community 23 - "EmbeddingStore"
Cohesion: 0.20
Nodes (12): Document, Embedding, Ingested document from any source (code, PR, Jira, Confluence, Jenkins)., Vector embedding for semantic search. Uses pgvector on PostgreSQL, JSON array…, EmbeddingStore, Manages document embeddings for semantic search., Generate and store embeddings for a document. If text is not provided, reads…, Index all unindexed documents. Returns stats. (+4 more)

### Community 24 - "EventSource"
Cohesion: 0.16
Nodes (16): EventSource, Enum, str, Event types for the backend event bus., post, Request, Response, TestEventSource (+8 more)

### Community 25 - "TestEnvironment"
Cohesion: 0.11
Nodes (4): deployment, Deployment tests: verify environment, dependencies, and configuration., TestEnvironment, TestWindowsCompatibility

### Community 26 - "backend/database/models.py"
Cohesion: 0.17
Nodes (12): _get_database_url(), get_engine(), KnowledgeEdge, KnowledgeNode, SQLAlchemy ORM models for the Developer AI Platform. Includes: Event Store,…, Node in the engineering knowledge graph., Edge (relationship) in the engineering knowledge graph., Knowledge Graph - Engineering relationship graph stored in PostgreSQL. Node… (+4 more)

### Community 27 - "github_integration.py"
Cohesion: 0.19
Nodes (17): _api(), comment_on_pr(), create_branch(), create_issue(), get_repo_activity(), _get_token(), Any, GitHub integration - create_issue, summarize_pull_request, comment_on_pr,… (+9 more)

### Community 28 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 29 - "test_integrations_mock.py"
Cohesion: 0.18
Nodes (13): fetch_build_logs(), get_build_status(), _get_client(), Any, Jenkins integration using python-jenkins. Platform-agnostic., Get Jenkins client from env., Trigger a Jenkins build. Args: job_name: Full job name (may include folder…, Get status of a Jenkins build. Args: job_name: Full job name. build_number:… (+5 more)

### Community 30 - "test_embeddings.py"
Cohesion: 0.17
Nodes (9): _chunk_text(), _cosine_similarity(), Split text into overlapping chunks., Compute cosine similarity between two vectors., fixture, Unit tests for the Embedding Store (in-memory cosine similarity)., _sqlite_in_memory(), TestChunking (+1 more)

### Community 31 - "get_session()"
Cohesion: 0.18
Nodes (10): get_session(), persist_tool_output(), Session, Get a new database session., Persist a tool output to the database. Use with orchestrator.ToolOutput., fixture, Unit tests for database models and utilities., sqlite_in_memory() (+2 more)

### Community 32 - "api.ts"
Cohesion: 0.19
Nodes (13): EventsPage(), payloadPreview(), ToolsPage(), WorkflowsPage(), Event, fetchEvents(), fetchTools(), fetchWorkflows() (+5 more)

### Community 33 - "fetchApi()"
Cohesion: 0.17
Nodes (12): FeedsPage(), Tab, EmailMessage, FeedPost, FeedResponse, fetchApi(), fetchIntegrationsConfig(), fetchLinkedInFeed() (+4 more)

### Community 34 - "KnowledgeGraph"
Cohesion: 0.17
Nodes (9): KnowledgeGraph, Get graph statistics., Interface over the PostgreSQL-backed knowledge graph., ConfluenceIndexer, JenkinsIndexer, JiraIndexer, Index Jira issues into documents and knowledge graph., Index Confluence documentation pages. (+1 more)

### Community 35 - "KnowledgeTools"
Cohesion: 0.17
Nodes (9): KnowledgeTools, Any, Knowledge query tools that can be registered in the capability registry., Semantic search across all indexed engineering documents., Find a repository and its relationships (files, pipelines, engineers)., Trace a commit through PRs, Jira issues, and modified files., Find documentation related to a repository, file, or issue., Explain a system or component by combining graph data and document search.… (+1 more)

### Community 36 - "Event"
Cohesion: 0.17
Nodes (9): Event, get_engine(), Get SQLAlchemy engine from DATABASE_URL or SQLite fallback., Persisted event from EventBus., deployment, fixture, Deployment tests: verify database can connect and create schema., TestDatabaseConnectivity (+1 more)

### Community 37 - "send_message()"
Cohesion: 0.17
Nodes (12): _get_client(), Any, Slack integration using slack_sdk. Platform-agnostic., Get Slack WebClient from env token., Send a message to a Slack channel. Args: channel: Channel ID or name (e.g.…, Read recent messages from a Slack channel. Args: channel: Channel ID or name.…, Respond to a Slack slash command via response_url. Args: response_url: URL…, read_channel_history() (+4 more)

### Community 38 - "test_backend_orchestrator.py"
Cohesion: 0.18
Nodes (9): ironclaw_mock(), orchestrator(), asyncio, fixture, Unit tests for the backend Orchestrator (IronClaw + tool registry)., registry(), _sqlite_in_memory(), TestOrchestratorHandleMessage (+1 more)

### Community 39 - "agent/orchestrator.py"
Cohesion: 0.20
Nodes (9): Agent module: orchestrator, memory, planner, and LLM integration., Orchestrator - coordinates LLM and tools for agent workflows. Supports…, Result of a tool execution., ToolOutput, _make_persist_callback(), Main entry point for Windows Developer Platform Agent. Run: python -m main (or…, Create callback that persists ToolOutput to database., Unit tests for LLMClient, Orchestrator, ToolOutput, TOOL_CALL_PATTERN. (+1 more)

### Community 40 - "PlanStep"
Cohesion: 0.23
Nodes (9): ActionPlan, PlanStep, Planner - decomposes goals into tool steps via LLM., Single step in an action plan., Plan with goal and ordered steps., Ask LLM to decompose goal into tool steps. Parse JSON response into ActionPlan.…, Unit tests for Planner, PlanStep, ActionPlan., TestActionPlan (+1 more)

### Community 41 - "Base"
Cohesion: 0.16
Nodes (15): AgentMemory, Base, ChatMessage, ChatSession, Persistent key-value memory for the agent., ChatMessage, A single message in a chat session (long-term memory)., DeclarativeBase (+7 more)

### Community 42 - "Any"
Cohesion: 0.20
Nodes (7): Any, Add an edge. Returns True if created, False if already exists., Get neighboring nodes. direction: out, in, both., Trace a commit through the graph: commit → PR → Jira issues → repo., Find documentation nodes related to any entity., Find a repository node by name or external ID., Create or update a node. Returns node_id.

### Community 43 - "markets/page.tsx"
Cohesion: 0.20
Nodes (13): ASSET_ORDER, ChartTooltip(), formatLargeNumber(), formatPrice(), MarketsPage(), PriceCard(), PriceChart(), PriceChartProps (+5 more)

### Community 44 - "LLMClient"
Cohesion: 0.23
Nodes (5): LLMClient, Unified LLM client for OpenRouter, OpenAI, and Ollama., Send chat completion request and return assistant message content. Args:…, patch, TestLLMClient

### Community 45 - "integrations/jira_integration.py"
Cohesion: 0.22
Nodes (13): create_ticket(), _get_client(), get_ticket_details(), link_github_issue(), Any, Jira integration using jira library. Platform-agnostic., Get Jira client from env., Create a Jira ticket. Args: project: Project key (e.g. PROJ). summary: Ticket… (+5 more)

### Community 46 - "TestWindowsPaths"
Cohesion: 0.14
Nodes (7): deployment, Deployment tests: verify all path handling is Windows-compatible., Scan all .py files for hardcoded /usr, /home, /tmp, ~/. paths., Verify key modules use pathlib.Path instead of os.path.join., Verify the database module can create data directories on Windows., Verify workflow directory glob works on Windows., TestWindowsPaths

### Community 47 - "test_knowledge_graph.py"
Cohesion: 0.15
Nodes (6): graph(), fixture, Unit tests for the Knowledge Graph., _sqlite_in_memory(), TestGraphQueries, TestNodeOperations

### Community 48 - "TestEventBusFallback"
Cohesion: 0.22
Nodes (7): bus(), _no_redis(), asyncio, fixture, Unit tests for the Redis-backed Event Bus (in-memory fallback mode)., Test in-memory fallback when Redis is unavailable., TestEventBusFallback

### Community 49 - "Planner"
Cohesion: 0.23
Nodes (6): Planner, Creates action plans by asking LLM to decompose goals into tool steps., Rich console chat loop - start_chat(orchestrator) with pretty printing, command…, Start interactive chat loop with Rich console. Commands: /quit - Exit /clear -…, start_chat(), TestPlanner

### Community 50 - "backend/workflows/engine.py"
Cohesion: 0.24
Nodes (9): AgentLog, Structured agent logs for all events, workflows, and decisions., Event Bus with Redis backing and in-memory fallback. Supports wildcard topic…, _get_nested(), _log_to_db(), Any, WorkflowEngine - Loads YAML workflows, subscribes to EventBus triggers,…, _render_template() (+1 more)

### Community 51 - "backend/integrations/gmail.py"
Cohesion: 0.24
Nodes (12): _get_credentials_path(), _get_service(), _get_token_path(), Any, Path, Gmail integration - read_emails, summarize_thread, send_email,…, Get Gmail API service (lazy import)., Read emails matching query. (+4 more)

### Community 52 - "backend/integrations/jira_integration.py"
Cohesion: 0.28
Nodes (12): _api(), create_ticket(), _get_config(), get_ticket_details(), link_github_issue(), Any, Jira integration - create_ticket, update_ticket, link_github_issue,…, Create a Jira ticket. (+4 more)

### Community 53 - "embeddings.py"
Cohesion: 0.18
Nodes (10): get_embeddings(), _get_embeddings_ollama(), _get_embeddings_openai(), Any, Embedding Store - Semantic search using pgvector on PostgreSQL (JSON array…, Semantic search across all indexed documents. Returns ranked results with…, Get embeddings from OpenAI-compatible API (OpenAI or OpenRouter)., Get embeddings from a local Ollama instance. (+2 more)

### Community 54 - "backend/security/secrets.py"
Cohesion: 0.18
Nodes (11): AppSecrets, get_secrets(), BaseSettings, LogRecord, Backend secrets management, webhook verification, and redaction. Uses pydantic-…, Logging filter that redacts secrets from log records., Application secrets loaded from environment., Return cached AppSecrets instance. (+3 more)

### Community 55 - "WorkflowEngine"
Cohesion: 0.21
Nodes (7): Path, Executes YAML-defined workflows triggered by events., WorkflowEngine, asyncio, TestWorkflowTriggerPipeline, asyncio, TestWorkflowEngine

### Community 56 - "integrations/gmail.py"
Cohesion: 0.22
Nodes (12): extract_action_items(), _get_service(), Any, Gmail integration using google-api-python-client. Platform-agnostic. Requires…, Send an email. Args: to: Recipient email. subject: Subject line. body: Plain…, Fetch thread and extract action items (heuristic: lines with TODO, FIXME,…, Get Gmail API service with OAuth credentials., Read emails matching query. Args: query: Gmail search query (default: unread).… (+4 more)

### Community 57 - "init_db()"
Cohesion: 0.21
Nodes (7): init_db(), Workflow execution records., WorkflowRun, index(), Run repository intelligence indexers., TestAllTablesCreated, TestWorkflowRunModel

### Community 58 - "backend/integrations/confluence.py"
Cohesion: 0.26
Nodes (11): _api(), create_page(), _get_config(), Any, Confluence integration - search_docs, summarize_page, create_page., Call Confluence REST API., Search Confluence using CQL., Fetch a page and return a text summary (title + body excerpt). (+3 more)

### Community 59 - "backend/integrations/jenkins.py"
Cohesion: 0.26
Nodes (11): _api(), fetch_build_logs(), get_build_status(), _get_config(), Any, Jenkins integration - trigger_build, get_build_status, fetch_build_logs., Call Jenkins API (crumb may be required)., Trigger a Jenkins build. Returns build queue info. (+3 more)

### Community 60 - "create_page()"
Cohesion: 0.23
Nodes (11): Confluence, create_page(), _get_client(), Any, Confluence integration using atlassian-python-api. Platform-agnostic., Get Confluence client from env., Search Confluence for documents matching query. Args: query: Search query…, Fetch a Confluence page and return a text summary. Args: page_id: Confluence… (+3 more)

### Community 61 - "app/page.tsx"
Cohesion: 0.23
Nodes (10): integrationNames, StatusPage(), StatusValue, toStatus(), Status, StatusCard(), StatusCardProps, statusDotClass() (+2 more)

### Community 62 - "main()"
Cohesion: 0.23
Nodes (11): main(), Start CLI chat with orchestrator., patch, Tests for main entry point., Verify main.py can be imported without errors., Verify persist callback can be constructed., Verify main() constructs orchestrator and starts chat., test_main_module_imports() (+3 more)

### Community 63 - "WorkflowEngine"
Cohesion: 0.22
Nodes (7): Any, Path, Workflow engine - runs event-driven workflows. Uses pathlib.Path for all file…, Executes workflows from YAML/JSON definitions., Load workflow definition by name., Run a workflow with the given event., WorkflowEngine

### Community 64 - "backend/integrations/slack.py"
Cohesion: 0.27
Nodes (10): _api(), _get_token(), Any, Slack integration - send_message, read_channel_history, respond_to_command., Send a message to a channel (optionally in a thread)., Read recent messages from a channel., Respond to a Slack slash command using the response_url., read_channel_history() (+2 more)

### Community 65 - "indexer.py"
Cohesion: 0.22
Nodes (7): _github_headers(), GitHubIndexer, Repository Intelligence Indexer. Ingests data from GitHub, Jira, Confluence,…, Create or update a document. Returns doc_id., Index GitHub repositories, files, commits, and pull requests., Index a repository: metadata, files (tree), recent commits, open PRs., _upsert_document()

### Community 66 - "test_conversation_memory.py"
Cohesion: 0.20
Nodes (5): memory(), fixture, Unit tests for backend ConversationMemory., _sqlite_in_memory(), TestConversationMemory

### Community 67 - "SlackCommandGateway"
Cohesion: 0.22
Nodes (6): Any, SlackCommandGateway - Handles Slack app_mention events, routes to orchestrator.…, Handles Slack app_mention events and routes to orchestrator., Register app_mention handler on the Slack Bolt app. Expects app to have…, Process a message and return the response. Used when the gateway is called…, SlackCommandGateway

### Community 68 - "chat/page.tsx"
Cohesion: 0.31
Nodes (8): ChatPage(), ChatMessageItem, ChatSessionSummary, createChatSession(), deleteChatSession(), fetchChatMessages(), fetchChatSessions(), sendChatMessage()

### Community 69 - "TestServiceHealth"
Cohesion: 0.20
Nodes (4): deployment, fixture, Deployment tests: verify services can start and respond to health checks., TestServiceHealth

### Community 71 - "LLMClient"
Cohesion: 0.25
Nodes (5): LLMClient, Any, LLM client supporting OpenRouter, OpenAI, and Ollama. Platform-agnostic HTTP…, Unified LLM client for OpenRouter, OpenAI, and Ollama., Send chat completion request and return assistant message content.

### Community 72 - "RepositoryIntelligenceIndexer"
Cohesion: 0.33
Nodes (4): Any, Orchestrates all indexers for a full reindex., Run all indexers. github_repos format: ['owner/repo', ...], RepositoryIntelligenceIndexer

### Community 73 - "database/models.py"
Cohesion: 0.22
Nodes (8): ChatSession, _get_data_dir(), Path, SQLAlchemy models and database utilities. Uses pathlib for paths; DATABASE_URL…, A chat session. Each new chat starts a fresh session (clean context window)., Data directory for DB and config. CLAW_DATA_DIR or ./data., api_chat_new(), Create a new chat session with a fresh context window.

### Community 76 - ".handle_message()"
Cohesion: 0.29
Nodes (4): Any, Register a tool by name with its handler and optional description., Get the handler for a tool by name., Process user message: send to LLM, parse TOOL_CALL blocks, execute tools,…

### Community 77 - "react"
Cohesion: 0.33
Nodes (5): ConversationsPage(), Conversation, fetchConversations(), Message, react

### Community 78 - "ModelSelector.tsx"
Cohesion: 0.38
Nodes (6): ModelSelector(), PROVIDERS, AvailableModel, fetchModelConfig(), ModelConfig, updateModelConfig()

### Community 79 - "package.json"
Cohesion: 0.29
Nodes (6): description, name, private, scripts, start, version

### Community 80 - "patch"
Cohesion: 0.38
Nodes (3): patch, TestConfluenceIntegration, TestJiraIntegration

### Community 81 - "logs/page.tsx"
Cohesion: 0.47
Nodes (5): LevelFilter, logLineColor(), LogsPage(), fetchLogs(), LogEntry

### Community 82 - "workflow-runs/page.tsx"
Cohesion: 0.53
Nodes (5): formatDuration(), statusBadge(), WorkflowRunsPage(), fetchWorkflowRuns(), WorkflowRun

### Community 83 - "create_app()"
Cohesion: 0.40
Nodes (5): create_app(), Any, FastAPI, Webhook server - receives events from Slack, GitHub, Jira, Jenkins. Uses…, Create FastAPI webhook application.

### Community 84 - ".get_messages()"
Cohesion: 0.40
Nodes (3): Any, Retrieve recent messages for a conversation., Get messages in format suitable for LLM chat API.

### Community 85 - "GitHubClient"
Cohesion: 0.40
Nodes (3): GitHubClient, GitHub client integration., GitHub API client wrapper.

### Community 86 - "JiraClient"
Cohesion: 0.40
Nodes (3): JiraClient, Jira client integration., Jira API client wrapper.

### Community 89 - "agent/tools.py"
Cohesion: 0.50
Nodes (3): Agent tools - summarization and helpers., Summarize text content., summarize()

### Community 90 - "_register_tools()"
Cohesion: 0.50
Nodes (4): extract_action_items(), Extract action items from email/thread text (simple heuristic)., Register all integration tools and knowledge tools., _register_tools()

## Knowledge Gaps
- **62 isolated node(s):** `nextConfig`, `name`, `version`, `private`, `dev` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 639 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EventBus` connect `EventBus` to `ConversationMemory`, `TestServiceHealth`, `set_event_bus()`, `test_platform_e2e.py`, `test_chat_api.py`, `test_markets_feeds_api.py`, `_make_event()`, `EventBus`, `backend/main.py`, `test_workflow_engine.py`, `TestEventBusFallback`, `backend/workflows/engine.py`, `backend/webhooks/server.py`, `WorkflowEngine`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `ToolRegistry` connect `ToolRegistry` to `ConversationMemory`, `agent/orchestrator.py`, `TestToolRegistry`, `.handle_message()`, `main()`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `event_bus()` connect `ConversationMemory` to `EventBus`, `EventBus`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `EventBus` (e.g. with `run()` and `WorkflowEngine`) actually correct?**
  _`EventBus` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `KnowledgeGraph` (e.g. with `KnowledgeEdge` and `KnowledgeNode`) actually correct?**
  _`KnowledgeGraph` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `nextConfig`, `name`, `version` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ConversationMemory` be split into smaller, more focused modules?**
  _Cohesion score 0.057004830917874394 - nodes in this community are weakly interconnected._