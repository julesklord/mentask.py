# askgem — Development Roadmap

> **Version:** `0.8.0` (current)
> **Target:** `1.0.0` stable release
> **Updated:** April 2026
> **Maintainer:** [@julesklord](https://github.com/julesklord)

This document maps the path from the current `0.8.0` pre-release to a `1.0.0`
stable release, and beyond. Milestones are sequenced by dependency and priority.
Each item includes the technical problem, the proposed solution, and acceptance
criteria so progress is unambiguous.

---

## Table of Contents

1. [Where we are: v0.8.0](#1-where-we-are-v080)
2. [v0.9.0 — Correctness & Robustness](#2-v090--correctness--robustness)
3. [v0.9.5 — Search & Code Intelligence](#3-v095--search--code-intelligence)
4. [v1.0.0 — Stable Release](#4-v100--stable-release)
5. [Post-1.0 — Web & Metrics](#5-post-10--web--metrics)
6. [Long-term — LSP & Plugins](#6-long-term--lsp--plugins)
7. [Non-goals](#7-non-goals)
8. [Release timeline](#8-release-timeline)

---

## 1. Where we are: v0.8.0

### What works

| Feature | Module | Status |
|---|---|---|
| Multi-turn chat with Gemini models | `agent/chat.py` | ✅ |
| `read_file` with line range support | `tools/file_tools.py` | ✅ |
| `edit_file` with `.bkp` backup | `tools/file_tools.py` | ✅ |
| `execute_bash` with 60s timeout | `tools/system_tools.py` | ✅ |
| `list_directory` | `tools/system_tools.py` | ✅ |
| Human-in-the-loop confirmations | `agent/chat.py` | ✅ |
| `/mode auto\|manual` | `agent/chat.py` | ✅ |
| `/model` hot-swap | `agent/chat.py` | ✅ |
| Exponential backoff retry (3 attempts) | `agent/chat.py` | ✅ |
| Rolling window session persistence | `core/history_manager.py` | ✅ |
| `/history list\|load\|delete` | `agent/chat.py` | ✅ |
| i18n auto-detection (8 languages) | `core/i18n.py` + `locales/` | ✅ |
| Rich TUI — streaming Markdown, spinners | `cli/` + `rich` | ✅ |
| JSON config persistence | `core/config_manager.py` | ✅ |
| Debug logging to `~/.askgem/askgem.log` | `agent/chat.py` | ✅ |

### Known gaps (blocking 1.0.0)

1. **No `write_file` tool** — creating new files requires abusing `edit_file` with
   empty `find_text`, which is semantically wrong and has edge cases.
2. **No `/undo` command** — `.bkp` files exist but there's no in-session way to
   restore them.
3. **No search tools** — the agent can't grep for patterns or find files by glob
   without burning tokens reading every file manually.
4. **No context overflow protection** — if a session exceeds the model's context
   limit, the SDK throws an opaque `InvalidArgument` instead of recovering gracefully.
5. **`edit_file` uniqueness guard missing** *(fixed in `[Unreleased]`)* — was
   silently replacing all occurrences.
6. **`read_file` no char cap** *(fixed in `[Unreleased]`)* — could explode context
   on large files.
7. **CI/CD not wired** — no automated test run on push.
8. **PyPI package not current** — published version predates the rewrite.

---

## 2. v0.9.0 — Correctness & Robustness

**Priority:** 🔴 Critical — fix the gaps that cause data loss or silent failures.
**Target:** May 2026

### 2.1 `write_file` tool

**Problem:** Creating new files via `edit_file(path, find_text="", ...)` is a hack.
The intent is ambiguous and the edge case where `os.path.dirname()` returns `""` on
a bare filename causes a silent `FileNotFoundError`.

**Solution:** First-class `write_file(path, content)` tool with explicit semantics.

```python
def write_file(path: str, content: str) -> str:
    """Creates a new file at path with the given content.
    Fails if the file already exists to prevent accidental overwrites.
    Use edit_file to modify existing files."""
```

- Creates all parent directories as needed
- Refuses to overwrite an existing file (returns error, doesn't silently clobber)
- Human-in-the-loop confirmation in manual mode
- Unit tests: creation, parent dir creation, overwrite rejection, permission errors

**Files:** `tools/file_tools.py`, `agent/chat.py` (register + dispatch)

**Acceptance criteria:**
- [ ] `write_file("src/new_module.py", "...")` creates the file and all parent dirs
- [ ] Calling it on an existing path returns a clear error
- [ ] Test coverage ≥ 4 cases

### 2.2 `/undo` command

**Problem:** Every `edit_file` creates a `.bkp` but there's no in-session way to
restore it. Users have to manually copy files from the terminal.

**Solution:** Track the last edited file path in `ChatAgent`. `/undo` copies
`<path>.bkp` back to `<path>` and confirms success.

- Only the most recent edit is undoable (single-level undo — `/undo` again does nothing)
- Clear message if no backup exists
- Manual mode: shows what will be restored, asks confirmation
- Adds i18n keys: `cmd.desc.undo`, `cmd.undo.success`, `cmd.undo.none`,
  `cmd.undo.confirm`

**Files:** `agent/chat.py`

**Acceptance criteria:**
- [ ] `/undo` after an `edit_file` restores the previous content
- [ ] `/undo` with no prior edit shows a clean "nothing to undo" message
- [ ] The restored file matches the `.bkp` byte-for-byte

### 2.3 Graceful context overflow recovery

**Problem:** When a reloaded session + new input exceeds the model's context limit,
the SDK raises `InvalidArgument: ... tokens exceed the limit`. The user gets a raw
Python exception.

**Solution:** Catch `InvalidArgument` in `_stream_response`. If the error string
mentions tokens/context, call `history_manager.truncate_half()` and retry once
before surfacing an error.

```python
def truncate_half(self) -> None:
    """Drops the oldest 50% of the current session history in-memory."""
```

- Notifies the user that context was trimmed
- Retries the same message automatically
- Falls through to normal error handling if retry also fails

**Files:** `agent/chat.py`, `core/history_manager.py`

**Acceptance criteria:**
- [ ] A session with a loaded history that overflows triggers one automatic trim+retry
- [ ] User sees "Context trimmed, retrying..." — not a stack trace
- [ ] Second attempt with trimmed context succeeds (tested with a mock that raises
  once then succeeds)

### 2.4 CI/CD via GitHub Actions

**Problem:** No automated quality gate on push or PR.

**Solution:** `.github/workflows/ci.yml` that runs on every push and PR to `main`:

```
ruff check src/ tests/
pytest tests/ -v
python -m build --check
```

- Fails fast on lint errors before running tests
- Matrix: Python 3.10, 3.11, 3.12
- Separate `publish.yml` triggered on version tag push (`v*`) that uploads to PyPI
  via `twine`

**Files:** `.github/workflows/ci.yml`, `.github/workflows/publish.yml`

**Acceptance criteria:**
- [ ] Push with a ruff violation fails CI at the lint step
- [ ] Push with a broken test fails CI at the test step
- [ ] Tag push `v0.9.0` triggers publish workflow

---

## 3. v0.9.5 — Search & Code Intelligence

**Priority:** 🟠 High — transforms the agent from a file editor into a codebase navigator.
**Target:** June 2026

### 3.1 `grep_search` tool

**Problem:** The agent has no way to find where a function is defined, where a
variable is used, or which files import a given module. It must read every file
manually — expensive in tokens and slow.

**Solution:** `grep_search(pattern, path, is_regex, case_sensitive)` using Python's
`pathlib.Path.rglob()` + line-by-line matching.

```python
def grep_search(
    pattern: str,
    path: str = ".",
    is_regex: bool = False,
    case_sensitive: bool = False,
) -> str:
    """Search for a string or regex pattern across all text files under path.
    Returns matching lines with file:line_number prefixes, capped at 50 results.
    Skips binary files, .git/, __pycache__/, node_modules/, .venv/."""
```

- Returns `file:line: matching_line` format, max 50 results
- Binary detection via null-byte check in first 8KB
- Skips common noise dirs automatically
- Result cap prevents context overflow

**Files:** `tools/search_tools.py` (new), `agent/chat.py` (register + dispatch)

**Acceptance criteria:**
- [ ] `grep_search("def authenticate", "src/")` returns file paths and line numbers
- [ ] Results capped at 50
- [ ] Binary files skipped silently
- [ ] Regex mode works (`is_regex=True`)
- [ ] Unit tests: match, no match, binary skip, cap enforcement

### 3.2 `glob_find` tool

**Problem:** The agent can't discover files by name pattern — e.g., "find all YAML
configs" or "which Python files are in the tests directory".

**Solution:** `glob_find(pattern, path)` using `pathlib.Path.rglob()`.

```python
def glob_find(pattern: str, path: str = ".") -> str:
    """Find all files matching a glob pattern under path.
    Example: glob_find('*.py', 'src/') or glob_find('**/*.yaml', '.')
    Skips .git/, __pycache__/, node_modules/, .venv/."""
```

**Files:** `tools/search_tools.py`

**Acceptance criteria:**
- [ ] `glob_find("*.py", "src/")` returns all Python files under `src/`
- [ ] `glob_find("**/*.json", ".")` finds nested JSON files
- [ ] Noise dirs excluded from results

### 3.3 `diff_file` tool

**Problem:** After an edit, the agent (and the user) has no easy way to review
what changed. `.bkp` files exist but aren't surfaced as diffs.

**Solution:** `diff_file(path)` compares the file against its `.bkp` using
`difflib.unified_diff`.

```python
def diff_file(path: str) -> str:
    """Show a unified diff between the current file and its last .bkp backup.
    Returns 'No backup found' if no .bkp exists."""
```

- Output is standard unified diff format
- Works on any file that has a `.bkp` alongside it
- Useful as a pre-commit review step

**Files:** `tools/file_tools.py`

**Acceptance criteria:**
- [ ] Shows correct unified diff after an `edit_file` call
- [ ] Returns clean message when no `.bkp` exists
- [ ] Empty diff when file and backup are identical

---

## 4. v1.0.0 — Stable Release

**Priority:** 🔴 Gate — nothing ships as 1.0 until all items below are complete.
**Target:** July 2026

### Requirements for 1.0.0

All of the following must be true before tagging `v1.0.0`:

**Correctness**
- [ ] All items in v0.9.0 and v0.9.5 shipped and tested
- [ ] `edit_file` uniqueness guard in place (done in `[Unreleased]`)
- [ ] `read_file` char cap in place (done in `[Unreleased]`)
- [ ] No known data-loss bugs

**Stability**
- [ ] CI passes on Python 3.10, 3.11, 3.12
- [ ] Test coverage ≥ 70% across `tools/` and `core/`
- [ ] No bare `except:` blocks anywhere in production code
- [ ] All public functions have complete Google-style docstrings

**Documentation**
- [ ] README accurate and complete
- [ ] All 8 locale files have every key present (verified by `diagnostic_usability.py`)
- [ ] CHANGELOG up to date
- [ ] `wiki/` covers Installation, Usage, API Reference, Architecture, FAQ

**Distribution**
- [ ] PyPI package current and installable via `pip install askgem`
- [ ] `pip install askgem && askgem` works on a clean Python 3.10+ environment
- [ ] Version string consistent across `pyproject.toml`, `__init__.py`, and git tag

### 4.1 Session exit summary

Small but polished: on `exit`/`quit`, show a brief panel with session stats.

```
┌─────────────────────────────┐
│       Session Summary       │
│  Messages:      12          │
│  Tool calls:     7          │
│  Files modified: 3          │
└─────────────────────────────┘
```

Requires tracking `session_messages`, `session_tools`, `modified_files_count` in
`ChatAgent` — straightforward counters incremented in the dispatch loop.

**Files:** `agent/chat.py`

---

## 5. Post-1.0 — Web & Metrics

**Priority:** 🟡 Medium. Valuable but not blocking 1.0.
**Target:** Q3 2026

### 5.1 `web_search` tool (Google Custom Search API)

Integrate the [Google Custom Search JSON API](https://developers.google.com/custom-search/v1/overview)
as a registered tool. Returns top 5 results: title, URL, snippet.

- Config: `google_search_api_key` + `google_cx_id` in `settings.json`
- HTTP via `urllib.request` — zero new dependencies
- Setup wizard on first use if keys are missing
- 100 free queries/day on the free tier

### 5.2 `web_fetch` tool

Download a URL and extract readable text content.

- `urllib.request.urlopen` with 10s timeout
- Lightweight HTML tag stripping (no `beautifulsoup4` dependency)
- Output capped at 4,000 characters with truncation notice
- Supports `text/html`, `text/plain`, `application/json`

### 5.3 Token usage tracking (`/usage` command)

Extract `usage_metadata` from each Gemini response chunk and maintain session totals.

```
/usage
  Input tokens:   4,821
  Output tokens:  1,203
  Estimated cost: $0.003 (gemini-2.0-flash)
```

- `core/metrics.py` — `TokenTracker` class
- Cost estimates based on published Gemini pricing, configurable per model
- Shown automatically on session exit summary

---

## 6. Long-term — LSP & Plugins

**Priority:** 🔵 Research / Future. High complexity, low urgency.
**Target:** 2027

### 6.1 LSP diagnostics bridge

Spawn a language server subprocess (e.g., `pyright-langserver --stdio`) and expose
a `get_diagnostics(file_path)` tool that returns syntax and type errors before an
edit is applied.

```
get_diagnostics("src/auth.py")
→ [{line: 42, message: "Cannot find name 'jwt'", severity: "error"}]
```

The agent can use diagnostics to self-correct instead of applying broken code and
looping on errors.

- JSON-RPC over stdio — no external dependencies
- Read-only (diagnostics only, no completions or refactoring)
- 5s hard timeout per request
- Graceful fallback if no language server installed

### 6.2 Plugin system

Allow community-contributed tools without modifying core code.

- Plugin discovery from `~/.askgem/plugins/`
- Each plugin: a Python file with `register(agent)` that calls
  `agent.register_tool(func)`
- `plugin.json` manifest per plugin
- Bundled first-party plugin: git integration (`git_status`, `git_diff`, `git_log`,
  `git_commit`)

---

## 7. Non-goals

Explicitly out of scope for this project:

| Feature | Reason |
|---|---|
| Multi-agent orchestration | Requires IPC + process management infrastructure beyond solo maintainer scope |
| Voice input/output | Hardware-dependent, out of terminal-first scope |
| GUI / Electron wrapper | askgem is a terminal tool by design |
| OpenAI / Anthropic model support | Would fragment the SDK layer; askgem is purpose-built for Gemini |
| Jupyter notebook editing | `.ipynb` JSON structure is complex and error-prone for find-and-replace |
| Real-time collaboration | Requires a server component — out of scope for a CLI tool |
| MCP server hosting | Acting as an MCP server requires persistent TCP + auth beyond current scope |

---

## 8. Release timeline

```
2026-04   v0.8.0  ████████████████  current — pre-release, rebrand complete
2026-05   v0.9.0  ░░░░░░░░░░░░      write_file, /undo, context overflow guard, CI
2026-06   v0.9.5  ░░░░░░░░          grep_search, glob_find, diff_file
2026-07   v1.0.0  ░░░░░░            stable — full docs, 70%+ coverage, PyPI current
2026-Q3   v1.1.0  ░░░░              web_search, web_fetch
2026-Q3   v1.2.0  ░░░               /usage, token tracking, session exit summary
2027      v2.0.0  ░░                LSP diagnostics, plugin system
```

> This timeline assumes a solo maintainer working part-time.
> Dates shift based on real usage feedback after v1.0.0.

---

*This is a living document — updated as milestones complete or priorities change.*
