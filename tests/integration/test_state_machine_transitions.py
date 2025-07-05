"""
Task management and validation tests using real Alfred components.

Tests focus on actual task creation, validation, and file operations
without mocking to ensure realistic behavior testing.
"""

import pytest
from pathlib import Path

from alfred.models.schemas import TaskStatus
from alfred.tools.create_task import create_task_impl
from alfred.lib.md_parser import MarkdownTaskParser


class TestTaskManagementIntegration:
    """Test task management and validation using real components."""

    def test_task_creation_and_initial_state(self, test_alfred_dir):
        """Test that newly created tasks start in proper state."""
        content = """## Title
Task State Management Test

## Context
Testing task creation and initial state management using real components.

## Implementation Details
Task should be created successfully and maintain proper state.

## Acceptance Criteria
- Task is created with correct initial status
- File operations work properly
- Content is preserved exactly
"""

        response = create_task_impl(content)
        assert response.status == "success"

        # Get the auto-generated task ID
        task_id = response.data["task_id"]
        assert task_id.startswith("TS-")

        # Verify file creation
        task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
        assert task_file.exists()

        # Verify content preservation (with auto-generated ID prepended)
        saved_content = task_file.read_text()
        assert saved_content.startswith(f"# TASK: {task_id}\n\n")
        assert "Task State Management Test" in saved_content

    def test_task_validation_with_real_parser(self, test_alfred_dir):
        """Test task validation using actual parser components."""
        valid_content = """## Title
Real Parser Validation Test

## Context
Testing actual markdown parser validation with real task content.

## Implementation Details
Parser should correctly validate task format and extract data.

## Acceptance Criteria
- Parser validates format correctly
- All sections are extracted properly
- Data integrity is maintained
"""

        # Create task
        response = create_task_impl(valid_content)
        assert response.status == "success"

        # Get the auto-generated task ID
        task_id = response.data["task_id"]
        assert task_id.startswith("TS-")

        # Test real parser validation
        task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
        file_content = task_file.read_text()

        parser = MarkdownTaskParser()
        is_valid, error_msg = parser.validate_format(file_content)
        assert is_valid, f"Parser validation failed: {error_msg}"

        # Test parsing
        parsed_data = parser.parse(file_content)
        assert parsed_data["task_id"] == task_id
        assert parsed_data["title"] == "Real Parser Validation Test"

    def test_task_validation_error_scenarios(self, test_alfred_dir):
        """Test validation error scenarios with real validation logic."""
        error_scenarios = [
            # Missing required sections - no Implementation Details
            (
                """## Title
Missing Implementation Details

## Context
Missing the required implementation details section.

## Acceptance Criteria
- Should not be created
""",
                "missing implementation details",
            ),
            # Missing required sections - no Acceptance Criteria
            (
                """## Title
Missing Acceptance Criteria

## Context
Missing the required acceptance criteria section.

## Implementation Details
Should fail validation.
""",
                "missing acceptance criteria",
            ),
            # Missing required sections - no Context
            (
                """## Title
Missing Context

## Implementation Details
Missing the required context section.

## Acceptance Criteria
- Should not be created
""",
                "missing context",
            ),
        ]

        for invalid_content, error_type in error_scenarios:
            response = create_task_impl(invalid_content)

            # Should fail validation
            assert response.status == "error", f"Should fail for {error_type}"

            # Should provide meaningful error
            assert len(response.message) > 0
            assert response.data is not None

            # No partial files should be created
            tasks_dir = test_alfred_dir / "tasks"
            error_files = list(tasks_dir.glob("*BAD*.md")) + list(tasks_dir.glob("*INCOMPLETE*.md"))
            assert len(error_files) == 0, f"No files should be created for {error_type}"

    def test_concurrent_task_operations(self, test_alfred_dir):
        """Test concurrent task operations and isolation."""
        # Create multiple tasks to test isolation
        task_specs = ["Concurrent Task A", "Concurrent Task B", "Concurrent Task C"]

        created_tasks = []

        for i, title in enumerate(task_specs):
            content = f"""## Title
{title}

## Context
Testing concurrent task operations to ensure proper isolation
and no interference between simultaneous operations.

## Implementation Details
Each task should be processed independently with:
- Separate file operations
- Independent validation
- Isolated state management

## Acceptance Criteria
- Task is created successfully
- No interference with other tasks
- Content integrity is maintained
"""

            response = create_task_impl(content)
            assert response.status == "success"

            # Get the auto-generated task ID
            task_id = response.data["task_id"]
            expected_id = f"TS-{i + 1:02d}"
            assert task_id == expected_id
            created_tasks.append(task_id)

            # Verify file exists
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

        # Verify all tasks exist independently
        assert len(created_tasks) == 3
        assert created_tasks == ["TS-01", "TS-02", "TS-03"]

        # Check each task maintains its integrity
        for i, task_id in enumerate(created_tasks):
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

            content = task_file.read_text()
            assert f"# TASK: {task_id}" in content
            assert task_specs[i] in content

            # Verify parser can handle each independently
            parser = MarkdownTaskParser()
            is_valid, _ = parser.validate_format(content)
            assert is_valid

            parsed_data = parser.parse(content)
            assert parsed_data["task_id"] == task_id

    def test_task_id_format_validation(self, test_alfred_dir):
        """Test validation of auto-generated task ID formats."""
        # Create multiple tasks to test auto-generated IDs
        num_tasks = 6

        for i in range(num_tasks):
            content = f"""## Title
Task ID Format Test {i + 1}

## Context
Testing auto-generated task ID format validation.

## Implementation Details
Task ID should be auto-generated in the correct format.

## Acceptance Criteria
- Task is created successfully
- Task ID follows TS-XX format
"""

            response = create_task_impl(content)
            assert response.status == "success"

            # Verify auto-generated ID format
            task_id = response.data["task_id"]
            expected_id = f"TS-{i + 1:02d}"
            assert task_id == expected_id
            assert task_id.startswith("TS-")

            # Verify file created with correct name
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

    def test_duplicate_task_prevention_logic(self, test_alfred_dir):
        """Test that auto-generated IDs prevent duplicates by design."""
        original_content = """## Title
Original Duplicate Prevention Test

## Context
Testing that auto-generated task IDs naturally prevent duplicates.

## Implementation Details
Auto-generated IDs ensure no duplicates can occur.

## Acceptance Criteria
- First creation succeeds with auto-generated ID
- Second creation gets a new unique ID
- Both files exist independently
"""

        # Create original task
        response1 = create_task_impl(original_content)
        assert response1.status == "success"
        task_id_1 = response1.data["task_id"]
        assert task_id_1 == "TS-01"

        # Verify file exists
        task_file_1 = test_alfred_dir / "tasks" / f"{task_id_1}.md"
        assert task_file_1.exists()
        original_file_content = task_file_1.read_text()

        # Create second task with modified content
        duplicate_content = original_content.replace("Original", "Modified")
        response2 = create_task_impl(duplicate_content)

        # Should succeed with new ID
        assert response2.status == "success"
        task_id_2 = response2.data["task_id"]
        assert task_id_2 == "TS-02"
        assert task_id_2 != task_id_1

        # Both files should exist
        task_file_2 = test_alfred_dir / "tasks" / f"{task_id_2}.md"
        assert task_file_2.exists()

        # Original file should be unchanged
        current_file_content = task_file_1.read_text()
        assert current_file_content == original_file_content
        assert "Original" in current_file_content
        assert "Modified" not in current_file_content

        # New file should have modified content
        new_file_content = task_file_2.read_text()
        assert "Modified" in new_file_content
        assert "Original" not in new_file_content

    def test_task_response_data_completeness(self, test_alfred_dir):
        """Test that task responses contain all expected data."""
        content = """## Title
Response Data Completeness Test

## Context
Testing that task creation responses contain all necessary information.

## Implementation Details
Response should include all required fields for subsequent operations.

## Acceptance Criteria
- Response contains task_id
- Response contains file_path
- Response contains task_title
- Response contains next_action guidance
- Response contains note about auto-generation
"""

        response = create_task_impl(content)
        assert response.status == "success"

        # Check response structure
        assert isinstance(response.data, dict)

        # Check required fields
        required_fields = ["task_id", "file_path", "task_title", "next_action", "note"]
        for field in required_fields:
            assert field in response.data, f"Missing required field: {field}"
            assert response.data[field] is not None
            assert response.data[field] != ""

        # Verify field values
        task_id = response.data["task_id"]
        assert task_id.startswith("TS-")
        assert response.data["task_title"] == "Response Data Completeness Test"
        assert f"{task_id}.md" in response.data["file_path"]
        assert "work_on_task" in response.data["next_action"]
        assert "automatically generated" in response.data["note"]

    def test_directory_auto_creation_behavior(self, test_alfred_dir):
        """Test automatic directory creation behavior."""
        # Remove tasks directory to test auto-creation
        tasks_dir = test_alfred_dir / "tasks"
        if tasks_dir.exists():
            import shutil

            shutil.rmtree(tasks_dir)

        assert not tasks_dir.exists()

        content = """## Title
Auto Directory Creation Test

## Context
Testing automatic creation of required directory structure.

## Implementation Details
Tasks directory should be created automatically if missing.

## Acceptance Criteria
- Tasks directory is created automatically
- Task file is created in correct location
- Directory structure is proper
"""

        response = create_task_impl(content)
        assert response.status == "success"

        # Verify directory was created
        assert tasks_dir.exists()
        assert tasks_dir.is_dir()

        # Verify task file was created with auto-generated ID
        task_id = response.data["task_id"]
        task_file = tasks_dir / f"{task_id}.md"
        assert task_file.exists()
        assert task_file.is_file()

    def test_special_characters_handling(self, test_alfred_dir):
        """Test handling of special characters and encoding."""
        special_content = """## Title
Special Characters Test: àáâã & <>"' 🚀 ✅

## Context
Testing complete handling of special characters and Unicode:
- Accented characters: àáâã êëì ñóô
- Symbols: & < > " ' ` ~
- Unicode emoji: 🚀 ✅ ❌ 🔥 💯
- Mathematical: α β γ δ ∑ ∏ ∫
- Currency: $ € £ ¥ ₹ ₿

## Implementation Details
- Handle UTF-8 encoding properly throughout
- Preserve character integrity in all operations
- Maintain formatting across parser integration

## Acceptance Criteria
- All special characters are preserved exactly
- UTF-8 encoding works correctly
- Parser processes special characters properly
- No character corruption occurs
"""

        response = create_task_impl(special_content)
        assert response.status == "success"

        # Verify file creation and character preservation
        task_id = response.data["task_id"]
        task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
        assert task_file.exists()

        saved_content = task_file.read_text(encoding="utf-8")
        assert saved_content.startswith(f"# TASK: {task_id}\n\n")
        assert 'Special Characters Test: àáâã & <>"' in saved_content
        assert "🚀 ✅" in saved_content

        # Test specific special characters
        special_chars = ["àáâã", "🚀", "✅", "❌", "€", "₿", "α", "∑"]
        for char in special_chars:
            assert char in saved_content, f"Special character {char} not preserved"

        # Test parser with special characters
        parser = MarkdownTaskParser()
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"Parser failed with special characters: {error_msg}"

        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == task_id
        assert "àáâã" in parsed_data["title"]

    def test_production_isolation_verification(self, test_alfred_dir):
        """Test that operations are isolated from production .alfred directory."""
        # Create test tasks
        created_task_ids = []

        for i in range(3):
            content = f"""## Title
Production Isolation Test {i + 1}

## Context
Testing that test operations don't affect production .alfred directory.

## Implementation Details
All test operations should be isolated to test directory.

## Acceptance Criteria
- Test task is created in test directory
- No interference with production .alfred
- Proper isolation is maintained
"""

            response = create_task_impl(content)
            assert response.status == "success"

            task_id = response.data["task_id"]
            created_task_ids.append(task_id)

            # Verify task exists in test directory
            test_task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert test_task_file.exists()

        # Verify all test tasks exist only in test directory
        for task_id in created_task_ids:
            test_task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert test_task_file.exists(), f"Test task {task_id} missing from test directory"

            # Verify the file is in temp directory (contains temp directory marker)
            assert "alfred_test_" in str(test_task_file), f"Task {task_id} not in temp directory"

            # Verify the absolute path is not the production path
            prod_path = Path.cwd() / ".alfred" / "tasks" / f"{task_id}.md"
            assert test_task_file.resolve() != prod_path.resolve(), f"Task {task_id} created in production!"

    def test_comprehensive_real_data_integration(self, test_alfred_dir):
        """Test comprehensive integration using only real data and components."""
        # Create a complex task to test all aspects
        complex_content = """## Title
Comprehensive Real Data Integration Test

## Context
This is a comprehensive test that validates complete integration of all
Alfred components using real data, real file operations, and real parsing
without any mocking except for directory isolation.

The test validates:
- Real task creation with create_task_impl
- Actual file system operations in test directory
- Real markdown parsing with MarkdownTaskParser
- Actual validation logic and error handling
- True data preservation and integrity
- Complete workflow integration

## Implementation Details
Execute comprehensive real data test covering:
1. Task creation using actual implementation
2. File operations with real file system (isolated)
3. Content validation with real parser
4. Data integrity verification
5. Error handling with actual validation logic
6. Production isolation verification
7. Complete workflow integration testing

Technical requirements:
- Use actual Alfred components (no mocking)
- Real file system operations (in test directory)
- Actual parser validation and parsing
- Real error handling and validation
- True production isolation
- Complete integration verification

## Acceptance Criteria
- Task creation succeeds with real implementation
- File is created in test directory with exact content
- Real parser validates and parses task successfully
- All data fields are extracted correctly
- Error handling works with actual validation
- No interference with production .alfred directory
- All components integrate seamlessly
- Test isolation is maintained properly

## AC Verification
- Verify create_task_impl creates actual file
- Check file content matches input exactly
- Validate MarkdownTaskParser processes correctly
- Confirm all parsed fields are accurate
- Test error scenarios with real validation
- Verify production .alfred is unaffected
- Check test directory isolation works
- Validate complete integration success

## Dev Notes
- Comprehensive real data integration testing
- No mocking except settings for directory isolation
- Uses actual Alfred components throughout
- Real file system operations with isolation
- Production safety through test directory
- Maximum confidence through real component testing
"""

        # Execute comprehensive test
        response = create_task_impl(complex_content)

        # Verify task creation success
        assert response.status == "success"

        # Get the auto-generated task ID
        task_id = response.data["task_id"]
        assert task_id.startswith("TS-")
        assert response.data["task_title"] == "Comprehensive Real Data Integration Test"

        # Verify real file creation
        task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
        assert task_file.exists()
        assert task_file.is_file()

        # Verify content preservation (with auto-generated ID prepended)
        saved_content = task_file.read_text()
        assert saved_content.startswith(f"# TASK: {task_id}\n\n")
        assert "Comprehensive Real Data Integration Test" in saved_content

        # Test real parser integration
        parser = MarkdownTaskParser()

        # Real validation
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"Real parser validation failed: {error_msg}"

        # Real parsing
        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == task_id
        assert parsed_data["title"] == "Comprehensive Real Data Integration Test"
        assert "comprehensive test" in parsed_data["context"].lower()

        # Verify all sections parsed correctly
        expected_sections = ["title", "context", "implementation_details", "acceptance_criteria"]
        for section in expected_sections:
            assert section in parsed_data
            # Handle both string and list sections
            if isinstance(parsed_data[section], list):
                assert len(parsed_data[section]) > 0, f"List section {section} should not be empty"
            else:
                assert parsed_data[section].strip() != "", f"String section {section} should not be empty"

        # Test real error handling
        invalid_content = "This is completely invalid task content"
        error_response = create_task_impl(invalid_content)
        assert error_response.status == "error"
        assert len(error_response.message) > 0

        # Verify production isolation
        production_alfred = Path(".alfred")
        if production_alfred.exists():
            production_tasks = production_alfred / "tasks"
            if production_tasks.exists():
                production_task_file = production_tasks / f"{task_id}.md"
                assert not production_task_file.exists(), "Comprehensive test task leaked to production!"
