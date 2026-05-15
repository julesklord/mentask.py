import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch

from mentask.tools.worktree_tools import enter_worktree, exit_worktree


class TestWorktreeTools(unittest.TestCase):
    @patch("mentask.tools.worktree_tools.subprocess.run")
    @patch("mentask.tools.worktree_tools.subprocess.check_output")
    @patch("os.makedirs")
    @patch("os.chdir")
    @patch("os.getcwd")
    def test_enter_worktree_success(self, mock_getcwd, mock_chdir, mock_makedirs, mock_check_output, mock_run):
        # Mocking
        mock_run.side_effect = [
            MagicMock(stdout=""),  # git status
            MagicMock(),  # git rev-parse (branch exists)
            MagicMock(),  # git worktree add
        ]
        mock_check_output.return_value = "/repo/root"

        # Call
        result = enter_worktree("test-branch")

        # Verify
        self.assertIn("Success", result)
        self.assertIn("test-branch", result)
        mock_chdir.assert_called()

    @patch("mentask.tools.worktree_tools.subprocess.run")
    @patch("mentask.tools.worktree_tools.subprocess.check_output")
    @patch("os.chdir")
    @patch("os.getcwd")
    def test_exit_worktree_success(self, mock_getcwd, mock_chdir, mock_check_output, mock_run):
        # Mocking
        mock_getcwd.return_value = "/repo/root/.mentask/worktrees/test-branch"
        mock_check_output.return_value = "/repo/root"

        # Call
        result = exit_worktree()

        # Verify
        self.assertIn("Success", result)
        mock_chdir.assert_called_with("/repo/root")
        mock_run.assert_called()

    @patch("mentask.tools.worktree_tools.subprocess.run")
    def test_enter_worktree_dirty(self, mock_run):
        # Mocking
        mock_run.return_value = MagicMock(stdout=" M somefile.py")

        # Call & Verify
        with self.assertRaisesRegex(RuntimeError, "dirty"):
            enter_worktree("test-branch")

    @patch("mentask.tools.worktree_tools.subprocess.run")
    @patch("mentask.tools.worktree_tools.subprocess.check_output")
    @patch("os.makedirs")
    @patch("os.chdir")
    @patch("os.getcwd")
    def test_enter_worktree_new_branch(self, mock_getcwd, mock_chdir, mock_makedirs, mock_check_output, mock_run):
        # Mocking
        mock_run.side_effect = [
            MagicMock(stdout=""),  # git status
            subprocess.CalledProcessError(
                1, ["git", "rev-parse", "--verify", "test-branch"]
            ),  # git rev-parse (branch does not exist)
            MagicMock(),  # git worktree add
        ]
        mock_check_output.return_value = "/repo/root"

        # Call
        result = enter_worktree("test-branch")

        # Verify
        self.assertIn("Success", result)
        self.assertIn("test-branch", result)
        mock_chdir.assert_called()

        expected_path = os.path.join("/repo/root", ".mentask/worktrees", "test-branch")

        mock_run.assert_any_call(
            ["git", "worktree", "add", "-b", "test-branch", expected_path],
            check=True,
            capture_output=True,
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
