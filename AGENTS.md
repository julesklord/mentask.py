# AI Agent Instructions for askgem

This document guides AI coding agents to be immediately productive in the **askgem** codebase.

---

## Quick Start

**What is askgem?**  
A professional, autonomous coding agent for the terminal. Powered by Google Gemini, it reads files, edits code, runs commands, and navigates filesystems within an interactive session with hardened security guardrails.

**Current version:** `0.13.4` (Active stabilization)  
**Python support:** 3.10+ (validated 3.10–3.13 via tox)  
**Key stack:** Pydantic, Rich, google-genai, keyring, pytest

---

## Repository Structure

Follow [STANDARD.md](STANDARD.md) for the canonical reference. Key rules:

- `src/` → Product code only
- `tests/` → Unit & integration tests only (no experimental probes)
- `scratch/` → Temporary diagnostics and disposable experiments
- `root/` → Packaging, policy, and core docs only

**Do not:** Create scripts in root or stale UI claims in docs.

---

## Architecture & Design Patterns

**Layers:**
1. **Presentation (CLI)** — `src/askgem/cli/`
   - `main.py`: Session entry point
   - `renderer.py`: Rich-based terminal UI

2. **Orchestration** — `src/askgem/agent/orchestrator.py`
   - Central *Thinking → Action → Observation* loop
   - Delegates to specialized managers

3. **Cognitive Managers** — `src/askgem/agent/core/`
   - `session.py`: API lifecycle, backoff logic, simulation injection
   - `context.py`: Project blueprint scanning, system prompt assembly
   - `stream.py`: Tool extraction, metrics tracking

4. **State & Safety** — `src/askgem/core/`
   - `identity_manager.py`: Hierarchical Knowledge Hub (Standard → Global → Local)
   - `trust_manager.py`: Directory whitelist validation
   - `security.py`: Real-time path traversal and risk analysis
   - `paths.py`: Package internals, `.askgem/` local config, `~/.askgem` global

**Key design rules:**
- Orchestration logic decomposed into small helpers (not one giant method)
- Dependencies composed explicitly (see `ChatAgentDependencies`)
- UI, orchestration, session, and tools remain distinct layers
- Behavioral rules are modular markdown files in the Knowledge Hub (not hardcoded)

See [wiki/Architecture.md](wiki/Architecture.md) for detailed diagrams and flow.

---

## Development Commands

### Testing

```bash
# Run full test suite across Python 3.10–3.13
tox

# CLI contract tests only
pytest tests/cli -q

# Core orchestration & LSP integration
pytest tests/test_orchestrator.py tests/test_lsp_integration.py -q

# Targeted agent tests for a changed surface
pytest tests/agent/test_chat_agent.py -v
```

### Code Quality

```bash
# Ruff lint (replaces flake8, black, isort)
ruff check src/ tests/

# Format (if needed)
ruff format src/ tests/
```

### Running Locally

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the CLI
askgem
```

---

## Common Patterns & Conventions

### Testing Standard

- **CLI entrypoints** have contract tests (see `tests/cli/test_cli_main.py`)
- **Orchestration flows** have focused unit tests (see `tests/test_orchestrator.py`)
- **External integrations** are isolated from unit tests; use mocking where practical
- **CI prefers deterministic/mocked tests** for reliability
- **No heavyweight external process boots** in unit tests unless explicitly integration tests
- **When behavior changes:** Update tests *immediately* instead of tolerating stale coverage

### Module Organization

- Use Pydantic models for all internal communication (type safety)
- Import from `src/askgem/` not relative paths (clarity and testability)
- Manager classes should handle construction of dependencies, not just logic
- Use `async/await` for I/O-bound operations (Gemini API, file reads, etc.)

### File Operations

- Use dedicated tools from `src/askgem/tools/` (e.g., `FileTools`, `SystemTools`)
- Always validate paths through `TrustManager` before operations
- Catch and surface security violations clearly to the user
- Log file operations in history via `HistoryManager`

### Error Handling

- Exponential backoff for API rate limits (429) is built into `SessionManager`
- Surface user-facing errors in Rich-formatted console output
- Log internal state changes to diagnostic files in `.askgem/`

---

## Roadmap & Known Gaps

Current stabilization focus (v0.13.4):
- ✅ Multimodal reasoning (images, audio, video)
- ✅ Hierarchical Knowledge Hub
- ✅ TrustManager security layer
- ✅ Full test coverage across unit/integration
- 🔄 Language-aware code editing (in progress)

See [ROADMAP.md](ROADMAP.md) for detailed timeline.

---

## Git & Release Hygiene

- Semantic versioning in `pyproject.toml`
- CHANGELOG reflects actual runtime behavior
- Default branch is clean; long-lived branches have documented reasons
- `.gitignore` blocks local artifacts, environments, caches, backups

See [STANDARD.md](STANDARD.md) sections 2 & 3 for full expectations.

---

## Security & Trust Model

- **TrustManager** maintains a whitelist of authorized directories
- **SecurityCheck** validates paths before file operations
- All external API calls (Gemini) pass through `SessionManager` with retry logic
- Sensitive credentials stored via `keyring` (not in plaintext)

See [SECURITY.md](SECURITY.md) for detailed threat model.

---

## Documentation

- `README.md` → Current behavior, not historical
- `wiki/` → Detailed technical reference (Architecture, API, Dependencies, etc.)
- `STANDARD.md` → Canonical conventions and standards
- `ROADMAP.md` → Prioritized milestones and feature status
- `.github/` + `.gitignore` + `LICENSE` → Governance

**Link to existing docs instead of duplicating.**

---

## When to Ask for Clarification

- Unclear architectural layer for a change
- Whether a feature belongs in Core, Tools, or CLI
- If a test needs to mock external services or stay deterministic
- Whether security implications need TrustManager review
- If documentation needs updating after behavior changes

---

## Key Contacts & References

- **Maintainer:** [@julesklord](https://github.com/julesklord)
- **Issue tracking:** GitHub Issues
- **Main repository:** [github.com/julesklord/askgem.py](https://github.com/julesklord/askgem.py)
- **Type checking:** Pydantic v2
- **API provider:** Google Gemini (google-genai ≥0.2.0)
