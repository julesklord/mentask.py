# GEMINI.md - mentask Project Instructions

You are an expert Python engineer working on `mentask`, a self-evolving autonomous AI coding agent.

## Project Overview

`mentask` is a terminal-based AI orchestrator that automates engineering tasks. It doesn't just suggest code; it executes it, validates it, and self-corrects.

- **Autonomy:** Level 4 (Autonomous Forge Engine for dynamic tool building).
- **Features:** Neon Contextual System (Coding, Music, Analysis, Creative).
- **Architecture:** 3-tier decoupled engine (CLI/UI, Agent, Core State).
- **Primary Tech:** Python 3.10+, `google-genai`, `rich`, `keyring`, `pydantic`, `mcp`, `uv`.
- **Security:** Zero-trust path validation via `TrustManager`.

## Core Mandates

- **Security:** All file/system operations **must** use tools in `src/mentask/tools/` and validate paths through `TrustManager` (`src/mentask/core/trust_manager.py`).
- **Imports:** Always use absolute imports from `src/mentask/`.
- **Extensibility:** Use `forge_plugin` for repetitive or highly specific tasks to extend the agent's capabilities dynamically.
- **Hygiene:** Follow the standards defined in `STANDARD.md`. No throwaway scripts in root.

## Development Workflows

### Environment Setup
- **Recommended:** `uv sync --all-extras --dev`
- **Standard:** `pip install -e ".[dev]"`

### Building and Running
- **Launch CLI:** `python run.py` or `uv run python run.py`
- **Session Management:** `mentask <session_id>` to resume.

### Testing and Validation
- **Run all tests:** `uv run pytest` or `tox`
- **CLI specific:** `uv run pytest tests/cli -q`
- **Orchestration/LSP:** `uv run pytest tests/test_orchestrator.py tests/test_lsp_integration.py -q`
- **Linter Integration:** The agent integrates with Ruff LSP to intercept and fix diagnostics (`E999`, `F821`).

### Code Quality
- **Lint:** `uv run ruff check .`
- **Format:** `uv run ruff format .`
- **CI Sequence:** Lint → Format Check → Test.

## Key Architecture References

- **The Heart:** `src/mentask/agent/orchestrator.py` (Thinking -> Action -> Observation loop).
- **The Guard:** `src/mentask/core/trust_manager.py` (Zero-trust whitelist security).
- **The Snap:** `src/mentask/agent/core/context.py` (Context snapping/compression at 80% buffer).
- **The Evolver:** `src/mentask/core/plugin_loader.py` (Runtime tool injection).
- **The Registry:** `src/mentask/agent/tools_registry.py` (Tool dispatch).

## Documentation Hierarchy

1. `README.md`: High-level overview and installation.
2. `STANDARD.md`: Repository hygiene and architecture boundaries.
3. `DESIGN.md`: Core components and philosophy.
4. `AGENTS.md`: Development commands and constraints.
5. `SECURITY.md`: Security policy and vulnerability reporting.
6. `wiki/`: Detailed technical documentation.

When implementing changes, always update the relevant tests and ensure documentation remains aligned with the new behavior.
