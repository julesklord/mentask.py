import json
import os
from unittest.mock import MagicMock, patch

from mentask.core.config_manager import ConfigManager

_mock_console = MagicMock()


def test_load_settings_corrupt_global_json(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path") as mock_path:
        settings_file = str(tmp_path / "settings.json")
        mock_path.return_value = settings_file
        with open(settings_file, "w") as f:
            f.write("NOT VALID JSON {{{")

        ConfigManager(_mock_console)
        # Should not crash, and should print error
        error_calls = [
            call for call in _mock_console.print.call_args_list if "Error loading global settings.json" in str(call)
        ]
        assert len(error_calls) == 1


def test_load_settings_corrupt_local_json(tmp_path):
    _mock_console.reset_mock()
    with (
        patch("mentask.core.config_manager.get_config_path", return_value="/tmp/nonexistent"),
        patch("os.getcwd", return_value=str(tmp_path)),
    ):
        local_dir = tmp_path / ".mentask"
        local_dir.mkdir()
        local_settings = local_dir / "settings.json"

        with open(local_settings, "w") as f:
            f.write("NOT VALID JSON {{{")

        ConfigManager(_mock_console)
        error_calls = [
            call
            for call in _mock_console.print.call_args_list
            if "Error loading local .mentask/settings.json" in str(call)
        ]
        assert len(error_calls) == 1


def test_load_settings_keyring_error_fallback(tmp_path):
    _mock_console.reset_mock()
    with (
        patch("mentask.core.config_manager.get_config_path", return_value="/tmp/nonexistent"),
        patch("os.getcwd", return_value=str(tmp_path)),
        patch("keyring.get_password", side_effect=Exception("Keyring failed")),
        patch.dict(os.environ, {"GOOGLE_API_KEY": "env-fallback-key"}),
    ):
        cm = ConfigManager(_mock_console)
        assert cm.settings.get("google_api_key") == "env-fallback-key"
        error_calls = [
            call
            for call in _mock_console.print.call_args_list
            if "Error accessing keyring for google_api_key" in str(call)
        ]
        assert len(error_calls) >= 1


def test_load_api_key_return_source(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path", return_value="/tmp/nonexistent"):
        cm = ConfigManager(_mock_console)
        # Test 1: Local Settings with return_source
        cm.settings["google_api_key"] = "local-key"
        key, source = cm.load_api_key("google", return_source=True)
        assert key == "local-key"
        assert source == "Local Settings"

        # Test 2: Keyring with return_source
        cm.settings["openai_api_key"] = "STORED_IN_KEYRING"
        with patch("keyring.get_password", return_value="keyring-key"):
            key, source = cm.load_api_key("openai", return_source=True)
            assert key == "keyring-key"
            assert source == "Keyring"

        # Test 3: Env var with return_source
        cm.settings["anthropic_api_key"] = ""
        with patch("keyring.get_password", return_value=None), patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"}):
            key, source = cm.load_api_key("anthropic", return_source=True)
            assert key == "env-key"
            assert source == "Environment Variable"

        # Test 4: Fallback Google env var with return_source
        cm.settings["google_api_key"] = ""
        with (
            patch("keyring.get_password", return_value=None),
            patch.dict(os.environ, {"GEMINI_API_KEY": "gemini-env-key"}, clear=True),
        ):
            key, source = cm.load_api_key("google", return_source=True)
            assert key == "gemini-env-key"
            assert source == "Environment Variable"

        # Test 5: No key found with return_source
        cm.settings["deepseek_api_key"] = ""
        with patch("keyring.get_password", return_value=None), patch.dict(os.environ, {}, clear=True):
            key, source = cm.load_api_key("deepseek", return_source=True)
            assert key is None
            assert source is None


def test_load_api_key_keyring_error(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path", return_value="/tmp/nonexistent"):
        cm = ConfigManager(_mock_console)
        cm.settings["google_api_key"] = "STORED_IN_KEYRING"
        with (
            patch("keyring.get_password", side_effect=Exception("Keyring read failed")),
            patch.dict(os.environ, {"GOOGLE_API_KEY": "env-after-keyring-fail"}),
        ):
            key = cm.load_api_key("google")
            assert key == "env-after-keyring-fail"

            error_calls = [
                call for call in _mock_console.print.call_args_list if "Error accessing keyring for google" in str(call)
            ]
            assert len(error_calls) >= 1


def test_detect_provider_others(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path", return_value="/tmp/nonexistent"):
        cm = ConfigManager(_mock_console)
        assert cm.detect_provider("gsk_12345") == "groq"
        assert cm.detect_provider("sk-12345") == "openai"


def test_save_settings_full(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path") as mock_path:
        settings_file = str(tmp_path / "settings.json")
        mock_path.return_value = settings_file

        cm = ConfigManager(_mock_console)
        cm.settings["model_name"] = "test-model"

        # Test sensitive key stored properly
        cm.settings["google_api_key"] = "test-key"

        with patch("keyring.set_password") as mock_set:
            cm.save_settings()

            mock_set.assert_any_call(cm.SERVICE_NAME, "GOOGLE_API_KEY", "test-key")

            with open(settings_file) as f:
                saved_data = json.load(f)

            assert saved_data["model_name"] == "test-model"
            assert saved_data["google_api_key"] == "STORED_IN_KEYRING"


def test_save_api_key_exceptions(tmp_path):
    _mock_console.reset_mock()
    cm = ConfigManager(_mock_console)
    with patch("keyring.set_password", side_effect=Exception("Keyring fails!")):
        assert cm.save_api_key("sk-test-key", "openai") is False


def test_detect_provider_all():
    _mock_console.reset_mock()
    cm = ConfigManager(_mock_console)
    assert cm.detect_provider("sk-ant-123") == "anthropic"
    assert cm.detect_provider("sk-proj-123") == "openai"
    assert cm.detect_provider("gsk_123") == "groq"
    assert cm.detect_provider("sk-123") == "openai"
    assert cm.detect_provider("AIzaSy123") == "google"
    assert cm.detect_provider("something_else") == "google"


def test_save_settings_json_write_error(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path") as mock_path:
        settings_file = str(tmp_path / "settings.json")
        mock_path.return_value = settings_file

        cm = ConfigManager(_mock_console)
        with patch("builtins.open", side_effect=Exception("Disk full")):
            cm.save_settings()

        error_calls = [call for call in _mock_console.print.call_args_list if "Error saving settings:" in str(call)]
        assert len(error_calls) >= 1


def test_save_settings_keyring_error(tmp_path):
    _mock_console.reset_mock()
    with patch("mentask.core.config_manager.get_config_path") as mock_path:
        settings_file = str(tmp_path / "settings.json")
        mock_path.return_value = settings_file

        cm = ConfigManager(_mock_console)
        cm.settings["google_api_key"] = "test-key"

        with patch("keyring.set_password", side_effect=Exception("Keyring fails!")):
            cm.save_settings()

        error_calls = [
            call
            for call in _mock_console.print.call_args_list
            if "Error saving google_api_key to keyring:" in str(call)
        ]
        assert len(error_calls) >= 1


def test_load_settings_local_secrets_warning(tmp_path):
    _mock_console.reset_mock()
    with (
        patch("mentask.core.config_manager.get_config_path", return_value="/tmp/nonexistent"),
        patch("os.getcwd", return_value=str(tmp_path)),
    ):
        local_dir = tmp_path / ".mentask"
        local_dir.mkdir()
        local_settings = local_dir / "settings.json"

        with open(local_settings, "w") as f:
            json.dump({"google_api_key": "some-secret"}, f)

        ConfigManager(_mock_console)
        warning_calls = [call for call in _mock_console.print.call_args_list if "Security Warning" in str(call)]
        assert len(warning_calls) >= 1


def test_save_api_key_success(tmp_path):
    _mock_console.reset_mock()
    cm = ConfigManager(_mock_console)
    with patch("keyring.set_password") as mock_set:
        assert cm.save_api_key("sk-test-key", "openai") is True
        mock_set.assert_called_with(cm.SERVICE_NAME, "OPENAI_API_KEY", "sk-test-key")
        success_calls = [
            call for call in _mock_console.print.call_args_list if "saved securely in system keyring" in str(call)
        ]
        assert len(success_calls) >= 1


def test_get_resolved_theme_mocking(tmp_path):
    _mock_console.reset_mock()
    cm = ConfigManager(_mock_console)
    # create fake modules since they're lazy imported
    from types import ModuleType

    mock_contextual = ModuleType("mentask.cli.contextual_prompts")

    class DummyNeonTheme:
        @classmethod
        def get(cls, name):
            return "neon_" + name

    mock_contextual.NeonTheme = DummyNeonTheme

    mock_themes = ModuleType("mentask.cli.themes")

    def dummy_get_theme(name):
        return "legacy_" + name

    mock_themes.get_theme = dummy_get_theme

    with patch.dict(
        "sys.modules", {"mentask.cli.contextual_prompts": mock_contextual, "mentask.cli.themes": mock_themes}
    ):
        cm.settings["theme"] = "neon_cyan"
        assert cm.get_resolved_theme() == "neon_neon_cyan"

        cm.settings["theme"] = "sakura"
        assert cm.get_resolved_theme() == "legacy_sakura"
