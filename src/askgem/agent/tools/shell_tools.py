import asyncio
import os
import platform
import subprocess
from pydantic import BaseModel, Field
from .base import BaseTool, ToolResult

class ShellInput(BaseModel):
    command: str = Field(description="The shell command to execute.")

class ShellTool(BaseTool):
    name = "execute_command"
    description = "Executes a shell command on the host system. Use for running tests, build scripts, or system tasks."
    input_schema = ShellInput
    requires_confirmation = True

    async def execute(self, command: str) -> ToolResult:
        try:
            # Determine shell based on OS
            is_windows = platform.system() == "Windows"
            
            if is_windows:
                # Use powershell for better experience on modern Windows
                shell_executable = "powershell.exe"
                full_command = f"& {{ {command} }}"
            else:
                shell_executable = "/bin/bash"
                full_command = command

            # Run process
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # On Windows, create_subprocess_shell uses 'cmd /c', 
                # but we might want more control later.
            )

            try:
                # 30 second timeout as safety
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)
            except asyncio.TimeoutError:
                process.kill()
                return ToolResult(tool_call_id="", content="Error: Command timed out after 30 seconds.", is_error=True)

            out_str = stdout.decode("utf-8", errors="replace")
            err_str = stderr.decode("utf-8", errors="replace")

            combined_output = out_str
            if err_str:
                combined_output += f"\n--- STDERR ---\n{err_str}"

            exit_code = process.returncode
            if exit_code != 0:
                return ToolResult(tool_call_id="", content=f"Command failed (exit {exit_code}):\n{combined_output}", is_error=True)

            return ToolResult(tool_call_id="", content=combined_output or "(Command finished with no output)")

        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error executing command: {str(e)}", is_error=True)
