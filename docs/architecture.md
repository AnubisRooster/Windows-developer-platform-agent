# Windows Developer Platform Agent — Architecture

This document describes the architecture of the **Windows Developer Platform Agent**, the Windows port of Claw Agent. It connects Slack, GitHub, Jira, Jenkins, Gmail, and Confluence with event-driven workflows.

> **Platform note:** All file paths use `pathlib.Path` for Windows compatibility. No hardcoded Unix paths.

---

## 1. System Overview

```mermaid
flowchart TB
    subgraph External["External Services"]
        Slack[Slack]
        GitHub[GitHub]
        Jira[Jira]
        Jenkins[Jenkins]
        Gmail[Gmail]
        Confluence[Confluence]
    end

    subgraph Agent["Windows Developer Platform Agent"]
        CLI[Click CLI]
        Webhook[Webhook Server]
        Orch[Orchestrator]
        WF[Workflow Engine]
        LLM[LLM Client]
        Tools[Tools]
    end

    subgraph LLMProviders["LLM Providers"]
        OpenRouter[OpenRouter]
        OpenAI[OpenAI]
        Ollama[Ollama]
    end

    Slack --> Webhook
    GitHub --> Webhook
    Jira --> Webhook
    Jenkins --> Webhook

    CLI --> Orch
    Webhook --> Orch
    Orch --> LLM
    Orch --> WF
    Orch --> Tools

    LLM --> OpenRouter
    LLM --> OpenAI
    LLM --> Ollama

    Tools --> Slack
    Tools --> GitHub
    Tools --> Jira
    Tools --> Jenkins
    Tools --> Gmail
    Tools --> Confluence
```

---

## 2. Component Architecture

```mermaid
flowchart LR
    subgraph Entry["Entry Points"]
        main[main.py]
        chat[chat command]
        run[run command]
        webhook[webhook-server]
    end

    subgraph Core["Core Components"]
        orchestrator[Orchestrator]
        llm_client[LLMClient]
        workflow_engine[WorkflowEngine]
    end

    subgraph Integrations["Integrations"]
        slack_client[SlackClient]
        github_client[GitHubClient]
        jira_client[JiraClient]
        confluence_client[ConfluenceClient]
        jenkins_client[JenkinsClient]
        gmail_client[GmailClient]
    end

    subgraph Infrastructure["Infrastructure"]
        config[config/config.yaml]
        workflows[workflows/]
        data[data/]
    end

    main --> chat
    main --> run
    main --> webhook

    chat --> orchestrator
    run --> workflow_engine
    webhook --> orchestrator

    orchestrator --> llm_client
    orchestrator --> workflow_engine
    workflow_engine --> orchestrator

    orchestrator --> slack_client
    orchestrator --> github_client
    orchestrator --> jira_client
    orchestrator --> confluence_client
    orchestrator --> jenkins_client
    orchestrator --> gmail_client

    config --> main
    workflows --> workflow_engine
    data --> orchestrator
```

---

## 3. IronClaw Flow

IronClaw is the external workflow execution service. The agent calls it for long-running or complex operations.

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Orch as Orchestrator
    participant IronClaw
    participant LLM

    User->>Agent: Request (chat/run)
    Agent->>Orch: Process request
    Orch->>LLM: Generate response / plan
    LLM-->>Orch: Response

    alt Needs IronClaw
        Orch->>IronClaw: POST workflow
        IronClaw-->>Orch: Job ID
        Orch->>IronClaw: Poll status
        IronClaw-->>Orch: Result
    end

    Orch-->>Agent: Final response
    Agent-->>User: Output
```

---

## 4. Webhook Flow

Webhooks receive events from external services and trigger workflows.

```mermaid
sequenceDiagram
    participant Slack
    participant GitHub
    participant Jira
    participant Jenkins
    participant Webhook as Webhook Server
    participant Orch as Orchestrator
    participant WF as Workflow Engine

    Slack->>Webhook: POST /webhooks/slack
    GitHub->>Webhook: POST /webhooks/github
    Jira->>Webhook: POST /webhooks/jira
    Jenkins->>Webhook: POST /webhooks/jenkins

    Webhook->>Webhook: Validate signature
    Webhook->>WF: Match event to workflow
    WF->>Orch: Execute workflow
    Orch->>Orch: Run steps (LLM + tools)
    Orch-->>WF: Result
    WF-->>Webhook: Response
    Webhook-->>Slack: 200 OK
