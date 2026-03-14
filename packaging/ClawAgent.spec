# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Claw Agent
# Run from project root: pyinstaller packaging/ClawAgent.spec

from pathlib import Path

# SPECPATH = directory containing this .spec file (packaging/)
spec_dir = Path(SPECPATH).resolve()
project_root = spec_dir.parent

# Dashboard: frontend/out copied to dist/dashboard
dashboard_src = project_root / "frontend" / "out"
dashboard_datas = [(str(dashboard_src), "dashboard")] if dashboard_src.exists() else []

a = Analysis(
    [str(spec_dir / "launcher.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (str(project_root / "workflows"), "workflows"),
        *dashboard_datas,
    ],
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "webhooks.server",
        "database.models",
        "events.bus",
        "events.types",
        "workflows.loader",
        "security.secrets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ClawAgent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
