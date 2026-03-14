"""Deployment tests: verify all path handling is Windows-compatible."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.deployment
class TestWindowsPaths:
    def test_project_root_exists(self):
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    def test_no_hardcoded_unix_paths_in_python(self):
        """Scan all .py files for hardcoded /usr, /home, /tmp, ~/. paths."""
        unix_patterns = ["/usr/", "/home/", "/tmp/", "~/.", "/var/", "/etc/"]
        violations = []
        for py_file in PROJECT_ROOT.rglob("*.py"):
            if ".venv" in str(py_file) or "node_modules" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pattern in unix_patterns:
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern in line and not line.strip().startswith("#") and "test_" not in py_file.name:
                        violations.append(f"{py_file}:{i}: {line.strip()}")
        assert violations == [], f"Hardcoded Unix paths found:\n" + "\n".join(violations[:20])

    def test_pathlib_used_for_file_operations(self):
        """Verify key modules use pathlib.Path instead of os.path.join."""
        key_modules = [
            PROJECT_ROOT / "main.py",
            PROJECT_ROOT / "database" / "models.py",
            PROJECT_ROOT / "workflows" / "loader.py",
            PROJECT_ROOT / "workflows" / "engine.py",
        ]
        for mod_path in key_modules:
            if not mod_path.exists():
                continue
            content = mod_path.read_text(encoding="utf-8")
            if "os.path.join" in content:
                pytest.fail(f"{mod_path.name} uses os.path.join instead of pathlib.Path")

    def test_data_directory_creation(self, tmp_path, monkeypatch):
        """Verify the database module can create data directories on Windows."""
        monkeypatch.setenv("DATABASE_URL", "")
        monkeypatch.chdir(tmp_path)

        import database.models as db
        db._engine = None
        db._SessionLocal = None
        engine = db.get_engine()
        assert engine is not None
        data_dir = tmp_path / "data"
        assert data_dir.exists()

    def test_workflow_yaml_paths_resolve(self):
        """Verify workflow directory glob works on Windows."""
        wf_dir = PROJECT_ROOT / "workflows"
        if wf_dir.exists():
            yamls = list(wf_dir.glob("*.yaml"))
            assert len(yamls) > 0, "No YAML files found in workflows/"

    def test_config_yaml_path(self):
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        if config_path.exists():
            import yaml
            data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