```

---

## 5. Event Bus

Internal event flow between components.

```mermaid
flowchart TB
    subgraph Producers["Event Producers"]
        WebhookIn[Webhook Incoming]
        Scheduled[Scheduled Jobs]
        Manual[Manual Trigger]
    end

    subgraph Bus["Event Bus"]
        Queue[Event Queue]
        Router[Event Router]
    end

    subgraph Consumers["Event Consumers"]
        Workflow1[Workflow: PR Created]
        Workflow2[Workflow: Jira Update]
        Workflow3[Workflow: Jenkins Build]
    end

    WebhookIn --> Queue
    Scheduled --> Queue
    Manual --> Queue

    Queue --> Router
    Router --> Workflow1
    Router --> Workflow2
    Router --> Workflow3
```

---

## 6. Data Model

```mermaid
erDiagram
    WORKFLOW ||--o{ STEP : contains
    WORKFLOW {
        string id PK
        string name
        string description
        string trigger_type
    }

    STEP ||--o{ ACTION : performs
    STEP {
        string id PK
        string workflow_id FK
        string name
        string action_type
        int order
    }

    EXECUTION ||--o{ STEP_RESULT : produces
    EXECUTION {
        string id PK
        string workflow_id FK
        string event_id
        string status
        datetime started_at
        datetime completed_at
    }

    STEP_RESULT {
        string id PK
        string execution_id FK
        string step_id FK
        string output
        string status
    }

    INTEGRATION {
        string id PK
        string type
        string config
        boolean enabled
    }
```

---

## 7. Dashboard

Planned dashboard architecture for monitoring and control.

```mermaid
flowchart TB
    subgraph Frontend["Dashboard Frontend"]
        UI[Web UI]
        Charts[Charts]
        Logs[Log Viewer]
    end

    subgraph Backend["Dashboard Backend"]
        API[REST API]
        WS[WebSocket]
        Metrics[Metrics Store]
    end

    subgraph Agent["Windows Developer Platform Agent"]
        Orch[Orchestrator]
        WF[Workflow Engine]
        Webhook[Webhook Server]
    end

    UI --> API
    UI --> WS
    Charts --> Metrics
    Logs --> API

    API --> Orch
    API --> WF
    WS --> Webhook
    Orch --> Metrics
    WF --> Metrics
```

---

## File Layout (Windows)

All paths use `pathlib.Path`:

```
Windows-developer-platform-agent/
├── main.py                 # Entry point
├── config/
│   └── config.yaml        # Configuration
├── agent/
│   ├── llm.py             # LLM client
│   ├── orchestrator.py    # Orchestrator
│   ├── workflow_engine.py # Workflow execution
│   └── tools.py           # Tools (summarize, etc.)
├── integrations/
│   ├── slack.py
│   ├── github.py
│   ├── jira.py
│   ├── confluence.py
│   ├── jenkins.py
│   └── gmail.py
├── server/
│   └── webhook.py         # FastAPI webhook server
├── workflows/             # Workflow definitions
├── data/                  # Runtime data, DB fallback
└── logs/                  # Log files
```

---

## Environment Variables

See `.env.example` for the full list. Key variables:

- `OPENROUTER_API_KEY` / `OPENCLAW_API_KEY` — LLM provider key
- `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`
- `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`
- `JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`
- `JENKINS_URL`, `JENKINS_USER`, `JENKINS_API_TOKEN`
- `GMAIL_CREDENTIALS_FILE`, `GMAIL_TOKEN_FILE` (paths resolved via `pathlib`)
- `WEBHOOK_HOST`, `WEBHOOK_PORT`
- `DATABASE_URL`
