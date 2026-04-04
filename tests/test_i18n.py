import os
import locale
from unittest.mock import patch
from askgem.core.i18n import Translator

def test_detect_language_env_lang():
    translator = Translator()
    with patch.dict(os.environ, {"LANG": "fr_FR.UTF-8"}):
        assert translator._detect_language() == "fr"

def test_detect_language_env_lc_all():
    translator = Translator()
    with patch.dict(os.environ, {"LC_ALL": "es-ES"}, clear=True):
        assert translator._detect_language() == "es"

def test_detect_language_locale_getlocale():
    translator = Translator()
    with patch.dict(os.environ, {}, clear=True):
        with patch("locale.getlocale", return_value=("de_DE", "UTF-8")):
            assert translator._detect_language() == "de"

def test_detect_language_locale_none():
    translator = Translator()
    with patch.dict(os.environ, {}, clear=True):
        with patch("locale.getlocale", return_value=(None, None)):
            assert translator._detect_language() == "en"

def test_detect_language_exception():
    translator = Translator()
    with patch.dict(os.environ, {}, clear=True):
        with patch("locale.getlocale", side_effect=Exception("locale error")):
            assert translator._detect_language() == "en"
