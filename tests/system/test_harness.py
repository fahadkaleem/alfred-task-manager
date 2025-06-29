# tests/system/test_harness.py
"""
System-level tests for the Alfred testing harness.
This file contains the specific test mentioned in AL-10 acceptance criteria.
"""
from pathlib import Path
from src.alfred.models.schemas import Task, TaskStatus
from tests.conftest import AlfredTestProject


def test_fixture_creates_isolated_environment(alfred_test_project: AlfredTestProject):
    """
    AC Verification test from AL-10:
    - Create a simple test that verifies the fixture creates an isolated environment
    - Call alfred_test_project.create_task_file(...)
    - Assert that the task.md file is created inside the temporary directory structure 
      (tmp_path/.alfred/workspace/...) and NOT in the main project's .alfred folder
    """
    # Initialize the test project
    alfred_test_project.initialize()
    
    # Create a test task
    test_task = Task(
        task_id="ISOLATION-VERIFY",
        task_status=TaskStatus.NEW,
        title="AL-10 Acceptance Criteria Test",
        context="This test verifies the AL-10 acceptance criteria for isolated test environments.",
        implementation_details="Ensures task files are created in test directory, not main project."
    )
    
    # Call alfred_test_project.create_task_file(...) as specified in AC
    alfred_test_project.create_task_file(test_task)
    
    # Assert that the task markdown file is created inside the temporary directory structure
    # The current implementation uses .alfred-test instead of .alfred
    expected_task_file = alfred_test_project.alfred_dir / "tasks" / "ISOLATION-VERIFY.md"
    assert expected_task_file.exists(), f"Task file should exist at {expected_task_file}"
    
    # Verify the file is in the temporary directory structure, not the main project
    assert str(expected_task_file).startswith(str(alfred_test_project.root))
    assert ".alfred-test" in str(expected_task_file)
    
    # Verify it's NOT in the main project's .alfred folder
    main_project_alfred = Path.cwd() / ".alfred"
    if main_project_alfred.exists():
        main_project_task_file = main_project_alfred / "tasks" / "ISOLATION-VERIFY.md"
        assert not main_project_task_file.exists(), "Task file should NOT be created in main project .alfred directory"
    
    # Additional verification: load the task back to ensure it's correct
    loaded_task = alfred_test_project.load_task("ISOLATION-VERIFY")
    assert loaded_task is not None
    assert loaded_task.task_id == "ISOLATION-VERIFY"
    assert loaded_task.title == "AL-10 Acceptance Criteria Test"
    assert loaded_task.task_status == TaskStatus.NEW