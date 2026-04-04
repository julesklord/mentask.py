"""
Tests for core/memory_manager.py
"""
import os
import stat
from unittest.mock import patch
from askgem.core.memory_manager import MemoryManager, DEFAULT_MEMORY_TEMPLATE


class TestMemoryManager:
    def test_read_memory_success(self, tmp_path):
        """Test that read_memory successfully reads the file."""
        memory_file = tmp_path / "memory.md"
        with patch("askgem.core.memory_manager.get_memory_path") as mock_path:
            mock_path.return_value = str(memory_file)

            manager = MemoryManager()

            # The constructor creates the file with a template if it doesn't exist
            # Let's verify the content can be read
            content = manager.read_memory()
            assert "AskGem Persistent Memory" in content

            # Override with custom content and test again
            with open(memory_file, "w", encoding="utf-8") as f:
                f.write("Custom memory content")

            content = manager.read_memory()
            assert content == "Custom memory content"

    def test_read_memory_permission_error(self, tmp_path):
        """Test the exception path in read_memory when there is a PermissionError."""
        memory_file = tmp_path / "memory.md"
        with patch("askgem.core.memory_manager.get_memory_path") as mock_path:
            mock_path.return_value = str(memory_file)

            manager = MemoryManager()

            # Verify file was created
            assert memory_file.exists()

            # Remove read permissions
            # Get current permissions
            current_permissions = os.stat(memory_file).st_mode

            try:
                # Remove read permission for owner, group, and others
                os.chmod(memory_file, stat.S_IWUSR)

                # Should hit the exception path and return empty string
                content = manager.read_memory()
                assert content == ""
            finally:
                # Restore permissions so the test runner can clean up the temp directory
                os.chmod(memory_file, current_permissions)
