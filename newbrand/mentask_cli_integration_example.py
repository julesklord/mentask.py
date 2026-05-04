# mentask/cli/main.py - INTEGRACIÓN CON SISTEMA CONTEXTUAL
"""
Ejemplo de cómo integrar el sistema contextual en main.py existente.
Esto muestra el flujo de inicialización y uso.
"""

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from mentask.core.config_manager import ConfigManager
from mentask.core.models_hub import hub
from mentask.cli.contextual_prompts import (
    ContextualOrchestrator,
    ContextualConfigManager,
    ContextType,
    NeonTheme,
    ContextualPromptLibrary,
)
from mentask.cli.themes import get_theme


class MentaskCLI:
    """CLI mejorada con sistema contextual neon."""

    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager(self.console)
        self.contextual_config = ContextualConfigManager()
        self.orchestrator = ContextualOrchestrator(
            self.contextual_config,
            self.console
        )

    def show_context_menu(self) -> None:
        """Menú interactivo para seleccionar contexto."""
        self.console.print("\n")
        self.console.print(
            Panel(
                "[bold]Selecciona tu contexto de trabajo[/bold]\n" +
                "1. 🧑‍💻 Coding (Ingeniería de software)\n" +
                "2. 🎵 Music Production (Producción musical)\n" +
                "3. 📊 Analysis (Análisis de datos)\n" +
                "4. 🎨 Creative (Creativo)\n" +
                "5. 💬 General (General)",
                title="[bold cyan]Contextos Disponibles[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
        )

        choice = Prompt.ask(
            "[cyan]Selecciona contexto[/cyan]",
            choices=["1", "2", "3", "4", "5"],
            default="5"
        )

        context_map = {
            "1": ContextType.CODING,
            "2": ContextType.MUSIC_PRODUCTION,
            "3": ContextType.ANALYSIS,
            "4": ContextType.CREATIVE,
            "5": ContextType.GENERAL,
        }

        selected = context_map[choice]
        self.contextual_config.set_context(selected)
        self.orchestrator.log_with_context(
            f"Contexto cambiado a {selected.value}",
            level="success"
        )

    def show_theme_menu(self) -> None:
        """Menú interactivo para seleccionar tema neon."""
        self.console.print("\n")
        self.console.print(
            Panel(
                "[bold]Selecciona tu tema Neon[/bold]\n" +
                "1. 🌺 Neon Pink\n" +
                "2. 💎 Neon Cyan\n" +
                "3. 💜 Neon Purple\n" +
                "4. 🟢 Neon Matrix",
                title="[bold magenta]Temas Disponibles[/bold magenta]",
                border_style="magenta",
                padding=(1, 2),
            )
        )

        choice = Prompt.ask(
            "[magenta]Selecciona tema[/magenta]",
            choices=["1", "2", "3", "4"],
            default="2"
        )

        theme_map = {
            "1": "neon_pink",
            "2": "neon_cyan",
            "3": "neon_purple",
            "4": "neon_matrix",
        }

        selected = theme_map[choice]
        self.contextual_config.set_theme(selected)
        self.orchestrator.renderer.theme = NeonTheme.get(selected)
        self.orchestrator.log_with_context(
            f"Tema cambiado a {selected}",
            level="success"
        )

    def initialize_session(self) -> None:
        """Inicializa una sesión con contexto y tema."""
        # 1. Mostrar contexto actual
        context = self.contextual_config.get_active_context()
        theme_name = self.contextual_config.contexts.get("active_theme", "neon_cyan")
        
        header = self.orchestrator.render_context_header()
        self.console.print(header)
        
        self.console.print(
            f"[{self.orchestrator.renderer.theme.text_secondary}]"
            f"Tema: {theme_name} | Contexto: {context.value}[/]"
        )

        # 2. Opcionalmente cambiar contexto
        if Confirm.ask("[cyan]¿Cambiar contexto?[/cyan]", default=False):
            self.show_context_menu()

        # 3. Opcionalmente cambiar tema
        if Confirm.ask("[magenta]¿Cambiar tema?[/magenta]", default=False):
            self.show_theme_menu()

        self.console.print()

    def get_system_prompt(self, model_id: str) -> str:
        """Obtiene el system prompt adaptado al contexto y modelo."""
        model_info = hub.get_model(model_id)
        model_family = "claude" if "claude" in model_id.lower() else "gpt" if "gpt" in model_id.lower() else "groq"
        
        system_prompt = self.orchestrator.prepare_system_prompt(model_family)
        
        # Log contextual
        context = self.contextual_config.get_active_context()
        self.orchestrator.log_with_context(
            f"Usando prompt contextual para {context.value} + {model_family}",
            level="info"
        )
        
        return system_prompt

    def show_context_info(self) -> None:
        """Muestra información del contexto actual."""
        context = self.contextual_config.get_active_context()
        prompt = ContextualPromptLibrary.get(context)
        
        self.console.print()
        self.console.print(
            Panel(
                f"[bold cyan]{prompt.context.value.upper()}[/bold cyan]\n\n"
                f"[yellow]Tono:[/yellow] {prompt.tone}\n"
                f"[yellow]Constraints:[/yellow]\n" +
                "\n".join(f"  • {c}" for c in prompt.constraints),
                title=f"[bold]Detalles del Contexto[/bold]",
                border_style="cyan",
                padding=(1, 2),
            )
        )
        self.console.print()

    def run_chatbot(self) -> None:
        """Loop principal del chatbot con contexto."""
        self.console.print(
            Panel(
                "[bold magenta]mentask v0.22.0[/bold magenta]\n"
                "[cyan]Multi-API + Contextos + Temas Neon[/cyan]",
                title="[bold]Bienvenido[/bold]",
                border_style="magenta",
            )
        )

        # Inicializar sesión
        self.initialize_session()

        # Loop principal (simplificado)
        while True:
            try:
                # Mostrar contexto actual
                context = self.contextual_config.get_active_context()
                theme = self.contextual_config.contexts.get("active_theme")
                
                prompt_text = (
                    f"[{self.orchestrator.renderer.theme.brand_primary}]"
                    f"[{context.value}] ❯[/]"
                )
                
                user_input = self.console.input(prompt_text)

                if not user_input.strip():
                    continue

                # Comandos especiales
                if user_input.lower() == "/context":
                    self.show_context_menu()
                    continue
                elif user_input.lower() == "/theme":
                    self.show_theme_menu()
                    continue
                elif user_input.lower() == "/info":
                    self.show_context_info()
                    continue
                elif user_input.lower() in ["/exit", "/quit", "exit"]:
                    self.orchestrator.log_with_context("Hasta luego!", level="success")
                    break

                # Procesar input normal (placeholder)
                self.console.print(
                    f"[{self.orchestrator.renderer.theme.info}]"
                    f"Procesando: {user_input}[/]"
                )

            except KeyboardInterrupt:
                self.orchestrator.log_with_context("Sesión interrumpida", level="warning")
                break
            except Exception as e:
                self.orchestrator.log_with_context(f"Error: {e}", level="error")


def run_chatbot():
    """Entry point."""
    cli = MentaskCLI()
    cli.run_chatbot()


# EJEMPLOS DE USO PROGRAMÁTICO
def example_programmatic_usage():
    """Ejemplo de uso programático del sistema."""
    
    # 1. Crear orchestrator
    contextual_config = ContextualConfigManager()
    console = Console()
    orchestrator = ContextualOrchestrator(contextual_config, console)

    # 2. Cambiar contexto
    contextual_config.set_context(ContextType.CODING)
    contextual_config.set_theme("neon_pink")

    # 3. Obtener system prompt
    system_prompt = orchestrator.prepare_system_prompt("claude")
    print("System Prompt:\n", system_prompt)

    # 4. Renderizar componentes
    console.print(orchestrator.render_context_header())
    console.print(orchestrator.renderer.render_code_block(
        "async def fetch_data():\n    return await client.get('/api')",
        language="python"
    ))

    # 5. Renderizar estadísticas
    stats = {
        "tokens_used": "2,450",
        "cost": "$0.012",
        "latency": "340ms",
    }
    console.print(orchestrator.renderer.render_stats(stats))


if __name__ == "__main__":
    # Descomentar para probar
    # example_programmatic_usage()
    run_chatbot()