# Changelog

All notable changes to askgem are documented here.
Follows [Semantic Versioning](https://semver.org/) and [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## [0.10.0] — 2026-04-14

### Added
- **Manager-Based Architecture:** Refactored the monolithic `ChatAgent` into specialized managers: `SessionManager`, `ContextManager`, `StreamProcessor`, and `CommandHandler`.
- **Push-Layout TUI Dashboard:** Completely redesigned Textual dashboard optimized for Windows performance. Features a sidebar for real-time stats and a hidden debug output pane.
- **Centralized Security Layer:** New `core/security.py` featuring automated risk analysis for shell commands and standardized CWD path enforcement.
- **Deterministic Testing:** Introduced `SimulationManager` allowing recording and replaying of agent turns for 100% reliable CI/CD verification.
- **Automated CD Pipeline:** Added GitHub Actions workflow for automated package builds and releases on version tags.
- **Reliable Test Suite:** Implemented 39+ unit and integration tests covering cognitive managers and security logic.

### Changed
- **English-Standardized Core:** Standardized all system instructions and internal logic strings to English to improve global model reliability and tool-calling consistency.
- **Proactive Context Summarization:** Improved context window management via automated thread compression.

### Fixed
- Resolved multiple TUI stability issues on Windows 10/11 including malformed Rich markup errors.
- Fixed session restoration logic to be compatible with modular managers.

---

## [0.9.0] — 2026-04-06
