# Graph Report - Windows-developer-platform-agent  (2026-10-26)

## Corpus Check
- 158 files · ~188,485 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: (none) 4, .example 2, .log 1)

## Summary
- 1831 nodes · 3441 edges · 140 communities (78 shown, 62 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 258 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- get_session()
- backend/security/secrets.py
- get_session()
- webhooks/server.py
- conftest.py
- EventBus
- test_knowledge_tools.py
- load_workflow()
- IronClawClient
- init_db()
- frontend/package.json
- set_event_bus()
- ToolRegistry
- embeddings.py
- backend/main.py
- test_platform_e2e.py
- ToolRegistry
- os
- EmbeddingStore
- pytest
- EventSource
- test_api_endpoints.py
- Planner
- backend/webhooks/server.py
- test_event_gateway.py
- ToolSchema
- TestEnvironment
- test_redis_event_bus.py
- EventBus
- _register_tools()
- test_backend_orchestrator.py
- .upsert_node()
- integrations/gmail.py
- main.py
- integrations/slack.py
- test_integrations_mock.py
- KnowledgeGraph
- compilerOptions
- integrations/jira_integration.py
- args
- api.ts
- TestChatSend
- integrations/jenkins.py
- LLMClient
- backend/integrations/gmail.py
- backend/workflows/build_failed.yaml
- WorkflowEngine
- feeds/page.tsx
- markets/page.tsx
- agent/orchestrator.py
- RepositoryIntelligenceIndexer
- test_workflow_engine.py
- test_chat_api.py
- backend/integrations/jira_integration.py
- _make_event()
- backend/integrations/confluence.py
- backend/integrations/jenkins.py
- httpx
- create_app()
- react
- app/page.tsx
- TestWindowsPaths
- index()
- backend/workflows/engine.py
- backend/workflows/jira_created.yaml
- backend/workflows/loader.py
- endpoints
- fetchApi()
- workflows/pr_opened.yaml
- WorkflowEngine
- SlackCommandGateway
- config.yaml
- integrations
- TestModelConfigAPI
- TestToolRegistry
- workflows/build_failed.yaml
- workflows/jira_created.yaml
- LLMClient
- package.json
- TestMarketsEndpoint
- full_app()
- agent
- embeddings
- jenkins
- jira
- server
- conversations/page.tsx
- logs/page.tsx
- workflow-runs/page.tsx
- TestConversationMemory
- confluence
- database
- slack
- GitHubClient
- JiraClient
- TestDashboardReadsWebhookData
- test_knowledge_graph.py
- TestToolCallPattern
- agent/tools.py
- redis
- tools/page.tsx
- next.config.js
- TestGitHubWebhook

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
- `api_tools()` --indirect_call--> `orchestrator()`  [INFERRED]
  backend/webhooks/server.py → tests/unit/test_backend_orchestrator.py
- `_make_persist_callback()` --uses--> `ToolOutput`  [INFERRED]
  main.py → agent/orchestrator.py
- `_db_persist()` --uses--> `ToolOutput`  [INFERRED]
  tests/integration/test_orchestrator_pipeline.py → agent/orchestrator.py
- `tool_registry()` --uses--> `ToolRegistry`  [INFERRED]
  tests/conftest.py → agent/orchestrator.py
- `memory()` --uses--> `ConversationMemory`  [INFERRED]
  tests/unit/test_conversation_memory.py → backend/agent/memory.py

## Import Cycles
- None detected.

## Communities (140 total, 62 thin omitted)

### Community 0 - "get_session()"
Cohesion: 0.06
Nodes (18): CachedSummary, Event, _get_data_dir(), get_engine(), get_session(), persist_tool_output(), ToolOutputModel, WorkflowRun (+10 more)

### Community 1 - "backend/security/secrets.py"
Cohesion: 0.06
Nodes (13): AppSecrets, get_secrets(), redact(), RedactingFilter, AppSecrets, get_secrets(), redact(), RedactingFilter (+5 more)

### Community 2 - "get_session()"
Cohesion: 0.07
Nodes (30): ChatMessage, ChatSession, get_session(), create_app(), api_chat_delete(), api_chat_messages(), api_chat_new(), api_chat_send() (+22 more)

### Community 3 - "webhooks/server.py"
Cohesion: 0.07
Nodes (28): api_chat_messages(), api_chat_sessions(), api_conversations(), api_events(), api_feeds_linkedin(), api_feeds_x(), api_integrations_config(), api_logs() (+20 more)

### Community 4 - "conftest.py"
Cohesion: 0.06
Nodes (11): ConversationMemory, Message, env_secrets(), event_bus(), memory(), _reset_db_globals(), _reset_secrets_cache(), tmp_workflow_dir() (+3 more)

### Community 5 - "EventBus"
Cohesion: 0.09
Nodes (12): AgentEvent, EventBus, main(), _setup_packaged_env(), TestEventWorkflowPipeline, mock_tool_resolver(), mock_tool_resolver(), handler() (+4 more)

### Community 6 - "test_knowledge_tools.py"
Cohesion: 0.08
Nodes (9): KnowledgeTools, _sqlite_in_memory(), TestExplainSystem, TestFindRelatedDocs, TestFindRepo, TestKnowledgeToolDefinitions, TestSearch, TestTraceCommit (+1 more)

### Community 7 - "load_workflow()"
Cohesion: 0.09
Nodes (10): TestLoadAllWorkflows, TestLoadProjectWorkflows, TestLoadWorkflow, TestWorkflowAction, TestWorkflowDefinition, load_all_workflows(), load_workflow(), _load_yaml() (+2 more)

### Community 8 - "IronClawClient"
Cohesion: 0.10
Nodes (7): IronClawClient, client(), TestHealth, TestInterpret, TestPlan, TestSelectTools, TestSummarize

### Community 9 - "init_db()"
Cohesion: 0.10
Nodes (15): AgentMemory, Base, CachedSummary, Event, _get_database_url(), get_engine(), init_db(), KnowledgeEdge (+7 more)

### Community 10 - "frontend/package.json"
Cohesion: 0.07
Nodes (31): next@^14.1.0, devDependencies, autoprefixer@^10.4.17, postcss@^8.4.33, tailwindcss@^3.4.1, @types/node@^20.11.0, @types/react@^18.2.0, @types/react-dom@^18.2.0 (+23 more)

### Community 11 - "set_event_bus()"
Cohesion: 0.07
Nodes (10): TestServiceHealth, client(), TestIntegrationsConfigEndpoint, TestLinkedInFeedEndpoint, TestOutlookEndpoint, TestStatusIncludesNewIntegrations, TestXFeedEndpoint, TestZohoEndpoint (+2 more)

### Community 12 - "ToolRegistry"
Cohesion: 0.13
Nodes (6): Orchestrator, ToolRegistry, _db_persist(), TestOrchestratorDatabasePipeline, _use_sqlite(), TestOrchestrator

### Community 13 - "embeddings.py"
Cohesion: 0.10
Nodes (8): _chunk_text(), _cosine_similarity(), get_embeddings(), _get_embeddings_ollama(), _get_embeddings_openai(), _sqlite_in_memory(), TestChunking, TestCosineSimilarity

### Community 14 - "backend/main.py"
Cohesion: 0.12
Nodes (10): _build_ironclaw(), cli(), main(), _register_knowledge_tools(), run(), _start_cloudflared(), _start_ironclaw(), _stop_all_children() (+2 more)

### Community 15 - "test_platform_e2e.py"
Cohesion: 0.12
Nodes (5): ConversationMemory, Orchestrator, AgentConversation, ToolOutput, TestOrchestratorPipeline

### Community 16 - "ToolRegistry"
Cohesion: 0.11
Nodes (6): TestBackendToolRegistry, TestToolEntry, TestToolSchema, ToolEntry, ToolRegistry, ToolSchema

### Community 18 - "EmbeddingStore"
Cohesion: 0.13
Nodes (8): Document, Embedding, EmbeddingStore, _upsert_document(), TestKnowledgePipeline, TestEmbeddingStore, TestDocumentModel, TestEmbeddingModel

### Community 19 - "pytest"
Cohesion: 0.13
Nodes (4): AgentEvent, EventSource, TestAgentEvent, TestEventSource

### Community 20 - "EventSource"
Cohesion: 0.12
Nodes (9): EventSource, ChatMessage, ChatSession, api_chat_new(), api_chat_send(), github_webhook(), jenkins_webhook(), jira_webhook() (+1 more)

### Community 21 - "test_api_endpoints.py"
Cohesion: 0.09
Nodes (8): client(), TestEventBusNotConfigured, TestGitHubWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook, _wire_event_bus()

### Community 22 - "Planner"
Cohesion: 0.18
Nodes (6): ActionPlan, Planner, PlanStep, TestActionPlan, TestPlanner, TestPlanStep

### Community 23 - "backend/webhooks/server.py"
Cohesion: 0.15
Nodes (13): AgentLog, verify_webhook_signature(), github_webhook(), gmail_webhook(), health(), jenkins_webhook(), jira_webhook(), slack_webhook() (+5 more)

### Community 24 - "test_event_gateway.py"
Cohesion: 0.09
Nodes (8): client(), _sqlite_in_memory(), TestDashboardAPI, TestGmailWebhook, TestHealthEndpoint, TestJenkinsWebhook, TestJiraWebhook, TestSlackWebhook

### Community 25 - "ToolSchema"
Cohesion: 0.13
Nodes (3): ToolEntry, ToolRegistry, ToolSchema

### Community 27 - "test_redis_event_bus.py"
Cohesion: 0.13
Nodes (4): bus(), _no_redis(), TestEventBusFallback, handler()

### Community 29 - "_register_tools()"
Cohesion: 0.19
Nodes (9): _api(), comment_on_pr(), create_branch(), create_issue(), get_repo_activity(), _get_token(), search_repos(), summarize_pull_request() (+1 more)

### Community 30 - "test_backend_orchestrator.py"
Cohesion: 0.15
Nodes (7): ironclaw_mock(), orchestrator(), registry(), _sqlite_in_memory(), TestOrchestratorExecuteTool, TestOrchestratorHandleMessage, TestOrchestratorMemory

### Community 31 - ".upsert_node()"
Cohesion: 0.17
Nodes (3): TestEdgeOperations, TestGraphQueries, TestNodeOperations

### Community 32 - "integrations/gmail.py"
Cohesion: 0.14
Nodes (5): extract_action_items(), _get_service(), read_emails(), send_email(), summarize_thread()

### Community 33 - "main.py"
Cohesion: 0.15
Nodes (6): start_chat(), main(), _make_persist_callback(), test_main_module_imports(), test_main_wires_orchestrator(), test_make_persist_callback()

### Community 34 - "integrations/slack.py"
Cohesion: 0.15
Nodes (5): _get_client(), read_channel_history(), respond_to_command(), send_message(), TestSlackIntegration

### Community 35 - "test_integrations_mock.py"
Cohesion: 0.16
Nodes (5): create_page(), _get_client(), search_docs(), summarize_page(), TestConfluenceIntegration

### Community 36 - "KnowledgeGraph"
Cohesion: 0.19
Nodes (6): KnowledgeGraph, ConfluenceIndexer, _github_headers(), GitHubIndexer, JenkinsIndexer, JiraIndexer

### Community 37 - "compilerOptions"
Cohesion: 0.11
Nodes (17): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+9 more)

