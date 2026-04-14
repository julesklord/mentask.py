# API / Module Reference

This section details the primary software contracts within AskGem, including the core managers introduced in **v0.10.0**.

## `src/askgem/agent/`

### **Class `ChatAgent`** (`chat.py`)

The primary orchestrator coordinating manager logic and high-level conversational state.

* **Method `setup_api`**: Determines active API mapping paths. Proxy for `SessionManager`.
* **Method `_stream_response`**: Manages recursive tool-calling loops using the `StreamProcessor`.
* **Method `start`**: Classic CLI prompt loop entry point.

### **Cognitive Managers** (`agent/core/`) [v0.10.0]

#### **Class `SessionManager`** (`session.py`)

Handles GenAI client lifecycle and auth persistence.
* **`ensure_session(config)`**: Lazy-loads the chat session with specific generative configurations.
* **`handle_retryable_error(e, attempt, ...)`**: Standardized exponential backoff implementation.

#### **Class `ContextManager`** (`context.py`)

Semantic state assembly.
* **`build_system_instruction()`**: Combines OS, Persistent Memory, and Mission metadata.
* **`summarize_if_needed(...)`**: Triggers proactive context compression logic.

#### **Class `StreamProcessor`** (`stream.py`)

Low-level SDK parsing.
* **`process_async_stream(...)`**: Consumes generators, extracts tool calls, and updates metrics.

#### **Class `CommandHandler`** (`commands.py`)

Interface for mid-conversation slash commands (`/model`, `/mode`, `/usage`).

#### **Class `SimulationManager`** (`simulation.py`)

Deterministic engine for replaying (`playback`) or capturing (`record`) API turns.

## `src/askgem/core/`

### **Module `security.py`** [v0.10.0 Hardened]

* **`analyze_command_safety(command)`**: Runs risk analysis returning a `SafetyReport` with categorized levels (`SAFE`, `NOTICE`, `WARNING`, `DANGEROUS`).
* **`ensure_safe_path(path)`**: Validates path boundaries against the current working directory.

### **Module `paths.py`**

* **`get_config_dir`**: Computes `~/.askgem` root resolution reliably tracking OS environments.
* **`get_config_path(filename)`**: Safe join paths.
* **`get_history_dir`**: History routing target paths.

### **Class `ConfigManager`**

* **Method `save_settings`**, **`load_settings`**: Manage dynamic state blocks serialized to `settings.json`.
* **Method `save_api_key`**: Disk flush logic using system keyring integrations.

### **Class `HistoryManager`**

* **Method `save_session(history_list)`**: Serializes SDK content parts to persistent JSON storage.
* **Method `load_session(session_id)`**: Loads and truncates windows against `MAX_CONTEXT_WINDOW`.

### **Class `TokenTracker`** (`metrics.py`) [v0.10.0]

* **`add_usage(prompt, completion)`**: Real-time counter updates.
* **`calculate_cost()`**: Model-specific USD estimation logic.

## `src/askgem/tools/`

**Function `read_file(path, start_line, end_line)`**
Extracts context data locally. Bound dynamically. Capped at 30k characters.

**Function `edit_file(path, find_text, replace_text)`**
Targets explicit blocks with atomic write guarantees and `.bkp` references.

**Function `execute_bash(command)`**
Asynchronous terminal execution gated by `security.py` risk analysis. 60s timeout.
