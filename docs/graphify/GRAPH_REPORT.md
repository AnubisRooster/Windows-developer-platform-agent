# Graph Report - Windows-developer-platform-agent  (2026-09-21)

## Corpus Check
- 158 files · ~274,652 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 4, .example 2, .log 1)

## Summary
- 1683 nodes · 3186 edges · 125 communities (83 shown, 42 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 195 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- load_workflow()
- KnowledgeGraph
- backend/security/secrets.py
- conftest.py
- typing
- frontend/package.json
- webhooks/server.py
- EmbeddingStore
- backend/main.py
- get_session()
- test_platform_e2e.py
- test_backend_orchestrator.py
- ToolRegistry
- WorkflowEngine
- ToolRegistry
- init_db()
- database/models.py
- test_orchestrator_pipeline.py
- pytest
- test_api_endpoints.py
- create_app()
- IronClawClient
- get_session()
- AgentEvent
- EventBus
- test_markets_feeds_api.py
- EventSource
- AgentEvent
- TestEnvironment
- integrations/gmail.py
- test_knowledge_tools.py
- Planner
- github_integration.py
- compilerOptions
- test_integrations_mock.py
- agent/orchestrator.py
- api.ts
- fetchApi()
- TestChatSend
- integrations/confluence.py
- KnowledgeTools
- _log_event()
- markets/page.tsx
- test_event_gateway.py
- TestEventBusFallback
- WorkflowEngine
- integrations/jira_integration.py
- LLMClient
- EventBus
- test_chat_api.py
- asyncio
- test_planner.py
- backend/workflows/engine.py
- backend/integrations/gmail.py
- backend/integrations/jira_integration.py
- asyncio
- ToolOutput
- backend/integrations/confluence.py
- backend/integrations/jenkins.py
- app/page.tsx
- integrations/slack.py
- TestWindowsPaths
- backend/integrations/slack.py
- test_service_health.py
- graphify_pipeline.py
- _cosine_similarity()
- chat/page.tsx
- patch
- api_model_config_post()
- WorkflowEngine
- SlackCommandGateway
- TestModelConfigAPI
- TestToolRegistry
- create_app()
- LLMClient
- react
- ModelSelector.tsx
- package.json
- TestMarketsEndpoint
- full_app()
- TestDashboardAPI
- logs/page.tsx
- workflow-runs/page.tsx
- TestConversationMemory
- GitHubClient
- JiraClient
- TestDashboardReadsWebhookData
- TestNodeOperations
- agent/tools.py
- _register_tools()
- TestGraphQueries
- TestKnowledgeToolDefinitions
- next.config.js
- TestGitHubWebhook
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
1. `get_session()` - 64 edges
2. `create_app()` - 64 edges
3. `EventBus` - 42 edges
4. `init_db()` - 40 edges
5. `KnowledgeGraph` - 37 edges
6. `EventBus` - 35 edges
7. `get_session()` - 34 edges
8. `_register_tools()` - 28 edges
9. `ToolRegistry` - 27 edges
10. `Orchestrator` - 24 edges

## Surprising Connections (you probably didn't know these)
- `_make_persist_callback()` --uses--> `ToolOutput`  [INFERRED]
  main.py → agent/orchestrator.py
- `_db_persist()` --uses--> `ToolOutput`  [INFERRED]
  tests/integration/test_orchestrator_pipeline.py → agent/orchestrator.py
- `tool_registry()` --uses--> `ToolRegistry`  [INFERRED]
  tests/conftest.py → agent/orchestrator.py
- `memory()` --uses--> `ConversationMemory`  [INFERRED]
  tests/unit/test_conversation_memory.py → backend/agent/memory.py
- `orchestrator()` --uses--> `Orchestrator`  [INFERRED]
  tests/unit/test_backend_orchestrator.py → backend/agent/orchestrator.py

## Import Cycles
- None detected.

## Communities (125 total, 42 thin omitted)

### Community 0 - "load_workflow()"
Cohesion: 0.06
Nodes (34): load_all_workflows(), load_workflow(), _parse_actions(), _parse_trigger(), Any, Path, Workflow loader - load YAML workflow definitions from disk. Supports the new…, Single action in a workflow. (+26 more)

### Community 1 - "KnowledgeGraph"
Cohesion: 0.06
Nodes (27): KnowledgeGraph, Any, Add an edge. Returns True if created, False if already exists., Get neighboring nodes. direction: out, in, both., Trace a commit through the graph: commit → PR → Jira issues → repo., Find documentation nodes related to any entity., Find a repository node by name or external ID., Get graph statistics. (+19 more)

### Community 2 - "backend/security/secrets.py"
Cohesion: 0.06
Nodes (34): AppSecrets, get_secrets(), BaseSettings, LogRecord, Backend secrets management, webhook verification, and redaction. Uses pydantic-…, Logging filter that redacts secrets from log records., Application secrets loaded from environment., Return cached AppSecrets instance. (+26 more)

### Community 3 - "conftest.py"
Cohesion: 0.06
Nodes (25): ConversationMemory, Message, Conversation memory for agent context. Platform-agnostic; uses in-memory…, Single message in conversation., Stores conversation history for agent context., Add a message to the conversation history., Return all messages in order., Return the last N messages (most recent context). (+17 more)

### Community 4 - "typing"
Cohesion: 0.09
Nodes (30): LLM client supporting OpenRouter, OpenAI, and Ollama. Platform-agnostic HTTP…, IronClawClient - HTTP client for IronClaw Rust reasoning engine. IronClaw runs…, SlackCommandGateway - Handles Slack app_mention events, routes to orchestrator.…, AgentMemory, Base, CachedSummary, ChatMessage, _get_database_url() (+22 more)

### Community 5 - "frontend/package.json"
Cohesion: 0.05
Nodes (36): dependencies, next, react, react-dom, recharts, devDependencies, autoprefixer, postcss (+28 more)

### Community 6 - "webhooks/server.py"
Cohesion: 0.08
Nodes (38): fastapi, fastapi_middleware_cors, fastapi_staticfiles, get, api_chat_messages(), api_chat_sessions(), api_conversations(), api_events() (+30 more)

### Community 7 - "EmbeddingStore"
Cohesion: 0.09
Nodes (24): Document, Embedding, Ingested document from any source (code, PR, Jira, Confluence, Jenkins)., Vector embedding for semantic search. Uses pgvector on PostgreSQL, JSON array…, _chunk_text(), EmbeddingStore, get_embeddings(), _get_embeddings_ollama() (+16 more)

### Community 8 - "backend/main.py"
Cohesion: 0.07
Nodes (35): asyncio, atexit, Event Bus with Redis backing and in-memory fallback. Supports wildcard topic…, _build_ironclaw(), cli(), main(), Path, Developer AI Platform - Backend CLI entry point. Commands: run - Full platform:… (+27 more)

### Community 9 - "get_session()"
Cohesion: 0.09
Nodes (19): CachedSummary, get_session(), Session, Get a new database session., Record of a workflow execution., Cached summary (e.g. PR summary, page summary)., Persisted tool output from Orchestrator (DB model; avoids conflict with…, ToolOutputModel (+11 more)

### Community 10 - "test_platform_e2e.py"
Cohesion: 0.10
Nodes (21): ConversationMemory, Any, ConversationMemory - Backend conversation persistence via SQLAlchemy. Stores…, Persists and retrieves conversation messages from the database., Persist a conversation message., Retrieve recent messages for a conversation., Get messages in format suitable for LLM chat API., Orchestrator (+13 more)

### Community 11 - "test_backend_orchestrator.py"
Cohesion: 0.09
Nodes (22): Register knowledge query tools in the capability registry., _register_knowledge_tools(), Any, Tool registry for the backend orchestrator. Registers tools with JSON Schema…, JSON Schema for a tool's parameters., Convert to OpenAPI/JSON Schema format for tool calls., Registered tool with handler and schema., Registry of tools available to the orchestrator. (+14 more)

### Community 12 - "ToolRegistry"
Cohesion: 0.11
Nodes (15): Unit tests for backend tools/registry module., TestBackendToolRegistry, TestToolEntry, TestToolSchema, Any, Tool registry for backend use - ToolSchema, ToolEntry, register, get_handler,…, Schema descriptor for a tool (name, description, parameters)., Registered tool with schema and handler. (+7 more)

### Community 13 - "WorkflowEngine"
Cohesion: 0.11
Nodes (13): Test full flow: event published → workflow engine triggers → tools execute., TestEventWorkflowPipeline, mock_tool_resolver(), mock_tool_resolver(), handler(), mock_tool_resolver(), mock_tool_resolver(), mock_tool_resolver() (+5 more)

### Community 14 - "ToolRegistry"
Cohesion: 0.14
Nodes (9): Agent module: orchestrator, memory, planner, and LLM integration., Orchestrator, Registry for tool handlers with descriptions., Return list of registered tool names., Return mapping of tool name to description., Coordinates LLM and registered tools, parses tool calls, executes them, returns…, ToolRegistry, TestOrchestratorDatabasePipeline (+1 more)

### Community 15 - "init_db()"
Cohesion: 0.12
Nodes (18): Event, init_db(), Standardized event from any webhook or internal source., Workflow execution records., WorkflowRun, index(), Run repository intelligence indexers., sys (+10 more)

### Community 16 - "database/models.py"
Cohesion: 0.11
Nodes (18): ChatSession, Event, _get_data_dir(), get_engine(), Path, SQLAlchemy models and database utilities. Uses pathlib for paths; DATABASE_URL…, Get SQLAlchemy engine from DATABASE_URL or SQLite fallback., Persisted event from EventBus. (+10 more)

### Community 17 - "test_orchestrator_pipeline.py"
Cohesion: 0.12
Nodes (22): persist_tool_output(), Persist a tool output to the database. Use with orchestrator.ToolOutput., main(), _make_persist_callback(), cb(), Main entry point for Windows Developer Platform Agent. Run: python -m main (or…, Create callback that persists ToolOutput to database., Start CLI chat with orchestrator. (+14 more)

### Community 18 - "pytest"
Cohesion: 0.10
Nodes (17): pathlib, pytest, Deployment tests: verify all path handling is Windows-compatible., memory(), fixture, Unit tests for backend ConversationMemory., _sqlite_in_memory(), Unit tests for the enhanced IronClaw client. (+9 more)

### Community 19 - "test_api_endpoints.py"
Cohesion: 0.10
Nodes (12): client(), fixture, Integration tests for FastAPI webhook endpoints., TestEventBusNotConfigured, TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook (+4 more)

### Community 20 - "create_app()"
Cohesion: 0.12
Nodes (15): create_app(), api_chat_new(), api_chat_send(), api_logs(), api_model_config_get(), api_model_config_post(), api_workflow_runs(), _check_ironclaw() (+7 more)

### Community 21 - "IronClawClient"
Cohesion: 0.17
Nodes (11): AsyncClient, IronClawClient, Any, Interpret user message. Returns: - content: str (assistant text) - tool_calls:…, Decompose a goal into an ordered list of steps with tool selections. Returns: -…, Given a task description and available tools, select the best tools to use.…, Summarize text. Uses IronClaw or OpenRouter., HTTP client for IronClaw runtime gateway. Env: IRONCLAW_URL,… (+3 more)

### Community 22 - "get_session()"
Cohesion: 0.10
Nodes (16): get_session(), Session, api_chat_delete(), api_chat_messages(), api_chat_sessions(), api_conversations(), api_document_detail(), api_documents() (+8 more)

### Community 23 - "AgentEvent"
Cohesion: 0.13
Nodes (23): ChatSession, AgentEvent, Event payload for the event bus., ChatMessage, A single message in a chat session (long-term memory)., delete, post, Request (+15 more)

### Community 24 - "EventBus"
Cohesion: 0.13
Nodes (11): EventBus, _consume(), Any, Dispatch event to all matching local handlers., Start consuming events from Redis stream in background., Async event bus with Redis stream backing and wildcard subscription support.…, Lazily connect to Redis., Publish an event to Redis stream and invoke local handlers. Event must have… (+3 more)

### Community 25 - "test_markets_feeds_api.py"
Cohesion: 0.10
Nodes (10): client(), fixture, Integration tests for Markets, Feeds, and Email integration API endpoints., TestIntegrationsConfigEndpoint, TestLinkedInFeedEndpoint, TestOutlookEndpoint, TestStatusIncludesNewIntegrations, TestXFeedEndpoint (+2 more)

### Community 26 - "EventSource"
Cohesion: 0.14
Nodes (8): EventSource, Enum, str, Event types for the backend event bus., _make_event(), Unit tests for EventBus., TestEventBus, TestEventSource

### Community 27 - "AgentEvent"
Cohesion: 0.17
Nodes (12): datetime, EventBus - async pub/sub with wildcard support and persistence., AgentEvent, EventSource, Enum, str, Event types for the developer platform. Platform-agnostic., Event propagated through the event bus. (+4 more)

### Community 28 - "TestEnvironment"
Cohesion: 0.10
Nodes (6): importlib, platform, deployment, Deployment tests: verify environment, dependencies, and configuration., TestEnvironment, TestWindowsCompatibility

### Community 29 - "integrations/gmail.py"
Cohesion: 0.13
Nodes (18): base64, google_auth_oauthlib_flow, google_auth_transport_requests, google_oauth2_credentials, googleapiclient_discovery, googleapiclient_errors, extract_action_items(), _get_service() (+10 more)

### Community 30 - "test_knowledge_tools.py"
Cohesion: 0.12
Nodes (10): asyncio, fixture, Unit tests for KnowledgeTools (query tools for IronClaw)., _sqlite_in_memory(), TestExplainSystem, TestFindRelatedDocs, TestFindRepo, TestSearch (+2 more)

### Community 31 - "Planner"
Cohesion: 0.15
Nodes (11): Planner, Creates action plans by asking LLM to decompose goals into tool steps., Rich console chat loop - start_chat(orchestrator) with pretty printing, command…, Start interactive chat loop with Rich console. Commands: /quit - Exit /clear -…, start_chat(), readline, rich_console, rich_markdown (+3 more)

### Community 32 - "github_integration.py"
Cohesion: 0.19
Nodes (17): _api(), comment_on_pr(), create_branch(), create_issue(), get_repo_activity(), _get_token(), Any, GitHub integration - create_issue, summarize_pull_request, comment_on_pr,… (+9 more)

### Community 33 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 34 - "test_integrations_mock.py"
Cohesion: 0.18
Nodes (13): fetch_build_logs(), get_build_status(), _get_client(), Any, Jenkins integration using python-jenkins. Platform-agnostic., Get Jenkins client from env., Trigger a Jenkins build. Args: job_name: Full job name (may include folder…, Get status of a Jenkins build. Args: job_name: Full job name. build_number:… (+5 more)

### Community 35 - "agent/orchestrator.py"
Cohesion: 0.15
Nodes (9): Orchestrator - coordinates LLM and tools for agent workflows. Supports…, Planner - decomposes goals into tool steps via LLM., Workflow engine - runs event-driven workflows. Uses pathlib.Path for all file…, dataclasses, json, re, Unit tests for LLMClient, Orchestrator, ToolOutput, TOOL_CALL_PATTERN., TestToolCallPattern (+1 more)

### Community 36 - "api.ts"
Cohesion: 0.19
Nodes (13): EventsPage(), payloadPreview(), ToolsPage(), WorkflowsPage(), Event, fetchEvents(), fetchTools(), fetchWorkflows() (+5 more)

### Community 37 - "fetchApi()"
Cohesion: 0.17
Nodes (12): FeedsPage(), Tab, EmailMessage, FeedPost, FeedResponse, fetchApi(), fetchIntegrationsConfig(), fetchLinkedInFeed() (+4 more)

### Community 38 - "TestChatSend"
Cohesion: 0.15
Nodes (5): patch, Each send should include all prior messages in that session's context., A new chat session should NOT include messages from a previous session., TestChatDelete, TestChatSend

### Community 39 - "integrations/confluence.py"
Cohesion: 0.17
Nodes (13): atlassian, Confluence, create_page(), _get_client(), Any, Confluence integration using atlassian-python-api. Platform-agnostic., Get Confluence client from env., Search Confluence for documents matching query. Args: query: Search query… (+5 more)

### Community 40 - "KnowledgeTools"
Cohesion: 0.17
Nodes (9): KnowledgeTools, Any, Knowledge query tools that can be registered in the capability registry., Semantic search across all indexed engineering documents., Find a repository and its relationships (files, pipelines, engineers)., Trace a commit through PRs, Jira issues, and modified files., Find documentation related to a repository, file, or issue., Explain a system or component by combining graph data and document search.… (+1 more)

### Community 41 - "_log_event()"
Cohesion: 0.23
Nodes (16): Verify webhook signature (HMAC-SHA256). - GitHub: X-Hub-Signature-256…, verify_webhook_signature(), github_webhook(), gmail_webhook(), health(), jenkins_webhook(), jira_webhook(), slack_webhook() (+8 more)

### Community 42 - "markets/page.tsx"
Cohesion: 0.18
Nodes (14): ASSET_ORDER, ChartTooltip(), formatLargeNumber(), formatPrice(), MarketsPage(), PriceCard(), PriceChart(), PriceChartProps (+6 more)

### Community 43 - "test_event_gateway.py"
Cohesion: 0.13
Nodes (9): client(), fixture, Unit tests for the Event Gateway (webhook server)., _sqlite_in_memory(), TestGmailWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook (+1 more)

### Community 44 - "TestEventBusFallback"
Cohesion: 0.17
Nodes (4): asyncio, Test in-memory fallback when Redis is unavailable., TestEventBusFallback, handler()

### Community 45 - "WorkflowEngine"
Cohesion: 0.17
Nodes (7): Path, Executes YAML-defined workflows triggered by events., WorkflowEngine, asyncio, TestWorkflowTriggerPipeline, asyncio, TestWorkflowEngine

### Community 46 - "integrations/jira_integration.py"
Cohesion: 0.20
Nodes (14): create_ticket(), _get_client(), get_ticket_details(), link_github_issue(), Any, Jira integration using jira library. Platform-agnostic., Get Jira client from env., Create a Jira ticket. Args: project: Project key (e.g. PROJ). summary: Ticket… (+6 more)

### Community 47 - "LLMClient"
Cohesion: 0.23
Nodes (5): LLMClient, Unified LLM client for OpenRouter, OpenAI, and Ollama., Send chat completion request and return assistant message content. Args:…, patch, TestLLMClient

### Community 48 - "EventBus"
Cohesion: 0.18
Nodes (9): EventBus, Pub/sub event bus with topic wildcards (e.g. github.*, *.opened). Handlers can…, Subscribe to a topic. Supports glob patterns: github.*, *.opened,…, Publish event to all matching subscribers and persist. Args: event: The event…, Check if topic matches pattern (supports * wildcard)., main(), Claw Agent launcher - entry point for packaged executable. Sets up data paths…, Configure environment for packaged or portable run. (+1 more)

### Community 49 - "test_chat_api.py"
Cohesion: 0.15
Nodes (7): client(), fixture, Integration tests for the Chat API endpoints., TestChatMessages, TestChatNewSession, TestChatSessions, _wire_event_bus()

### Community 50 - "asyncio"
Cohesion: 0.18
Nodes (6): asyncio, TestHealth, TestInterpret, TestPlan, TestSelectTools, TestSummarize

### Community 51 - "test_planner.py"
Cohesion: 0.26
Nodes (8): ActionPlan, PlanStep, Single step in an action plan., Plan with goal and ordered steps., Ask LLM to decompose goal into tool steps. Parse JSON response into ActionPlan.…, Unit tests for Planner, PlanStep, ActionPlan., TestActionPlan, TestPlanStep

### Community 52 - "backend/workflows/engine.py"
Cohesion: 0.27
Nodes (10): AgentLog, Structured agent logs for all events, workflows, and decisions., _get_nested(), _log_to_db(), Any, WorkflowEngine - Loads YAML workflows, subscribes to EventBus triggers,…, _render_template(), repl() (+2 more)

### Community 53 - "backend/integrations/gmail.py"
Cohesion: 0.24
Nodes (12): _get_credentials_path(), _get_service(), _get_token_path(), Any, Path, Gmail integration - read_emails, summarize_thread, send_email,…, Get Gmail API service (lazy import)., Read emails matching query. (+4 more)

### Community 54 - "backend/integrations/jira_integration.py"
Cohesion: 0.28
Nodes (12): _api(), create_ticket(), _get_config(), get_ticket_details(), link_github_issue(), Any, Jira integration - create_ticket, update_ticket, link_github_issue,…, Create a Jira ticket. (+4 more)

### Community 55 - "asyncio"
Cohesion: 0.22
Nodes (4): asyncio, TestOrchestratorExecuteTool, TestOrchestratorHandleMessage, TestOrchestratorMemory

### Community 56 - "ToolOutput"
Cohesion: 0.20
Nodes (7): Any, Register a tool by name with its handler and optional description., Get the handler for a tool by name., Process user message: send to LLM, parse TOOL_CALL blocks, execute tools,…, Result of a tool execution., ToolOutput, TestToolOutput

### Community 57 - "backend/integrations/confluence.py"
Cohesion: 0.26
Nodes (11): _api(), create_page(), _get_config(), Any, Confluence integration - search_docs, summarize_page, create_page., Call Confluence REST API., Search Confluence using CQL., Fetch a page and return a text summary (title + body excerpt). (+3 more)

### Community 58 - "backend/integrations/jenkins.py"
Cohesion: 0.26
Nodes (11): _api(), fetch_build_logs(), get_build_status(), _get_config(), Any, Jenkins integration - trigger_build, get_build_status, fetch_build_logs., Call Jenkins API (crumb may be required)., Trigger a Jenkins build. Returns build queue info. (+3 more)

### Community 59 - "app/page.tsx"
Cohesion: 0.23
Nodes (10): integrationNames, StatusPage(), StatusValue, toStatus(), Status, StatusCard(), StatusCardProps, statusDotClass() (+2 more)

### Community 60 - "integrations/slack.py"
Cohesion: 0.18
Nodes (11): _get_client(), Any, Slack integration using slack_sdk. Platform-agnostic., Get Slack WebClient from env token., Read recent messages from a Slack channel. Args: channel: Channel ID or name.…, Respond to a Slack slash command via response_url. Args: response_url: URL…, read_channel_history(), respond_to_command() (+3 more)

### Community 61 - "TestWindowsPaths"
Cohesion: 0.17
Nodes (6): deployment, Scan all .py files for hardcoded /usr, /home, /tmp, ~/. paths., Verify key modules use pathlib.Path instead of os.path.join., Verify the database module can create data directories on Windows., Verify workflow directory glob works on Windows., TestWindowsPaths

### Community 62 - "backend/integrations/slack.py"
Cohesion: 0.27
Nodes (10): _api(), _get_token(), Any, Slack integration - send_message, read_channel_history, respond_to_command., Send a message to a channel (optionally in a thread)., Read recent messages from a channel., Respond to a Slack slash command using the response_url., read_channel_history() (+2 more)

### Community 63 - "test_service_health.py"
Cohesion: 0.18
Nodes (5): fastapi_testclient, deployment, fixture, Deployment tests: verify services can start and respond to health checks., TestServiceHealth

### Community 64 - "graphify_pipeline.py"
Cohesion: 0.18
Nodes (9): graphify_analyze, graphify_build, graphify_cluster, graphify_detect, graphify_export, graphify_extract, graphify_llm, graphify_report (+1 more)

### Community 65 - "_cosine_similarity()"
Cohesion: 0.27
Nodes (5): _cosine_similarity(), Any, Semantic search across all indexed documents. Returns ranked results with…, Compute cosine similarity between two vectors., TestCosineSimilarity

### Community 66 - "chat/page.tsx"
Cohesion: 0.31
Nodes (8): ChatPage(), ChatMessageItem, ChatSessionSummary, createChatSession(), deleteChatSession(), fetchChatMessages(), fetchChatSessions(), sendChatMessage()

### Community 67 - "patch"
Cohesion: 0.29
Nodes (5): Send a message to a Slack channel. Args: channel: Channel ID or name (e.g.…, send_message(), patch, TestJiraIntegration, TestSlackIntegration

### Community 68 - "api_model_config_post()"
Cohesion: 0.24
Nodes (10): api_model_config_post(), _get_dashboard_dir(), _get_data_dir(), _get_model_config_path(), _llm_chat(), _load_model_config(), Path, Dashboard static files (Next.js export). Set CLAW_DASHBOARD_DIR or uses… (+2 more)

### Community 69 - "WorkflowEngine"
Cohesion: 0.28
Nodes (6): Any, Path, Executes workflows from YAML/JSON definitions., Load workflow definition by name., Run a workflow with the given event., WorkflowEngine

### Community 70 - "SlackCommandGateway"
Cohesion: 0.25
Nodes (5): Any, Handles Slack app_mention events and routes to orchestrator., Register app_mention handler on the Slack Bolt app. Expects app to have…, Process a message and return the response. Used when the gateway is called…, SlackCommandGateway

### Community 73 - "create_app()"
Cohesion: 0.25
Nodes (3): create_app(), Any, Create FastAPI webhook application.

### Community 74 - "LLMClient"
Cohesion: 0.33
Nodes (4): LLMClient, Any, Unified LLM client for OpenRouter, OpenAI, and Ollama., Send chat completion request and return assistant message content.

### Community 75 - "react"
Cohesion: 0.33
Nodes (5): ConversationsPage(), Conversation, fetchConversations(), Message, react

### Community 76 - "ModelSelector.tsx"
Cohesion: 0.38
Nodes (6): ModelSelector(), PROVIDERS, AvailableModel, fetchModelConfig(), ModelConfig, updateModelConfig()

### Community 77 - "package.json"
Cohesion: 0.29
Nodes (6): description, name, private, scripts, start, version

### Community 79 - "full_app()"
Cohesion: 0.29
Nodes (6): client(), full_app(), fixture, Create app with event bus and workflow engine wired up., Minimal app, no orchestrator., _sqlite_in_memory()

### Community 81 - "logs/page.tsx"
Cohesion: 0.47
Nodes (5): LevelFilter, logLineColor(), LogsPage(), fetchLogs(), LogEntry

### Community 82 - "workflow-runs/page.tsx"
Cohesion: 0.53
Nodes (5): formatDuration(), statusBadge(), WorkflowRunsPage(), fetchWorkflowRuns(), WorkflowRun

### Community 84 - "GitHubClient"
Cohesion: 0.40
Nodes (3): GitHubClient, GitHub client integration., GitHub API client wrapper.

### Community 85 - "JiraClient"
Cohesion: 0.40
Nodes (3): JiraClient, Jira client integration., Jira API client wrapper.

### Community 88 - "agent/tools.py"
Cohesion: 0.50
Nodes (3): Agent tools - summarization and helpers., Summarize text content., summarize()

### Community 89 - "_register_tools()"
Cohesion: 0.50
Nodes (4): extract_action_items(), Extract action items from email/thread text (simple heuristic)., Register all integration tools and knowledge tools., _register_tools()

## Knowledge Gaps
- **62 isolated node(s):** `nextConfig`, `name`, `version`, `private`, `dev` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 715 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **42 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EventBus` connect `EventBus` to `conftest.py`, `backend/main.py`, `test_platform_e2e.py`, `WorkflowEngine`, `WorkflowEngine`, `full_app()`, `EventBus`, `test_chat_api.py`, `pytest`, `test_api_endpoints.py`, `backend/workflows/engine.py`, `init_db()`, `test_markets_feeds_api.py`, `EventSource`, `test_service_health.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `KnowledgeGraph` connect `KnowledgeGraph` to `typing`, `KnowledgeTools`, `backend/main.py`, `test_platform_e2e.py`, `pytest`, `get_session()`, `test_knowledge_tools.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `create_app()` connect `create_app()` to `backend/security/secrets.py`, `typing`, `EmbeddingStore`, `backend/main.py`, `_log_event()`, `test_platform_e2e.py`, `test_backend_orchestrator.py`, `test_event_gateway.py`, `init_db()`, `full_app()`, `backend/workflows/engine.py`, `get_session()`, `AgentEvent`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `AgentConversation` and `AgentLog`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `EventBus` (e.g. with `run()` and `WorkflowEngine`) actually correct?**
  _`EventBus` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `nextConfig`, `name`, `version` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load_workflow()` be split into smaller, more focused modules?**
  _Cohesion score 0.06313497822931785 - nodes in this community are weakly interconnected._