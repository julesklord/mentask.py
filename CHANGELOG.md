# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.13.3] — 2026-04-16 ("Purity")


- **Multimodal Orchestration:** Native support for base64 media processing (images, audio, video) within the unified agentic loop.
- **Formal Security Protocol:** New `SECURITY.md` defining TrustManager boundaries, native `keyring` secret management, and human-in-the-loop safeguards.
- **Cognitive Resilience:** Integrated 129 comprehensive tests (100% functional coverage) validating every manager and tool interaction.

- **Async Unification:** Liquidated legacy `StreamProcessor` in favor of a optimized `AgentOrchestrator` using Google GenAI `AsyncClient`.
- **Linguistic Parity:** Synchronized 8 language locales (EN, ES, JA, DE, FR, IT, PT, ZH) to full feature parity.


- **AttributeError (SessionManager):** Patched usage metrics access during context compaction.
- **Mock Stability:** Aligned test mocks with v1beta asynchronous generator signatures.
- **Linter Cleanup:** Zero warnings policy reached; removed multiple unused variables and malformed absolute imports.

## [0.13.0] — 2026-04-15 ("Muad'Dib")

- **Hierarchical Knowledge Hub:** Three-tier instruction system: Standard (Core), Global (User Profile), and Local (Project Specific).
- **Pydantic Infrastructure:** Full migration of internal data handling to validated Pydantic models for absolute type safety.
- **Smart Compaction:** Automated context window summarization to preserve long-term coherence while optimizing token consumption.

## [0.12.0] — 2026-04-14 ("Bene Gesserit")

- **TrustManager:** Security architecture for recursive directory validation and path-traversal prevention.
- **SafeMode Terminal:** Proactive scanning of shell commands for destructive patterns before manual execution.

## [0.10.x] — 2026-04-14 ("The Modular Jump")

- **Manager-Based Architecture:** Massive refactor of the monolithic `ChatAgent` into specialized components: `SessionManager`, `ContextManager`, and `CommandHandler`.
- **Premium TUI Dashboard:** Redesigned Textual-based interface with real-time analytics sidebar and debug persistence.

- **English-Standard Intelligence:** Migrated all internal logic and system prompts to English to improve global model reasoning accuracy.

## [0.5.0 - 0.9.x] — 2025 Tardío - 2026 Temprano ("Expansion Era")

- **Advanced Web Intelligence:** Integration of Google Search and DuckDuckGo for live data retrieval and documentation analysis.
- **Tooling Overhaul:** Implementation of `grep_search`, `glob_find`, and `diff_file` for expert-level codebase navigation.
- **Budgetary Console:** First iteration of the token tracking engine with historical cost estimation.
- **Exponential Backoff:** Automated retry logic (Adaptive Resilience) for 429 API Error handling.

- Windows-specific character encoding bugs in the TUI terminal.
- Multiple concurrency issues in the early async generator loop.

## [0.1.0 - 0.4.x] — 2025-05-13 ("Genesis Era")

- **Initial Public Alpha:** Released as `PyGemAi` on PyPI, offering basic Gemini 1.0/1.5 chat capabilities.
- **CLI Foundations:** First terminal interface with Markdown rendering and basic session persistence.
- **CI/CD Genesis:** Setup of initial GitHub Actions for automated linting and release cycles.

- **Rebranding:** Migration from `PyGemAi` to `AskGem` to reflect the shift from a simple API wrapper to an autonomous engineering agent.

---
*Since May 13th, 2025 — The spice must flow, but the code must be stable.* 🛡️✨📡🧪🦾🪱
