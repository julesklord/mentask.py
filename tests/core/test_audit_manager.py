from unittest.mock import patch

import pytest
from rich.panel import Panel
from rich.table import Table

from mentask.core.audit_manager import AuditManager


class TestAuditManager:
    @pytest.fixture
    def manager(self, tmp_path):
        with patch("mentask.core.audit_manager.get_history_dir") as mock_dir:
            mock_dir.return_value = str(tmp_path)
            # Need to patch MemoryManager and TokenTracker initialization to prevent side-effects
            with patch("mentask.core.audit_manager.MemoryManager"), patch("mentask.core.audit_manager.TokenTracker"):
                yield AuditManager()

    def test_list_db(self, manager):
        manager.memory.read_memory.side_effect = [
            "## Global Category\n- Global Fact 1\n- Global Fact 2",
            "## Local Category\n- Local Fact 1",
        ]

        table = manager.list_db()

        assert isinstance(table, Table)
        assert table.title == "[bold blue]mentask Knowledge DB[/bold blue]"
        assert len(table.columns) == 3

        # We can't easily inspect table rows via public API, but we can verify calls
        assert manager.memory.read_memory.call_count == 2
        manager.memory.read_memory.assert_any_call(scope="global")
        manager.memory.read_memory.assert_any_call(scope="local")

    @patch("mentask.core.audit_manager.get_local_knowledge_path")
    @patch("mentask.core.audit_manager.get_memory_path")
    @patch("mentask.core.audit_manager.get_config_dir")
    def test_list_home(self, mock_config, mock_memory, mock_local, manager):
        mock_config.return_value = "/mock/config"
        mock_memory.return_value = "/mock/memory.md"
        mock_local.return_value = "/mock/local.md"

        table = manager.list_home()

        assert isinstance(table, Table)
        assert table.title == "[bold magenta]mentask Home Directories[/bold magenta]"
        assert len(table.columns) == 2

    def test_list_sessions(self, manager, tmp_path):
        # Create dummy session files in the mocked history_dir (tmp_path)
        session_file_1 = tmp_path / "session1.json"
        session_file_1.write_text("dummy content 1")
        session_file_2 = tmp_path / "session2.json"
        session_file_2.write_text("dummy content 2 is larger")

        table = manager.list_sessions()

        assert isinstance(table, Table)
        assert table.title == "[bold yellow]Saved Sessions[/bold yellow]"
        assert len(table.columns) == 2
        # Ensure it actually scans the mocked tmp_path

    def test_list_spend(self, manager):
        manager.metrics.get_historical_report.return_value = {
            "cost": 1.2345,
            "total": 1000,
            "prompt": 600,
            "candidate": 400,
            "saved_tokens": 500,
            "saved_cost": 0.50,
        }

        panel = manager.list_spend()

        assert isinstance(panel, Panel)
        assert panel.title == "[bold green]Budget & Savings Report[/bold green]"

        # Verify text content formatting inside the Panel
        renderable_text = panel.renderable.plain
        assert "Total Investment:" in renderable_text
        assert "$1.2345" in renderable_text
        assert "Total Tokens: 1,000" in renderable_text
        assert "Tokens Avoided: 500" in renderable_text
        assert "$0.5000" in renderable_text

    def test_list_changelog(self, manager):
        panel = manager.list_changelog()

        assert isinstance(panel, Panel)
        assert panel.title == "[bold white]Changelog[/bold white]"
        assert "v0.10.0" in panel.renderable
