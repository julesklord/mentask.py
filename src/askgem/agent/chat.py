"""
Main autonomous agent logic module.

Manages the conversational loop, tool routing, and API interactions with the generative models.
It does NOT manage filesystem paths or raw terminal rendering.
"""

import logging
import sys
from typing import Any, Callable, List, Optional, Union

from google.genai import types

from ..cli.console import console
from ..cli.ui_adapters import RichToolUIAdapter
from ..core.config_manager import ConfigManager
from ..core.history_manager import HistoryManager
from ..core.i18n import _
from ..core.metrics import TokenTracker
from .core.commands import CommandHandler
from .core.context import ContextManager
from .core.session import SessionManager
from .core.stream import StreamProcessor
from .tools_registry import ToolDispatcher

_logger = logging.getLogger("askgem")


class ChatAgent:
    """The central agent orchestrator.
    Coordinates session, context, streaming and commands.
    """

    def __init__(self, ui_adapter: Optional[Any] = None):
        """Initializes the chat agent and its specialized managers."""
        self.running = False
        self.config = ConfigManager(console)
        self.history = HistoryManager(console)
        # Settings
        self.model_name = self.config.settings.get("model_name", "gemini-1.5-flash")
        self.edit_mode = self.config.settings.get("edit_mode", "manual")
        # Managers
        self.session = SessionManager(self.config, self.model_name)
        self.context = ContextManager()
        self.metrics = TokenTracker(model_name=self.model_name)
        self.stream_processor = StreamProcessor(self.metrics)
        self.commands = CommandHandler(self)

        # UI & Tools
        self.ui_adapter = ui_adapter or RichToolUIAdapter()
        self.dispatcher = ToolDispatcher(
            config=self.config,
            ui=self.ui_adapter,
            logger=None,
        )

        # Stats
        self.session_messages = 0
        self.session_tools = 0
        self.interrupted = False

    def set_status_logger(self, logger_func: Callable[[str], None]):
        """Sets the callback for real-time status/debug logging.

        Args:
            logger_func: A callable that accepts a string to log status updates.
        """
        self.dispatcher.logger = logger_func

    def _build_config(self) -> types.GenerateContentConfig:
        """Helper to build consistent generation config."""
        return types.GenerateContentConfig(
            temperature=0.7,
            tools=self.dispatcher.get_tools_list(),
            system_instruction=self.context.build_system_instruction(),
        )

    async def setup_api(self, interactive: bool = True) -> bool:
        """Proxy for SessionManager setup."""
        return await self.session.setup_api(interactive)

    async def _stream_response(
        self, user_input: Union[str, List], callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """High-level streaming loop with tool iteration."""
        max_retries = 3
        base_delay = 2.0

        for attempt in range(1, max_retries + 1):
            try:
                chat_session = await self.session.ensure_session(self._build_config())
                # Turn loop
                current_input = user_input
                while True:
                    full_text, function_calls = await self.stream_processor.process_async_stream(
                        chat_session, current_input, callback
                    )
                    if not function_calls:
                        break
                    # Execute tools
                    results = []
                    for fc in function_calls:
                        results.append(await self.dispatcher.execute(fc))
                    current_input = results
                    self.session_tools += len(function_calls)

                # Maintenance
                if chat_session:
                    self.history.save_session(chat_session.get_history())
                await self.context.summarize_if_needed(self.session, self.model_name, self._build_config)
                return

            except Exception as e:
                if not await self.session.handle_retryable_error(e, attempt, max_retries, base_delay):
                    _logger.error("API Error: %s", e)
                    raise e

    async def start(self) -> None:
        """Classic CLI Entry Point."""
        if not await self.setup_api():
            sys.exit(1)

        self.running = True
        await self.session.ensure_session(self._build_config())

        from rich.prompt import Prompt

        while self.running:
            try:
                user_input = Prompt.ask(f"\n[user]{_('engine.you')}[/user]").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    await self.commands.execute(user_input)
                    continue

                self.session_messages += 1
                console.print(f"[{_('engine.agent_tag')}]AskGem:[/{_('engine.agent_tag')}]")
                await self._stream_response(user_input)

            except (KeyboardInterrupt, EOFError):
                self.running = False
                break

        console.print(f"\n[warning]{_('engine.shutdown')}[/warning]")
