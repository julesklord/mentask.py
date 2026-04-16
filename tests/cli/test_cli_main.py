from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from askgem.cli.main import _parse_args, run_chatbot


def test_parse_args_accepts_list_option(monkeypatch):
    monkeypatch.setattr("sys.argv", ["askgem", "--list", "all"])

    args = _parse_args()

    assert args == Namespace(list="all")


def test_parse_args_rejects_invalid_list_value(monkeypatch):
    monkeypatch.setattr("sys.argv", ["askgem", "--list", "invalid"])

    with pytest.raises(SystemExit):
        _parse_args()


def test_run_chatbot_starts_agent_when_no_list_requested():
    with patch("askgem.cli.main._parse_args", return_value=Namespace(list=None)), \
         patch("askgem.agent.chat.ChatAgent") as mock_agent_class, \
         patch("asyncio.run") as mock_asyncio_run:
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        run_chatbot()

    mock_agent_class.assert_called_once_with()
    mock_asyncio_run.assert_called_once_with(mock_agent.start())


def test_run_chatbot_lists_requested_audit_section():
    with patch("askgem.cli.main._parse_args", return_value=Namespace(list="sessions")), \
         patch("askgem.cli.console.console") as mock_console, \
         patch("askgem.core.audit_manager.AuditManager") as mock_audit_class, \
         patch("askgem.agent.chat.ChatAgent") as mock_agent_class:
        mock_audit = MagicMock()
        mock_audit.list_sessions.return_value = "session data"
        mock_audit_class.return_value = mock_audit

        run_chatbot()

    mock_audit_class.assert_called_once_with()
    mock_audit.list_sessions.assert_called_once_with()
    mock_agent_class.assert_not_called()
    assert mock_console.print.call_count == 3
    mock_console.print.assert_any_call("session data")


def test_run_chatbot_lists_all_audit_sections():
    with patch("askgem.cli.main._parse_args", return_value=Namespace(list="all")), \
         patch("askgem.cli.console.console") as mock_console, \
         patch("askgem.core.audit_manager.AuditManager") as mock_audit_class:
        mock_audit = MagicMock()
        mock_audit.list_db.return_value = "db"
        mock_audit.list_home.return_value = "home"
        mock_audit.list_sessions.return_value = "sessions"
        mock_audit.list_spend.return_value = "spend"
        mock_audit.list_changelog.return_value = "changelog"
        mock_audit_class.return_value = mock_audit

        run_chatbot()

    mock_audit.list_db.assert_called_once_with()
    mock_audit.list_home.assert_called_once_with()
    mock_audit.list_sessions.assert_called_once_with()
    mock_audit.list_spend.assert_called_once_with()
    mock_audit.list_changelog.assert_called_once_with()
    assert mock_console.print.call_count == 7
