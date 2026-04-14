"""
Slash command handling module for AskGem.

Parses and dispatches mid-conversation commands like /help, /model, /mode, etc.
"""

import logging
from typing import Any, List, Optional, Union

from rich.panel import Panel
from rich.table import Table

from ...core.i18n import _

_logger = logging.getLogger("askgem")

COMMAND_METADATA = {
    "/help": {"desc": _("cmd.desc.help"), "example": "/help", "category": "General"},
    "/model": {"desc": _("cmd.desc.model_list"), "example": "/model [name]", "category": "Config"},
    "/mode": {"desc": _("cmd.desc.mode_manual"), "example": "/mode auto/manual", "category": "Config"},
    "/clear": {"desc": _("cmd.desc.clear"), "example": "/clear", "category": "Session"},
    "/usage": {"desc": _("cmd.desc.usage"), "example": "/usage", "category": "Stats"},
    "/stats": {"desc": _("cmd.desc.stats"), "example": "/stats", "category": "Stats"},
    "/reset": {"desc": "Reinicia la sesión y contadores", "example": "/reset", "category": "Session"},
    "/stop": {"desc": "Interrumpe la generación actual", "example": "/stop", "category": "Control"},
    "/exit": {"desc": _("cmd.desc.exit"), "example": "/exit", "category": "Control"},
}


class CommandHandler:
    """Dispatches and executes slash commands."""

    def __init__(self, agent):
        self.agent = agent

    async def execute(self, user_input: str) -> Optional[Any]:
        """Parses and dispatches a command.
        Returns:
            Optional[any]: A Rich renderable (Table/Panel) if the command has output,
                          or True if handled silently, or None if unknown.
        """
        parts = user_input.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command == "/help":
            return self._cmd_help()
        elif command == "/model":
            return await self._cmd_model(args)
        elif command == "/mode":
            return self._cmd_mode(args)
        elif command == "/clear":
            await self.agent.session.reset_session(self.agent._build_config())
            return f"[success]{_('cmd.clear.success')}[/success]"
        elif command == "/usage":
            return self._cmd_usage()
        elif command == "/stats":
            return self._cmd_stats()
        elif command in ("/exit", "/quit", "/q"):
            self.agent.running = False
            return True
        elif command == "/stop":
            self.agent.stream_processor.interrupted = True
            return True
        elif command == "/reset":
            await self.agent.session.reset_session(self.agent._build_config())
            self.agent.session_messages = 0
            self.agent.session_tools = 0
            return "[bold red]Sesión reiniciada.[/]"
        return None

    def _cmd_help(self) -> Table:
        """Returns the help table as a Rich object."""
        table = Table(title=_("cmd.help.title"), show_header=True, header_style="bold #6366f1", box=None)
        table.add_column(_("cmd.help.header.cmd"), style="bold cyan")
        table.add_column(_("cmd.help.header.desc"))
        table.add_column("Ejemplo", style="dim")

        for cmd, meta in COMMAND_METADATA.items():
            table.add_row(cmd, meta["desc"], meta["example"])
        return table

    async def _cmd_model(self, args: List[str]) -> Union[str, Table]:
        """Lists or switches Gemini models."""
        if not args:
            try:
                models_response = await self.agent.session.client.aio.models.list()
                table = Table(title=_("cmd.model.available"), box=None)
                table.add_column("Modelo", style="#4285F4")
                table.add_column("Estado")
                async for m in models_response:
                    if "generateContent" in (m.supported_actions or []):
                        name = m.name.replace("models/", "")
                        status = "[success]Actual[/success]" if name == self.agent.model_name else ""
                        table.add_row(name, status)
                return table
            except Exception as e:
                return f"[dim]Error al listar modelos: {e}[/dim]"

        new_model = args[0]
        # Basic validation to avoid common typos (like 2.5)
        valid_prefixes = ("gemini-", "learnlm-", "lyria-", "nano-")
        if not any(new_model.startswith(p) for p in valid_prefixes):
            return f"[warning]Atención:[/] El modelo '{new_model}' podría no ser válido. Usa [bold]/model[/] sin argumentos para ver la lista."

        self.agent.model_name = new_model
        self.agent.session.model_name = new_model
        await self.agent.session.reset_session(self.agent._build_config())
        return f"[success]{_('cmd.model.switched')}[/success] [bold]{new_model}[/bold]"

    def _cmd_mode(self, args: List[str]) -> str:
        """Toggles edit mode."""
        if not args or args[0].lower() not in ("auto", "manual"):
            return f"[warning]{_('cmd.mode.current')}[/warning] [bold]{self.agent.edit_mode}[/bold]"
        mode = args[0].lower()
        self.agent.edit_mode = mode
        self.agent.config.settings["edit_mode"] = mode
        self.agent.config.save_settings()
        return f"[success]{_('cmd.mode.set')}[/success] [bold]{mode}[/bold]"

    def _cmd_usage(self) -> Panel:
        """Displays token usage."""
        summary = self.agent.metrics.get_summary()
        return Panel(summary, title=_("cmd.usage.title"), border_style="#6366f1")

    def _cmd_stats(self) -> Panel:
        """Displays session stats."""
        stats = (
            f"📩 Mensajes: [bold]{self.agent.session_messages}[/bold]\n"
            f"🛠️ Herramientas: [bold]{self.agent.session_tools}[/bold]\n"
            f"📝 Archivos: [bold]{self.agent.dispatcher.modified_files_count}[/bold]"
        )
        return Panel(stats, title=_("cmd.stats.title"), border_style="#6366f1", expand=False)
