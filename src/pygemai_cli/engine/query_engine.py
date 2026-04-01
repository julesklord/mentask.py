import sys
import os
import platform
import logging
from typing import List, Union

from google import genai
from google.genai import types
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Confirm
from rich.table import Table

from ..ui.console import console
from ..core.config_manager import ConfigManager, get_config_dir
from ..core.history_manager import HistoryManager
from ..tools.system_tools import list_directory, execute_bash
from ..tools.file_tools import read_file, edit_file

# Debug logger — writes to ~/.pygemai/pygemai.log so silent SDK failures
# leave a trace without crashing the streaming UI.
_log_path = os.path.join(str(get_config_dir()), "pygemai.log")
logging.basicConfig(
    filename=_log_path,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_logger = logging.getLogger("pygemai")


class QueryEngine:
    def __init__(self):
        self.running = False
        self.config = ConfigManager(console)
        self.history = HistoryManager(console)
        self.client = None
        self.chat_session = None

        # Load persisted settings
        self.model_name = self.config.settings.get("model_name", "gemini-2.5-pro")
        self.edit_mode = self.config.settings.get("edit_mode", "manual")

        # Registered autonomous tools
        self._tools = [list_directory, execute_bash, read_file, edit_file]

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def setup_api(self) -> bool:
        """Loads and validates the Google API key, prompting the user if absent."""
        api_key = self.config.load_api_key()

        if not api_key:
            console.print("\n[bold red]No valid API Key found.[/bold red]")
            api_key = console.input("[bold cyan]Please enter your Google API Key:[/bold cyan] ").strip()

            if not api_key:
                console.print("[red][X] The API Key is required to continue. Shutting down.[/red]")
                return False

            save_choice = console.input("Would you like to save it locally for future use? (Y/n): ").strip().lower()
            if save_choice != 'n':
                self.config.save_api_key(api_key)

        self.client = genai.Client(api_key=api_key)
        return True

    def _build_config(self) -> types.GenerateContentConfig:
        """Assembles the model config including live OS context as a system instruction."""
        sys_context = (
            f"You are PyGemAi, an advanced autonomous AI coding agent running in the CLI. "
            f"Operating system: {platform.system()} {platform.release()}. "
            f"Current working directory: {os.getcwd()}. "
            f"Use your tools to explore file structures, read source code, and apply precise edits. "
            f"Always call read_file before edit_file to obtain exact whitespace and indentation for the 'find_text' argument."
        )
        return types.GenerateContentConfig(
            temperature=0.7,
            tools=self._tools,
            system_instruction=sys_context,
        )

    # ------------------------------------------------------------------ #
    # Agentic tool dispatch                                                #
    # ------------------------------------------------------------------ #

    def _execute_tool(self, function_call: types.FunctionCall) -> types.Part:
        """Routes a model-requested function call to the matching local implementation."""
        tool_name = function_call.name
        args = function_call.args if function_call.args else {}

        console.print(f"[dim italic]⚙ Running autonomous tool: {tool_name}[/dim italic]")

        result: str = ""

        if tool_name == "list_directory":
            path = args.get("path", ".")
            result = list_directory(path)

        elif tool_name == "execute_bash":
            command = args.get("command", "")
            console.print(
                f"\n[bold yellow]⚠️  Action Required:[/bold yellow] "
                f"The model wants to run: [bold]'{command}'[/bold]"
            )
            if Confirm.ask("Allow this command execution?"):
                result = execute_bash(command)
            else:
                result = "System Notice: The user denied permission to run this command."

        elif tool_name == "read_file":
            result = read_file(
                args.get("path", ""),
                args.get("start_line", None),
                args.get("end_line", None),
            )

        elif tool_name == "edit_file":
            path = args.get("path", "")
            find_text = args.get("find_text", "")
            replace_text = args.get("replace_text", "")

            if self.edit_mode == "manual":
                console.print(
                    f"\n[bold yellow]⚠️  Action Required:[/bold yellow] "
                    f"The model wants to modify: [bold]'{path}'[/bold]"
                )
                console.print(
                    f"[dim]--- Replacing ---[/dim]\n{find_text}\n"
                    f"[dim]--- With ---[/dim]\n{replace_text}\n"
                    f"[dim]-----------------[/dim]"
                )
                if Confirm.ask("Allow this file modification?"):
                    result = edit_file(path, find_text, replace_text)
                else:
                    result = "System Notice: The user denied permission to modify this file."
            else:
                console.print(f"[italic green]=> Auto-approving file edit for '{path}'...[/italic green]")
                result = edit_file(path, find_text, replace_text)

        else:
            result = f"Error: Tool '{tool_name}' is not registered in this environment."

        return types.Part.from_function_response(
            name=tool_name,
            response={"result": result},
        )

    # ------------------------------------------------------------------ #
    # Core response loop                                                   #
    # ------------------------------------------------------------------ #

    def _stream_response(self, user_input: Union[str, List]) -> None:
        """
        Sends a message to the model and streams the response to the terminal.
        Uses dual function-call detection (SDK property + direct candidate parsing)
        to handle cross-version SDK differences in streaming mode.
        """
        try:
            response_stream = self.chat_session.send_message_stream(user_input)

            full_text = ""
            # Use a set to deduplicate function calls that may appear in both detection paths
            _seen_calls: set = set()
            function_calls_received: List[types.FunctionCall] = []

            with Live(Markdown(""), console=console, refresh_per_second=15) as live:
                for chunk in response_stream:
                    # Text payload — render progressively
                    if chunk.text:
                        full_text += chunk.text
                        live.update(Markdown(full_text))

                    # --- Primary detection: SDK aggregated helper property ---
                    try:
                        for fc in (chunk.function_calls or []):
                            key = (fc.name, str(sorted(fc.args.items()) if fc.args else []))
                            if key not in _seen_calls:
                                _seen_calls.add(key)
                                function_calls_received.append(fc)
                    except Exception as _sdk_err:
                        _logger.debug("SDK function_calls property failed on chunk: %s", _sdk_err)

                    # --- Fallback detection: direct candidate parts traversal ---
                    # Some SDK versions only expose function_calls on the final
                    # accumulated response, not on individual streaming chunks.
                    try:
                        for candidate in (chunk.candidates or []):
                            content = getattr(candidate, "content", None)
                            parts = getattr(content, "parts", []) or []
                            for part in parts:
                                fc = getattr(part, "function_call", None)
                                if fc and getattr(fc, "name", None):
                                    key = (fc.name, str(sorted(fc.args.items()) if fc.args else []))
                                    if key not in _seen_calls:
                                        _seen_calls.add(key)
                                        function_calls_received.append(fc)
                    except Exception as _candidate_err:
                        _logger.debug("Candidate parts fallback failed on chunk: %s", _candidate_err)

            console.print("")

            if function_calls_received:
                # Execute each tool the model requested and collect the results
                function_responses = [
                    self._execute_tool(fc) for fc in function_calls_received
                ]
                # Recursive feedback loop: send tool results back to the model
                if function_responses:
                    self._stream_response(function_responses)
            elif not full_text:
                # Model returned neither text nor function calls — surface a diagnostic hint
                console.print("[dim](No response content received — the model may have been rate-limited or the request was filtered.)[/dim]")

            # Autosave history after every fully resolved model turn
            if self.chat_session:
                raw_history = getattr(self.chat_session, "history", None)
                if raw_history:
                    self.history.save_session(raw_history)

        except Exception as e:
            console.print(f"\n[bold red][X] API Error:[/bold red] {e}")



    # ------------------------------------------------------------------ #
    # Slash commands                                                       #
    # ------------------------------------------------------------------ #

    def _process_slash_command(self, user_input: str) -> None:
        """Parses and dispatches mid-conversation slash commands."""
        parts = user_input.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if command == "/help":
            self._cmd_help()

        elif command == "/model":
            self._cmd_model(args)

        elif command == "/mode":
            self._cmd_mode(args)

        elif command == "/clear":
            self._cmd_clear()

        elif command == "/history":
            self._cmd_history(args)

        else:
            console.print(f"[yellow]Unknown command:[/yellow] {command}  — type [bold]/help[/bold] for available commands.")

    def _cmd_help(self) -> None:
        """Prints a formatted table of all available slash commands."""
        table = Table(title="PyGemAi Commands", show_header=True, header_style="bold cyan")
        table.add_column("Command", style="bold green", no_wrap=True)
        table.add_column("Description")

        table.add_row("/help", "Show this help message")
        table.add_row("/model", "List available Gemini models for your API key")
        table.add_row("/model <name>", "Switch to a different model (preserves chat history)")
        table.add_row("/mode auto", "Let the agent edit files without confirmation prompts")
        table.add_row("/mode manual", "Require confirmation before every file edit (default)")
        table.add_row("/clear", "Wipe the current context window (saves tokens)")
        table.add_row("/history list", "List all previously saved sessions")
        table.add_row("/history load <id>", "Resume a saved session (applies context window limit)")
        table.add_row("/history delete <id>", "Permanently delete a session from disk")
        table.add_row("exit / quit / q", "Exit PyGemAi")

        console.print(table)

    def _cmd_model(self, args: List[str]) -> None:
        """Lists available models or switches to the specified one."""
        if not args:
            console.print(f"[bold yellow]Active model:[/bold yellow] {self.model_name}")
            try:
                console.print("[dim]Fetching available generation models from your API key...[/dim]")
                available = []
                for model_obj in self.client.models.list():
                    # Check attribute name defensively — SDK versions differ
                    actions = getattr(model_obj, "supported_actions", None) or getattr(
                        model_obj, "supported_generation_methods", []
                    )
                    if "generateContent" in actions:
                        clean_name = model_obj.name.replace("models/", "")
                        if "gemini" in clean_name.lower():
                            available.append(clean_name)

                if available:
                    console.print("\n[bold]Available Gemini models:[/bold]")
                    for m in sorted(available):
                        active_marker = " [bold green]← active[/bold green]" if m == self.model_name else ""
                        console.print(f"  • [cyan]{m}[/cyan]{active_marker}")
            except Exception as e:
                console.print(f"[dim](Could not retrieve model list: {e})[/dim]")

            console.print("\n[dim]Usage: /model <model_name>[/dim]")
            return

        new_model = args[0]
        self.model_name = new_model
        self.config.settings["model_name"] = new_model
        self.config.save_settings()

        # Preserve history across model switch
        current_history = getattr(self.chat_session, "history", None)
        try:
            self.chat_session = self.client.chats.create(
                model=self.model_name,
                config=self._build_config(),
                history=current_history,
            )
            console.print(f"[bold green]Switched to model:[/bold green] {self.model_name}")
        except Exception as e:
            console.print(f"[bold red]Failed to switch model:[/bold red] {e}")

    def _cmd_mode(self, args: List[str]) -> None:
        """Toggles file edit confirmation mode between manual and auto."""
        if not args or args[0].lower() not in ("auto", "manual"):
            console.print(f"[bold yellow]Current edit mode:[/bold yellow] {self.edit_mode}")
            console.print("[dim]Usage: /mode auto  |  /mode manual[/dim]")
            return

        new_mode = args[0].lower()
        self.edit_mode = new_mode
        self.config.settings["edit_mode"] = new_mode
        self.config.save_settings()
        console.print(f"[bold green]Edit mode set to:[/bold green] {self.edit_mode}")

    def _cmd_clear(self) -> None:
        """Resets the in-memory context window without ending the session."""
        try:
            self.chat_session = self.client.chats.create(
                model=self.model_name,
                config=self._build_config(),
            )
            console.print(
                "[bold green]Context cleared.[/bold green] "
                "[dim]The model's memory has been reset. Previous messages are still saved on disk.[/dim]"
            )
        except Exception as e:
            console.print(f"[bold red]Failed to clear context:[/bold red] {e}")

    def _cmd_history(self, args: List[str]) -> None:
        """Manages saved sessions: list, load, or delete."""
        sub = args[0].lower() if args else "list"

        if sub == "list":
            sessions = self.history.list_sessions()
            if not sessions:
                console.print("[dim]No saved sessions found.[/dim]")
                return
            table = Table(title="Saved Sessions", show_header=True, header_style="bold cyan")
            table.add_column("#", style="dim", width=4)
            table.add_column("Session ID", style="cyan")
            for i, s in enumerate(reversed(sessions), 1):
                table.add_row(str(i), s)
            console.print(table)
            console.print("[dim]To restore one: /history load <session_id>[/dim]")

        elif sub == "load":
            if len(args) < 2:
                console.print("[yellow]Usage: /history load <session_id>[/yellow]")
                return
            session_id = args[1]
            history_data = self.history.load_session(session_id)
            if history_data is None:
                console.print(f"[red]Session '{session_id}' not found.[/red]")
                return
            try:
                self.chat_session = self.client.chats.create(
                    model=self.model_name,
                    config=self._build_config(),
                    history=history_data,
                )
                console.print(
                    f"[bold green]Session restored:[/bold green] {session_id} "
                    f"[dim]({len(history_data)} messages loaded, context window applied)[/dim]"
                )
            except Exception as e:
                console.print(f"[bold red]Failed to restore session:[/bold red] {e}")

        elif sub == "delete":
            if len(args) < 2:
                console.print("[yellow]Usage: /history delete <session_id>[/yellow]")
                return
            session_id = args[1]
            if self.history.delete_session(session_id):
                console.print(f"[bold green]Session deleted:[/bold green] {session_id}")
            else:
                console.print(f"[red]Session '{session_id}' not found.[/red]")

        else:
            console.print(f"[yellow]Unknown history sub-command:[/yellow] {sub}")
            console.print("[dim]Available: /history list | /history load <id> | /history delete <id>[/dim]")

    # ------------------------------------------------------------------ #
    # Main loop                                                            #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Initializes the client and runs the main interactive CLI loop."""
        if not self.setup_api():
            sys.exit(1)

        self.running = True

        try:
            self.chat_session = self.client.chats.create(
                model=self.model_name,
                config=self._build_config(),
            )
        except Exception as e:
            console.print(f"[bold red][X] Failed to initialize model '{self.model_name}':[/bold red] {e}")
            sys.exit(1)

        console.print(f"[dim]Model: [bold]{self.model_name}[/bold] | Edit mode: [bold]{self.edit_mode}[/bold] | Type [bold]/help[/bold] for commands.[/dim]")

        while self.running:
            try:
                user_input = console.input("\n[bold green]You:[/bold green] ").strip()
                if not user_input:
                    continue

                if user_input.lower() in ("exit", "quit", "q"):
                    self.running = False
                    break

                if user_input.startswith("/"):
                    self._process_slash_command(user_input)
                    continue

                console.print(f"[bold blue]{self.model_name}:[/bold blue]")
                self._stream_response(user_input)

            except (KeyboardInterrupt, EOFError):
                self.running = False
                break

        console.print("\n[bold yellow]Shutting down. Farewell![/bold yellow]")
