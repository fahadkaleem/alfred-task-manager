"""
Shared test fixtures and configuration for Alfred Task Manager tests.

This configuration uses REAL data and minimal mocking to ensure tests
run against actual implementation with proper isolation.
"""

import pytest
import shutil
from pathlib import Path
from unittest.mock import patch

from src.alfred.models.schemas import Task, TaskStatus, ToolResponse, Subtask
from src.alfred.models.planning_artifacts import ContextDiscoveryArtifact


# Test data directory - use real directory for test isolation
TEST_DATA_DIR = Path(__file__).parent / "test_data"
TEST_ALFRED_DIR = TEST_DATA_DIR / ".alfred"


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment():
    """Setup and cleanup test environment for each test."""
    # Ensure test data directory exists
    TEST_ALFRED_DIR.mkdir(parents=True, exist_ok=True)
    (TEST_ALFRED_DIR / "tasks").mkdir(exist_ok=True)
    (TEST_ALFRED_DIR / "workspace").mkdir(exist_ok=True)
    (TEST_ALFRED_DIR / "debug").mkdir(exist_ok=True)
    (TEST_ALFRED_DIR / "specs").mkdir(exist_ok=True)

    # Create basic config if it doesn't exist
    config_file = TEST_ALFRED_DIR / "config.json"
    if not config_file.exists():
        config_file.write_text('{"provider": "local", "project_name": "test_project", "version": "1.0.0"}')

    # Patch settings to use test directory - patch multiple import locations
    patches = [
        patch("alfred.config.settings.settings"),  # Patch the actual settings object
        patch("src.alfred.tools.create_task.settings"),
        patch("src.alfred.config.settings.settings"),
        patch("src.alfred.lib.logger.settings"),
        patch("src.alfred.lib.md_parser.settings", create=True),
        patch("src.alfred.state.manager.settings"),
        patch("src.alfred.task_providers.local_provider.settings"),
    ]

    try:
        # Start all patches
        mock_settings_list = []
        for p in patches:
            try:
                mock_settings = p.start()
                mock_settings.alfred_dir = str(TEST_ALFRED_DIR)
                mock_settings.project_root = str(TEST_DATA_DIR)
                mock_settings_list.append(mock_settings)
            except (ImportError, AttributeError):
                # Skip patches that don't apply
                pass

        yield mock_settings_list[0] if mock_settings_list else None

    finally:
        # Stop all patches
        for p in patches:
            try:
                p.stop()
            except:
                pass

    # Cleanup task files after each test to ensure isolation
    tasks_dir = TEST_ALFRED_DIR / "tasks"
    if tasks_dir.exists():
        for task_file in tasks_dir.glob("*.md"):
            if task_file.name != "README.md":  # Keep README for reference
                task_file.unlink()
        
        # Also remove task_counter.json to reset ID generation
        counter_file = tasks_dir / "task_counter.json"
        if counter_file.exists():
            counter_file.unlink()

    # Clean workspace directories
    workspace_dir = TEST_ALFRED_DIR / "workspace"
    if workspace_dir.exists():
        for workspace in workspace_dir.iterdir():
            if workspace.is_dir():
                shutil.rmtree(workspace)


@pytest.fixture
def test_alfred_dir():
    """Provide the test Alfred directory path."""
    return TEST_ALFRED_DIR


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
    from src.alfred.models.discovery_artifacts import ComplexityLevel

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
    """Utility function to clean up test files."""
    if TEST_ALFRED_DIR.exists():
        # Only clean task files, not the directory structure
        tasks_dir = TEST_ALFRED_DIR / "tasks"
        if tasks_dir.exists():
            for task_file in tasks_dir.glob("*.md"):
                if task_file.name not in ["README.md"]:
                    task_file.unlink()

        # Clean workspace directories
        workspace_dir = TEST_ALFRED_DIR / "workspace"
        if workspace_dir.exists():
            for workspace in workspace_dir.iterdir():
                if workspace.is_dir():
                    shutil.rmtree(workspace)


def get_test_alfred_dir():
    """Get the test Alfred directory path."""
    return TEST_ALFRED_DIR


def create_test_task_file(task_id: str, content: str) -> Path:
    """Create a test task file with given content."""
    task_file = TEST_ALFRED_DIR / "tasks" / f"{task_id}.md"
    task_file.write_text(content)
    return task_file


def verify_test_task_file(task_id: str) -> bool:
    """Verify a test task file exists."""
    task_file = TEST_ALFRED_DIR / "tasks" / f"{task_id}.md"
    return task_file.exists()


def read_test_task_file(task_id: str) -> str:
    """Read content of a test task file."""
    task_file = TEST_ALFRED_DIR / "tasks" / f"{task_id}.md"
    return task_file.read_text() if task_file.exists() else ""
