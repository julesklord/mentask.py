import logging
import os
import shlex
import subprocess

from pydantic import BaseModel, Field

from .base import BaseTool, ToolResult

_logger = logging.getLogger("mentask")


class WorktreeInput(BaseModel):
    branch_name: str = Field(..., description="The name of the branch to create/use for the worktree")
    base_dir: str = Field(".mentask/worktrees", description="Base directory to store worktrees")


class EnterWorktreeTool(BaseTool):
    """Creates an isolated git worktree for focused mission execution."""

    name = "enter_worktree"
    description = "Creates a new git worktree in an isolated directory and switches the agent's context to it."
    input_schema = WorktreeInput
    requires_confirmation = True

    async def execute(self, branch_name: str, base_dir: str = ".mentask/worktrees") -> ToolResult:
        try:
            # 1. Prepare paths
            repo_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], encoding="utf-8").strip()
            worktree_path = os.path.join(repo_root, base_dir, branch_name)
            os.makedirs(os.path.dirname(worktree_path), exist_ok=True)

            # 2. Check if branch exists
            try:
                subprocess.run(["git", "rev-parse", "--verify", branch_name], check=True, capture_output=True)
                # If exists, we just add the worktree for it
                cmd = ["git", "worktree", "add", worktree_path, branch_name]
            except subprocess.CalledProcessError:
                # If not, create a new branch
                cmd = ["git", "worktree", "add", "-b", branch_name, worktree_path]

            # 3. Execute git worktree add
            result = subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8")

            # 4. Change current working directory to the new worktree
            os.chdir(worktree_path)

            msg = f"Success: Created and entered worktree at {worktree_path} on branch {branch_name}."
            _logger.info(msg)
            return ToolResult(tool_call_id="", content=msg, is_error=False)

        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error entering worktree: {str(e)}", is_error=True)


class ExitWorktreeTool(BaseTool):
    """Removes a worktree and returns to the main repository root."""

    name = "exit_worktree"
    description = "Exits the current worktree, removes it from git, and returns to the main repository root."

    async def execute(self) -> ToolResult:
        try:
            # 1. Get current worktree path and repo top level
            current_path = os.getcwd()
            repo_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], encoding="utf-8").strip()

            if current_path == repo_root:
                return ToolResult(tool_call_id="", content="Already at repository root.", is_error=True)

            # 2. Move to repo root
            os.chdir(repo_root)

            # 3. Remove the worktree
            subprocess.run(["git", "worktree", "remove", current_path, "--force"], check=True, capture_output=True)

            msg = f"Success: Exited worktree {current_path} and returned to {repo_root}."
            _logger.info(msg)
            return ToolResult(tool_call_id="", content=msg, is_error=False)

        except Exception as e:
            return ToolResult(tool_call_id="", content=f"Error exiting worktree: {str(e)}", is_error=True)
