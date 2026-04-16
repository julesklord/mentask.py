import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from askgem.agent.schema import AssistantMessage, Message, Role, ToolCall
from askgem.core.history_manager import HistoryManager

# Patch the console so no Rich output is emitted during tests
_mock_console = MagicMock()


class TestHistoryManager:
    @pytest.fixture
    def manager(self, tmp_path):
        with patch("askgem.core.history_manager.get_history_dir") as mock_dir:
            mock_dir.return_value = str(tmp_path)
            yield HistoryManager(_mock_console)

    def test_init(self, manager, tmp_path):
        assert manager.history_dir == str(tmp_path)
        assert isinstance(manager.current_session_id, str)

    def test_message_to_dict_text(self, manager):
        msg = Message(role=Role.USER, content="hello")
        result = manager._message_to_dict(msg)
        assert result["role"] == "user"
        assert result["content"] == "hello"

    def test_message_to_dict_assistant_with_tools(self, manager):
        msg = AssistantMessage(content="Thinking...", tool_calls=[ToolCall(id="1", name="test", arguments={"a": 1})])
        result = manager._message_to_dict(msg)
        assert result["role"] == "assistant"
        assert result["tool_calls"][0]["name"] == "test"

    def test_dict_to_message_text(self, manager):
        data = {"role": "user", "content": "hello", "timestamp": datetime.now().isoformat(), "uuid": "test-uuid"}
        msg = manager._dict_to_message(data)
        assert msg.role == Role.USER
        assert msg.content == "hello"
        assert msg.uuid == "test-uuid"

    def test_save_session_empty(self, manager, tmp_path):
        manager.save_session([])
        files = os.listdir(tmp_path)
        assert len(files) == 0

    def test_save_session(self, manager, tmp_path):
        msg = Message(role=Role.USER, content="hello")
        manager.save_session([msg])

        filepath = os.path.join(tmp_path, f"{manager.current_session_id}.json")
        assert os.path.exists(filepath)

        with open(filepath) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["content"] == "hello"

    def test_load_session_basic(self, manager, tmp_path):
        session_id = "test_session"
        filepath = os.path.join(tmp_path, f"{session_id}.json")
        data = [{"role": "user", "content": "hello", "timestamp": datetime.now().isoformat(), "uuid": "test-uuid"}]
        with open(filepath, "w") as f:
            json.dump(data, f)

        loaded = manager.load_session(session_id)
        assert len(loaded) == 1
        assert loaded[0].role == Role.USER
        assert loaded[0].content == "hello"

    def test_list_sessions(self, manager, tmp_path):
        open(os.path.join(tmp_path, "session1.json"), "w").close()
        open(os.path.join(tmp_path, "session2.json"), "w").close()

        sessions = manager.list_sessions()
        assert len(sessions) == 2
        assert "session1" in sessions
        assert "session2" in sessions

    def test_delete_session(self, manager, tmp_path):
        session_id = "test_session"
        filepath = os.path.join(tmp_path, f"{session_id}.json")
        open(filepath, "w").close()

        assert manager.delete_session(session_id) is True
        assert not os.path.exists(filepath)

    def test_load_session_path_traversal(self, manager):
        assert manager.load_session("../../../etc/passwd") is None
