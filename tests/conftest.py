"""
Shared test fixtures and configuration for Alfred Task Manager tests.

This configuration uses REAL data and minimal mocking to ensure tests
run against actual implementation with proper isolation.

CRITICAL: Tests MUST use temporary directories and NEVER touch production .alfred

Test Isolation Strategy:
1. Each test gets a fresh temporary directory created with tempfile.TemporaryDirectory
2. All alfred settings are mocked to point to the temp directory
3. Tests verify files are created in temp directories, not production
4. Temp directories are automatically cleaned up after each test
5. Production .alfred directory is completely isolated from tests

This prevents any accidental data loss or corruption of production data.
"""

import pytest
import shutil
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from alfred.models.schemas import Task, TaskStatus, ToolResponse, Subtask
from alfred.models.planning_artifacts import ContextDiscoveryArtifact


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment(monkeypatch):
    """Setup and cleanup test environment for each test using temporary directories."""
    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory(prefix="alfred_test_") as temp_dir:
        test_dir = Path(temp_dir)
        test_alfred_dir = test_dir / ".alfred"

        # Create Alfred directory structure
        test_alfred_dir.mkdir(parents=True, exist_ok=True)
        (test_alfred_dir / "tasks").mkdir(exist_ok=True)
        (test_alfred_dir / "workspace").mkdir(exist_ok=True)
        (test_alfred_dir / "debug").mkdir(exist_ok=True)
        (test_alfred_dir / "specs").mkdir(exist_ok=True)

        # Create basic config
        config_file = test_alfred_dir / "config.json"
        config_file.write_text('{"provider": "local", "project_name": "test_project", "version": "1.0.0"}')

        # CRITICAL: We need to patch the settings BEFORE any imports happen
        # First, check if modules are already imported and reload them if needed
        import sys

        # Create a real settings object that matches the expected interface
        class MockSettings:
            def __init__(self, test_dir):
                self.alfred_dir = str(test_dir)
                self.project_root = str(test_dir.parent)
                # Add any other attributes that settings might have

        mock_settings = MockSettings(test_alfred_dir)

        # Patch at the source - the alfred.config.settings module
        if "alfred.config.settings" in sys.modules:
            monkeypatch.setattr("alfred.config.settings.settings", mock_settings)
        if "alfred.config" in sys.modules:
            monkeypatch.setattr("alfred.config.settings", mock_settings)

        # Now patch all the places where settings might be imported
        modules_to_patch = [
            ("alfred.tools.create_task", "settings"),
            ("alfred.lib.md_parser", "settings"),
            ("alfred.state.manager", "settings"),
            ("alfred.task_providers.local_provider", "settings"),
            ("alfred.lib.structured_logger", "settings"),
        ]

        for module_name, attr_name in modules_to_patch:
            if module_name in sys.modules:
                try:
                    module = sys.modules[module_name]
                    if hasattr(module, attr_name):
                        monkeypatch.setattr(f"{module_name}.{attr_name}", mock_settings)
                except (ImportError, AttributeError):
                    pass

        # Set environment variable to ensure any subprocess also uses test dir
        monkeypatch.setenv("ALFRED_DIR", str(test_alfred_dir))
        monkeypatch.setenv("ALFRED_TEST_MODE", "true")

        # Store test directories in pytest namespace for access by fixtures
        pytest.test_temp_dir = test_dir
        pytest.test_alfred_dir = test_alfred_dir

        yield mock_settings

        # Cleanup is automatic with tempfile.TemporaryDirectory
        # No need to manually delete files


@pytest.fixture
def test_alfred_dir():
    """Provide the test Alfred directory path from temporary directory."""
    return pytest.test_alfred_dir


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        task_id="SAMPLE-001",
        title="Sample Test Task",
        context="A task for testing purposes with real data",
        implementation_details="Implementation for comprehensive testing",
        task_status=TaskStatus.NEW,
        acceptance_criteria=["Task should be testable", "Task should use real data"],
    )


@pytest.fixture
def sample_task_content():
    """Sample task content in markdown format (without task ID line)."""
    return """## Title
Sample Test Task

## Context
This is a comprehensive test task for validating the Alfred system functionality
using real data and minimal mocking. It demonstrates proper task structure
and validation without interfering with production data.

## Implementation Details
- Create actual test functionality
- Use real file operations  
- Validate with actual data structures
- Test complete workflow integration

## Acceptance Criteria
- Task should be properly parsed by real parser
- Task should validate against actual schema
- Task should support real status transitions
- Task should integrate with actual file system

## AC Verification
- Run actual unit tests to validate parsing
- Check real schema validation
- Test actual status transition logic
- Verify real file operations

## Dev Notes
- Use real data for testing
- Minimal mocking approach
- Test isolation through dedicated directory
- No interference with production .alfred directory
"""