### Community 38 - "integrations/jira_integration.py"
Cohesion: 0.16
Nodes (6): create_ticket(), _get_client(), get_ticket_details(), link_github_issue(), update_ticket(), TestJiraIntegration

### Community 39 - "args"
Cohesion: 0.12
Nodes (16): actions, args, description, on_failure, tool, channel, github_url, owner (+8 more)

### Community 40 - "api.ts"
Cohesion: 0.18
Nodes (14): WorkflowsPage(), ModelSelector(), PROVIDERS, AvailableModel, ChatMessageItem, fetchIntegrationsConfig(), fetchModelConfig(), fetchWorkflows() (+6 more)

### Community 42 - "integrations/jenkins.py"
Cohesion: 0.18
Nodes (5): fetch_build_logs(), get_build_status(), _get_client(), trigger_build(), TestJenkinsIntegration

### Community 44 - "backend/integrations/gmail.py"
Cohesion: 0.20
Nodes (7): extract_action_items(), _get_credentials_path(), _get_service(), _get_token_path(), read_emails(), send_email(), summarize_thread()

### Community 45 - "backend/workflows/build_failed.yaml"
Cohesion: 0.13
Nodes (14): actions, args, description, on_failure, tool, build_number, channel, job (+6 more)

### Community 46 - "WorkflowEngine"
Cohesion: 0.17
Nodes (3): WorkflowEngine, TestWorkflowTriggerPipeline, TestWorkflowEngine

