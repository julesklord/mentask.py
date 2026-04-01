import os
import sys


def run_chatbot():
    """
    Main entry point for askgem v2.0.
    """
    from rich.align import Align
    from rich.markdown import Markdown
    from rich.panel import Panel

    from . import __version__
    from .core.i18n import _, get_current_language
    from .engine.query_engine import QueryEngine
    from .ui.console import console

    # Initialize the engine to load settings
    engine = QueryEngine()

    # Render stylized Welcome Panel
    welcome_text = (
        f"**{_('startup.welcome', version=__version__)}**\n\n"
        f"_{_('startup.init')}_\n\n"
        f"*{_('startup.dashboard', model=engine.model_name, mode=engine.edit_mode, lang=get_current_language())}*\n\n"
        f"{_('cmd.hint_help')}"
    )

    console.print()
    console.print(Panel(
        Align.center(Markdown(welcome_text)),
        border_style="bold cyan",
        padding=(1, 2)
    ))
    console.print()

    # Launch CLI
    engine.start()

if __name__ == "__main__":
    # Adjust python path for direct file execution execution
    if __package__ is None:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    run_chatbot()
