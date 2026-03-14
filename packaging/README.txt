================================================================================
  Claw Agent - Windows Developer Platform
================================================================================

QUICK START
-----------
1. Double-click ClawAgent.exe
2. Open http://localhost:8080 in your browser
3. For AI features (IronClaw), run "ironclaw run" in a separate terminal (see below)


IRONCLAW (AI ENGINE)
--------------------
IronClaw powers the AI assistant. It is included in this package.

To start IronClaw:
  1. Open a terminal (PowerShell or Command Prompt)
  2. cd to this folder
  3. Run: ironclaw run

  Or add the folder to PATH and run "ironclaw run" from anywhere.

On first run, IronClaw may prompt for setup (database, model). Use the default
options or follow the wizard.

Alternative: Add OPENROUTER_API_KEY to a .env file in this folder for
cloud-based AI fallback when IronClaw is not running.


MANUAL IRONCLAW INSTALL (optional)
----------------------------------
If you prefer the official IronClaw installer or a newer version:

  powershell -ExecutionPolicy Bypass -c "irm https://github.com/nearai/ironclaw/releases/download/v0.18.0/ironclaw-installer.ps1 | iex"

Or download from: https://github.com/nearai/ironclaw/releases


UPDATING IRONCLAW
-----------------
To upgrade IronClaw:
  - Re-run the installer command above, or
  - Replace ironclaw.exe in this folder with the new build from GitHub releases


DATA & CONFIGURATION
--------------------
- Data (database, model config) is stored in the "data" folder
- To use a custom location, set CLAW_DATA_DIR before starting
- Model configuration can be changed in the dashboard at http://localhost:8080


PORTS
-----
- Claw Agent: http://127.0.0.1:8080
- IronClaw (when running): http://127.0.0.1:3000


TROUBLESHOOTING
---------------
- Port 8080 in use: Set CLAW_PORT=8081 (or another port) before starting
- IronClaw not found: Ensure ironclaw.exe is in this folder or in your PATH
- Dashboard not loading: Check that ClawAgent.exe started without errors
