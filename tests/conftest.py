# tests/conftest.py
import pytest
import os
import shutil
import uuid
import logging
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

from src.alfred.tools.initialize import initialize_project
from src.alfred.models.schemas import Task
from src.alfred.lib.task_utils import save_task_state, load_task
from src.alfred.config.settings import Settings


@pytest.fixture(autouse=True)
def mock_logging_for_tests():
    """Mock only the specific logging setup that creates files during tests."""
    # Only mock the setup_task_logging function to prevent file creation
    with patch('src.alfred.lib.logger.setup_task_logging'), \
         patch('src.alfred.lib.logger.cleanup_task_logging'):
        yield


class AlfredTestProject:
    """A helper class to manage a temporary Alfred project for testing."""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.alfred_dir = self.root / ".alfred-test"
        # Create a test-specific settings instance
        self.settings = Settings(
            project_root=self.root,
            alfred_dir_name=".alfred-test"
        )
    
    def initialize(self, provider: str = "local"):
        """Initialize the test project with the specified provider."""
        result = initialize_project(provider, test_dir=self.alfred_dir)
        return result
    
    def create_task_file(self, task: Task):
        """Create a task markdown file in the test workspace."""
        # Create the tasks directory
        tasks_dir = self.alfred_dir / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the markdown file
        task_file = tasks_dir / f"{task.task_id}.md"
        markdown_content = f"""# TASK: {task.task_id}

## Title
{task.title}

## Context
{task.context}

## Implementation Details
{task.implementation_details}
"""
        
        if task.dev_notes:
            markdown_content += f"""
## Dev Notes
{task.dev_notes}
"""
        
        if task.acceptance_criteria:
            markdown_content += "\n## Acceptance Criteria\n"
            for criterion in task.acceptance_criteria:
                markdown_content += f"- {criterion}\n"
        
        if task.ac_verification_steps:
            markdown_content += "\n## AC Verification\n"
            for step in task.ac_verification_steps:
                markdown_content += f"- {step}\n"
        
        task_file.write_text(markdown_content)
        
        # Save the task state using the test project's settings
        from unittest.mock import patch
        with patch('src.alfred.lib.task_utils.settings', self.settings):
            save_task_state(task.task_id, task.task_status, self.root)
    
    def load_task(self, task_id: str) -> Task | None:
        """Load a task from the test workspace."""
        # Use the test project's settings by patching during the load
        from unittest.mock import patch
        with patch('src.alfred.lib.task_utils.settings', self.settings):
            return load_task(task_id, self.root)
    
    def get_task_state(self, task_id: str) -> Task | None:
        """Helper to get the current task state."""
        return self.load_task(task_id)
    
    def get_artifact_path(self, task_id: str, artifact_name: str) -> Path:
        """Get the path to an artifact within the test workspace."""
        return self.settings.workspace_dir / task_id / "artifacts" / artifact_name
    
    def run_tool(self, tool_name: str, **kwargs):
        """Helper to run a tool with test-specific settings."""
        # This would need to be implemented based on how tools are structured
        # For now, this is a placeholder
        raise NotImplementedError("Tool running not yet implemented in test harness")


@pytest.fixture
def alfred_test_project(request) -> Generator[AlfredTestProject, None, None]:
    """Pytest fixture to create and manage an isolated Alfred project for a test."""
    # Create temp directory within the current working directory's test structure
    current_working_dir = Path.cwd()
    temp_data_dir = current_working_dir / "tests" / "temp_data"
    temp_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create unique test directory using test name and UUID
    test_name = request.node.name
    unique_id = str(uuid.uuid4())[:8]
    test_dir_name = f"{test_name}_{unique_id}"
    test_temp_dir = temp_data_dir / test_dir_name
    test_temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Store original working directory
    original_cwd = Path.cwd()
    
    # Change to test directory
    os.chdir(test_temp_dir)
    
    # Create test project
    test_project = AlfredTestProject(test_temp_dir)
    test_project.test_dir_name = test_dir_name  # Store for easy identification
    
    yield test_project
    
    # Restore original working directory
    os.chdir(original_cwd)
    
    # Optional: Clean up test directory (comment this out to keep test data for inspection)
    # Set ALFRED_KEEP_TEST_DATA=1 environment variable to keep test directories
    if not os.getenv("ALFRED_KEEP_TEST_DATA"):
        shutil.rmtree(test_temp_dir, ignore_errors=True)