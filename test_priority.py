import os
from unittest.mock import patch

import keyring
from rich.console import Console

from mentask.core.config_manager import ConfigManager

console = Console()
cm = ConfigManager(console)

# Test priority: Keyring vs Env Var
provider = "test_provider"
env_var = "TEST_PROVIDER_API_KEY"
keyring_val = "keyring-key-789"
env_val = "env-key-123"

with patch.dict(os.environ, {env_var: env_val}):
    with patch("keyring.get_password", return_value=keyring_val):
        loaded = cm.load_api_key(provider)
        print(f"Keyring: {keyring_val} | Env: {env_val} | Loaded: {loaded}")
        # Now Keyring should win!
        assert loaded == keyring_val

with patch.dict(os.environ, {env_var: env_val}):
    with patch("keyring.get_password", return_value=None):
        loaded = cm.load_api_key(provider)
        print(f"Keyring: None | Env: {env_val} | Loaded: {loaded}")
        # Falls back to Env
        assert loaded == env_val

print("Priority tests passed!")
