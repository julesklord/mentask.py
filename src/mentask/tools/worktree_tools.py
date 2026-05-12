import logging
import os
import subprocess

_logger = logging.getLogger("mentask")


def enter_worktree(branch_name: str, base_dir: str = ".mentask/worktrees") -> str:
    """Enters an isolated git worktree."""
    status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=False)
    if status.stdout.strip():
        raise RuntimeError(
            "ERROR: The working directory is dirty (uncommitted changes exist). "
            "CRITICAL INSTRUCTION: Do NOT attempt to run 'git commit' or 'git stash' yourself. "
            "Stop and ask the user how they want to proceed."
        )

    repo_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], encoding="utf-8").strip()
    worktree_path = os.path.join(repo_root, base_dir, branch_name)
    os.makedirs(os.path.dirname(worktree_path), exist_ok=True)

    try:
        subprocess.run(["git", "rev-parse", "--verify", branch_name], check=True, capture_output=True)
        cmd = ["git", "worktree", "add", worktree_path, branch_name]
    except subprocess.CalledProcessError:
        cmd = ["git", "worktree", "add", "-b", branch_name, worktree_path]

    subprocess.run(cmd, check=True, capture_output=True, encoding="utf-8")
    os.chdir(worktree_path)

    msg = f"Success: Created and entered worktree at {worktree_path} on branch {branch_name}."
    _logger.info(msg)
    return msg


def exit_worktree() -> str:
    """Exits the current worktree."""
    current_path = os.getcwd()
    repo_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], encoding="utf-8").strip()

    if current_path == repo_root:
        raise RuntimeError("Already at repository root.")

    os.chdir(repo_root)
    subprocess.run(["git", "worktree", "remove", current_path, "--force"], check=True, capture_output=True)

    msg = f"Success: Exited worktree {current_path} and returned to {repo_root}."
    _logger.info(msg)
    return msg
