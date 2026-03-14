# Claw Agent — Developer Automation Platform (Windows)

A personal AI assistant that lives in your **Slack** workspace and connects to your engineering tools: GitHub, Jira, Jenkins, Gmail, and Confluence. Instead of switching between tabs all day, you type a message in Slack and the agent handles it.

This is the **Windows** version of the platform, adapted from the Mac edition with full Windows path handling, PowerShell scripts, and Windows-compatible setup.

---

## Architecture

```
  You (in Slack)
       │
       ▼
  Python Backend (runs on your PC, port 8080)
       │
       ▼
  IronClaw AI Engine (gateway port 3000) ─or─ OpenRouter / OpenAI / Ollama
       │
       ▼
  Tools: GitHub, Jira, Jenkins, Gmail, Confluence, Slack
       │
       ▼
  PostgreSQL / SQLite Database
       │
       ▼
  Web Dashboard (localhost:3001)
```

| Piece              | What It Does                                                            |
| ------------------ | ----------------------------------------------------------------------- |
| **Slack**          | Where you talk to the agent                                             |
| **Python Backend** | FastAPI server that receives messages and coordinates everything         |
| **IronClaw**       | AI engine that reads your message and decides which tools to use        |
| **Integrations**   | Connections to GitHub, Jira, Jenkins, Gmail, Confluence, Slack           |
| **Database**       | Stores events, conversations, workflow history (PostgreSQL or SQLite)    |
| **Web Dashboard**  | Next.js app showing status, events, workflows, tools, and conversations |

---

## Prerequisites

| Software       | Install Command                              | Verify                |
| -------------- | -------------------------------------------- | --------------------- |
| **Python 3.10+** | `winget install Python.Python.3.13`        | `python --version`    |
| **Node.js 18+**  | `winget install OpenJS.NodeJS.LTS`         | `node --version`      |
| **PostgreSQL** (optional) | `winget install PostgreSQL.PostgreSQL` | `psql --version` |

SQLite is used as a fallback if PostgreSQL is not configured.

---

## Quick Start

```powershell
# Clone or download the project
cd C:\Users\YourName\Documents\Windows-developer-platform-agent

# Run automated setup
.\scripts\setup.ps1

# Edit .env with your API keys
notepad .env

# Start services
.\scripts\start.ps1

# Run tests
.\scripts\test.ps1
```

---

## Packaged Executable (Faster Install)

To build a single executable and portable package for easier distribution:

```powershell
.\scripts\build-exe.ps1
```

This produces:
- `dist/ClawAgent.exe` — single executable (backend + dashboard)
- `dist/ClawAgent-Portable/` — folder with exe, ironclaw.exe, data/, README.txt

**To use:** Double-click `ClawAgent.exe`, open http://localhost:8080. For AI, run `ironclaw run` in a terminal (see `packaging/README.txt`).

**Build options:**
- `-SkipFrontend` — reuse existing frontend build
- `-SkipIronClaw` — do not download IronClaw (user installs separately)

---

## Manual Setup

### 1. Create Virtual Environment

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
# Edit .env with your tokens and API keys
```

At minimum, you need:
- `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` — from [api.slack.com/apps](https://api.slack.com/apps)
- `GITHUB_TOKEN` — from [github.com/settings/tokens](https://github.com/settings/tokens)

### 4. (Optional) Set Up PostgreSQL

```powershell
psql -U postgres -c "CREATE USER claw WITH PASSWORD 'claw';"
psql -U postgres -c "CREATE DATABASE clawagent OWNER claw;"
```

If you skip this, the agent uses SQLite (`data/platform.db`) automatically.

### 5. Start the Backend

```powershell
.venv\Scripts\Activate.ps1
python -m uvicorn webhooks.server:app --host 127.0.0.1 --port 8080
```

### 6. Start the Dashboard

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3001 in your browser.

---

## Using the Agent

### Slack Commands

| What You Type                            | What Happens                                       |
| ---------------------------------------- | -------------------------------------------------- |
| `@claw summarize today's PRs`            | Fetches PRs from GitHub and posts a summary        |
| `@claw investigate Jenkins build 1234`   | Fetches logs, analyzes failure, explains what broke |
| `@claw create Jira ticket from this email` | Reads email thread and creates a Jira ticket     |

### Web Dashboard (localhost:3001)

| Page              | What It Shows                                         |
| ----------------- | ----------------------------------------------------- |
| **Status**        | Health of IronClaw, database, and integrations        |
| **Events**        | Live feed of webhooks and agent events                |
| **Workflows**     | Automation rules defined in YAML                      |
| **Runs**          | History of workflow executions                         |
| **Tools**         | All registered tools and their parameters             |
| **Conversations** | Full Slack conversation history                       |
| **Logs**          | Filterable, color-coded log viewer                    |

---

## Automated Workflows

