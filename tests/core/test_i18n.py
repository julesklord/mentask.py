import os
from unittest.mock import mock_open, patch

import pytest

from mentask.core.i18n import Translator, _, _i18n, get_current_language


@pytest.fixture
def fresh_translator():
    """Returns a fresh Translator instance for isolated testing."""
    return Translator()

class TestTranslatorLanguageDetection:
    @patch.dict(os.environ, {"LANG": "es_ES.UTF-8", "LC_ALL": ""}, clear=True)
    def test_detect_language_env_lang(self):
        t = Translator()
        assert t._detect_language() == "es"

    @patch.dict(os.environ, {"LANG": "", "LC_ALL": "fr_FR.UTF-8"}, clear=True)
    def test_detect_language_env_lc_all(self):
        t = Translator()
        assert t._detect_language() == "fr"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_language_locale_getdefaultlocale(self):
        with patch("sys.version_info", (3, 10)):
            with patch("locale.getdefaultlocale", return_value=("de_DE", "cp1252")):
                t = Translator()
                assert t._detect_language() == "de"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_language_locale_getlocale(self):
        with patch("sys.version_info", (3, 11)), patch("locale.getlocale", return_value=("it_IT", "cp1252")):
            t = Translator()
            assert t._detect_language() == "it"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_language_locale_getlocale_none(self):
        with patch("sys.version_info", (3, 11)), patch("locale.getlocale", return_value=(None, None)):
            t = Translator()
            assert t._detect_language() == "en"

    @patch.dict(os.environ, {}, clear=True)
    def test_detect_language_fallback_on_exception(self):
        with patch("os.environ.get", side_effect=Exception("Failed")):
            t = Translator()
            assert t._detect_language() == "en"

class TestTranslatorLoadTranslations:
    @patch("mentask.core.i18n.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"hello": "hola"}')
    def test_load_translations_target_exists(self, mock_file, mock_exists, fresh_translator):
        mock_exists.return_value = True

        fresh_translator._load_translations()

        assert fresh_translator.language == "en"
        assert fresh_translator.translations == {"hello": "hola"}

    @patch("mentask.core.i18n.Path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='{"fallback": "yes"}')
    def test_load_translations_target_missing_fallback(self, mock_file, mock_exists, fresh_translator):
        # exists() returns False, so it falls back to en.json
        mock_exists.return_value = False

        fresh_translator._load_translations()

        assert fresh_translator.language == "en"
        assert fresh_translator.translations == {"fallback": "yes"}

    @patch("mentask.core.i18n.Path.exists")
    @patch("builtins.open", side_effect=Exception("File read error"))
    def test_load_translations_file_read_error(self, mock_file, mock_exists, fresh_translator):
        mock_exists.return_value = True

        fresh_translator._load_translations()

        assert fresh_translator.translations == {}

class TestTranslatorGet:
    def test_get_existing_key(self, fresh_translator):
        fresh_translator.translations = {"greet": "Hello"}
        assert fresh_translator.get("greet") == "Hello"

    def test_get_missing_key(self, fresh_translator):
        fresh_translator.translations = {"greet": "Hello"}
        assert fresh_translator.get("missing_key") == "missing_key"

    def test_get_with_kwargs_formatting(self, fresh_translator):
        fresh_translator.translations = {"greet_user": "Hello {name}"}
        assert fresh_translator.get("greet_user", name="Alice") == "Hello Alice"

    def test_get_with_kwargs_missing_in_string(self, fresh_translator):
        # kwargs provided, but string has no format placeholders
        fresh_translator.translations = {"greet": "Hello"}
        assert fresh_translator.get("greet", name="Alice") == "Hello"

    def test_get_with_missing_kwargs(self, fresh_translator):
        # suppress(KeyError) handles this scenario
        fresh_translator.translations = {"greet_user": "Hello {name} and {other}"}
        assert fresh_translator.get("greet_user", name="Alice") == "Hello {name} and {other}"

class TestGlobalHelpers:
    def test_get_current_language(self):
        _i18n.language = "test_lang"
        assert get_current_language() == "test_lang"

    def test_underscore_function(self):
        _i18n.translations = {"test_key": "Test Value"}
        assert _("test_key") == "Test Value"

        _i18n.translations = {"test_format": "Value: {val}"}
        assert _("test_format", val=42) == "Value: 42"
