"""
Unit tests for create_task tool functionality using real data.

Tests use actual file operations and minimal mocking for realistic validation.
"""

import pytest
from pathlib import Path

from src.alfred.tools.create_task import create_task_impl
from src.alfred.models.schemas import ToolResponse
from src.alfred.lib.md_parser import MarkdownTaskParser


class TestCreateTaskImplementation:
    """Test the create_task implementation with real data."""

    def test_create_task_success(self, test_alfred_dir, sample_task_content):
        """Test successful task creation with real file operations."""
        response = create_task_impl(sample_task_content)

        assert response.status == "success"
        assert "SAMPLE-001" in response.message
        assert response.data is not None
        assert response.data["task_id"] == "SAMPLE-001"

        # Verify actual file was created
        task_file = test_alfred_dir / "tasks" / "SAMPLE-001.md"
        assert task_file.exists()

        # Verify file content matches exactly
        saved_content = task_file.read_text()
        assert saved_content == sample_task_content

    def test_create_task_file_creation_and_content(self, test_alfred_dir, sample_task_content):
        """Test that task file is actually created with correct content."""
        response = create_task_impl(sample_task_content)

        assert response.status == "success"

        # Check file was created in correct location
        task_file = test_alfred_dir / "tasks" / "SAMPLE-001.md"
        assert task_file.exists()
        assert task_file.is_file()

        # Check file content is preserved exactly
        content = task_file.read_text()
        assert "# TASK: SAMPLE-001" in content
        assert "Sample Test Task" in content
        assert "comprehensive test task" in content
        assert "## Acceptance Criteria" in content

    def test_create_task_response_data_structure(self, test_alfred_dir, sample_task_content):
        """Test the structure and content of response data."""
        response = create_task_impl(sample_task_content)

        assert response.status == "success"
        assert isinstance(response.data, dict)

        # Check all required fields are present
        required_fields = ["task_id", "file_path", "task_title", "next_action"]
        for field in required_fields:
            assert field in response.data
            assert response.data[field] is not None
            assert response.data[field] != ""

        # Verify field values
        assert response.data["task_id"] == "SAMPLE-001"
        assert response.data["task_title"] == "Sample Test Task"
        assert "SAMPLE-001.md" in response.data["file_path"]
        assert "work_on_task" in response.data["next_action"]

    def test_create_multiple_valid_tasks(self, test_alfred_dir, valid_task_contents):
        """Test creating multiple valid tasks independently."""
        created_task_ids = []

        for i, task_content in enumerate(valid_task_contents):
            response = create_task_impl(task_content)

            assert response.status == "success"
            task_id = f"VALID-{i + 1:03d}"
            assert response.data["task_id"] == task_id
            created_task_ids.append(task_id)

            # Verify each file exists
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

        # Verify all tasks were created independently
        assert len(created_task_ids) == 3

        # Check all files exist simultaneously
        for task_id in created_task_ids:
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

    def test_create_task_validation_errors(self, test_alfred_dir, invalid_task_contents):
        """Test validation with various invalid task formats."""
        for i, invalid_content in enumerate(invalid_task_contents):
            response = create_task_impl(invalid_content)

            assert response.status == "error", f"Invalid content {i} should fail validation"

            # Error should be informative
            assert any(keyword in response.message.lower() for keyword in ["format", "validation", "invalid", "required", "empty"])

            # Should provide helpful guidance
            assert "template" in response.data or "help" in response.data

            # No files should be created for invalid content
            tasks_dir = test_alfred_dir / "tasks"
            created_files = list(tasks_dir.glob("INVALID-*.md"))
            assert len(created_files) == 0, "No files should be created for invalid content"

    def test_create_task_duplicate_prevention(self, test_alfred_dir, sample_task_content):
        """Test prevention of duplicate task creation."""
        # Create first task
        response1 = create_task_impl(sample_task_content)
        assert response1.status == "success"
        assert response1.data["task_id"] == "SAMPLE-001"

        # Verify file exists
        task_file = test_alfred_dir / "tasks" / "SAMPLE-001.md"
        assert task_file.exists()
        original_content = task_file.read_text()

        # Attempt to create duplicate
        response2 = create_task_impl(sample_task_content)
        assert response2.status == "error"
        assert "already exists" in response2.message.lower()

        # Verify original file is unchanged
        assert task_file.exists()
        current_content = task_file.read_text()
        assert current_content == original_content

    def test_create_task_with_special_characters(self, test_alfred_dir):
        """Test task creation with special characters and Unicode."""
        special_content = """# TASK: SPECIAL-001

## Title
Task with Special Characters: àáâã & <>"' 🚀

## Context
Testing special characters and Unicode symbols: ✅ ❌ 🔥 💯
Newlines and tabs: \n\t\r
Various quotes: "double" 'single' `backtick`

## Implementation Details
- Handle UTF-8 encoding properly
- Preserve all special characters exactly
- Maintain formatting integrity across file operations

## Acceptance Criteria
- Special characters are preserved exactly
- Unicode symbols display correctly  
- No encoding corruption occurs
- File operations maintain integrity
"""

        response = create_task_impl(special_content)
        assert response.status == "success"

        # Verify file was created
        task_file = test_alfred_dir / "tasks" / "SPECIAL-001.md"
        assert task_file.exists()

        # Verify special characters are preserved
        saved_content = task_file.read_text(encoding="utf-8")
        assert "àáâã" in saved_content
        assert "🚀" in saved_content
        assert "✅" in saved_content
        assert "❌" in saved_content

        # Check that the essential content matches (normalize line endings)
        # Remove carriage returns for comparison since file systems may normalize them
        normalized_original = special_content.replace("\r", "")
        normalized_saved = saved_content.replace("\r", "")
        assert normalized_saved == normalized_original

    def test_create_task_directory_auto_creation(self, test_alfred_dir):
        """Test automatic creation of tasks directory if missing."""
        # Remove tasks directory
        tasks_dir = test_alfred_dir / "tasks"
        if tasks_dir.exists():
            import shutil

            shutil.rmtree(tasks_dir)

        assert not tasks_dir.exists()

        content = """# TASK: AUTO-DIR-001

## Title
Auto Directory Creation Test

## Context
Testing automatic creation of required directory structure.

## Implementation Details
Tasks directory should be created automatically if it doesn't exist.

## Acceptance Criteria
- Tasks directory is created automatically
- Task file is created in correct location
- Directory permissions are correct
"""

        response = create_task_impl(content)
        assert response.status == "success"

        # Verify directory was created
        assert tasks_dir.exists()
        assert tasks_dir.is_dir()

        # Verify task file was created
        task_file = tasks_dir / "AUTO-DIR-001.md"
        assert task_file.exists()
        assert task_file.is_file()

    def test_create_task_parser_integration(self, test_alfred_dir):
        """Test integration with real markdown parser."""
        parser_content = """# TASK: PARSER-001

## Title
Parser Integration Test

## Context
Testing integration between create_task and the actual markdown parser
to ensure real parsing functionality works correctly.

## Implementation Details
- Parse markdown correctly using real parser
- Extract all required fields accurately
- Validate structure against real schema

## Acceptance Criteria
- Task ID is extracted correctly by parser
- All sections are parsed and accessible
- Validation passes with real data
- Parser handles edge cases properly

## AC Verification
- Verify parser extracts task_id = "PARSER-001"
- Check all sections are identified
- Validate against actual Task schema

## Dev Notes
- Uses actual MarkdownTaskParser class
- No mocking of parser functionality
- Real integration testing approach
"""

        response = create_task_impl(parser_content)
        assert response.status == "success"

        # Verify parser integration worked
        assert response.data["task_id"] == "PARSER-001"
        assert response.data["task_title"] == "Parser Integration Test"

        # Test real parser functionality
        parser = MarkdownTaskParser()
        task_file = test_alfred_dir / "tasks" / "PARSER-001.md"
        saved_content = task_file.read_text()

        # Validate format using real parser
        is_valid, error_msg = parser.validate_format(saved_content)
        assert is_valid, f"Parser validation failed: {error_msg}"

        # Parse using real parser
        parsed_data = parser.parse(saved_content)
        assert parsed_data["task_id"] == "PARSER-001"
        assert parsed_data["title"] == "Parser Integration Test"

    def test_create_task_empty_and_whitespace_content(self, test_alfred_dir):
        """Test handling of empty and whitespace-only content."""
        test_cases = [("", "empty content"), ("   ", "whitespace only"), ("\n\t\r\n  \t", "mixed whitespace"), ("   \n\n\n   ", "newlines and spaces")]

        for content, description in test_cases:
            response = create_task_impl(content)

            assert response.status == "error", f"Should fail for {description}"
            assert "empty" in response.message.lower() or "format" in response.message.lower()

            # No files should be created
            tasks_dir = test_alfred_dir / "tasks"
            task_files = [f for f in tasks_dir.glob("*.md") if f.name != "README.md"]
            assert len(task_files) == 0, f"No files should be created for {description}"

    def test_create_task_missing_sections_validation(self, test_alfred_dir):
        """Test validation of missing required sections."""
        incomplete_tasks = [
            # Missing Implementation Details
            (
                """# TASK: MISSING-001

## Title
Missing Implementation

## Context
Task missing implementation details section.

## Acceptance Criteria
- Should fail validation
""",
                "Implementation Details",
            ),
            # Missing Acceptance Criteria
            (
                """# TASK: MISSING-002

## Title
Missing Criteria

## Context
Task missing acceptance criteria section.

## Implementation Details
Has implementation but no criteria.
""",
                "Acceptance Criteria",
            ),
            # Missing Context
            (
                """# TASK: MISSING-003

## Title
Missing Context

## Implementation Details
Has implementation but no context.

## Acceptance Criteria
- Should fail validation
""",
                "Context",
            ),
        ]

        for content, missing_section in incomplete_tasks:
            response = create_task_impl(content)

            assert response.status == "error"
            # Check for validation error in the message or data
            error_found = any(
                [
                    "required sections" in response.message.lower(),
                    "missing" in response.message.lower(),
                    response.data and "validation_error" in response.data and "missing" in response.data["validation_error"].lower(),
                ]
            )
            assert error_found, f"Expected validation error but got: {response.message}, data: {response.data}"

            # Verify no partial files created
            tasks_dir = test_alfred_dir / "tasks"
            missing_files = list(tasks_dir.glob("MISSING-*.md"))
            assert len(missing_files) == 0, f"No files should be created when missing {missing_section}"

    def test_create_task_concurrent_operations(self, test_alfred_dir):
        """Test concurrent task creation operations."""
        # Create multiple tasks with different IDs to simulate concurrency
        task_data = [("CONCURRENT-001", "First Concurrent Task"), ("CONCURRENT-002", "Second Concurrent Task"), ("CONCURRENT-003", "Third Concurrent Task")]

        responses = []

        for task_id, title in task_data:
            content = f"""# TASK: {task_id}

## Title
{title}

## Context
Testing concurrent task creation and state isolation.

## Implementation Details  
Each task should be created independently without interference.

## Acceptance Criteria
- Task is created with unique identifier
- No interference with other concurrent tasks
- Files are created correctly
"""

            response = create_task_impl(content)
            responses.append((response, task_id, title))

        # Verify all tasks created successfully
        for response, task_id, title in responses:
            assert response.status == "success"
            assert response.data["task_id"] == task_id
            assert response.data["task_title"] == title

            # Verify file exists
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

        # Verify all files exist simultaneously (no overwriting)
        for _, task_id, _ in responses:
            task_file = test_alfred_dir / "tasks" / f"{task_id}.md"
            assert task_file.exists()

            # Verify content integrity
            content = task_file.read_text()
            assert f"# TASK: {task_id}" in content
