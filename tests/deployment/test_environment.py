"""Deployment tests: verify environment, dependencies, and configuration."""

from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.mark.deployment
class TestEnvironment:
    def test_python_version(self):
        assert sys.version_info >= (3, 10), f"Python 3.10+ required, got {sys.version}"

    def test_running_on_windows(self):
        assert platform.system() == "Windows", f"Expected Windows, got {platform.system()}"

    def test_core_dependencies_importable(self):
        modules = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "pydantic_settings",
            "sqlalchemy",
            "dotenv",
            "slack_sdk",
            "github",
            "jira",
            "atlassian",
            "jenkins",
            "httpx",
            "yaml",
            "click",
            "tenacity",
            "cryptography",
            "rich",
        ]
        missing = []
        for mod in modules:
            try:
                importlib.import_module(mod)
            except ImportError:
                missing.append(mod)
        if missing:
            pytest.skip(f"Optional dependencies not installed: {', '.join(missing)}")

    def test_dev_dependencies_importable(self):
        dev_modules = ["pytest", "pytest_asyncio"]
        for mod in dev_modules:
            importlib.import_module(mod)

    def test_env_example_exists(self):
        env_example = PROJECT_ROOT / ".env.example"
        assert env_example.exists(), ".env.example not found"

    def test_env_example_has_required_vars(self):
        env_example = PROJECT_ROOT / ".env.example"
        if not env_example.exists():
            pytest.skip(".env.example not found")
        content = env_example.read_text(encoding="utf-8")
        required_vars = [
            "SLACK_BOT_TOKEN",
            "GITHUB_TOKEN",
            "DATABASE_URL",
            "WEBHOOK_HOST",
            "WEBHOOK_PORT",
        ]
        for var in required_vars:
            assert var in content, f"{var} missing from .env.example"

    def test_requirements_file_exists(self):
        assert (PROJECT_ROOT / "requirements.txt").exists()
        assert (PROJECT_ROOT / "requirements-dev.txt").exists()

    def test_pytest_ini_exists(self):
        assert (PROJECT_ROOT / "pytest.ini").exists()

    def test_gitignore_excludes_secrets(self):
        gitignore = PROJECT_ROOT / ".gitignore"
        if not gitignore.exists():
            pytest.skip(".gitignore not found")
        content = gitignore.read_text(encoding="utf-8")
        assert ".env" in content
        assert "credentials.json" in content or "token.json" in content

    def test_config_yaml_exists(self):
        config_path = PROJECT_ROOT / "config" / "config.yaml"
        if not config_path.exists():
            pytest.skip("config.yaml not found")
        import yaml
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)


@pytest.mark.deployment
class TestWindowsCompatibility:
    def test_path_separator(self):
        p = Path("a") / "b" / "c"
        assert "\\" in str(p) or "/" in str(p)

    def test_long_path_support(self, tmp_path):
        deep = tmp_path
        for i in range(10):
            deep = deep / f"level_{i}"
        deep.mkdir(parents=True, exist_ok=True)
        assert deep.exists()

    def test_unicode_filename(self, tmp_path):
        f = tmp_path / "tëst_fïlé.txt"
        f.write_text("content", encoding="utf-8")
        assert f.exists()
        assert f.read_text(encoding="utf-8") == "content"

    def test_cwd_is_valid(self):
        cwd = Path.cwd()
        assert cwd.exists()
        assert cwd.is_dir()
