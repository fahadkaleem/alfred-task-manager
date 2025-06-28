# tests/test_harness_verification.py
"""
Verification tests for the Alfred testing harness.
"""
from pathlib import Path
from src.alfred.models.schemas import Task, TaskStatus
from tests.conftest import AlfredTestProject


def test_project_initialization(alfred_test_project: AlfredTestProject):
    """Test that the testing harness can initialize a project correctly."""
    # Initialize the test project
    result = alfred_test_project.initialize()
    
    # Verify successful initialization
    assert result.status == "success"
    
    # Verify the .alfred-test directory exists
    assert alfred_test_project.alfred_dir.exists()
    
    # Verify core files exist
    assert (alfred_test_project.alfred_dir / "workflow.yml").exists()
    assert (alfred_test_project.alfred_dir / "personas").exists()
    assert (alfred_test_project.alfred_dir / "templates").exists()
    
    # Verify workspace directory structure
    workspace_dir = alfred_test_project.alfred_dir / "workspace"
    assert workspace_dir.exists()
    
    # Verify we're not creating or modifying the actual .alfred directory
    actual_alfred_dir = Path.cwd() / ".alfred"
    assert not actual_alfred_dir.exists() or not (actual_alfred_dir / "test-created-marker").exists()


def test_task_file_operations(alfred_test_project: AlfredTestProject):
    """Test that task file operations work correctly in the test environment."""
    # Initialize the project first
    alfred_test_project.initialize()
    
    # Create a test task
    test_task = Task(
        task_id="TEST-001",
        task_status=TaskStatus.NEW,
        title="Test task for harness verification",
        context="This is a test task to verify the testing harness works correctly.",
        implementation_details="Simple verification task for testing the harness functionality."
    )
    
    # Save the task using the test project
    alfred_test_project.create_task_file(test_task)
    
    # Verify the task file was created in the correct location
    expected_task_file = alfred_test_project.settings.workspace_dir / "TEST-001" / "task.json"
    assert expected_task_file.exists()
    
    # Load the task back and verify it's correct
    loaded_task = alfred_test_project.load_task("TEST-001")
    assert loaded_task is not None
    assert loaded_task.task_id == "TEST-001"
    assert loaded_task.title == "Test task for harness verification"
    assert loaded_task.task_status == TaskStatus.NEW


def test_isolation_between_tests(alfred_test_project: AlfredTestProject):
    """Test that each test gets its own isolated environment."""
    # Initialize and create a task
    alfred_test_project.initialize()
    
    test_task = Task(
        task_id="ISOLATION-TEST",
        task_status=TaskStatus.IN_DEVELOPMENT,
        title="Isolation test task",
        context="This task tests isolation between test runs.",
        implementation_details="Verification that each test gets its own environment."
    )
    
    alfred_test_project.create_task_file(test_task)
    
    # Verify the task exists
    loaded_task = alfred_test_project.load_task("ISOLATION-TEST")
    assert loaded_task is not None
    assert loaded_task.task_id == "ISOLATION-TEST"
    
    # This test should pass even if run multiple times, proving isolation


def test_artifact_path_resolution(alfred_test_project: AlfredTestProject):
    """Test that artifact paths are resolved correctly."""
    alfred_test_project.initialize()
    
    # Test artifact path resolution
    artifact_path = alfred_test_project.get_artifact_path("TEST-TASK", "test_artifact.md")
    
    # Verify the path structure
    expected_path = alfred_test_project.settings.workspace_dir / "TEST-TASK" / "artifacts" / "test_artifact.md"
    assert artifact_path == expected_path
    
    # Verify it's within the test directory
    assert str(artifact_path).startswith(str(alfred_test_project.root))
    assert ".alfred-test" in str(artifact_path)