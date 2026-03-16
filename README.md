# Developer AI Platform

An **internal developer AI platform** that automates engineering workflows, reasons over events from GitHub/Jira/Jenkins/Confluence/Gmail/Slack, understands repository relationships via a knowledge graph, and answers engineering questions through semantic search.

The system runs **locally** but supports cloud webhook gateways. IronClaw (Rust-based reasoning engine) handles task planning, tool selection, and summarization; the Python backend executes tool calls and orchestrates workflows.

This is the **Windows** edition with pathlib-friendly paths, PowerShell scripts, and Windows-compatible setup.

---

## Architecture

```
                          External Services
    GitHub    Slack    Jira    Jenkins    Confluence    Gmail
        │       │       │         │            │          │
        └───────┴───────┴─────────┴────────────┴──────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Event Gateway (FastAPI)                        │
│  /webhooks/github | slack | jira | jenkins | gmail               │
│  Standardized events → { event_id, source, type, actor, payload } │
└─────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
            │ Event Store │  │  Redis      │  │ Workflow    │
            │ (PostgreSQL)│  │  Event Bus │  │ Engine      │
            └─────────────┘  └─────────────┘  └─────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              IronClaw Runtime (Rust, port 3000)                  │
│  Task planning | Tool selection | Summarization | Interpret      │
│                     ─ or ─ OpenRouter / OpenAI fallback         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Capability Registry & Orchestrator              │
│  github.* | slack.* | jira.* | jenkins.* | gmail.* | confluence.*│
│  knowledge.search | find_repo | trace_commit | explain_system     │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ Knowledge     │         │ Repository      │         │ Embeddings      │
│ Graph         │         │ Intelligence    │         │ (pgvector)      │
│ Nodes & Edges │         │ Indexer         │         │ Semantic search │
└───────────────┘         └─────────────────┘         └─────────────────┘
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    │
                                    ▼
                        PostgreSQL / SQLite
                                    │
                                    ▼
                        Web Dashboard (port 3001)
```

---

## System Components

| Component | Description |
|-----------|-------------|
| **Event Gateway** | FastAPI webhook server; converts source-specific payloads into standardized events; stores events in PostgreSQL |
| **Event Bus** | Redis-backed queue for durable event delivery; workers consume events; in-memory fallback when Redis unavailable |
| **Event Store** | PostgreSQL (or SQLite) tables for events with `event_id`, `source`, `type`, `timestamp`, `actor`, `payload` |
| **Workflow Engine** | YAML-defined workflows; triggers on event types (e.g. `jenkins.build.failed`); executes tool sequences |
| **Capability Registry** | Registry of tools with name, description, JSON schema, handler; used by IronClaw for tool-calling |
| **IronClaw Runtime** | Rust reasoning engine; task planning, tool selection, summarization; Python executes returned tool calls |
| **Knowledge Graph** | Engineering relationship graph (repos, files, commits, PRs, issues, pipelines, docs, engineers); stored in PostgreSQL |
| **Repository Intelligence Indexer** | Ingesters for GitHub, Jira, Confluence, Jenkins; stores artifacts as documents |
| **Embeddings** | pgvector/JSON embeddings for semantic search over code, PRs, Jira comments, Confluence pages |
| **Knowledge Tools** | `knowledge.search`, `knowledge.find_repo`, `knowledge.trace_commit`, `knowledge.find_related_docs`, `knowledge.explain_system` |

---

## Prerequisites

| Software | Install Command | Verify |
|----------|-----------------|--------|
| **Python 3.10+** | `winget install Python.Python.3.13` | `python --version` |
| **Node.js 18+** | `winget install OpenJS.NodeJS.LTS` | `node --version` |
| **cloudflared** | `winget install Cloudflare.cloudflared` | `cloudflared --version` |
| **PostgreSQL** (optional) | `winget install PostgreSQL.PostgreSQL` | `psql --version` |
| **Redis** (optional) | `winget install Redis.Redis` or Docker | `redis-cli ping` |
| **IronClaw** (optional) | See IronClaw docs | OpenRouter used as fallback |

SQLite is the default database when PostgreSQL is not configured. The event bus uses in-memory mode when Redis is unavailable. `cloudflared` is used to expose the local Event Gateway to external webhook sources.

