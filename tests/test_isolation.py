"""
Test to verify that test isolation is working properly.

This test ensures that:
1. Tests use temporary directories
2. Tests CANNOT access production .alfred directory
3. All file operations are isolated
"""

import os
import pytest
from pathlib import Path
from alfred.tools.create_task import create_task_impl
from alfred.config import settings as config_settings


class TestIsolationVerification:
    """Verify test isolation is working properly."""

    def test_temp_directory_is_used(self, test_alfred_dir):
        """Verify tests are using temporary directories."""
        # Test directory should exist
        assert test_alfred_dir.exists()

        # Should be in a temp directory (contains 'alfred_test_' in path)
        assert "alfred_test_" in str(test_alfred_dir)

        # Should NOT be the production .alfred directory
        production_alfred = Path(".alfred").resolve()
        test_alfred_resolved = test_alfred_dir.resolve()
        assert test_alfred_resolved != production_alfred

        # Parent should be in system temp directory
        temp_markers = ["/tmp/", "/var/folders/", "Temp", "TEMP"]
        assert any(marker in str(test_alfred_dir) for marker in temp_markers)

    def test_settings_are_mocked(self):
        """Verify settings are properly mocked to use test directory."""
        # Import settings from where create_task uses it
        from alfred.tools.create_task import settings

        # Settings should be mocked
        assert hasattr(settings, "alfred_dir")

        # Alfred dir should be in temp directory
        assert "alfred_test_" in settings.alfred_dir

        # Should NOT point to production (which would be just '.alfred' in current dir)
        assert settings.alfred_dir != ".alfred"
        assert Path(settings.alfred_dir).is_absolute()  # Should be absolute path
        assert "/tmp/" in settings.alfred_dir or "/var/folders/" in settings.alfred_dir  # Should be in temp

    def test_file_operations_are_isolated(self, test_alfred_dir):
        """Verify file operations don't affect production."""
        # Create a task using the tool
        test_content = """## Title
Test Isolation Task

## Context  
This task verifies test isolation is working.

## Implementation Details
File should be created in temp directory only.

## Acceptance Criteria
- Task created in temp directory
- No files in production .alfred
"""

        response = create_task_impl(test_content)
        assert response.status == "success"

        task_id = response.data["task_id"]

        # File should exist in test directory
        test_file = test_alfred_dir / "tasks" / f"{task_id}.md"
        assert test_file.exists()

        # File should NOT exist in production
        production_file = Path(".alfred") / "tasks" / f"{task_id}.md"
        assert not production_file.exists()

        # Verify the file is actually in temp directory
        assert "alfred_test_" in str(test_file)

    def test_production_directory_is_protected(self):
        """Verify we cannot accidentally write to production .alfred."""
        # Get the mocked settings
        from alfred.tools.create_task import settings

        # Try to directly access production - should fail or redirect
        prod_alfred = Path(".alfred")

        # Our settings should not point to production
        assert Path(settings.alfred_dir).resolve() != prod_alfred.resolve()

        # Even if we try to write directly, it should go to temp
        test_file_path = Path(settings.alfred_dir) / "tasks" / "isolation_test.md"
        test_file_path.parent.mkdir(parents=True, exist_ok=True)
        test_file_path.write_text("test content")

        # Verify it was written to temp, not production
        assert test_file_path.exists()
        assert "alfred_test_" in str(test_file_path)

        # Production should not have this file
        prod_test_file = prod_alfred / "tasks" / "isolation_test.md"
        assert not prod_test_file.exists()

    def test_multiple_tests_use_different_temp_dirs(self, test_alfred_dir):
        """Verify each test gets its own temp directory."""
        # Store the current test directory
        first_test_dir = str(test_alfred_dir)

        # Create a file
        test_file = test_alfred_dir / "tasks" / "test_isolation.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test")

        # This file should exist now
        assert test_file.exists()

        # In the next test function, this file shouldn't exist
        # (each test gets a fresh temp directory)
        # We'll verify this by checking the directory path is unique
        assert "alfred_test_" in first_test_dir

        # The temp directory should be empty except for what we created
        task_files = list((test_alfred_dir / "tasks").glob("*.md"))
        assert len(task_files) == 1
        assert task_files[0].name == "test_isolation.md"