@pytest.fixture
def valid_task_contents():
    """Multiple valid task contents for testing (without task ID lines)."""
    return [
        """## Title
First Valid Task

## Context
Testing multiple valid task creation.

## Implementation Details
First implementation details.

## Acceptance Criteria
- First criterion
""",
        """## Title
Second Valid Task

## Context
Testing concurrent task operations.

## Implementation Details
Second implementation details.

## Acceptance Criteria
- Second criterion
""",
        """## Title
Third Valid Task

## Context
Testing batch task operations.

## Implementation Details
Third implementation details.

## Acceptance Criteria
- Third criterion
""",
    ]


@pytest.fixture
def invalid_task_contents():
    """Multiple invalid task contents for testing validation."""
    return [
        # Missing required sections - no Implementation Details
        """## Title
Missing Implementation Details

## Context
This task is missing Implementation Details section

## Acceptance Criteria
- Criterion
""",
        # Missing required sections - no Acceptance Criteria
        """## Title
Missing Acceptance Criteria

## Context
This task is missing Acceptance Criteria section

## Implementation Details
Some implementation details here
""",
        # Missing Title section
        """## Context
Missing Title Section

## Implementation Details
Details

## Acceptance Criteria
- Criterion
""",
        # Empty content
        "",
        # Only whitespace
        "   \n\t  \n  ",
    ]


@pytest.fixture
def sample_context_discovery():
    """Sample context discovery artifact with real data."""
    from alfred.models.discovery_artifacts import ComplexityLevel

    return ContextDiscoveryArtifact(
        codebase_understanding={"main_components": ["Task system", "State machine", "Planning workflow"], "architecture": "Clean separation between models, core logic, and tools"},
        relevant_files=["tests/test_data/", "src/alfred/core/"],
        existing_components={"task_parser": "Handles task file parsing and validation", "state_manager": "Manages workflow state transitions"},
        complexity_assessment=ComplexityLevel.MEDIUM,
        discovery_notes=["Use real data for comprehensive testing", "Ensure test isolation from production", "Validate actual file operations"],
    )


@pytest.fixture
def sample_subtasks():
    """Sample subtasks with real specifications."""
    return [
        Subtask(
            subtask_id="REAL-ST-001",
            title="Create real test setup",
            location="tests/test_data/",
            operation="CREATE",
            specification=["Create actual test directory structure", "Set up real configuration files", "Initialize actual test environment"],
            test=["Verify test directory exists", "Check configuration is valid", "Validate environment setup"],
        ),
        Subtask(
            subtask_id="REAL-ST-002",
            title="Implement real test logic",
            location="tests/unit/",
            operation="CREATE",
            specification=["Write tests using real data", "Test actual file operations", "Validate real system integration"],
            test=["Run actual tests", "Check real file creation", "Verify system integration"],
        ),
    ]


@pytest.fixture
def success_response():
    """Standard success response for testing."""
    return ToolResponse(status="success", message="Operation completed successfully with real data", data={"result": "real_test_data"})


@pytest.fixture
def error_response():
    """Standard error response for testing."""
    return ToolResponse(status="error", message="Operation failed with real error", data={"error_code": "REAL_TEST_ERROR"})


# Test data constants
SAMPLE_TASK_IDS = ["TEST-001", "TEST-002", "TEST-003"]
VALID_TASK_STATUSES = list(TaskStatus)


def cleanup_test_files():
    """Utility function to clean up test files.
    NOTE: With temporary directories, this is rarely needed as cleanup is automatic.
    """
    if hasattr(pytest, "test_alfred_dir") and pytest.test_alfred_dir.exists():
        # Only clean task files, not the directory structure
        tasks_dir = pytest.test_alfred_dir / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.md"):
                if task_file.name not in ["README.md"]:
                    task_file.unlink()

        # Clean workspace directories
        workspace_dir = pytest.test_alfred_dir / "workspace"
        if workspace_dir.exists():
            for workspace in workspace_dir.iterdir():
                if workspace.is_dir():
                    shutil.rmtree(workspace)


def get_test_alfred_dir():
    """Get the test Alfred directory path."""
    return pytest.test_alfred_dir if hasattr(pytest, "test_alfred_dir") else None


def create_test_task_file(task_id: str, content: str) -> Path:
    """Create a test task file with given content."""
    if not hasattr(pytest, "test_alfred_dir"):
        raise RuntimeError("Test environment not set up properly")
    task_file = pytest.test_alfred_dir / "tasks" / f"{task_id}.md"
    task_file.write_text(content)
    return task_file


def verify_test_task_file(task_id: str) -> bool:
    """Verify a test task file exists."""
    if not hasattr(pytest, "test_alfred_dir"):
        return False
    task_file = pytest.test_alfred_dir / "tasks" / f"{task_id}.md"
    return task_file.exists()


def read_test_task_file(task_id: str) -> str:
    """Read content of a test task file."""
    if not hasattr(pytest, "test_alfred_dir"):
        return ""
    task_file = pytest.test_alfred_dir / "tasks" / f"{task_id}.md"
    return task_file.read_text() if task_file.exists() else ""