### Community 47 - "feeds/page.tsx"
Cohesion: 0.21
Nodes (14): EmailRow(), FeedsPage(), LinkedInPost(), NotConfigured(), Tab, XPost(), EmailMessage, FeedPost (+6 more)

### Community 48 - "markets/page.tsx"
Cohesion: 0.23
Nodes (13): ASSET_ORDER, ChartTooltip(), formatLargeNumber(), formatPrice(), MarketsPage(), PriceCard(), PriceChart(), PriceChartProps (+5 more)

### Community 52 - "test_workflow_engine.py"
Cohesion: 0.22
Nodes (5): load_all_workflows(), load_workflow(), WorkflowDefinition, _sqlite_in_memory(), TestWorkflowLoader

### Community 53 - "test_chat_api.py"
Cohesion: 0.15
Nodes (5): client(), TestChatMessages, TestChatNewSession, TestChatSessions, _wire_event_bus()

### Community 54 - "backend/integrations/jira_integration.py"
Cohesion: 0.28
Nodes (6): _api(), create_ticket(), _get_config(), get_ticket_details(), link_github_issue(), update_ticket()

### Community 56 - "backend/integrations/confluence.py"
Cohesion: 0.26
Nodes (5): _api(), create_page(), _get_config(), search_docs(), summarize_page()

