"""Tests for main entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
def test_main_module_imports():
    """Verify main.py can be imported without errors."""
    import main
    assert hasattr(main, "main")
    assert callable(main.main)


@pytest.mark.unit
def test_make_persist_callback():
    """Verify persist callback can be constructed."""
    from main import _make_persist_callback
    cb = _make_persist_callback()
    assert callable(cb)


@pytest.mark.unit
@patch("main.LLMClient")
@patch("main.ToolRegistry")
@patch("main.Orchestrator")
@patch("cli.chat.start_chat")
def test_main_wires_orchestrator(mock_start_chat, mock_orch_class, mock_reg_class, mock_llm_class):
    """Verify main() constructs orchestrator and starts chat."""
    from main import main
    main()
    mock_llm_class.assert_called_once()
    mock_reg_class.assert_called_once()
    mock_orch_class.assert_called_once()
    mock_start_chat.assert_called_once()
