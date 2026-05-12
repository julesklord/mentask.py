import asyncio
import json
import logging
import shlex
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from ....core.compression import ContextCompressor
from ...schema import Message, Role, ToolCall, UsageMetrics
from .base import BaseProvider

_logger = logging.getLogger("mentask")


class CLIProvider(BaseProvider):
    """
    Provider that bridges MentAsk to external CLI agents (e.g., gemini-cli, codex).
    It translates history and tools into a text prompt, runs the binary, and parses stdout.
    """

    def __init__(self, model_name: str, config: Any):
        # We strip the 'cli:' prefix if present
        pure_cmd = model_name.split(":", 1)[1] if ":" in model_name and model_name.startswith("cli:") else model_name
        super().__init__(pure_cmd, config)
        # cli_command can be just the binary 'gemini-cli' or a template 'gemini-cli --system "..." {prompt}'
        self.cli_command = pure_cmd

    async def setup(self) -> bool:
        import shutil

        # Extract binary from command (first part)
        try:
            binary = shlex.split(self.cli_command)[0]
            if shutil.which(binary) is None:
                _logger.error(f"CLI binary '{binary}' not found in PATH.")
                return False
        except Exception:
            return False
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

    async def generate_stream(
        self,
        history: list[Message],
        tools_schema: list[dict[str, Any]],
        config: Any | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:

        system_instruction = config.get("system_instruction", "") if config else ""
        full_prompt = self._build_prompt(history, tools_schema, system_instruction)

        # Build command. If {prompt} is in the string, replace it. Otherwise append.
        if "{prompt}" in self.cli_command:
            cmd_str = self.cli_command.replace("{prompt}", full_prompt)
            args = shlex.split(cmd_str)
        else:
            args = shlex.split(self.cli_command) + [full_prompt]

        _logger.debug(f"Invoking CLI Bridge: {args[0]} (prompt len: {len(full_prompt)})")

        try:
            process = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            if process.stdout is None:
                raise RuntimeError("Failed to open stdout pipe")

            json_buffer = ""
            in_json_block = False

            # Read stdout line by line
            while True:
                line_bytes = await process.stdout.readline()
                if not line_bytes:
                    break

                line = line_bytes.decode("utf-8")

                # Logic to detect JSON blocks even if mixed with text
                if "```json" in line:
                    in_json_block = True
                    json_buffer = ""
                    # If there's text before the block on the same line, yield it
                    pre = line.split("```json")[0]
                    if pre.strip():
                        yield {"type": "text", "content": pre}
                    continue

                if in_json_block:
                    if "```" in line:
                        in_json_block = False
                        # Handle text after the block
                        post = line.split("```")[1]

                        try:
                            # Clean potential trailing characters from json_buffer
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

            await process.wait()

            # Emit dummy metrics
            yield {"type": "metrics", "content": UsageMetrics(input_tokens=len(full_prompt) // 4, output_tokens=0)}

        except Exception as e:
            _logger.error(f"CLI Bridge failure ({self.cli_command}): {e}")
            yield {"type": "error", "content": f"CLI Bridge Error: {e}"}

    async def list_models(self) -> list[str]:
        # CLI models are usually dynamic or just represent the binary name
        return [self.cli_command]

    async def check_health(self, model_name: str) -> tuple[bool, str | None]:
        import shutil

        try:
            binary = shlex.split(model_name)[0]
            if shutil.which(binary) is not None:
                return True, None
        except Exception:
            pass
        return False, "Binary not found in PATH"
