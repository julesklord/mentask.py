# askgem — Development Roadmap

> **Last Updated:** April 16, 2026
> **Current Version:** `0.13.3` ("hotfix")
> **Maintainer:** [@julesklord](https://github.com/julesklord)
> **Status:** Full Stability Reached

This document outlines the comprehensive engineering roadmap for `askgem`, organized into prioritized milestones. With the release of v0.13.2, we have achieved the goal of a bulletproof, multimodal autonomous core.

---

## Current State Assessment

### What askgem v0.13.2 Can Do Today

| Capability | Status | Description |
| :--- | :--- | :--- |
| **Multimodal Reasoning** | ✅ Shipped | Processes images, audio, and video via base64 encoding. |
| **Hierarchical Hub** | ✅ Shipped | Context management across Standard, Global, and Local scopes. |
| **Autonomous Orchestration** | ✅ Shipped | Advanced Think -> Act -> Observe loop with 429 retry logic. |
| **TrustManager Security** | ✅ Shipped | Recursive directory validation and Path Traversal prevention. |
| **Web Research** | ✅ Shipped | Live internet search (Google/DDG) and content extraction. |
| **Full Validation** | ✅ Shipped | 129 unit/integration tests ensuring 100% stability on Windows. |
| **Unified Pydantic Core** | ✅ Shipped | Type-safe communication between managers and tools. |
| **TUI Dashboard** | ✅ Shipped | Premium Textual-based interface with real-time analytics. |

### Architecture Diagram

```mermaid
graph TD
    A[main.py CLI Entry] --> B[AgentOrchestrator]
    B --> C[SessionManager]
    B --> D[ContextManager]
    B --> E[ToolRegistry]
    E --> F[FileTools]
    E --> G[SystemTools]
    E --> H[WebTools]
    C --> I[MemoryManager]
    C --> J[TokenTracker]
```

---

## Milestone 1: Visual Identity and Stability (COMPLETED)
- [x] API Error Retry with Exponential Backoff
- [x] Dedicated `write_file` Tool
- [x] `/undo` Command (Restores `.bkp` snapshots)
- [x] Graceful Truncation of Oversized Context

## Milestone 2: Code Search Navigation (COMPLETED)
- [x] `grep_search` Tool (Pattern matching)
- [x] `glob_find` Tool (File discovery)
- [x] `diff_file` Tool (Unified diff previews)

## Milestone 3: Web Research Integration (COMPLETED)
- [x] `web_search` Tool (Google Search API integration)
- [x] `web_fetch` Tool (Markdown-friendly content extraction)

## Milestone 4: Architectural Sovereignty (COMPLETED)
- [x] Transition from Monolith to Specialized Managers
- [x] Pydantic integration for Agentturn schemas
- [x] Hierarchical Knowledge Hub (Standard/Global/Local)

---

## Milestone 5: Language Intelligence ("Bene Gesserit")

**Priority:** 🔴 High
**Estimated Effort:** Q2 2026
**Theme:** Transition from blind code editing to language-aware engineering.

### 5.1 LSP Client Bridge
- **Goal:** Implement a light-weight LSP client to verify syntax and imports before applying edits.
- [ ] Integration with `pyright` and `tsserver` via JSON-RPC.
- [ ] Automated Lint-Fix Loop (Agent detects diagnostic and self-corrects).

### 5.2 Context Optimization
- **Goal:** Intelligent pruning of context window based on relevance rather than age.
- [ ] Semantic Truncation (Keep relevant imports and function signatures).

---

## Technical Debt & Maintenance

| Item | Priority | Status |
| :--- | :--- | :--- |
| **Translation Parity** | High | ✅ Solved in v0.13.2 (8 locales synchronized). |
| **Test Coverage** | Medium | ✅ 129 tests reaching critical modules. |
| **Type Hinting** | Low | Partially complete; Move towards `mypy --strict`. |

---

## Version Release Timeline

```text
2026-04-14  v0.10.0  ████      The Modular Jump
2026-04-15  v0.13.0  ████████  Muad'Dib: Pydantic Core
2026-04-16  v0.13.3  ████████  hotfix (CURRENT)
2026-05     v0.14.0  ░░░       Bene Gesserit: Optimization & LSP
```

---
*The spice must flow, but the code must be stable.* 🛡️✨📡🧪