Workflows are YAML files in `workflows/` that trigger on events:

### PR Opened (`workflows/pr_opened.yaml`)
- Trigger: `github.pull_request.opened`
- Actions: Summarize PR → Notify Slack → Link Jira

### Build Failed (`workflows/build_failed.yaml`)
- Trigger: `jenkins.build.failed`
- Actions: Fetch logs → Summarize failure → Alert Slack

### Jira Created (`workflows/jira_created.yaml`)
- Trigger: `jira.issue.created`
- Actions: Create GitHub issue → Notify Slack → Update Jira

---

## Running Tests

```powershell
# All tests
.\scripts\test.ps1

# Unit tests only
.\scripts\test.ps1 -Unit

# Integration tests only
.\scripts\test.ps1 -Integration

# Deployment tests only
.\scripts\test.ps1 -Deployment

# With coverage report
.\scripts\test.ps1 -Coverage -Verbose

# Or directly with pytest
.venv\Scripts\python.exe -m pytest tests/ -v
```

### Test Categories

| Category       | Location              | What It Tests                                   |
| -------------- | --------------------- | ----------------------------------------------- |
| **Unit**       | `tests/unit/`         | Memory, planner, registry, orchestrator, events, workflows, secrets, database |
| **Integration** | `tests/integration/` | API endpoints, event→workflow pipeline, orchestrator→DB, integration mocks    |
| **Deployment** | `tests/deployment/`   | Windows paths, service health, DB connectivity, environment, dependencies     |

---

## Project Structure

```
Windows-developer-platform-agent/
│
├── agent/                  ← Root agent module (LLM client, orchestrator, memory, planner)
├── integrations/           ← Slack, GitHub, Jira, Confluence, Jenkins, Gmail clients
├── events/                 ← Event types and pub/sub bus
├── database/               ← SQLAlchemy models and session management
├── workflows/              ← Workflow engine, loader, and YAML definitions
├── webhooks/               ← FastAPI webhook server
├── security/               ← Secrets management, redaction, signature verification
├── tools/                  ← Tool registry with schemas
├── cli/                    ← Interactive chat CLI with Rich
│
├── backend/                ← Backend variant with IronClaw integration
│   ├── agent/              ← IronClaw client, Slack gateway, backend orchestrator
│   ├── integrations/       ← Backend integration clients
│   ├── tools/              ← Backend tool registry
│   ├── database/           ← Extended models (AgentMemory, AgentConversation, AgentLog)
│   ├── events/             ← Backend event bus
│   ├── workflows/          ← Backend workflows with template variables
│   ├── webhooks/           ← Full FastAPI app with dashboard API
│   └── security/           ← Backend secrets
│
├── frontend/               ← Next.js 14 dashboard (React, Tailwind, TypeScript)
│   ├── src/app/            ← Pages: status, events, workflows, runs, tools, conversations, logs
│   ├── src/components/     ← Sidebar, StatusCard, ModelSelector
│   └── src/lib/api.ts      ← API client
│
├── config/                 ← config.yaml
├── docs/                   ← Architecture documentation with Mermaid diagrams
├── scripts/                ← PowerShell scripts (setup, start, stop, test)
├── tests/                  ← Test suite
│   ├── unit/               ← Unit tests (memory, planner, registry, orchestrator, etc.)
│   ├── integration/        ← Integration tests (API, pipelines, mocks)
│   └── deployment/         ← Deployment tests (paths, health, DB, environment)
│
├── main.py                 ← Root CLI entry point
├── requirements.txt        ← Python dependencies
├── requirements-dev.txt    ← Dev/test dependencies
├── pytest.ini              ← Pytest configuration
├── .env.example            ← Environment variable template
├── .gitignore              ← Git exclusions
└── README.md               ← This file
```

---

## Stopping Services

```powershell
# If started with scripts\start.ps1, press Ctrl+C

# Or run:
.\scripts\stop.ps1
```

---

## Security Notes

- API keys and tokens are stored only in `.env` on your machine — never in code.
- `.env` is in `.gitignore` so it won't be committed.
- Webhook requests are verified with HMAC-SHA256 signatures.
- Secrets are automatically scrubbed from logs via `RedactingFilter`.

---

## Differences from Mac Version

| Aspect              | Mac                         | Windows                          |
| ------------------- | --------------------------- | -------------------------------- |
| Package manager     | Homebrew (`brew`)           | winget / chocolatey / manual     |
| Scripts             | Bash (`.sh`)                | PowerShell (`.ps1`)              |
| Paths               | `/Users/you/...`            | `C:\Users\you\...` (pathlib)     |
| Python command       | `python3`                  | `python`                         |
| Service management  | `brew services`             | PowerShell Jobs / Task Scheduler |
| Default DB path     | `~/Documents/.../data/`     | `.\data\platform.db`            |
