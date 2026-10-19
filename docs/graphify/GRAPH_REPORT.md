# Graph Report - Windows-developer-platform-agent  (2026-10-19)

## Corpus Check
- 158 files · ~187,183 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 4, .example 2, .log 1)

## Summary
- 1683 nodes · 3289 edges · 119 communities (59 shown, 60 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 258 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- KnowledgeGraph
- get_session()
- backend/security/secrets.py
- conftest.py
- webhooks/server.py
- frontend/package.json
- get_session()
- IronClawClient
- test_knowledge_tools.py
- load_workflow()
- ToolRegistry
- backend/database/models.py
- EventBus
- backend/main.py
- ToolRegistry
- init_db()
- WorkflowEngine
- ToolSchema
- test_api_endpoints.py
- os
- test_workflow_engine.py
- pytest
- Planner
- test_markets_feeds_api.py
- TestEnvironment
- test_redis_event_bus.py
- _register_tools()
- main.py
- EventSource
- integrations/gmail.py
- app/page.tsx
- integrations/slack.py
- test_integrations_mock.py
- compilerOptions
- integrations/jira_integration.py
- AgentEvent
- test_platform_e2e.py
- TestChatSend
- markets/page.tsx
- integrations/jenkins.py
- test_event_gateway.py
- Base
- backend/integrations/gmail.py
- api.ts
- feeds/page.tsx
- LLMClient
- Orchestrator
- backend/workflows/engine.py
- EventBus
- test_chat_api.py
- test_orchestrator.py
- backend/integrations/jira_integration.py
- ConversationMemory
- backend/integrations/confluence.py
- backend/integrations/jenkins.py
- httpx
- create_app()
- fetchApi()
- TestWindowsPaths
- _register_knowledge_tools()
- test_service_health.py
- asyncio
- test_conversation_memory.py
- test_backend_orchestrator.py
- WorkflowEngine
- SlackCommandGateway
- react
- TestModelConfigAPI
- _chunk_text()
- LLMClient
- package.json
- TestMarketsEndpoint
- TestDashboardAPI
- TestToolRegistry
- .get_tool_definitions()
- logs/page.tsx
- workflow-runs/page.tsx
- Event
- WorkflowRun
- GitHubClient
- JiraClient
- TestDashboardReadsWebhookData
- agent/tools.py
- next.config.js

## God Nodes (most connected - your core abstractions)
1. `get_session()` - 64 edges
2. `create_app()` - 64 edges
3. `EventBus` - 42 edges
4. `init_db()` - 40 edges
5. `KnowledgeGraph` - 38 edges
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
- `TestOrchestratorPipeline` --uses--> `Orchestrator`  [INFERRED]
  tests/integration/test_platform_e2e.py → backend/agent/orchestrator.py

## Import Cycles
- None detected.

## Communities (119 total, 60 thin omitted)

### Community 0 - "KnowledgeGraph"
Cohesion: 0.05
Nodes (16): KnowledgeEdge, KnowledgeNode, KnowledgeGraph, ConfluenceIndexer, _github_headers(), GitHubIndexer, JenkinsIndexer, JiraIndexer (+8 more)

### Community 1 - "get_session()"
Cohesion: 0.06
Nodes (39): get_session(), verify_webhook_signature(), create_app(), api_chat_delete(), api_chat_messages(), api_chat_new(), api_chat_send(), api_chat_sessions() (+31 more)

### Community 2 - "backend/security/secrets.py"
Cohesion: 0.06
Nodes (13): AppSecrets, get_secrets(), redact(), RedactingFilter, AppSecrets, get_secrets(), redact(), RedactingFilter (+5 more)

### Community 3 - "conftest.py"
Cohesion: 0.06
Nodes (11): ConversationMemory, Message, env_secrets(), event_bus(), memory(), _reset_db_globals(), _reset_secrets_cache(), tmp_workflow_dir() (+3 more)

### Community 4 - "webhooks/server.py"
Cohesion: 0.07
Nodes (26): api_chat_messages(), api_chat_sessions(), api_conversations(), api_events(), api_feeds_linkedin(), api_feeds_x(), api_integrations_config(), api_logs() (+18 more)

### Community 5 - "frontend/package.json"
Cohesion: 0.05
Nodes (36): dependencies, next, react, react-dom, recharts, devDependencies, autoprefixer, postcss (+28 more)

### Community 6 - "get_session()"
Cohesion: 0.08
Nodes (12): CachedSummary, CachedSummary, get_session(), persist_tool_output(), ToolOutputModel, WorkflowRun, TestDatabaseIntegration, _use_sqlite() (+4 more)

### Community 7 - "IronClawClient"
Cohesion: 0.10
Nodes (7): IronClawClient, client(), TestHealth, TestInterpret, TestPlan, TestSelectTools, TestSummarize

### Community 8 - "test_knowledge_tools.py"
Cohesion: 0.08
Nodes (8): KnowledgeTools, _sqlite_in_memory(), TestExplainSystem, TestFindRelatedDocs, TestFindRepo, TestSearch, TestTraceCommit, tools()

### Community 9 - "load_workflow()"
Cohesion: 0.10
Nodes (10): TestLoadAllWorkflows, TestLoadProjectWorkflows, TestLoadWorkflow, TestWorkflowAction, TestWorkflowDefinition, load_all_workflows(), load_workflow(), _load_yaml() (+2 more)

### Community 10 - "ToolRegistry"
Cohesion: 0.12
Nodes (6): Orchestrator, ToolRegistry, _db_persist(), TestOrchestratorDatabasePipeline, _use_sqlite(), TestOrchestrator

### Community 12 - "backend/database/models.py"
Cohesion: 0.10
Nodes (7): _get_database_url(), get_engine(), Event, _get_data_dir(), get_engine(), TestDatabaseConnectivity, _use_sqlite()

### Community 13 - "EventBus"
Cohesion: 0.10
Nodes (3): EventBus, _consume(), TestWorkflowEngine

### Community 14 - "backend/main.py"
Cohesion: 0.12
Nodes (10): _build_ironclaw(), cli(), main(), run(), _start_cloudflared(), _start_ironclaw(), _stop_all_children(), _stop_child() (+2 more)

### Community 15 - "ToolRegistry"
Cohesion: 0.11
Nodes (6): TestBackendToolRegistry, TestToolEntry, TestToolSchema, ToolEntry, ToolRegistry, ToolSchema

### Community 16 - "init_db()"
Cohesion: 0.15
Nodes (10): Document, Embedding, init_db(), EmbeddingStore, TestKnowledgePipeline, TestEmbeddingStore, _sqlite_in_memory(), TestAllTablesCreated (+2 more)

### Community 17 - "WorkflowEngine"
Cohesion: 0.11
Nodes (8): TestEventWorkflowPipeline, mock_tool_resolver(), mock_tool_resolver(), handler(), mock_tool_resolver(), mock_tool_resolver(), mock_tool_resolver(), WorkflowEngine

### Community 18 - "ToolSchema"
Cohesion: 0.12
Nodes (4): ToolEntry, ToolRegistry, ToolSchema, TestOrchestratorPipeline

### Community 19 - "test_api_endpoints.py"
Cohesion: 0.10
Nodes (9): client(), TestEventBusNotConfigured, TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook, _wire_event_bus() (+1 more)

### Community 20 - "os"
Cohesion: 0.12
Nodes (6): _cosine_similarity(), get_embeddings(), _get_embeddings_ollama(), _get_embeddings_openai(), _sqlite_in_memory(), TestCosineSimilarity

### Community 21 - "test_workflow_engine.py"
Cohesion: 0.13
Nodes (8): load_all_workflows(), load_workflow(), _parse_actions(), _parse_trigger(), WorkflowAction, WorkflowDefinition, _sqlite_in_memory(), TestWorkflowLoader

### Community 22 - "pytest"
Cohesion: 0.16
Nodes (3): AgentEvent, EventSource, TestAgentEvent

### Community 23 - "Planner"
Cohesion: 0.18
Nodes (6): ActionPlan, Planner, PlanStep, TestActionPlan, TestPlanner, TestPlanStep

### Community 24 - "test_markets_feeds_api.py"
Cohesion: 0.10
Nodes (8): client(), TestIntegrationsConfigEndpoint, TestLinkedInFeedEndpoint, TestOutlookEndpoint, TestStatusIncludesNewIntegrations, TestXFeedEndpoint, TestZohoEndpoint, _wire_event_bus()

### Community 26 - "test_redis_event_bus.py"
Cohesion: 0.13
Nodes (4): bus(), _no_redis(), TestEventBusFallback, handler()

### Community 27 - "_register_tools()"
Cohesion: 0.19
Nodes (9): _api(), comment_on_pr(), create_branch(), create_issue(), get_repo_activity(), _get_token(), search_repos(), summarize_pull_request() (+1 more)

### Community 28 - "main.py"
Cohesion: 0.14
Nodes (7): start_chat(), main(), _make_persist_callback(), cb(), test_main_module_imports(), test_main_wires_orchestrator(), test_make_persist_callback()

### Community 29 - "EventSource"
Cohesion: 0.16
Nodes (4): EventSource, _make_event(), TestEventBus, TestEventSource

### Community 30 - "integrations/gmail.py"
Cohesion: 0.14
Nodes (5): extract_action_items(), _get_service(), read_emails(), send_email(), summarize_thread()

### Community 31 - "app/page.tsx"
Cohesion: 0.16
Nodes (16): integrationNames, StatusPage(), StatusValue, toStatus(), ModelSelector(), PROVIDERS, Status, StatusCard() (+8 more)

### Community 32 - "integrations/slack.py"
Cohesion: 0.15
Nodes (5): _get_client(), read_channel_history(), respond_to_command(), send_message(), TestSlackIntegration

### Community 33 - "test_integrations_mock.py"
Cohesion: 0.16
Nodes (5): create_page(), _get_client(), search_docs(), summarize_page(), TestConfluenceIntegration

### Community 34 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 35 - "integrations/jira_integration.py"
Cohesion: 0.16
Nodes (6): create_ticket(), _get_client(), get_ticket_details(), link_github_issue(), update_ticket(), TestJiraIntegration

### Community 36 - "AgentEvent"
Cohesion: 0.19
Nodes (8): AgentEvent, api_chat_new(), api_model_config_post(), github_webhook(), jenkins_webhook(), jira_webhook(), _save_model_config(), slack_webhook()

### Community 37 - "test_platform_e2e.py"
Cohesion: 0.17
Nodes (5): WorkflowEngine, client(), full_app(), _sqlite_in_memory(), TestWorkflowTriggerPipeline

### Community 39 - "markets/page.tsx"
Cohesion: 0.21
Nodes (14): ASSET_ORDER, ChartTooltip(), formatLargeNumber(), formatPrice(), MarketsPage(), PriceCard(), PriceChart(), PriceChartProps (+6 more)

### Community 40 - "integrations/jenkins.py"
Cohesion: 0.18
Nodes (5): fetch_build_logs(), get_build_status(), _get_client(), trigger_build(), TestJenkinsIntegration

### Community 41 - "test_event_gateway.py"
Cohesion: 0.13
Nodes (7): client(), _sqlite_in_memory(), TestGmailWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook

### Community 42 - "Base"
Cohesion: 0.16
Nodes (8): AgentMemory, Base, ChatMessage, ChatSession, ChatMessage, ChatSession, api_chat_delete(), api_chat_send()

### Community 43 - "backend/integrations/gmail.py"
Cohesion: 0.20
Nodes (7): extract_action_items(), _get_credentials_path(), _get_service(), _get_token_path(), read_emails(), send_email(), summarize_thread()

### Community 44 - "api.ts"
Cohesion: 0.22
Nodes (12): ConversationsPage(), MessageBubble(), EventsPage(), payloadPreview(), Conversation, Event, fetchConversations(), fetchEvents() (+4 more)

### Community 45 - "feeds/page.tsx"
Cohesion: 0.21
Nodes (14): EmailRow(), FeedsPage(), LinkedInPost(), NotConfigured(), Tab, XPost(), EmailMessage, FeedPost (+6 more)

### Community 48 - "backend/workflows/engine.py"
Cohesion: 0.24
Nodes (7): AgentLog, _get_nested(), _log_to_db(), _render_template(), repl(), _resolve_args(), handler()

### Community 49 - "EventBus"
Cohesion: 0.18
Nodes (3): EventBus, main(), _setup_packaged_env()

### Community 51 - "test_chat_api.py"
Cohesion: 0.15
Nodes (5): client(), TestChatMessages, TestChatNewSession, TestChatSessions, _wire_event_bus()

### Community 52 - "test_orchestrator.py"
Cohesion: 0.19
Nodes (3): ToolOutput, TestToolCallPattern, TestToolOutput

### Community 53 - "backend/integrations/jira_integration.py"
Cohesion: 0.28
Nodes (6): _api(), create_ticket(), _get_config(), get_ticket_details(), link_github_issue(), update_ticket()

### Community 55 - "backend/integrations/confluence.py"
Cohesion: 0.26
Nodes (5): _api(), create_page(), _get_config(), search_docs(), summarize_page()

### Community 56 - "backend/integrations/jenkins.py"
Cohesion: 0.26
Nodes (5): _api(), fetch_build_logs(), get_build_status(), _get_config(), trigger_build()

### Community 57 - "httpx"
Cohesion: 0.27
Nodes (5): _api(), _get_token(), read_channel_history(), respond_to_command(), send_message()

### Community 59 - "fetchApi()"
Cohesion: 0.32
Nodes (11): ChatPage(), MessageBubble(), ChatMessageItem, ChatSessionSummary, createChatSession(), deleteChatSession(), fetchApi(), fetchChatMessages() (+3 more)

### Community 61 - "_register_knowledge_tools()"
Cohesion: 0.24
Nodes (3): index(), _register_knowledge_tools(), reindex_embeddings()

### Community 64 - "test_conversation_memory.py"
Cohesion: 0.20
Nodes (3): memory(), _sqlite_in_memory(), TestConversationMemory

### Community 65 - "test_backend_orchestrator.py"
Cohesion: 0.27
Nodes (6): api_tools(), ironclaw_mock(), orchestrator(), registry(), _sqlite_in_memory(), TestOrchestratorMemory

### Community 68 - "react"
Cohesion: 0.28
Nodes (7): ToolsPage(), WorkflowsPage(), fetchTools(), fetchWorkflows(), Tool, Workflow, react

### Community 74 - "package.json"
Cohesion: 0.29
Nodes (6): description, name, private, scripts, start, version

### Community 79 - "logs/page.tsx"
Cohesion: 0.47
Nodes (5): LevelFilter, logLineColor(), LogsPage(), fetchLogs(), LogEntry

### Community 80 - "workflow-runs/page.tsx"
Cohesion: 0.53
Nodes (5): formatDuration(), statusBadge(), WorkflowRunsPage(), fetchWorkflowRuns(), WorkflowRun

## Knowledge Gaps
- **7 isolated node(s):** `react-dom`, `@types/node`, `@types/react`, `@types/react-dom`, `autoprefixer` (+2 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 684 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **60 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EventBus` connect `EventBus` to `conftest.py`, `test_platform_e2e.py`, `typing`, `backend/main.py`, `backend/workflows/engine.py`, `EventBus`, `WorkflowEngine`, `test_api_endpoints.py`, `test_chat_api.py`, `test_workflow_engine.py`, `test_markets_feeds_api.py`, `test_redis_event_bus.py`, `EventSource`, `test_service_health.py`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `AgentConversation` and `AgentLog`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `react-dom`, `@types/node`, `@types/react` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `KnowledgeGraph` be split into smaller, more focused modules?**
  _Cohesion score 0.05160662122687439 - nodes in this community are weakly interconnected._
- **Why does `KnowledgeGraph` connect `KnowledgeGraph` to `test_knowledge_tools.py`, `init_db()`, `test_platform_e2e.py`, `backend/main.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `EventBus` (e.g. with `run()` and `WorkflowEngine`) actually correct?**
  _`EventBus` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `get_session()` be split into smaller, more focused modules?**
  _Cohesion score 0.055178652193577565 - nodes in this community are weakly interconnected._