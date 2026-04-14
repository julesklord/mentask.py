"""Console UI module for AskGem.

This module provides a globally configured rich console instance with the
Google Brand Identity theme (Web 2.0 colors) for standardized logging
and output formatting.
"""

from rich.console import Console
from rich.theme import Theme

# Define Google Identity Theme for AskGem
# Blue = Agent/Global, Yellow = User/Action
askgem_theme = Theme(
    {
        "google.blue": "#4285F4",
        "google.yellow": "#FBBC05",
        "google.red": "#EA4335",
        "google.green": "#34A853",
        "agent": "bold #4285F4",
        "user": "bold #FBBC05",
        "status": "italic #4285F4",
        "warning": "bold #FBBC05",
        "error": "bold #EA4335",
        "success": "bold #34A853",
    }
)

# Global configured console instance to print rich output throughout the app
console = Console(theme=askgem_theme)
