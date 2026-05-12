import asyncio
import json
import logging
import re
import shlex
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from ....core.compression import ContextCompressor
from ...schema import Message, Role, ToolCall, UsageMetrics
from .base import BaseProvider

_logger = logging.getLogger("mentask")

# Patterns to ignore in stderr (repetitive system warnings)
_IGNORED_STDERR_PATTERNS = [
    r"Windows 10 detected",
    r"Windows 11 is recommended",
    r"Ripgrep is not available",
    r"Falling back to GrepTool",
    r"True color \(24-bit\) support not detected",
    r"DEP0190",  # Node.js deprecation warning for shell option
    r"Use `node --trace-deprecation",
]


# Alias map: user-facing shorthand → list of candidate binary names (in priority order)
_CLI_ALIAS_MAP: dict[str, list[str]] = {
    "gemini": ["gemini", "gemini-cli"],
    "gemini-cli": ["gemini-cli", "gemini"],
    "codex": ["codex"],
    "opencode": ["opencode"],
    "claude": ["claude"],
    "aider": ["aider"],
}


def _resolve_binary(name: str) -> str | None:
    """Resolves a CLI alias or binary name to its full path. Returns None if not found."""
    import shutil

    candidates = _CLI_ALIAS_MAP.get(name.lower(), [name])
    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return path
    return None


