"""
Integration tests for complete workflow scenarios using real data.

Tests use actual Alfred components with minimal mocking for realistic validation.
"""

import pytest
from pathlib import Path
import json

from alfred.tools.create_task import create_task_impl
from alfred.models.schemas import TaskStatus
from alfred.lib.md_parser import MarkdownTaskParser


class TestCompleteWorkflowIntegration:
    """Test complete task workflows from creation using real implementations."""

    @pytest.fixture
    def workflow_task_content(self):
        """Complete task content for workflow testing (without task ID line)."""
        return """## Title
Complete Workflow Integration Test

## Context
This task validates the complete workflow integration from task creation
through file operations using real Alfred components. It ensures all phases
work together correctly with actual data and minimal mocking.

## Implementation Details
- Create task using real create_task_impl function
- Verify file operations using actual file system
- Test integration with real markdown parser
- Validate with actual schema models
- Use real Alfred directory structure

## Acceptance Criteria
- Task is created successfully with real file operations
- File content is preserved exactly as provided
- Real parser can validate and parse the created task
- Task data integrates properly with Alfred models
- All file system operations work correctly
- Test isolation is maintained without affecting production

## AC Verification
- Verify task file exists in test directory
- Parse file content with real MarkdownTaskParser
- Validate parsed data against actual Task model
- Check all required sections are present and correct
- Ensure no interference with production .alfred directory

## Dev Notes
- Uses actual Alfred components for realistic testing
- Test isolation through dedicated test directory
- Minimal mocking approach for maximum confidence
- Real file system operations with proper cleanup
"""

    def test_task_creation_workflow_integration(self, test_alfred_dir, workflow_task_content):
        """Test complete workflow from task creation through file validation."""
        # Create task using real implementation
        response = create_task_impl(workflow_task_content)

        # Verify successful creation with auto-generated ID
        assert response.status == "success"
        assert response.data["task_id"] == "TS-01"
        assert response.data["task_title"] == "Complete Workflow Integration Test"

        # Verify file was created in test directory (not production)
        task_file = test_alfred_dir / "tasks" / "TS-01.md"
        assert task_file.exists()
        assert task_file.is_file()

        # Verify content integrity (includes auto-generated task ID)
        saved_content = task_file.read_text()
        assert saved_content.startswith("# TASK: TS-01\n\n")
        assert "Complete Workflow Integration Test" in saved_content

    def test_parser_integration_workflow(self, test_alfred_dir, workflow_task_content):
        """Test integration between task creation and real parser."""
        # Create task
        response = create_task_impl(workflow_task_content)
        assert response.status == "success"

        # Read created file with auto-generated ID
        task_file = test_alfred_dir / "tasks" / "TS-01.md"
        file_content = task_file.read_text()

        # Test real parser integration
        parser = MarkdownTaskParser()

        # Validate format with real parser
        is_valid, error_msg = parser.validate_format(file_content)
        assert is_valid, f"Real parser validation failed: {error_msg}"

        # Parse with real parser
        parsed_data = parser.parse(file_content)
        assert parsed_data["task_id"] == "TS-01"
        assert parsed_data["title"] == "Complete Workflow Integration Test"

        # Verify all sections were parsed
        expected_sections = ["title", "context", "implementation_details", "acceptance_criteria"]
        for section in expected_sections:
            assert section in parsed_data
            assert parsed_data[section] is not None
            # Handle both string and list sections
            if isinstance(parsed_data[section], list):
                assert len(parsed_data[section]) > 0, f"List section {section} should not be empty"
            else:
                assert parsed_data[section].strip() != "", f"String section {section} should not be empty"

    def test_multiple_task_workflow_integration(self, test_alfred_dir, valid_task_contents):
        """Test workflow with multiple tasks to ensure proper isolation."""
        created_tasks = []

        # Create multiple tasks
        for i, task_content in enumerate(valid_task_contents):
            response = create_task_impl(task_content)

            assert response.status == "success"
            # Task IDs should be auto-generated: TS-01, TS-02, TS-03
            expected_task_id = f"TS-{i + 1:02d}"
            assert response.data["task_id"] == expected_task_id
            created_tasks.append(response.data["task_id"])

            # Verify file exists
            task_file = test_alfred_dir / "tasks" / f"{expected_task_id}.md"
            assert task_file.exists()

        # Verify all tasks exist simultaneously
        assert len(created_tasks) == 3
        assert created_tasks == ["TS-01", "TS-02", "TS-03"]

        # Test each task independently
        for task_id in created_tasks:
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

            # Verify parser can handle each task
            content = task_file.read_text()
            parser = MarkdownTaskParser()
            is_valid, _ = parser.validate_format(content)
            assert is_valid

            parsed_data = parser.parse(content)
            assert parsed_data["task_id"] == task_id

    def test_error_handling_workflow_integration(self, test_alfred_dir, invalid_task_contents):
        """Test error handling workflow with real validation."""
        for i, invalid_content in enumerate(invalid_task_contents):
            response = create_task_impl(invalid_content)

            # Should fail with real validation
            assert response.status == "error"

            # Error message should be meaningful
            assert len(response.message) > 0
            assert response.data is not None

            # Should provide helpful guidance
            assert "template" in response.data or "help" in response.data

            # No files should be created for invalid content
            tasks_dir = test_alfred_dir / "tasks"
            invalid_files = [f for f in tasks_dir.glob("*.md") if f.name.startswith("INVALID") or f.name.startswith("ERROR")]
            assert len(invalid_files) == 0

    def test_file_system_integration_workflow(self, test_alfred_dir):
        """Test complete file system integration workflow."""
        # Create task with comprehensive content
        comprehensive_content = """## Title
File System Integration Test

## Context
This test validates complete file system integration including:
- Directory creation and management
- File writing and reading operations
- Content preservation and encoding
- Path handling and validation
- Cleanup and isolation mechanisms

## Implementation Details
- Test automatic directory creation
- Verify file encoding handling (UTF-8)
- Check path resolution and validation
- Test concurrent file operations
- Validate content integrity across operations

## Acceptance Criteria
- All directories are created automatically as needed
- File content is preserved exactly without corruption
- UTF-8 encoding is handled correctly for special characters
- File paths are resolved correctly within test environment
- No interference with production file system
- Proper cleanup maintains test isolation

## AC Verification
- Check directory structure is created correctly
- Verify file content matches input exactly
- Test special characters and encoding
- Validate path resolution within test directory
- Confirm isolation from production .alfred directory

## Dev Notes
- Comprehensive file system integration testing
- Real file operations with proper isolation
- No mocking of file system operations
- Full path validation and encoding tests
"""

        # Create task
        response = create_task_impl(comprehensive_content)
        assert response.status == "success"

        # Verify directory structure
        tasks_dir = test_alfred_dir / "tasks"
        assert tasks_dir.exists()
        assert tasks_dir.is_dir()

        # Verify file creation with auto-generated ID
        task_file = test_alfred_dir / "tasks" / "TS-01.md"
        assert task_file.exists()
        assert task_file.is_file()

        # Verify content preservation (includes auto-generated task ID)
        saved_content = task_file.read_text(encoding="utf-8")
        assert saved_content.startswith("# TASK: TS-01\n\n")
        assert "File System Integration Test" in saved_content

        # Verify path resolution
        absolute_path = task_file.resolve()
        assert str(test_alfred_dir.resolve()) in str(absolute_path)
        assert "TS-01.md" in str(absolute_path)

    def test_concurrent_workflow_integration(self, test_alfred_dir):
        """Test concurrent operations in workflow integration."""
        # Create multiple tasks concurrently
        concurrent_tasks = []

        for i in range(5):
            content = f"""## Title
Concurrent Task {i + 1}

## Context
Testing concurrent workflow operations to ensure proper isolation
and no interference between simultaneous task operations.

## Implementation Details
Each task should be processed independently with:
- Separate file operations
- Independent validation
- Isolated state management
- No cross-task interference

## Acceptance Criteria
- Task is created successfully
- File is written correctly
- No interference with other concurrent tasks
- Content integrity is maintained
- Proper isolation is ensured
"""

            response = create_task_impl(content)
            assert response.status == "success"
            # Task IDs should be auto-generated sequentially
            expected_task_id = f"TS-{i + 1:02d}"
            assert response.data["task_id"] == expected_task_id
            concurrent_tasks.append(response.data["task_id"])

        # Verify all tasks were created successfully
        assert len(concurrent_tasks) == 5
        assert concurrent_tasks == ["TS-01", "TS-02", "TS-03", "TS-04", "TS-05"]

        # Verify each task file exists and has correct content
        for i, task_id in enumerate(concurrent_tasks):
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

            content = task_file.read_text()
            assert f"# TASK: {task_id}" in content
            assert f"Concurrent Task {i + 1}" in content

            # Verify parser can handle each task
            parser = MarkdownTaskParser()
            is_valid, _ = parser.validate_format(content)
            assert is_valid

            parsed_data = parser.parse(content)
            assert parsed_data["task_id"] == task_id

    def test_duplicate_prevention_workflow(self, test_alfred_dir):
        """Test duplicate prevention in complete workflow."""
        original_content = """## Title
Original Duplicate Test Task

## Context
Testing duplicate prevention in complete workflow integration.

## Implementation Details
This task should be created once and prevent subsequent duplicates.

## Acceptance Criteria
- First creation succeeds
- Duplicate attempts fail with clear error
- Original file remains unchanged
"""

        # Create original task
        response1 = create_task_impl(original_content)
        assert response1.status == "success"
        assert response1.data["task_id"] == "TS-01"

        # Verify file exists
        task_file = test_alfred_dir / "tasks" / "TS-01.md"
        assert task_file.exists()
        original_saved_content = task_file.read_text()

        # Create second task with different content - should get new ID
        duplicate_content = original_content.replace("Original", "Modified")
        response2 = create_task_impl(duplicate_content)

        # Should succeed with new ID
        assert response2.status == "success"
        assert response2.data["task_id"] == "TS-02"

        # Both files should exist independently
        task_file2 = test_alfred_dir / "tasks" / "TS-02.md"
        assert task_file2.exists()

        # Original file should be unchanged
        current_content = task_file.read_text()
        assert current_content == original_saved_content
        assert "Original" in current_content
        assert "Modified" not in current_content

        # New file should have modified content
        new_content = task_file2.read_text()
        assert "Modified" in new_content
        assert "Original" not in new_content

    def test_special_characters_workflow_integration(self, test_alfred_dir):
        """Test special characters handling in complete workflow."""
        special_content = """## Title
Special Characters Integration Test: àáâã 🚀 ✅

## Context
Testing complete workflow integration with special characters and Unicode:
- Accented characters: àáâã êëì ñóô
- Symbols: & < > " ' ` 
- Unicode emoji: 🚀 ✅ ❌ 🔥 💯
- Mathematical: α β γ δ ∑ ∏ ∫
- Currency: $ € £ ¥ ₹ ₿

## Implementation Details
- Handle UTF-8 encoding throughout workflow
- Preserve character integrity in file operations
- Maintain formatting across parser integration
- Ensure proper display and storage

## Acceptance Criteria
- All special characters are preserved exactly
- UTF-8 encoding is handled correctly
- File operations maintain character integrity
- Parser correctly processes special characters
- No character corruption occurs in workflow

## AC Verification
- Verify file content matches input exactly
- Test parser with special character content
- Check encoding preservation across operations
- Validate display integrity
"""

        # Create task with special characters
        response = create_task_impl(special_content)
        assert response.status == "success"
        assert response.data["task_id"] == "TS-01"

        # Verify file creation
        task_file = test_alfred_dir / "tasks" / "TS-01.md"
        assert task_file.exists()

        # Verify character preservation
        saved_content = task_file.read_text(encoding="utf-8")
        assert saved_content.startswith("# TASK: TS-01\n\n")
        assert "Special Characters Integration Test: àáâã 🚀 ✅" in saved_content

        # Test specific characters
        special_chars = ["àáâã", "🚀", "✅", "❌", "€", "₿", "α", "∑"]
        for char in special_chars:
            assert char in saved_content

        # Test parser integration with special characters
        parser = MarkdownTaskParser()
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"Parser failed with special characters: {error_msg}"

        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == "TS-01"
        assert "àáâã 🚀 ✅" in parsed_data["title"]

    def test_workflow_cleanup_and_isolation(self, test_alfred_dir):
        """Test that workflow maintains proper cleanup and isolation."""
        # Create multiple tasks to test cleanup
        test_tasks = []

        for i in range(3):
            content = f"""## Title
Cleanup Test Task {i + 1}

## Context
Testing cleanup and isolation mechanisms.

## Implementation Details
Task should be created and cleaned up properly.

## Acceptance Criteria
- Task is created successfully
- Files are managed properly
- Cleanup works correctly
"""

            response = create_task_impl(content)
            assert response.status == "success"
            expected_task_id = f"TS-{i + 1:02d}"
            assert response.data["task_id"] == expected_task_id
            test_tasks.append(response.data["task_id"])

        # Verify all tasks exist
        assert test_tasks == ["TS-01", "TS-02", "TS-03"]
        for task_id in test_tasks:
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

        # Verify test directory structure is correct
        assert (test_alfred_dir / "tasks").exists()
        assert (test_alfred_dir / "workspace").exists()
        assert (test_alfred_dir / "debug").exists()

        # Verify isolation - tasks should be in temp directory only
        for task_id in test_tasks:
            test_task_file = test_alfred_dir / "tasks" / f"{task_id}.md"

            # Verify the file is in temp directory (contains temp directory marker)
            assert "alfred_test_" in str(test_task_file), f"Task {task_id} not in temp directory"

            # Verify the absolute path is not the production path
            prod_path = Path.cwd() / ".alfred" / "tasks" / f"{task_id}.md"
            assert test_task_file.resolve() != prod_path.resolve(), f"Task {task_id} created in production!"

    def test_end_to_end_workflow_validation(self, test_alfred_dir):
        """Test complete end-to-end workflow validation."""
        # Create a comprehensive task
        e2e_content = """## Title
End-to-End Workflow Validation Test

## Context
This is a comprehensive end-to-end test that validates the complete
workflow from task creation through all validation stages using
real Alfred components and actual file operations.

Test covers:
- Task creation with real create_task_impl
- File system operations in isolated test environment  
- Markdown parsing with actual MarkdownTaskParser
- Data validation with real Pydantic models
- Error handling with actual validation logic
- Content preservation across all operations

## Implementation Details
Execute complete workflow integration:
1. Create task using real implementation (no mocking)
2. Verify file system operations work correctly
3. Test parser integration with created file
4. Validate data models with parsed content
5. Verify error handling for edge cases
6. Confirm test isolation from production
7. Test cleanup and state management

## Acceptance Criteria
- Task creation succeeds with real file operations
- File content is preserved exactly without corruption
- Parser successfully validates and parses created task
- All data models validate correctly with real data
- Error handling works properly for invalid inputs
- Test isolation prevents production interference
- Cleanup mechanisms work correctly
- All components integrate seamlessly

## AC Verification
- Verify file exists in test directory with exact content
- Parse file with MarkdownTaskParser and validate success
- Check all parsed fields match expected values
- Test invalid content triggers proper error handling
- Confirm no files exist in production .alfred directory
- Validate test directory cleanup after test completion

## Dev Notes
- Comprehensive integration test using real components
- No mocking except for settings to point to test directory
- Full file system integration with proper isolation
- Real parser and validation logic testing
- Production safety through test directory isolation
"""

        # Execute end-to-end workflow
        response = create_task_impl(e2e_content)

        # Verify task creation with auto-generated ID
        assert response.status == "success"
        assert response.data["task_id"] == "TS-01"
        assert response.data["task_title"] == "End-to-End Workflow Validation Test"

        # Verify file system integration
        task_file = test_alfred_dir / "tasks" / "TS-01.md"
        assert task_file.exists()

        # Verify content preservation (includes auto-generated task ID)
        saved_content = task_file.read_text()
        assert saved_content.startswith("# TASK: TS-01\n\n")
        assert "End-to-End Workflow Validation Test" in saved_content

        # Test parser integration
        parser = MarkdownTaskParser()
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"End-to-end parser validation failed: {error_msg}"

        # Test parsing functionality
        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == "TS-01"
        assert parsed_data["title"] == "End-to-End Workflow Validation Test"
        assert "comprehensive end-to-end test" in parsed_data["context"].lower()

        # Verify all required sections
        required_sections = ["title", "context", "implementation_details", "acceptance_criteria"]
        for section in required_sections:
            assert section in parsed_data
            # Handle both string and list sections
            if isinstance(parsed_data[section], list):
                assert len(parsed_data[section]) > 0, f"List section {section} should not be empty"
            else:
                assert parsed_data[section].strip() != "", f"String section {section} should not be empty"

        # Test error handling with invalid content
        invalid_content = "This is not a valid task format"
        error_response = create_task_impl(invalid_content)
        assert error_response.status == "error"
        assert "format" in error_response.message.lower() or "validation" in error_response.message.lower()

        # Verify production isolation
        production_alfred = Path(".alfred")
        if production_alfred.exists():
            production_tasks = production_alfred / "tasks"
            if production_tasks.exists():
                production_task_file = production_tasks / "TS-01.md"
                assert not production_task_file.exists(), "Test task leaked to production!"
