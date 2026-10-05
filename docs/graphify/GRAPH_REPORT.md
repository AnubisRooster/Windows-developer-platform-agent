# Graph Report - Windows-developer-platform-agent  (2026-10-05)

## Corpus Check
- 158 files · ~291,274 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 4, .example 2, .log 1)

## Summary
- 1683 nodes · 3226 edges · 125 communities (59 shown, 66 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 195 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- load_workflow()
- KnowledgeGraph
- backend/security/secrets.py
- conftest.py
- frontend/package.json
- webhooks/server.py
- backend/main.py
- get_session()
- ToolRegistry
- EmbeddingStore
- test_platform_e2e.py
- ToolRegistry
- WorkflowEngine
- os
- init_db()
- database/models.py
- test_api_endpoints.py
- create_app()
- IronClawClient
- get_session()
- AgentEvent
- EventBus
- test_backend_orchestrator.py
- Planner
- persist_tool_output()
- test_markets_feeds_api.py
- embeddings.py
- AgentEvent
- TestEnvironment
- integrations/gmail.py
- app/page.tsx
- integrations/slack.py
- test_event_gateway.py
- test_knowledge_tools.py
- pytest
- test_integrations_mock.py
- github_integration.py
- ToolRegistry
- compilerOptions
- integrations/jira_integration.py
- TestChatSend
- KnowledgeTools
- _log_event()
- markets/page.tsx
- integrations/jenkins.py
- TestEventBusFallback
- WorkflowEngine
- api.ts
- feeds/page.tsx
- LLMClient
- EventBus
- test_chat_api.py
- asyncio
- backend/workflows/engine.py
- backend/integrations/gmail.py
- backend/integrations/jira_integration.py
- _make_event()
- test_knowledge_graph.py
- ToolOutput
- backend/integrations/confluence.py
- backend/integrations/jenkins.py
- create_app()
- fetchApi()
- TestWindowsPaths
- backend/integrations/slack.py
- test_service_health.py
- api_model_config_post()
- WorkflowEngine
- SlackCommandGateway
- react
- TestModelConfigAPI
- TestToolRegistry
- EventSource
- LLMClient
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
- TestToolCallPattern
- agent/tools.py
- _register_tools()
- TestKnowledgeToolDefinitions
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
- `orchestrator()` --uses--> `Orchestrator`  [INFERRED]
  tests/unit/test_backend_orchestrator.py → backend/agent/orchestrator.py

## Import Cycles
- None detected.

## Communities (125 total, 66 thin omitted)

### Community 0 - "load_workflow()"
Cohesion: 0.06
Nodes (17): load_all_workflows(), load_workflow(), _parse_actions(), _parse_trigger(), WorkflowAction, WorkflowDefinition, TestWorkflowLoader, TestLoadAllWorkflows (+9 more)

### Community 1 - "KnowledgeGraph"
Cohesion: 0.06
Nodes (9): KnowledgeGraph, ConfluenceIndexer, _github_headers(), GitHubIndexer, JenkinsIndexer, JiraIndexer, RepositoryIntelligenceIndexer, _upsert_document() (+1 more)

### Community 2 - "backend/security/secrets.py"
Cohesion: 0.06
Nodes (13): AppSecrets, get_secrets(), redact(), RedactingFilter, AppSecrets, get_secrets(), redact(), RedactingFilter (+5 more)

### Community 3 - "conftest.py"
Cohesion: 0.06
Nodes (11): ConversationMemory, Message, env_secrets(), event_bus(), memory(), _reset_db_globals(), _reset_secrets_cache(), tmp_workflow_dir() (+3 more)

### Community 4 - "frontend/package.json"
Cohesion: 0.05
Nodes (36): dependencies, next, react, react-dom, recharts, devDependencies, autoprefixer, postcss (+28 more)

### Community 5 - "webhooks/server.py"
Cohesion: 0.08
Nodes (21): api_chat_messages(), api_chat_sessions(), api_conversations(), api_events(), api_feeds_linkedin(), api_feeds_x(), api_integrations_config(), api_logs() (+13 more)

### Community 6 - "backend/main.py"
Cohesion: 0.09
Nodes (13): _build_ironclaw(), cli(), index(), main(), _register_knowledge_tools(), reindex_embeddings(), run(), _start_cloudflared() (+5 more)

### Community 7 - "get_session()"
Cohesion: 0.09
Nodes (10): CachedSummary, get_session(), ToolOutputModel, WorkflowRun, TestDatabaseIntegration, _use_sqlite(), sqlite_in_memory(), TestDatabaseSession (+2 more)

### Community 8 - "ToolRegistry"
Cohesion: 0.12
Nodes (6): Orchestrator, ToolRegistry, _db_persist(), TestOrchestratorDatabasePipeline, _use_sqlite(), TestOrchestrator

### Community 9 - "EmbeddingStore"
Cohesion: 0.12
Nodes (8): Document, Embedding, _chunk_text(), EmbeddingStore, _sqlite_in_memory(), TestChunking, TestEmbeddingStore, TestEmbeddingModel

### Community 10 - "test_platform_e2e.py"
Cohesion: 0.12
Nodes (5): ConversationMemory, Orchestrator, AgentConversation, ToolOutput, TestOrchestratorPipeline

### Community 11 - "ToolRegistry"
Cohesion: 0.11
Nodes (6): TestBackendToolRegistry, TestToolEntry, TestToolSchema, ToolEntry, ToolRegistry, ToolSchema

### Community 12 - "WorkflowEngine"
Cohesion: 0.11
Nodes (8): TestEventWorkflowPipeline, mock_tool_resolver(), mock_tool_resolver(), handler(), mock_tool_resolver(), mock_tool_resolver(), mock_tool_resolver(), WorkflowEngine

### Community 13 - "os"
Cohesion: 0.13
Nodes (8): AgentMemory, CachedSummary, ChatMessage, _get_database_url(), get_engine(), KnowledgeEdge, KnowledgeNode, TestKnowledgeGraphModels

### Community 14 - "init_db()"
Cohesion: 0.13
Nodes (11): Base, Event, init_db(), WorkflowRun, memory(), _sqlite_in_memory(), _sqlite_in_memory(), TestAllTablesCreated (+3 more)

### Community 15 - "database/models.py"
Cohesion: 0.10
Nodes (6): ChatSession, Event, _get_data_dir(), get_engine(), TestDatabaseConnectivity, _use_sqlite()

### Community 16 - "test_api_endpoints.py"
Cohesion: 0.10
Nodes (9): client(), TestEventBusNotConfigured, TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook, _wire_event_bus() (+1 more)

### Community 17 - "create_app()"
Cohesion: 0.12
Nodes (13): create_app(), api_chat_send(), api_document_detail(), api_logs(), api_model_config_get(), api_model_config_post(), api_workflow_runs(), _check_ironclaw() (+5 more)

### Community 20 - "get_session()"
Cohesion: 0.10
Nodes (14): get_session(), api_chat_delete(), api_chat_messages(), api_chat_new(), api_chat_sessions(), api_conversations(), api_documents(), api_event_detail() (+6 more)

### Community 21 - "AgentEvent"
Cohesion: 0.13
Nodes (10): ChatSession, AgentEvent, ChatMessage, api_chat_delete(), api_chat_new(), api_chat_send(), github_webhook(), jenkins_webhook() (+2 more)

### Community 23 - "test_backend_orchestrator.py"
Cohesion: 0.14
Nodes (9): ToolSchema, api_tools(), ironclaw_mock(), orchestrator(), registry(), _sqlite_in_memory(), TestOrchestratorExecuteTool, TestOrchestratorHandleMessage (+1 more)

### Community 24 - "Planner"
Cohesion: 0.16
Nodes (6): ActionPlan, Planner, PlanStep, TestActionPlan, TestPlanner, TestPlanStep

### Community 25 - "persist_tool_output()"
Cohesion: 0.13
Nodes (8): start_chat(), persist_tool_output(), main(), _make_persist_callback(), cb(), test_main_module_imports(), test_main_wires_orchestrator(), test_make_persist_callback()

### Community 26 - "test_markets_feeds_api.py"
Cohesion: 0.10
Nodes (8): client(), TestIntegrationsConfigEndpoint, TestLinkedInFeedEndpoint, TestOutlookEndpoint, TestStatusIncludesNewIntegrations, TestXFeedEndpoint, TestZohoEndpoint, _wire_event_bus()

### Community 27 - "embeddings.py"
Cohesion: 0.13
Nodes (5): _cosine_similarity(), get_embeddings(), _get_embeddings_ollama(), _get_embeddings_openai(), TestCosineSimilarity

### Community 28 - "AgentEvent"
Cohesion: 0.17
Nodes (3): AgentEvent, EventSource, TestAgentEvent

### Community 30 - "integrations/gmail.py"
Cohesion: 0.14
Nodes (5): extract_action_items(), _get_service(), read_emails(), send_email(), summarize_thread()

### Community 31 - "app/page.tsx"
Cohesion: 0.16
Nodes (16): integrationNames, StatusPage(), StatusValue, toStatus(), ModelSelector(), PROVIDERS, Status, StatusCard() (+8 more)

### Community 32 - "integrations/slack.py"
Cohesion: 0.15
Nodes (5): _get_client(), read_channel_history(), respond_to_command(), send_message(), TestSlackIntegration

### Community 33 - "test_event_gateway.py"
Cohesion: 0.11
Nodes (8): client(), _sqlite_in_memory(), TestGitHubWebhook, TestGmailWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook

### Community 34 - "test_knowledge_tools.py"
Cohesion: 0.12
Nodes (7): _sqlite_in_memory(), TestExplainSystem, TestFindRelatedDocs, TestFindRepo, TestSearch, TestTraceCommit, tools()

### Community 35 - "pytest"
Cohesion: 0.16
Nodes (3): bus(), _no_redis(), _sqlite_in_memory()

### Community 36 - "test_integrations_mock.py"
Cohesion: 0.16
Nodes (5): create_page(), _get_client(), search_docs(), summarize_page(), TestConfluenceIntegration

### Community 37 - "github_integration.py"
Cohesion: 0.19
Nodes (8): _api(), comment_on_pr(), create_branch(), create_issue(), get_repo_activity(), _get_token(), search_repos(), summarize_pull_request()

### Community 39 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 40 - "integrations/jira_integration.py"
Cohesion: 0.16
Nodes (6): create_ticket(), _get_client(), get_ticket_details(), link_github_issue(), update_ticket(), TestJiraIntegration

### Community 43 - "_log_event()"
Cohesion: 0.23
Nodes (11): verify_webhook_signature(), github_webhook(), gmail_webhook(), health(), jenkins_webhook(), jira_webhook(), slack_webhook(), _log_event() (+3 more)

### Community 44 - "markets/page.tsx"
Cohesion: 0.21
Nodes (14): ASSET_ORDER, ChartTooltip(), formatLargeNumber(), formatPrice(), MarketsPage(), PriceCard(), PriceChart(), PriceChartProps (+6 more)

### Community 45 - "integrations/jenkins.py"
Cohesion: 0.18
Nodes (5): fetch_build_logs(), get_build_status(), _get_client(), trigger_build(), TestJenkinsIntegration

### Community 47 - "WorkflowEngine"
Cohesion: 0.17
Nodes (3): WorkflowEngine, TestWorkflowTriggerPipeline, TestWorkflowEngine

### Community 48 - "api.ts"
Cohesion: 0.22
Nodes (12): ConversationsPage(), MessageBubble(), EventsPage(), payloadPreview(), Conversation, Event, fetchConversations(), fetchEvents() (+4 more)

### Community 49 - "feeds/page.tsx"
Cohesion: 0.21
Nodes (14): EmailRow(), FeedsPage(), LinkedInPost(), NotConfigured(), Tab, XPost(), EmailMessage, FeedPost (+6 more)

### Community 51 - "EventBus"
Cohesion: 0.18
Nodes (3): EventBus, main(), _setup_packaged_env()

### Community 52 - "test_chat_api.py"
Cohesion: 0.15
Nodes (5): client(), TestChatMessages, TestChatNewSession, TestChatSessions, _wire_event_bus()

### Community 53 - "asyncio"
Cohesion: 0.18
Nodes (5): TestHealth, TestInterpret, TestPlan, TestSelectTools, TestSummarize

### Community 54 - "backend/workflows/engine.py"
Cohesion: 0.27
Nodes (7): AgentLog, _get_nested(), _log_to_db(), _render_template(), repl(), _resolve_args(), handler()

### Community 55 - "backend/integrations/gmail.py"
Cohesion: 0.24
Nodes (6): _get_credentials_path(), _get_service(), _get_token_path(), read_emails(), send_email(), summarize_thread()

### Community 56 - "backend/integrations/jira_integration.py"
Cohesion: 0.28
Nodes (6): _api(), create_ticket(), _get_config(), get_ticket_details(), link_github_issue(), update_ticket()

### Community 58 - "test_knowledge_graph.py"
Cohesion: 0.17
Nodes (4): graph(), _sqlite_in_memory(), TestEdgeOperations, TestGraphQueries

### Community 60 - "backend/integrations/confluence.py"
Cohesion: 0.26
Nodes (5): _api(), create_page(), _get_config(), search_docs(), summarize_page()

### Community 61 - "backend/integrations/jenkins.py"
Cohesion: 0.26
Nodes (5): _api(), fetch_build_logs(), get_build_status(), _get_config(), trigger_build()

### Community 63 - "fetchApi()"
Cohesion: 0.32
Nodes (11): ChatPage(), MessageBubble(), ChatMessageItem, ChatSessionSummary, createChatSession(), deleteChatSession(), fetchApi(), fetchChatMessages() (+3 more)

### Community 65 - "backend/integrations/slack.py"
Cohesion: 0.27
Nodes (5): _api(), _get_token(), read_channel_history(), respond_to_command(), send_message()

### Community 68 - "api_model_config_post()"
Cohesion: 0.24
Nodes (7): api_model_config_post(), _get_dashboard_dir(), _get_data_dir(), _get_model_config_path(), _llm_chat(), _load_model_config(), _save_model_config()

### Community 71 - "react"
Cohesion: 0.28
Nodes (7): ToolsPage(), WorkflowsPage(), fetchTools(), fetchWorkflows(), Tool, Workflow, react

### Community 77 - "package.json"
Cohesion: 0.29
Nodes (6): description, name, private, scripts, start, version

### Community 79 - "full_app()"
Cohesion: 0.29
Nodes (3): client(), full_app(), _sqlite_in_memory()

### Community 81 - "logs/page.tsx"
Cohesion: 0.47
Nodes (5): LevelFilter, logLineColor(), LogsPage(), fetchLogs(), LogEntry

### Community 82 - "workflow-runs/page.tsx"
Cohesion: 0.53
Nodes (5): formatDuration(), statusBadge(), WorkflowRunsPage(), fetchWorkflowRuns(), WorkflowRun

## Knowledge Gaps
- **62 isolated node(s):** `nextConfig`, `name`, `version`, `private`, `dev` (+57 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 703 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **66 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EventBus` connect `EventBus` to `test_service_health.py`, `conftest.py`, `pytest`, `backend/main.py`, `test_platform_e2e.py`, `WorkflowEngine`, `WorkflowEngine`, `test_api_endpoints.py`, `full_app()`, `typing`, `EventBus`, `test_chat_api.py`, `backend/workflows/engine.py`, `_make_event()`, `test_markets_feeds_api.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `AgentConversation` and `AgentLog`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `nextConfig`, `name`, `version` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `load_workflow()` be split into smaller, more focused modules?**
  _Cohesion score 0.06359189378057302 - nodes in this community are weakly interconnected._
- **Why does `KnowledgeGraph` connect `KnowledgeGraph` to `test_knowledge_tools.py`, `backend/main.py`, `KnowledgeTools`, `test_platform_e2e.py`, `os`, `get_session()`, `test_knowledge_graph.py`, `embeddings.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `EventBus` (e.g. with `run()` and `WorkflowEngine`) actually correct?**
  _`EventBus` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `KnowledgeGraph` be split into smaller, more focused modules?**
  _Cohesion score 0.06485671191553545 - nodes in this community are weakly interconnected._