class CLIProvider(BaseProvider):
    """
    Provider that bridges MentAsk to external CLI agents (e.g., gemini-cli, codex).
    It translates history and tools into a text prompt, runs the binary, and parses stdout.
    """

    def __init__(self, model_name: str, config: Any):
        # Strip 'cli:' prefix if present
        pure_cmd = model_name.removeprefix("cli:")
        super().__init__(pure_cmd, config)
        # cli_command is the user-facing alias or a full template string
        self.cli_command = pure_cmd
        # Resolved binary path (set in setup())
        self._binary_path: str | None = None
        # Display name for renderer
        self.display_name = pure_cmd

    async def setup(self) -> bool:
        # If the command is a template string (contains spaces or {prompt}), extract the binary
        try:
            first_token = shlex.split(self.cli_command)[0]
        except Exception:
            first_token = self.cli_command

        resolved = _resolve_binary(first_token)
        if resolved is None:
            _logger.error(
                f"CLI binary '{first_token}' not found in PATH. "
                f"Tried aliases: {_CLI_ALIAS_MAP.get(first_token.lower(), [first_token])}"
            )
            return False

        self._binary_path = resolved
        _logger.info(f"CLI Bridge: resolved '{first_token}' → '{resolved}'")
        return True

    def _build_prompt(self, history: list[Message], tools_schema: list[dict[str, Any]], system_instruction: str) -> str:
        prompt_parts = []

        # 1. System Instruction & Tool Schema
        # We use a very prominent format to ensure the "Brain" CLI sees it
        prompt_parts.append("### MENTASK CORE PROTOCOL")
        prompt_parts.append(f"MISSION: {system_instruction}")

        if tools_schema:
            prompt_parts.append("\n### TOOLBOX")
            prompt_parts.append("You are the BRAIN of an autonomous agent. MentAsk is your BODY.")
            prompt_parts.append("To execute an action, you MUST output a JSON block in your response. ")
            prompt_parts.append("FORMAT:")
            prompt_parts.append(
                '```json\n{\n  "mentask_tool_call": {\n    "name": "tool_name",\n    "arguments": {"arg": "val"}\n  }\n}\n```'
            )

            prompt_parts.append("\nAVAILABLE TOOLS (JSON Schema):")
            for tool in tools_schema:
                # Keep it compact to save CLI args space
                minimal_tool = {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                }
                prompt_parts.append(f"- {tool['name']}: {json.dumps(minimal_tool)}")

        prompt_parts.append("\n### CONVERSATION LOG")

        # Only send last 10 messages to avoid shell arg limits
        for msg in history[-10:]:
            if msg.role == Role.SYSTEM:
                continue

            role = "USER" if msg.role in (Role.USER, Role.TOOL) else "AGENT"
            content = ContextCompressor.smart_compress(str(msg.content))

            if msg.role == Role.TOOL:
                tool_name = msg.metadata.get("tool_name", "unknown")
                prompt_parts.append(f"[{role} - {tool_name} RESULT]: {content}")
            else:
                prompt_parts.append(f"[{role}]: {content}")

        prompt_parts.append("\n### YOUR RESPONSE (AGENT):")
        return "\n".join(prompt_parts)

    def _build_cli_args(self, full_prompt: str) -> tuple[list[str], bool]:
        """
        Builds the argv list for the subprocess.
        Returns a tuple of (args, uses_stdin).
        """
        binary = self._binary_path or self.cli_command
        binary_name = Path(binary).stem.lower()

        # Non-interactive / pipe-friendly flags per known CLI tool
        _NON_INTERACTIVE_FLAGS: dict[str, list[str]] = {
            "gemini": ["-p", "-"],  # gemini -p - (read from stdin)
            "gemini-cli": ["-p", "-"],
            "codex": ["--full-auto", "-q"],  # codex --full-auto -q
            "opencode": ["run"],
            "claude": ["-p"],
            "aider": ["--message"],
        }

        if "{prompt}" in self.cli_command:
            # User-defined template: replace {prompt} and split
            cmd_str = self.cli_command.replace("{prompt}", full_prompt)
            parts = shlex.split(cmd_str)
            parts[0] = binary
            return parts, False

        flags = _NON_INTERACTIVE_FLAGS.get(binary_name, [])

        # Heuristic: if flags include a way to read from stdin, or if prompt is large
        # We prefer stdin for gemini specifically as we know it supports it via '-p -'
        if binary_name in ("gemini", "gemini-cli"):
            return [binary, *flags], True

        return [binary, *flags, full_prompt], False

    async def generate_stream(
        self,
        history: list[Message],
        tools_schema: list[dict[str, Any]],
        config: Any | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:

        system_instruction = config.get("system_instruction", "") if config else ""
        full_prompt = self._build_prompt(history, tools_schema, system_instruction)
        args, use_stdin = self._build_cli_args(full_prompt)

        _logger.debug(f"Invoking CLI Bridge: {args[0]} (prompt len: {len(full_prompt)}, stdin: {use_stdin})")

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE if use_stdin else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            if use_stdin and process.stdin:
                process.stdin.write(full_prompt.encode("utf-8"))
                await process.stdin.drain()
                process.stdin.close()

            if process.stdout is None or process.stderr is None:
                raise RuntimeError("Failed to open process pipes")

            json_buffer = ""
            in_json_block = False

            async def read_stream(stream, is_stderr=False):
                nonlocal in_json_block, json_buffer
                while True:
                    line_bytes = await stream.readline()
                    if not line_bytes:
                        break

                    try:
                        line = line_bytes.decode("utf-8", errors="replace")
                    except Exception:
                        line = str(line_bytes)

                    if is_stderr:
                        # Filter out ignored patterns
                        if any(re.search(p, line) for p in _IGNORED_STDERR_PATTERNS):
                            continue

                        # Yield stderr as text but only if it looks like an error or a useful warning
                        if line.strip():
                            yield {"type": "text", "content": f"[stderr] {line}"}
                        continue

                    # Logic to detect JSON blocks even if mixed with text
                    if "```json" in line:
                        in_json_block = True
                        json_buffer = ""
                        pre = line.split("```json")[0]
                        if pre.strip():
                            yield {"type": "text", "content": pre}
                        continue

                    if in_json_block:
                        if "```" in line:
                            in_json_block = False
                            post = line.split("```")[1]
                            try:
                                clean_json = json_buffer.strip()
                                parsed = json.loads(clean_json)
                                if "mentask_tool_call" in parsed:
                                    tc_data = parsed["mentask_tool_call"]
                                    yield {
                                        "type": "tool_call",
                                        "content": ToolCall(
                                            id=str(uuid.uuid4()),
                                            name=tc_data.get("name", ""),
                                            arguments=tc_data.get("arguments", {}),
                                        ),
                                    }
                                else:
                                    yield {"type": "text", "content": "```json\n" + json_buffer + "\n```"}
                            except Exception:
                                yield {"type": "text", "content": "```json\n" + json_buffer + "\n```"}

                            if post.strip():
                                yield {"type": "text", "content": post}
                        else:
                            json_buffer += line
                    else:
                        yield {"type": "text", "content": line}

            async def stream_merger():
                queue = asyncio.Queue()

                async def producer(generator):
                    try:
                        async for item in generator:
                            await queue.put(item)
                    except Exception as e:
                        _logger.error(f"Producer error: {e}")

                tasks = [
                    asyncio.create_task(producer(read_stream(process.stdout, is_stderr=False))),
                    asyncio.create_task(producer(read_stream(process.stderr, is_stderr=True))),
                ]

                while True:
                    if all(t.done() for t in tasks) and queue.empty():
                        break

                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=0.05)
                        yield item
                    except asyncio.TimeoutError:
                        continue

            async def stream_merger_wrapper():
                async for event in stream_merger():
                    yield event

            async for event in stream_merger_wrapper():
                yield event

            await process.wait()

            if process.returncode != 0:
                _logger.warning(f"CLI Bridge process exited with code {process.returncode}")

            # Flush json_buffer if we died mid-block
            if in_json_block and json_buffer:
                yield {"type": "text", "content": "```json\n" + json_buffer + "\n```"}

            # Emit dummy metrics
            yield {"type": "metrics", "content": UsageMetrics(input_tokens=len(full_prompt) // 4, output_tokens=0)}

        except Exception as e:
            _logger.error(f"CLI Bridge failure ({self.cli_command}): {e}")
            yield {"type": "error", "content": f"CLI Bridge Error: {e}"}

    async def list_models(self) -> list[str]:
        # Return the resolved binary path if available, else the original command
        name = self._binary_path or self.cli_command
        return [name]

    async def check_health(self, model_name: str) -> tuple[bool, str | None]:
        # model_name here is the user alias, not necessarily a binary name
        alias = model_name.removeprefix("cli:")
        try:
            first_token = shlex.split(alias)[0]
        except Exception:
            first_token = alias

        path = _resolve_binary(first_token)
        if path is not None:
            return True, None
        return False, f"Binary not found in PATH (tried: {_CLI_ALIAS_MAP.get(first_token.lower(), [first_token])})"

    @property
    def key_source(self) -> str:
        return "local binary"
