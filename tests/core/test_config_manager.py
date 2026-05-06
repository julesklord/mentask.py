"""
Tests for core/config_manager.py — ConfigManager v2.0
"""

import os
from unittest.mock import MagicMock, patch

from mentask.core.config_manager import ConfigManager
from mentask.core.paths import get_config_dir, get_config_path

# Patch the console so no Rich output is emitted during tests
_mock_console = MagicMock()


class TestGetConfigDir:
    def test_returns_path_object(self):
        result = get_config_dir()
        from pathlib import Path

        assert isinstance(result, Path)

    def test_directory_name_is_mentask(self):
        result = get_config_dir()
        assert result.name == ".mentask"

    def test_directory_exists_after_call(self):
        result = get_config_dir()
        assert result.exists()


class TestGetConfigPath:
    def test_returns_absolute_path(self):
        path = get_config_path("settings.json")
        assert os.path.isabs(path)

    def test_contains_mentask(self):
        path = get_config_path("settings.json")
        assert ".mentask" in path

    def test_ends_with_filename(self):
        path = get_config_path("myfile.json")
        assert path.endswith("myfile.json")


class TestConfigManagerSettings:
    def test_default_model_is_set(self):
        with (
            patch("mentask.core.config_manager.get_config_path") as mock_path,
            patch("os.path.exists", return_value=False),
        ):
            mock_path.return_value = "/tmp/nonexistent.json"
            cm = ConfigManager(_mock_console)
            assert "model_name" in cm.settings
            assert isinstance(cm.settings["model_name"], str)

    def test_default_edit_mode_is_manual(self):
        with (
            patch("mentask.core.config_manager.get_config_path") as mock_path,
            patch("os.path.exists", return_value=False),
        ):
            mock_path.return_value = "/tmp/nonexistent.json"
            cm = ConfigManager(_mock_console)
            assert cm.settings.get("edit_mode") == "manual"

    def test_save_and_reload_settings(self, tmp_path):
        """Verifies the round-trip: save → reload recovers the same values."""
        with patch("mentask.core.paths.get_config_path") as mock_path:
            settings_file = str(tmp_path / "settings.json")
            mock_path.return_value = settings_file

            cm = ConfigManager(_mock_console)
            cm.settings["model_name"] = "gemini-2.5-flash"
            cm.settings["edit_mode"] = "auto"
            cm.save_settings()

            cm2 = ConfigManager(_mock_console)
            assert cm2.settings["model_name"] == "gemini-2.5-flash"
            assert cm2.settings["edit_mode"] == "auto"

    def test_load_settings_handles_corrupt_json(self, tmp_path):
        """ConfigManager must not crash when the settings file is corrupted."""
        with patch("mentask.core.paths.get_config_path") as mock_path:
            settings_file = str(tmp_path / "settings.json")
            mock_path.return_value = settings_file
            with open(settings_file, "w") as f:
                f.write("NOT VALID JSON {{{")

            cm = ConfigManager(_mock_console)
            # Falls back to defaults — must not raise
            assert "model_name" in cm.settings


class TestConfigManagerApiKey:
    def test_loads_from_env_variable(self):
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key-123"}),
            patch("keyring.get_password", return_value=None),
        ):
            cm = ConfigManager(_mock_console)
            assert cm.load_api_key() == "env-key-123"

    def test_keyring_overrides_env_variable(self):
        with (
            patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key-123"}),
            patch("keyring.get_password", return_value="keyring-key-789"),
        ):
            cm = ConfigManager(_mock_console)
            # Keyring wins in v2.1+
            assert cm.load_api_key() == "keyring-key-789"

    def test_detect_provider(self):
        cm = ConfigManager(_mock_console)
        assert cm.detect_provider("sk-proj-123") == "openai"
        assert cm.detect_provider("sk-ant-123") == "anthropic"
        assert cm.detect_provider("AIzaSy123") == "google"
        assert cm.detect_provider("random") == "google"

    def test_returns_none_when_no_key(self, tmp_path):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("mentask.core.config_manager.get_config_path") as mock_path,
            patch("keyring.get_password", return_value=None),
        ):
            mock_path.return_value = str(tmp_path / "nonexistent.key")
            cm = ConfigManager(_mock_console)
            assert cm.load_api_key() is None

    def test_saves_and_loads_api_key(self, tmp_path):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("keyring.set_password") as mock_set,
            patch("keyring.get_password") as mock_get,
            patch("pathlib.Path.home", return_value=tmp_path),
        ):
            mock_get.return_value = "my-test-key"
            cm = ConfigManager(_mock_console)
            cm.save_api_key("my-test-key")
            mock_set.assert_called_with("mentask", "GOOGLE_API_KEY", "my-test-key")
            assert cm.load_api_key() == "my-test-key"

    def test_save_api_key_success(self):
        with (
            patch("keyring.set_password") as mock_set,
        ):
            cm = ConfigManager(_mock_console)
            # Need to mock console.print to check if it's called properly
            cm.console = MagicMock()

            result = cm.save_api_key("  test-key-xyz  ", "OpenAI")

            assert result is True
            mock_set.assert_called_once_with("mentask", "OPENAI_API_KEY", "test-key-xyz")
            cm.console.print.assert_called_once()
            assert "[success]" in str(cm.console.print.call_args)

    def test_save_api_key_failure(self):
        with (
            patch("keyring.set_password", side_effect=Exception("Keyring error")) as mock_set,
        ):
            cm = ConfigManager(_mock_console)
            cm.console = MagicMock()

            result = cm.save_api_key("test-key-xyz", "Anthropic")

            assert result is False
            mock_set.assert_called_once_with("mentask", "ANTHROPIC_API_KEY", "test-key-xyz")
            cm.console.print.assert_called_once()
            assert "[error]" in str(cm.console.print.call_args)
