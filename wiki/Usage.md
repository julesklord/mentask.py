# Usage

Launch `askgem` simply via standard terminal hook in the root:

```bash
askgem
```

## Common Workflows

**1. Context Switch**
Ask the agent to analyze multiple project files simultaneously.
> *User: Read my pyproject.toml and my tox.ini.*
> AskGem dynamically executes `read_file` loops on both paths and feeds the output payloads back to the generative engine before replying with an aggregated summary.

**2. Auto-Refactoring**
Change modes using the built-in command parameters prior to execution.
> *User: `/mode auto`*
> *User: Edit my settings template to match standard OAuth2 defaults.*
> AskGem processes text without demanding `(Y/n)` confirmations.

**3. State Interruption [v0.10.0]**
Interrupt an ongoing model generation if the path diverges.
> *User: `/stop`*
> The `StreamProcessor` halts the active async generator immediately.

## Interactive Slash Commands

| Command | Action |
|---------|--------|
| `/help` | Complete mapping dump. |
| `/model` | Poll Google endpoints for standard access mappings. |
| `/model <name>` | Swap live configuration mid-stream context. |
| `/mode [auto/manual]` | Enable or disable the destructive confirmation guardrails. |
| `/clear` | Wipe memory window but retain configuration identity. |
| `/usage` | **[v0.10.0]** Detailed token consumption and cost report. |
| `/stats` | **[v0.10.0]** Session performance summary (messages, tools, files). |
| `/stop` | **[v0.10.0]** Interrupts generative streaming. |
| `/history` | Enter sub-command contexts (`list`, `load`, `delete`). |
| `exit` / `q` | Soft terminal exit. |

## Edge Cases and Known Limitations

1. **Block Replacement Failures:** `edit_file` requires **exact** syntax string matching string blocks. A single divergent space character results in an `Error` exception block rejecting the replace payload.
2. **Binary Unreadability:** The tools only scan standard encoding inputs. Loading binaries crashes tools returning `UnicodeDecodeError` blocks.
3. **Command Deadlocks:** Interactive executing CLI calls (`vim`, `nano`, `python` REPL loops) within `execute_bash` will infinite process lock until the 60-second timeout forces a kill-signal dump. Risk mitigated by version 0.10.0 risk analysis.
