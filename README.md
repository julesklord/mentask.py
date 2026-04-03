# askgem — Autonomous AI Coding Agent for the Terminal

[![PyPI version](https://img.shields.io/pypi/v/askgem.svg)](https://pypi.org/project/askgem/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-green.svg)](LICENSE)
[![Powered by Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**askgem** is a lightweight, autonomous coding agent that lives in your terminal. Powered by Google Gemini, it reads your files, edits your code, runs shell commands, and navigates your entire filesystem — all within an interactive session and with configurable safety guardrails that keep you in control.

No GUI. No cloud sync. No bloat. Just a fast, opinionated CLI agent you can trust with your codebase.

![askgem terminal session](docs/askgem.webp)

---

## Contents

- [How it works](#how-it-works)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Slash commands](#slash-commands)
- [Safety model](#safety-model)
- [Architecture](#architecture)
- [Development](#development)
- [Internationalization](#internationalization)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## How it works

askgem runs a synchronous agentic loop backed by the `google-genai` SDK. On each turn:

1. Your message is sent to the selected Gemini model along with a set of registered tool definitions.
2. The model reasons about the request and may call one or more tools (read a file, run a command, list a directory).
3. askgem intercepts those tool calls, executes them locally (with confirmation in manual mode), and feeds results back to the model.
4. The model synthesizes a final response, streamed to your terminal in real-time Markdown.
5. The full conversation is auto-saved to `~/.askgem/history/` after every turn.

This loop repeats until the model stops requesting tools or you exit the session.

---

## Features

### Agentic tool engine
The agent has direct access to your local environment through a set of registered tools:

| Tool | Description |
|---|---|
| `list_directory` | Explore filesystem trees recursively |
| `read_file` | Read any file with optional line ranges — prevents token overflow on large files (30k char cap) |
| `edit_file` | Find-and-replace code blocks with uniqueness check and automatic `.bkp` backup |
| `execute_bash` | Run shell commands with a 60s timeout and full stdout/stderr capture |

### Human-in-the-loop safety
Every destructive action requires explicit `(Y/n)` confirmation by default. Two modes available — switch anytime mid-session:

- **`/mode manual`** (default) — Approve each file edit and shell command individually
- **`/mode auto`** — Trust the agent fully; all actions execute without prompts

### Streaming Markdown UI
Responses stream to the terminal in real-time via `rich.Live`, with syntax-highlighted code blocks, spinner feedback during tool execution, and styled panels — not a wall of plain text.

### Persistent session history
Every conversation is auto-saved to `~/.askgem/history/` as JSON. Reload any past session with `/history load <id>`. A rolling context window (20 messages / 40k chars) keeps reloaded sessions within token budget automatically.

### Model hot-swapping
Switch Gemini models mid-conversation with `/model <name>` — full chat history is preserved across the switch.

### Exponential backoff & retry
Transient API errors (429 rate limit, 500/503 server errors) trigger automatic retries with exponential backoff up to 3 attempts. You see a countdown spinner, not a crash.

### Multi-language interface
The entire UI auto-detects your OS locale and renders in your language. Override anytime with `LANG=fr_FR askgem`. See [Internationalization](#internationalization) for the full language list.

---

## Installation

### Prerequisites

- **Python 3.8+**
- A **Google API Key** — get one free at [Google AI Studio](https://aistudio.google.com/)

### From PyPI

```bash
pip install askgem
```

### From source

```bash
git clone https://github.com/julesklord/askgem.py
cd askgem.py
pip install -e ".[dev]"
```

---

## Configuration

### API key

askgem loads your API key from these sources, in order:

1. **Environment variable** — `GOOGLE_API_KEY=your_key askgem`
2. **Saved file** — `~/.askgem/.gemini_api_key_unencrypted` (created on first run if you choose to save)

On first launch without a key configured, askgem prompts you interactively and optionally saves the key for future sessions.

### Settings file

User preferences are stored in `~/.askgem/settings.json`:

```json
{
    "model_name": "gemini-2.0-flash",
    "edit_mode": "manual"
}
```

All settings can be changed mid-session via slash commands and persist automatically.

### Configuration paths reference

| Path | Purpose |
|---|---|
| `~/.askgem/settings.json` | Model name, edit mode, and other preferences |
| `~/.askgem/.gemini_api_key_unencrypted` | Locally stored API key (plaintext — protect this file) |
| `~/.askgem/history/` | Auto-saved session JSON files |
| `~/.askgem/askgem.log` | Debug log — silent SDK errors and retry events |

> **Security note:** The API key file is stored in plaintext. On POSIX systems, askgem sets permissions to `0600` (owner read-only). On Windows, no additional ACL is applied — keep this in mind if you share your user profile.

---
## Usage

Launch the interactive agent:

```bash
askgem
```

On first launch you'll see a welcome panel showing your active model, edit mode, and detected language. From there, just type naturally:

```
You: refactor the authenticate() function in src/auth.py to use JWT instead of session tokens
You: find all TODO comments in the project and summarize them
You: create a new file tests/test_auth.py with basic unit tests for the auth module
You: what's using the most memory in my Python process right now?
```

The agent will plan, use tools as needed, and stream its response directly to your terminal.

### Exiting

Type `exit`, `quit`, `q`, or press `Ctrl+C`.

---

## Slash commands

Commands available mid-session:

| Command | Description |
|---|---|
| `/help` | Show full command reference |
| `/model` | List available Gemini models for your API key |
| `/model <n>` | Switch to model number `n` from the list (history preserved) |
| `/mode auto` | Execute file edits and commands without confirmation |
| `/mode manual` | Require approval before every destructive action (default) |
| `/clear` | Reset the context window — frees tokens without ending the session |
| `/history list` | List all saved sessions with timestamps |
| `/history load <id>` | Resume a saved session (rolling window applied automatically) |
| `/history delete <id>` | Permanently remove a session from disk |
| `exit` / `quit` / `q` | Exit askgem |
| `Ctrl+C` | Interrupt current generation or force-quit |

---

## Safety model

askgem is designed to be used with real codebases, so it takes an explicit position on safety:

**In `manual` mode (default):**
- Every `edit_file` call shows you exactly what will be replaced and with what, then asks `(Y/n)`
- Every `execute_bash` call shows you the exact command before running it
- No action modifies your filesystem without your approval

**In `auto` mode:**
- Actions execute immediately without prompts
- `edit_file` still creates `.bkp` backups before every change
- Use this for trusted, well-scoped tasks where you want speed

**Always, regardless of mode:**
- `edit_file` verifies `find_text` appears exactly once in the file — ambiguous replacements are rejected
- Every file edit produces a `.bkp` backup at `<original_path>.bkp`
- `read_file` is capped at 30,000 characters to prevent context window explosion
- Shell commands run with a 60-second hard timeout

---
## Architecture

```
askgem.py/
├── src/askgem/
│   ├── __init__.py              # Package version string
│   ├── agent/
│   │   └── chat.py              # ChatAgent — main agentic loop, tool dispatch, slash commands
│   ├── cli/
│   │   ├── console.py           # Shared Rich console instance
│   │   └── main.py              # Entry point — welcome panel, boots ChatAgent
│   ├── core/
│   │   ├── config_manager.py    # JSON settings persistence, API key load/save
│   │   ├── history_manager.py   # Session serialization, rolling window context
│   │   ├── i18n.py              # Locale auto-detection, translation engine
│   │   └── paths.py             # Cross-platform config/history directory resolution
│   ├── tools/
│   │   ├── file_tools.py        # read_file, edit_file (with backup + uniqueness guard)
│   │   └── system_tools.py      # list_directory, execute_bash
│   └── locales/
│       ├── en.json              # English (fallback)
│       ├── es.json              # Español
│       ├── fr.json              # Français
│       ├── pt.json              # Português
│       ├── de.json              # Deutsch
│       ├── it.json              # Italiano
│       ├── ja.json              # 日本語
│       └── zh.json              # 中文 (简体)
├── tests/
│   ├── test_config_manager.py
│   ├── test_file_tools.py
│   ├── test_system_tools.py
│   └── diagnostic_usability.py  # Cross-language smoke tests
├── docs/
├── wiki/
├── pyproject.toml
├── CHANGELOG.md
├── ROADMAP.md
└── tox.ini
```

### Data flow

```
User input
    │
    ▼
ChatAgent._stream_response()
    │  sends to Gemini SDK → streams chunks
    │
    ├─ chunk.text → rendered via rich.Live (real-time Markdown)
    │
    └─ chunk.function_calls → _execute_tool()
            │
            ├─ list_directory  →  returns directory tree string
            ├─ read_file       →  returns file content (with line range + char cap)
            ├─ edit_file       →  uniqueness check → .bkp backup → write
            └─ execute_bash    →  subprocess with 60s timeout → stdout/stderr
                    │
                    ▼
            Tool result → fed back as function_response
                    │
                    ▼
            Recursive _stream_response() → final model answer
```

---

## Development

### Setup

```bash
git clone https://github.com/julesklord/askgem.py
cd askgem.py
pip install -e ".[dev]"
```

### Running tests

```bash
# Full test suite
pytest tests/

# With coverage report
pytest tests/ --cov=src/askgem --cov-report=term-missing

# Specific module
pytest tests/test_file_tools.py -v
```

### Static analysis

```bash
# Lint + style check
ruff check src/ tests/

# Auto-fix safe violations
ruff check src/ tests/ --fix
```

### Building for distribution

```bash
python -m build
twine check dist/*
```

### Running via tox

```bash
tox          # runs ruff + pytest across all configured Python versions
tox -e lint  # lint only
```

### Adding a new tool

1. Implement the function in `src/askgem/tools/` with a clear docstring — Gemini uses the docstring as the tool description.
2. Import and add it to `self._tools` in `ChatAgent.__init__`.
3. Add a dispatch case in `ChatAgent._execute_tool()`.
4. Add confirmation UX (manual mode) if the tool is destructive.
5. Add i18n keys for any new UI strings to all locale files under `src/askgem/locales/`.
6. Write tests in `tests/`.

---
## Internationalization

askgem auto-detects your OS locale on startup. The detection order:

1. `LANG` or `LC_ALL` environment variables
2. `locale.getlocale()` system call
3. Falls back to English if nothing matches

**Override example:**
```bash
LANG=ja_JP askgem    # force Japanese UI
LANG=de_DE askgem    # force German UI
```

**Supported languages:**

| Code | Language | File |
|---|---|---|
| `en` | English | `en.json` |
| `es` | Español | `es.json` |
| `fr` | Français | `fr.json` |
| `pt` | Português | `pt.json` |
| `de` | Deutsch | `de.json` |
| `it` | Italiano | `it.json` |
| `ja` | 日本語 | `ja.json` |
| `zh` | 中文 (简体) | `zh.json` |

### Adding a new language

1. Copy `src/askgem/locales/en.json` to `src/askgem/locales/<lang_code>.json`
2. Translate all string values — keep every key name unchanged
3. Run `python tests/diagnostic_usability.py` to verify all keys resolve correctly
4. Submit a pull request

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full development plan. Summary:

| Version | Theme | Status |
|---|---|---|
| `v2.0` | Autonomous agent, i18n, streaming TUI | ✅ Shipped |
| `v2.1` | Stability — retry logic, `/undo`, `write_file` | 🔄 In progress |
| `v2.2` | Code search — `grep_search`, `glob_find`, `diff_file` | 📋 Planned |
| `v2.3` | Web tools — Google Search API, `web_fetch` | 📋 Planned |
| `v2.4` | Token economy — usage tracking, cost estimation | 📋 Planned |
| `v2.5` | LSP integration — syntax-aware diagnostics | 🔵 Research |
| `v3.0` | Plugin ecosystem | 🔵 Future |

---

## Contributing

Pull requests are welcome. For significant changes, open an issue first to discuss scope.

**Quick checklist before submitting:**
- [ ] `ruff check src/ tests/` passes with no violations
- [ ] `pytest tests/` passes
- [ ] New public functions have Google-style docstrings
- [ ] New UI strings are added to all 8 locale files
- [ ] `CHANGELOG.md` entry added under an `[Unreleased]` section

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE) for full terms.

In short: free to use, modify, and distribute. Derivative works must also be GPL-licensed and open source.

---

Built by [julesklord](https://github.com/julesklord).