---

## Quick Start

```powershell
# Clone or download the project
cd C:\Users\YourName\Documents\Windows-developer-platform-agent

# Create venv and install dependencies
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Copy and edit environment
Copy-Item .env.example .env
notepad .env

# Run automated setup (if available)
.\scripts\setup.ps1

# Start the full platform
python -m backend.main run

# In another terminal: frontend dashboard
cd frontend && npm install && npm run dev
```

Open http://localhost:8080 (API) and http://localhost:3001 (dashboard).

---

## Manual Setup

### 1. Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. Configure Environment

```powershell
Copy-Item .env.example .env
notepad .env
```

**Required for Slack-based agent:**

| Variable | Description |
|---------|-------------|
| `SLACK_BOT_TOKEN` | From [api.slack.com/apps](https://api.slack.com/apps) |
| `SLACK_SIGNING_SECRET` | Webhook signing secret |

**For LLM (if IronClaw is not running):**

| Variable | Description |
|---------|-------------|
| `OPENROUTER_API_KEY` | From [openrouter.ai](https://openrouter.ai) |
| `OPENROUTER_MODEL` | e.g. `anthropic/claude-sonnet-4` |

**For integrations (as needed):**

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET` | GitHub API and webhooks |
| `JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`, `JIRA_WEBHOOK_SECRET` | Jira API and webhooks |
| `JENKINS_URL`, `JENKINS_USER`, `JENKINS_API_TOKEN`, `JENKINS_WEBHOOK_SECRET` | Jenkins API and webhooks |
| `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN` | Confluence API |
| `GMAIL_CREDENTIALS_FILE`, `GMAIL_TOKEN_FILE` | Gmail OAuth |

**Optional infrastructure:**

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | e.g. `postgresql://claw:claw@localhost:5432/clawagent` |
| `REDIS_URL` | e.g. `redis://localhost:6379/0` |
| `OPENAI_API_KEY` or `OPENROUTER_API_KEY` | For embeddings (semantic search) |
| `IRONCLAW_URL` | IronClaw service, default `http://localhost:3000` |

### 4. (Optional) PostgreSQL

```powershell
psql -U postgres -c "CREATE USER claw WITH PASSWORD 'claw';"
psql -U postgres -c "CREATE DATABASE clawagent OWNER claw;"
```

If skipped, SQLite is used (`data/platform.db`).

### 5. Start the Backend

```powershell
.venv\Scripts\Activate.ps1
python -m backend.main run
```

**CLI commands:**

| Command | Description |
|---------|-------------|
| `python -m backend.main run` | Full platform: Event Gateway, workflows, IronClaw, knowledge |
| `python -m backend.main webhook-server` | Webhooks only (no orchestrator) |
| `python -m backend.main index` | Run repository intelligence indexers |
| `python -m backend.main reindex-embeddings` | Regenerate embeddings |

**Index examples:**

```powershell
# Index GitHub repos, Jira project, Confluence space
python -m backend.main index --github owner/repo1 --github owner/repo2 --jira PROJECT --confluence SPACE

# Index Jenkins
python -m backend.main index --jenkins
```

### 6. (Optional) IronClaw

If using IronClaw instead of OpenRouter:

```powershell
# In a separate terminal
ironclaw run
```

### 7. Start the Dashboard

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3001.

---

## Webhook Configuration (Cloudflare Tunnel)

The platform runs locally but external services (GitHub, Slack, Jira, Jenkins, Gmail) need a public URL to deliver webhooks. We use [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) to expose the local Event Gateway securely — no open ports, no NAT configuration.

### Install `cloudflared`

```powershell
# Windows (winget)
winget install Cloudflare.cloudflared

# Or download from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

Verify:

```powershell
cloudflared --version
```

### Option A: Quick Tunnel (no Cloudflare account required)

For development and testing, a quick tunnel gives you a temporary public URL:

```powershell
cloudflared tunnel --url http://localhost:8080
```

`cloudflared` will print a URL like `https://random-words.trycloudflare.com`. Use that as your webhook base URL.

### Option B: Named Tunnel (persistent, recommended for production)

A named tunnel gives you a stable hostname and survives restarts.

**1. Authenticate:**

```powershell
cloudflared tunnel login
```

This opens a browser to authorize Cloudflare. A certificate is saved to `~/.cloudflared/cert.pem`.

**2. Create the tunnel:**

```powershell
cloudflared tunnel create dev-ai-platform
```

Note the tunnel UUID printed.

**3. Configure DNS:**

```powershell
cloudflared tunnel route dns dev-ai-platform webhooks.your-domain.com
```

This creates a CNAME record pointing `webhooks.your-domain.com` to your tunnel.

**4. Create a config file** at `~/.cloudflared/config.yml`:

```yaml
tunnel: <tunnel-uuid>
credentials-file: C:\Users\YourName\.cloudflared\<tunnel-uuid>.json

ingress:
  - hostname: webhooks.your-domain.com
    service: http://localhost:8080
  - service: http_status:404
```

**5. Run the tunnel:**

```powershell
cloudflared tunnel run dev-ai-platform
```

Or install as a Windows service:

```powershell
cloudflared service install
```

### Configure `.env`

Add your tunnel hostname to `.env` so the platform knows its public URL:

```ini
WEBHOOK_BASE_URL=https://webhooks.your-domain.com
```

Or for quick tunnels:

```ini
WEBHOOK_BASE_URL=https://random-words.trycloudflare.com
```

### Register Webhooks with Services

| Service | Webhook URL | Notes |
|---------|-------------|-------|
| GitHub | `https://webhooks.your-domain.com/webhooks/github` | Set in repo Settings → Webhooks; requires `GITHUB_WEBHOOK_SECRET` |
| Slack | `https://webhooks.your-domain.com/webhooks/slack` | Set in app Event Subscriptions; requires `SLACK_SIGNING_SECRET` |
| Jira | `https://webhooks.your-domain.com/webhooks/jira` | Set in Jira Settings → System → WebHooks; optional `JIRA_WEBHOOK_SECRET` |
| Jenkins | `https://webhooks.your-domain.com/webhooks/jenkins` | Configure in job post-build actions; optional token |
| Gmail | `https://webhooks.your-domain.com/webhooks/gmail` | Configure in Google Cloud Pub/Sub push subscription |

### Verify the Tunnel

```powershell
# Health check through the tunnel
curl https://webhooks.your-domain.com/health
```

Expected response:

```json
{"status": "ok", "platform": "developer-ai", "version": "2.0.0", ...}
```

---

## Using the Agent

### Slack Commands

| What You Type | What Happens |
|---------------|--------------|
| `@claw summarize today's PRs` | Fetches PRs from GitHub and posts a summary |
| `@claw investigate Jenkins build 1234` | Fetches logs, analyzes failure, explains what broke |
| `@claw create Jira ticket from this email` | Reads email thread and creates a Jira ticket |
| `@claw trace commit abc123` | Traces commit through PRs and Jira issues (knowledge graph) |

### Dashboard (localhost:3001)

| Page | What It Shows |
|------|---------------|
| **Status** | Health, event/workflow/doc/node counts |
| **Event Stream** | Webhooks and agent events |
| **Workflow Runs** | Workflow execution history |
| **Tool Registry** | Capabilities with schemas |
| **Agent Conversations** | Chat history |
| **Knowledge Explorer** | Graph nodes and edges |
| **Repository Search** | Documents and semantic search |

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Platform health |
| `GET /api/events` | Event stream (filter by source/type) |
| `GET /api/workflow-runs` | Workflow runs |
| `GET /api/tools` | Registered capabilities |
| `GET /api/knowledge/nodes` | Knowledge graph nodes |
| `GET /api/documents` | Indexed documents |
| `POST /api/chat` | Send message to agent |

---

## Workflows

Workflows are YAML files in `backend/workflows/`. Trigger format:

```yaml
name: Jenkins Failure Alert
trigger:
  type: jenkins.build.failed
description: Fetch logs, summarize, notify Slack
actions:
  - tool: jenkins.fetch_build_logs
    args:
      job: "{{ job_name }}"
      build_number: "{{ build_number }}"
  - tool: agent.summarize_logs
    args:
      text: "{{ build_log }}"
  - tool: slack.send_message
    args:
      channel: "#dev-notifications"
      text: "Build failed: {{ summary }}"
```

**Built-in workflows:**

| Workflow | Trigger | Actions |
|----------|---------|---------|
| PR Opened | `github.pull_request.opened` | Summarize PR → Slack → Link Jira |
| Jenkins Failure | `jenkins.build.failed` | Fetch logs → Summarize → Alert Slack |
| Jira Created | `jira.issue.created` | Create GitHub issue → Slack → Update Jira |

---

## Knowledge Graph

The graph models engineering relationships:

**Node types:** `repository`, `file`, `commit`, `pull_request`, `jira_issue`, `pipeline`, `documentation`, `engineer`

**Edge types:** `repo_contains_file`, `file_modified_by_commit`, `commit_part_of_pr`, `pr_links_to_issue`, `repo_deployed_by_pipeline`, `authored_by`, `reviewed_by`, `assigned_to`

**Knowledge tools for IronClaw:**

| Tool | Purpose |
|------|---------|
| `knowledge.search` | Semantic search across indexed documents |
| `knowledge.find_repo` | Repository details and relationships |
| `knowledge.trace_commit` | Commit → PRs → Jira issues → files |
| `knowledge.find_related_docs` | Related documentation |
| `knowledge.explain_system` | Explain a system using graph + docs |

---

## Running Tests

```powershell
# All tests
python -m pytest tests/ -v

# Platform unit tests
python -m pytest tests/unit/test_platform_models.py tests/unit/test_event_gateway.py tests/unit/test_knowledge_graph.py tests/unit/test_backend_orchestrator.py tests/unit/test_conversation_memory.py tests/unit/test_knowledge_tools.py -v

# Platform integration tests
python -m pytest tests/integration/test_platform_e2e.py -v

# With coverage
python -m pytest tests/ -v --cov=backend --cov-report=html
```

**Test categories (98 platform tests):**

| Category | Location | What It Tests |
|----------|----------|---------------|
| **Unit** | `tests/unit/` | Models, graph, event bus, workflows, IronClaw client, embeddings, orchestrator, memory, knowledge tools |
| **Integration** | `tests/integration/` | Webhook → event store, dashboard reads, knowledge pipeline, orchestrator pipeline, workflow triggers |
| **Deployment** | `tests/deployment/` | Paths, health, DB, environment |

---

## Project Structure

```
Windows-developer-platform-agent/
│
├── backend/
│   ├── agent/              IronClaw client, orchestrator, memory
│   ├── integrations/       GitHub, Slack, Jira, Jenkins, Confluence, Gmail
│   ├── database/           SQLAlchemy models (events, workflows, knowledge graph, documents, embeddings)
│   ├── events/             Redis-backed event bus
│   ├── workflows/          YAML loader and engine
│   ├── webhooks/           FastAPI Event Gateway + dashboard API
│   ├── knowledge/          Graph, indexer, embeddings, query tools
│   ├── tools/              Capability registry
│   └── security/           Secrets, webhook verification, redaction
│
├── frontend/               Next.js 14 dashboard
├── config/                 config.yaml
├── scripts/                PowerShell (setup, start, stop, test)
├── tests/
├── main.py                 Root CLI
├── requirements.txt
├── .env.example
└── README.md
```

---

## Stopping Services

```powershell
# If started with scripts\start.ps1, press Ctrl+C

# Or:
.\scripts\stop.ps1
```

---

## Security

- API keys and tokens go in `.env` — never in code.
- `.env` is in `.gitignore`.
- Webhooks are verified with HMAC-SHA256 where supported.
- Secrets are redacted from logs via `RedactingFilter`.
- Do not log tokens or credentials.

---

## Packaged Executable

To build a single executable:

```powershell
.\scripts\build-exe.ps1
```

Produces `dist/ClawAgent.exe` and `dist/ClawAgent-Portable/`. Run `ironclaw run` separately for AI.

---

## Differences from Mac Version

| Aspect | Mac | Windows |
|--------|-----|---------|
| Package manager | Homebrew | winget / chocolatey |
| Scripts | Bash (`.sh`) | PowerShell (`.ps1`) |
| Paths | `/Users/you/...` | `C:\Users\you\...` |
| Python | `python3` | `python` |
| Default DB | SQLite in `data/platform.db` | Same |
