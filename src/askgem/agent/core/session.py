"""
Session management module for AskGem.

Handles API authentication, client initialization, and exponential backoff retry logic.
"""

import asyncio
import logging
import os
import random
from typing import Any, Optional

from google import genai
from rich.prompt import Prompt

from ...cli.console import console
from ...core.i18n import _
from .simulation import SimulationManager, SimulationSession

_logger = logging.getLogger("askgem")

RETRYABLE_KEYWORDS = (
    "429",
    "resource exhausted",
    "rate limit",
    "500",
    "internal",
    "503",
    "unavailable",
    "deadline exceeded",
    "timeout",
)


class SessionManager:
    """Manages the Google GenAI client and chat sessions."""

    def __init__(self, config_manager, model_name: str, simulation: Optional[SimulationManager] = None):
        self.config = config_manager
        self.model_name = model_name
        self.client: Optional[genai.Client] = None
        self.chat_session: Optional[Any] = None
        self.simulation = simulation

    async def setup_api(self, interactive: bool = True) -> bool:
        """Loads and validates the Google API key (Async)."""
        # Playback mode doesn't need real API keys
        if self.simulation and self.simulation.mode == "playback":
            return True

        # Priority: 1. Environment Variable, 2. Config File
        api_key = os.environ.get("GEMINI_API_KEY") or self.config.load_api_key()

        if not api_key:
            if not interactive:
                _logger.error("API key missing in non-interactive mode.")
                return False

            console.print(f"\n[error]{_('api.missing')}[/error]")
            api_key = Prompt.ask(f"[google.blue]{_('api.prompt')}[/google.blue]").strip()

            if not api_key:
                console.print(f"[error][X] {_('api.fatal')}[/error]")
                return False

            save_choice = Prompt.ask(_("api.save")).strip().lower()
            if save_choice != "n":
                self.config.save_api_key(api_key)

        self.client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
        return True

    async def ensure_session(self, model_config: any) -> Any:
        """Ensures an active chat session is correctly initialized."""
        if self.chat_session is not None:
            return self.chat_session

        if self.simulation:
            real_session = None
            if self.simulation.mode == "record":
                if self.client is None:
                    raise RuntimeError("API not setup for recording. Call setup_api() first.")
                real_session = self.client.aio.chats.create(
                    model=self.model_name,
                    config=model_config,
                )
            self.chat_session = SimulationSession(self.simulation, real_session=real_session)
            return self.chat_session

        if self.client is None:
            raise RuntimeError("API not setup. Call setup_api() first.")
        self.chat_session = self.client.aio.chats.create(
            model=self.model_name,
            config=model_config,
        )
        return self.chat_session

    async def handle_retryable_error(self, e: Exception, attempt: int, max_retries: int, base_delay: float) -> bool:
        """Evaluates if an API error is retryable and sleeps if appropriate."""
        error_str = str(e).lower()
        is_retryable = any(keyword in error_str for keyword in RETRYABLE_KEYWORDS)

        if is_retryable and attempt < max_retries:
            delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
            _logger.warning("Retryable API error (attempt %d/%d): %s", attempt, max_retries, e)
            console.print(
                f"\n[warning]{_('engine.retry', attempt=attempt, max=max_retries, delay=f'{delay:.1f}')}[/warning]"
            )
            await asyncio.sleep(delay)
            return True
        if is_retryable:
            _logger.error("All %d retry attempts exhausted: %s", max_retries, e)
        return False

    async def reset_session(self, model_config: Any):
        """Force resets the current chat session."""
        if self.client:
            # Ensure we invalidate the old object first
            self.chat_session = None
            self.chat_session = self.client.aio.chats.create(
                model=self.model_name,
                config=model_config,
                history=[],  # Force empty history
            )
