# Usage

Launch `askgem` simply via standard terminal hook in the root:

```bash
askgem
```

## Common Workflows

**1. Workspace Initialization [v0.11.0]**
When you launch AskGem in a folder for the first time, it checks for a `.askgem/` directory.
- If not found, it asks: *"Initialize Workspace in CWD?"*
- Selecting **Yes** creates a local isolation layer for history, memory, and project-specific blueprints.

**2. Trusting External Directories [v0.11.0]**
If you need the agent to read or write files outside your current project.
> *User: `/trust G:/COMMON_LIBS`*
> AskGem adds this path to the permanent whitelist, allowing cross-drive or cross-folder operations that were previously blocked by the security guards.

**3. Hyper-Context Analysis**
AskGem performs a **Project Blueprint** scan on startup.
> *User: "Analyze my project and find security flaws."*
> You don't need to specify the files; the agent already knows the project structure and stack from the initial scan.

## Interactive Slash Commands

| Command | Action |
|---------|--------|
| `/help` | Complete mapping dump. |
| `/model <name>` | Swap live configuration mid-stream context. |
| `/mode [auto/manual]` | Enable or disable the destructive confirmation guardrails. |
| `/trust [path]` | **[v0.11.0]** Authorize a specific directory for file operations. |
| `/untrust [path]` | **[v0.11.0]** Revoke authorization for a directory. |
| `/clear` | Wipe memory window but retain configuration identity. |
| `/usage` | Detailed token consumption and cost report. |
| `/stats` | Session performance summary (messages, tools, files). |
| `/stop` | Interrupts generative streaming. |
| `/history` | Enter sub-command contexts (`list`, `load`, `delete`). |
| `exit` / `q` | Soft terminal exit (history auto-saves). |

## Edge Cases and Known Limitations

1. **Cross-Drive Blocks:** Without an explicit `/trust` command, AskGem will fail with a `SecurityError` when attempting to access files on a different drive letter (Windows).
2. **Keyring Access:** On some Linux distros without a D-Bus secret service, AskGem will fall back to `~/.askgem/settings.json` for key storage.
3. **Context Explosion:** Even with proactive summarization, massive file reads (e.g., >50 files) in a single turn may approach the Gemini context window limits.