### Community 57 - "backend/integrations/jenkins.py"
Cohesion: 0.26
Nodes (5): _api(), fetch_build_logs(), get_build_status(), _get_config(), trigger_build()

### Community 58 - "httpx"
Cohesion: 0.27
Nodes (5): _api(), _get_token(), read_channel_history(), respond_to_command(), send_message()

### Community 60 - "react"
Cohesion: 0.20
Nodes (11): dependencies, react@^18.2.0, react-dom@^18.2.0, recharts@^3.8.0, EventsPage(), payloadPreview(), Event, fetchEvents() (+3 more)

### Community 61 - "app/page.tsx"
Cohesion: 0.24
Nodes (10): integrationNames, StatusPage(), StatusValue, toStatus(), Status, StatusCard(), StatusCardProps, statusDotClass() (+2 more)

### Community 63 - "index()"
Cohesion: 0.25
Nodes (3): index(), reindex_embeddings(), webhook_server()

### Community 65 - "backend/workflows/engine.py"
Cohesion: 0.33
Nodes (5): _get_nested(), _render_template(), repl(), _resolve_args(), handler()

### Community 66 - "backend/workflows/jira_created.yaml"
Cohesion: 0.18
Nodes (10): actions, args, on_failure, tool, channel, text, description, enabled (+2 more)

### Community 67 - "backend/workflows/loader.py"
Cohesion: 0.24
Nodes (3): _parse_actions(), _parse_trigger(), WorkflowAction

### Community 68 - "endpoints"
Cohesion: 0.20
Nodes (10): health, interpret, plan, select_tools, summarize, ironclaw, endpoints, retries (+2 more)

### Community 69 - "fetchApi()"
Cohesion: 0.42
Nodes (9): ChatPage(), MessageBubble(), ChatSessionSummary, createChatSession(), deleteChatSession(), fetchApi(), fetchChatMessages(), fetchChatSessions() (+1 more)

### Community 70 - "workflows/pr_opened.yaml"
Cohesion: 0.20
Nodes (9): actions, args, on_failure, tool, channel, description, enabled, name (+1 more)

### Community 73 - "config.yaml"
Cohesion: 0.22
Nodes (8): edge_types, node_types, knowledge, graph, workflows, auto_load, default_timeout, dir

