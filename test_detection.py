from rich.console import Console

from mentask.core.config_manager import ConfigManager

console = Console()
cm = ConfigManager(console)

keys = [
    ("sk-proj-openai-key-long-one", "openai"),
    ("sk-ant-anthropic-key", "anthropic"),
    ("AIzaSy-google-key", "google"),
    ("sk-generic-key", "openai"),
]

for key, expected in keys:
    detected = cm.detect_provider(key)
    print(f"Key: {key[:10]}... | Detected: {detected} | Expected: {expected}")
    assert detected == expected

print("Tests passed!")
