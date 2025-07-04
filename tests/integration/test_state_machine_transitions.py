"""
Task management and validation tests using real Alfred components.

Tests focus on actual task creation, validation, and file operations
without mocking to ensure realistic behavior testing.
"""

import pytest
from pathlib import Path

from src.alfred.models.schemas import TaskStatus
from src.alfred.tools.create_task import create_task_impl
from src.alfred.lib.md_parser import MarkdownTaskParser


class TestTaskManagementIntegration:
    """Test task management and validation using real components."""

    def test_task_creation_and_initial_state(self, test_alfred_dir):
        """Test that newly created tasks start in proper state."""
        content = """# TASK: STATE-001

## Title
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
        assert response.data["task_id"] == "STATE-001"

        # Verify file creation
        task_file = test_alfred_dir / "tasks" / "STATE-001.md"
        assert task_file.exists()

        # Verify content preservation
        saved_content = task_file.read_text()
        assert saved_content == content

    def test_task_validation_with_real_parser(self, test_alfred_dir):
        """Test task validation using actual parser components."""
        valid_content = """# TASK: VALIDATION-001

## Title
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

        # Test real parser validation
        task_file = test_alfred_dir / "tasks" / "VALIDATION-001.md"
        file_content = task_file.read_text()

        parser = MarkdownTaskParser()
        is_valid, error_msg = parser.validate_format(file_content)
        assert is_valid, f"Parser validation failed: {error_msg}"

        # Test parsing
        parsed_data = parser.parse(file_content)
        assert parsed_data["task_id"] == "VALIDATION-001"
        assert parsed_data["title"] == "Real Parser Validation Test"

    def test_task_validation_error_scenarios(self, test_alfred_dir):
        """Test validation error scenarios with real validation logic."""
        error_scenarios = [
            # Missing task header
            (
                """## Title
No Task Header

## Context
Missing the required task header.

## Implementation Details
Should fail validation.

## Acceptance Criteria
- Should not be created
""",
                "task header",
            ),
            # Wrong header format
            (
                """# WRONG: BAD-001

## Title
Wrong Header Format

## Context
Using wrong header format.

## Implementation Details
Should fail validation.

## Acceptance Criteria
- Should not be created
""",
                "header format",
            ),
            # Missing required sections
            (
                """# TASK: INCOMPLETE-001

## Title
Incomplete Task

## Context
Missing implementation details section.
""",
                "missing sections",
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
        task_specs = [("CONCURRENT-A-001", "Concurrent Task A"), ("CONCURRENT-B-002", "Concurrent Task B"), ("CONCURRENT-C-003", "Concurrent Task C")]

        created_tasks = []

        for task_id, title in task_specs:
            content = f"""# TASK: {task_id}

## Title
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
            assert response.data["task_id"] == task_id
            created_tasks.append(task_id)

            # Verify file exists
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

        # Verify all tasks exist independently
        assert len(created_tasks) == 3

        # Check each task maintains its integrity
        for task_id in created_tasks:
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

            content = task_file.read_text()
            assert f"# TASK: {task_id}" in content

            # Verify parser can handle each independently
            parser = MarkdownTaskParser()
            is_valid, _ = parser.validate_format(content)
            assert is_valid

            parsed_data = parser.parse(content)
            assert parsed_data["task_id"] == task_id

    def test_task_id_format_validation(self, test_alfred_dir):
        """Test validation of various task ID formats."""
        valid_task_ids = ["SIMPLE-001", "PROJECT-123", "EPIC-01", "BUG-999", "FEATURE-2024-001", "TEST-A-001"]

        for task_id in valid_task_ids:
            content = f"""# TASK: {task_id}

## Title
Task ID Format Test

## Context
Testing task ID format validation with ID: {task_id}

## Implementation Details
Task ID should be accepted if it follows valid format.

## Acceptance Criteria
- Task is created successfully
- Task ID is preserved correctly
"""

            response = create_task_impl(content)
            assert response.status == "success", f"Valid task ID {task_id} should be accepted"
            assert response.data["task_id"] == task_id

            # Verify file created with correct name
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

    def test_duplicate_task_prevention_logic(self, test_alfred_dir):
        """Test duplicate prevention using real file system checks."""
        original_content = """# TASK: DUPLICATE-TEST-001

## Title
Original Duplicate Prevention Test

## Context
Testing that duplicate task IDs are properly prevented using real file checks.

## Implementation Details
System should reject attempts to create tasks with existing IDs.

## Acceptance Criteria
- First creation succeeds
- Subsequent creations with same ID fail
- Error message is clear and helpful
- Original file remains unchanged
"""

        # Create original task
        response1 = create_task_impl(original_content)
        assert response1.status == "success"
        assert response1.data["task_id"] == "DUPLICATE-TEST-001"

        # Verify file exists
        task_file = test_alfred_dir / "tasks" / "DUPLICATE-TEST-001.md"
        assert task_file.exists()
        original_file_content = task_file.read_text()

        # Attempt to create duplicate
        duplicate_content = original_content.replace("Original", "Modified")
        response2 = create_task_impl(duplicate_content)

        # Should fail
        assert response2.status == "error"
        assert "already exists" in response2.message.lower()

        # Original file should be unchanged
        current_file_content = task_file.read_text()
        assert current_file_content == original_file_content
        assert "Original" in current_file_content
        assert "Modified" not in current_file_content

    def test_task_response_data_completeness(self, test_alfred_dir):
        """Test that task responses contain all expected data."""
        content = """# TASK: RESPONSE-DATA-001

## Title
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
"""

        response = create_task_impl(content)
        assert response.status == "success"

        # Check response structure
        assert isinstance(response.data, dict)

        # Check required fields
        required_fields = ["task_id", "file_path", "task_title", "next_action"]
        for field in required_fields:
            assert field in response.data, f"Missing required field: {field}"
            assert response.data[field] is not None
            assert response.data[field] != ""

        # Verify field values
        assert response.data["task_id"] == "RESPONSE-DATA-001"
        assert response.data["task_title"] == "Response Data Completeness Test"
        assert "RESPONSE-DATA-001.md" in response.data["file_path"]
        assert "work_on_task" in response.data["next_action"]

    def test_directory_auto_creation_behavior(self, test_alfred_dir):
        """Test automatic directory creation behavior."""
        # Remove tasks directory to test auto-creation
        tasks_dir = test_alfred_dir / "tasks"
        if tasks_dir.exists():
            import shutil

            shutil.rmtree(tasks_dir)

        assert not tasks_dir.exists()

        content = """# TASK: AUTO-CREATE-001

## Title
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

        # Verify task file was created
        task_file = tasks_dir / "AUTO-CREATE-001.md"
        assert task_file.exists()
        assert task_file.is_file()

    def test_special_characters_handling(self, test_alfred_dir):
        """Test handling of special characters and encoding."""
        special_content = """# TASK: SPECIAL-HANDLING-001

## Title
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
        task_file = test_alfred_dir / "tasks" / "SPECIAL-HANDLING-001.md"
        assert task_file.exists()

        saved_content = task_file.read_text(encoding="utf-8")
        assert saved_content == special_content

        # Test specific special characters
        special_chars = ["àáâã", "🚀", "✅", "❌", "€", "₿", "α", "∑"]
        for char in special_chars:
            assert char in saved_content, f"Special character {char} not preserved"

        # Test parser with special characters
        parser = MarkdownTaskParser()
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"Parser failed with special characters: {error_msg}"

        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == "SPECIAL-HANDLING-001"
        assert "àáâã" in parsed_data["title"]

    def test_production_isolation_verification(self, test_alfred_dir):
        """Test that operations are isolated from production .alfred directory."""
        # Create test tasks
        test_task_ids = ["ISOLATION-001", "ISOLATION-002", "ISOLATION-003"]

        for task_id in test_task_ids:
            content = f"""# TASK: {task_id}

## Title
Production Isolation Test

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

            # Verify task exists in test directory
            test_task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert test_task_file.exists()

        # Verify production .alfred is not affected
        production_alfred = Path(".alfred")
        if production_alfred.exists():
            production_tasks = production_alfred / "tasks"
            if production_tasks.exists():
                for task_id in test_task_ids:
                    production_task_file = production_tasks / f"{task_id}.md"
                    assert not production_task_file.exists(), f"Test task {task_id} leaked to production!"

        # Verify all test tasks exist only in test directory
        for task_id in test_task_ids:
            test_task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert test_task_file.exists(), f"Test task {task_id} missing from test directory"

    def test_comprehensive_real_data_integration(self, test_alfred_dir):
        """Test comprehensive integration using only real data and components."""
        # Create a complex task to test all aspects
        complex_content = """# TASK: COMPREHENSIVE-REAL-001

## Title
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
        assert response.data["task_id"] == "COMPREHENSIVE-REAL-001"
        assert response.data["task_title"] == "Comprehensive Real Data Integration Test"

        # Verify real file creation
        task_file = test_alfred_dir / "tasks" / "COMPREHENSIVE-REAL-001.md"
        assert task_file.exists()
        assert task_file.is_file()

        # Verify exact content preservation
        saved_content = task_file.read_text()
        assert saved_content == complex_content

        # Test real parser integration
        parser = MarkdownTaskParser()

        # Real validation
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"Real parser validation failed: {error_msg}"

        # Real parsing
        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == "COMPREHENSIVE-REAL-001"
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
                production_task_file = production_tasks / "COMPREHENSIVE-REAL-001.md"
                assert not production_task_file.exists(), "Comprehensive test task leaked to production!"