### Community 74 - "integrations"
Cohesion: 0.22
Nodes (9): enabled, token, webhook_secret, credentials_file, enabled, token_file, integrations, github (+1 more)

### Community 77 - "workflows/build_failed.yaml"
Cohesion: 0.22
Nodes (8): actions, args, tool, channel, description, enabled, name, trigger

### Community 78 - "workflows/jira_created.yaml"
Cohesion: 0.22
Nodes (8): actions, args, tool, channel, description, enabled, name, trigger

### Community 82 - "package.json"
Cohesion: 0.29
Nodes (6): description, name, private, scripts, start, version

### Community 84 - "full_app()"
Cohesion: 0.29
Nodes (3): client(), full_app(), _sqlite_in_memory()

### Community 85 - "agent"
Cohesion: 0.33
Nodes (6): agent, max_tokens, name, system_prompt, temperature, version

### Community 86 - "embeddings"
Cohesion: 0.33
Nodes (6): embeddings, chunk_overlap, chunk_size, dimensions, model, provider

### Community 87 - "jenkins"
Cohesion: 0.33
Nodes (6): jenkins, api_token, enabled, url, user, webhook_secret

### Community 88 - "jira"
Cohesion: 0.33
Nodes (6): jira, api_token, enabled, url, user, webhook_secret

### Community 89 - "server"
Cohesion: 0.33
Nodes (6): server, host, log_dir, log_level, port, workers

### Community 90 - "conversations/page.tsx"
Cohesion: 0.47
Nodes (5): ConversationsPage(), MessageBubble(), Conversation, fetchConversations(), Message

### Community 91 - "logs/page.tsx"
Cohesion: 0.47
Nodes (5): LevelFilter, logLineColor(), LogsPage(), fetchLogs(), LogEntry

### Community 92 - "workflow-runs/page.tsx"
Cohesion: 0.53
Nodes (5): formatDuration(), statusBadge(), WorkflowRunsPage(), fetchWorkflowRuns(), WorkflowRun

### Community 95 - "confluence"
Cohesion: 0.40
Nodes (5): api_token, enabled, url, user, confluence

### Community 96 - "database"
Cohesion: 0.40
Nodes (5): database, echo, path, pool_size, url

### Community 97 - "slack"
Cohesion: 0.40
Nodes (5): slack, app_token, bot_token, enabled, signing_secret

### Community 104 - "redis"
Cohesion: 0.50
Nodes (4): redis, consumer_group, stream_key, url

### Community 105 - "tools/page.tsx"
Cohesion: 0.67
Nodes (3): ToolsPage(), fetchTools(), Tool

## Knowledge Gaps
- **62 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `EventBus` connect `EventBus` to `backend/workflows/engine.py`, `conftest.py`, `EventBus`, `set_event_bus()`, `.__init__()`, `WorkflowEngine`, `backend/main.py`, `test_platform_e2e.py`, `typing`, `full_app()`, `test_api_endpoints.py`, `test_chat_api.py`, `_make_event()`, `test_workflow_engine.py`, `test_redis_event_bus.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `create_app()` (e.g. with `AgentConversation` and `AgentLog`) actually correct?**
  _`create_app()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `get_session()` be split into smaller, more focused modules?**
  _Cohesion score 0.059907834101382486 - nodes in this community are weakly interconnected._
- **Why does `create_app()` connect `get_session()` to `backend/security/secrets.py`, `init_db()`, `backend/main.py`, `test_platform_e2e.py`, `EmbeddingStore`, `full_app()`, `backend/webhooks/server.py`, `test_event_gateway.py`, `index()`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `EventBus` (e.g. with `run()` and `WorkflowEngine`) actually correct?**
  _`EventBus` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `backend/security/secrets.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06033182503770739 - nodes in this community are weakly interconnected._
- **Why does `KnowledgeGraph` connect `KnowledgeGraph` to `Any`, `get_session()`, `test_knowledge_graph.py`, `test_knowledge_tools.py`, `init_db()`, `backend/main.py`, `test_platform_e2e.py`, `typing`, `RepositoryIntelligenceIndexer`, `EmbeddingStore`, `.upsert_node()`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._