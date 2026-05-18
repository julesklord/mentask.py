import json
import logging
import os
import subprocess
import urllib.request
from typing import Any

_logger = logging.getLogger("mentask")


def _get_wsl_ips() -> list[str]:
    """Attempts to get WSL VM IP addresses (Windows only)."""
    try:
        result = subprocess.run(
            ["wsl.exe", "--", "hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return [ip for ip in result.stdout.strip().split() if ip.count(".") == 3]
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
        _logger.debug(f"WSL IP detection failed: {e}")
    return []


def resolve_base_url(config: Any | None = None) -> str:
    """
    Returns the Ollama base URL (without path) to use for API calls and discovery.

    Priority:
      1. Custom ``ollama_endpoint`` from settings (strips trailing ``/v1`` if present)
      2. ``http://localhost:11434``
      3. WSL-detected IP on Windows (fallback if localhost fails later)
    """
    if config:
        custom = config.settings.get("ollama_endpoint")
        if custom:
            base = custom.rstrip("/")
            if base.endswith("/v1"):
                base = base[:-3]
            return base
    return "http://localhost:11434"


def probe_ollama(config: Any | None = None) -> tuple[str, list[str]]:
    """
    Probes candidate Ollama endpoints and returns ``(base_url, model_names)``
    for the first one that responds.

    Tries in order:
      1. Configured endpoint (from ``ollama_endpoint`` setting)
      2. ``http://localhost:11434``
      3. Each WSL-detected IP (Windows only)
    """
    candidates: list[str] = []

    if config:
        custom = config.settings.get("ollama_endpoint")
        if custom:
            base = custom.rstrip("/")
            if base.endswith("/v1"):
                base = base[:-3]
            if base not in candidates:
                candidates.append(base)

    default = "http://localhost:11434"
    if default not in candidates:
        candidates.append(default)

    if os.name == "nt":
        for ip in _get_wsl_ips():
            url = f"http://{ip}:11434"
            if url not in candidates:
                candidates.append(url)

    for base_url in candidates:
        models = fetch_ollama_models(base_url)
        if models:
            _logger.info("Ollama discovered at %s (%d models)", base_url, len(models))
            return base_url, models

    _logger.debug("Ollama not found on any probed endpoint")
    return candidates[0] if candidates else default, []


def fetch_ollama_models(base_url: str, timeout: int = 3) -> list[str]:
    """Fetch model names from an Ollama ``/api/tags`` endpoint."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
            return [m["name"] for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def check_ollama_running(base_url: str | None = None, config: Any | None = None) -> bool:
    """Quick health check — returns True if Ollama responds at *base_url*."""
    url = base_url or resolve_base_url(config)
    try:
        req = urllib.request.Request(f"{url.rstrip('/')}/api/tags")
        with urllib.request.urlopen(req, timeout=2):
            return True
    except Exception:
        return False
