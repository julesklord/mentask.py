"""
Tests for tools/analysis_logic.py
"""

from unittest.mock import MagicMock, patch

from mentask.tools.analysis_logic import (
    detect_project_blueprint,
    get_git_diff_stat,
    get_repo_structure,
)


class TestGetGitDiffStat:
    @patch("mentask.tools.analysis_logic.subprocess.run")
    def test_get_git_diff_stat_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=" 1 file changed, 1 insertion(+)", stderr="")
        result = get_git_diff_stat()
        assert "1 file changed" in result
        mock_run.assert_called_once_with(["git", "diff", "--stat", "HEAD"], capture_output=True, text=True, check=False)

    @patch("mentask.tools.analysis_logic.subprocess.run")
    def test_get_git_diff_stat_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr="Not a git repository")
        result = get_git_diff_stat()
        assert "Error: Git diff failed" in result
        assert "Not a git repository" in result

    @patch("mentask.tools.analysis_logic.subprocess.run")
    def test_get_git_diff_stat_no_changes(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = get_git_diff_stat()
        assert "No changes detected" in result

    @patch("mentask.tools.analysis_logic.subprocess.run")
    def test_get_git_diff_stat_exception(self, mock_run):
        mock_run.side_effect = Exception("Subprocess error")
        result = get_git_diff_stat()
        assert "Error executing git: Subprocess error" in result


class TestGetRepoStructure:
    @patch("mentask.tools.analysis_logic.subprocess.run")
    def test_get_repo_structure_git_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="src/main.py\nsrc/utils/tool.py\nREADME.md\n"
        )
        result = get_repo_structure(max_depth=1)
        assert "- README.md" in result
        assert "- src" in result
        assert "  - main.py" in result
        assert "  - utils" in result
        # tool.py is at depth 2, should not be in result with max_depth=1
        assert "tool.py" not in result

    @patch("mentask.tools.analysis_logic.subprocess.run")
    @patch("os.listdir")
    def test_get_repo_structure_fallback(self, mock_listdir, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        mock_listdir.return_value = ["file1.txt", "dir1"]
        result = get_repo_structure()
        assert "Not a git repository" in result
        assert "file1.txt" in result
        assert "dir1" in result

    @patch("mentask.tools.analysis_logic.subprocess.run")
    def test_get_repo_structure_exception(self, mock_run):
        mock_run.side_effect = Exception("Unexpected error")
        result = get_repo_structure()
        assert "Error mapping repo: Unexpected error" in result

    @patch("mentask.tools.analysis_logic.subprocess.run")
    @patch("os.listdir")
    def test_get_repo_structure_fallback_exception(self, mock_listdir, mock_run):
        mock_run.return_value = MagicMock(returncode=1)
        mock_listdir.side_effect = Exception("OS Listdir error")
        result = get_repo_structure()
        assert "Error mapping repo: OS Listdir error" in result

class TestDetectProjectBlueprint:
    @patch("os.listdir")
    def test_detect_python_project(self, mock_listdir):
        mock_listdir.return_value = ["pyproject.toml", "src"]
        result = detect_project_blueprint()
        assert "Python Project" in result

    @patch("os.listdir")
    def test_detect_node_project(self, mock_listdir):
        mock_listdir.return_value = ["package.json", "node_modules"]
        result = detect_project_blueprint()
        assert "Node.js/TypeScript Project" in result

    @patch("os.listdir")
    def test_detect_rust_project(self, mock_listdir):
        mock_listdir.return_value = ["Cargo.toml", "src"]
        result = detect_project_blueprint()
        assert "Rust Project" in result

    @patch("os.listdir")
    def test_detect_go_project(self, mock_listdir):
        mock_listdir.return_value = ["go.mod", "main.go"]
        result = detect_project_blueprint()
        assert "Go Project" in result

    @patch("os.listdir")
    def test_detect_multiple_projects(self, mock_listdir):
        mock_listdir.return_value = ["package.json", "pyproject.toml"]
        result = detect_project_blueprint()
        assert "Node.js/TypeScript Project" in result
        assert "Python Project" in result

    @patch("os.listdir")
    def test_detect_unknown_project(self, mock_listdir):
        mock_listdir.return_value = ["random_file.txt"]
        result = detect_project_blueprint()
        assert "Generic or unknown project structure" in result
