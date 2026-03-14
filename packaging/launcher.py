"""
Claw Agent launcher - entry point for packaged executable.
Sets up data paths and runs the FastAPI server with integrated dashboard.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _setup_packaged_env() -> None:
    """Configure environment for packaged or portable run."""
    if getattr(sys, "frozen", False):
        # PyInstaller: MEIPASS is the temp dir where bundle is extracted
        exe_dir = Path(sys.executable).resolve().parent
        meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
        # Use ./data next to exe if writable, else %LOCALAPPDATA%\ClawAgent
        data_dir = exe_dir / "data"
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / ".write_test").write_text("")
            (data_dir / ".write_test").unlink()
        except OSError:
            data_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "ClawAgent"
            data_dir.mkdir(parents=True, exist_ok=True)
        os.environ["CLAW_DATA_DIR"] = str(data_dir)
        # Dashboard is in the bundle (extracted to MEIPASS/dashboard)
        dashboard_dir = meipass / "dashboard"
        os.environ["CLAW_DASHBOARD_DIR"] = str(dashboard_dir)
    else:
        # Dev mode: use project-relative paths
        root = Path(__file__).resolve().parent.parent
        dashboard_dir = root / "frontend" / "out"
        if dashboard_dir.exists():
            os.environ["CLAW_DASHBOARD_DIR"] = str(dashboard_dir)


def main() -> None:
    _setup_packaged_env()

    import uvicorn
    from webhooks.server import app

    host = os.environ.get("CLAW_HOST", "127.0.0.1")
    port = int(os.environ.get("CLAW_PORT", "8080"))

    from events.bus import EventBus
    from webhooks.server import set_event_bus
    set_event_bus(EventBus())

    print(f"Claw Agent starting at http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
