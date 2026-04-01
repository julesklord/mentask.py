# PyGemAi v2.0 (Beta)

PyGemAi is a powerful, autonomous command-line interface (CLI) client for interacting with Google's Gemini AI models. Designed for terminal-based development, it now comes equipped with agentic tools that allow it to read, write, and execute commands directly on your machine.

![PyGemAi Logo](docs/PyGemAi.webp)

## ✨ Key Features (v2.0 Redesign)

*   **⚡ Autonomous Agentic Engine:** PyGemAi integrates natively with `google-genai>=0.2.0`, enabling multi-step reasoning, filesystem exploration (`list_directory`, `read_file`), and autonomous actions (`edit_file`, `execute_bash`).
*   **🛡️ Human-in-the-Loop Safety:** A built-in guardrail system prompts for user confirmation before executing potentially destructive actions like modifying files or running bash scripts. Use `/mode auto` if you trust the model completely, or `/mode manual` to explicitly approve every action. Mandatory `*.bkp` files are generated for all edits.
*   **🏠 Centralized Configuration:** Easily manage settings via `~/.pygemai/settings.json`.
*   **📚 Smart Context Windows:** Sessions are persisted automatically per model (`~/.pygemai/history/`). Loads old chat logs utilizing dynamic token "Rolling Windows" to conserve API costs.
*   **🌈 Interactive Markdown:** Rich terminal rendering with real-time UI streaming for code blocks, tables, and standard outputs.

## 🚀 Quick Installation

### Prerequisites
*   Python 3.8 or higher.
*   A Google API Key (Get yours at [Google AI Studio](https://aistudio.google.com/)).

### Install for Development
```bash
git clone https://github.com/julesklord/PyGemAi.git
cd PyGemAi
# Install development dependencies and the cli globally
pip install -e ".[dev]"
```

## 📖 Basic Usage

Launch the interactive assistant by running:
```bash
pygemai
```

### In-Chat Slash Commands:
*   `/model [model_name]`: Switch the active generation model seamlessly (e.g., `/model gemini-2.5-flash`). Run `/model` alone to see all available models for your API key.
*   `/mode [auto|manual]`: Toggle safety prompt blocks for CLI/filesystem side-effects.
*   `/history list`: Browse automatically saved past sessions.
*   `/history load [id]`: Reload an old context.
*   `/history delete [id]`: Remove specific conversations.
*   `/clear`: Wipe the current working context for a fresh slate without losing saved disk history.
*   `/help`: View the full command sheet.

*   `exit`, `quit`: Close the CLI.
*   `Ctrl+C`: Interrupt generation or forcefully close the program.

## 🛠️ Development & Testing

Since PyGemAi directly manipulates your filesystem during development requests, it is strongly recommended to isolate dependencies properly or run it in a container if working on highly sensitive tasks.

```bash
# Install dependencies including testing tools
pip install -e ".[dev]"

# Run test suite
pytest tests/
```

## 📝 License
This project is licensed under the **GNU General Public License v3 (GPLv3)**. Please review the `LICENSE` file for details.

---
Built with ❤️ by [julesklord](mailto:julioglez.93@gmail.com)
