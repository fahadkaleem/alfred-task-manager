"""
Pytest configuration for Epic Task Manager tests
"""

from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch

import pytest

from epic_task_manager.config.settings import Settings


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_epic_task_manager_dir(temp_dir, monkeypatch):
    """Mock the epic_task_manager directory to use temp dir"""
    epic_task_manager_dir = temp_dir / ".epictaskmanager"
    epic_task_manager_dir.mkdir()

    # Import settings and patch the project root
    from src.epic_task_manager.config.settings import settings

    # Patch the project_root to point to temp_dir
    monkeypatch.setattr(settings, "project_root", temp_dir)

    # Create subdirectories
    (epic_task_manager_dir / "contexts").mkdir()
    (epic_task_manager_dir / "prompts").mkdir()

    return epic_task_manager_dir


@pytest.fixture
def epic_task_manager_dir():
    """Provides a temporary directory for epic task manager tests"""
    with tempfile.TemporaryDirectory() as temp_dir:
        epic_task_manager_dir = Path(temp_dir) / ".epictaskmanager"
        epic_task_manager_dir.mkdir(parents=True, exist_ok=True)
        yield epic_task_manager_dir


@pytest.fixture(scope="function")
def temp_test_dir():
    """Create a temporary test directory for each test function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="function")
def isolated_epic_settings(temp_test_dir):
    """Create isolated Epic Task Manager settings for testing."""
    # Create a completely new Settings instance with isolated project_root
    test_settings = Settings()
    # Override the project_root to point to our test directory
    test_settings.__dict__["project_root"] = temp_test_dir

    # Create isolated singleton instances that use the test settings
    from epic_task_manager.config.config_manager import ConfigManager
    from epic_task_manager.execution.artifact_manager import ArtifactManager
    from epic_task_manager.execution.prompter import Prompter
    from epic_task_manager.state.manager import StateManager

    test_config_manager = ConfigManager(config_file=test_settings.config_file)
    test_state_manager = StateManager()
    test_state_manager.state_file_path = test_settings.state_file  # Override the captured path
    test_artifact_manager = ArtifactManager()
    test_prompter = Prompter()

    # Patch all modules that import settings
    patches = [
        patch("epic_task_manager.config.settings.settings", test_settings),
        patch("epic_task_manager.state.manager.settings", test_settings),
        patch("epic_task_manager.execution.artifact_manager.settings", test_settings),
        patch("epic_task_manager.tools.initialize.settings", test_settings),
        patch("epic_task_manager.tools.task_tools.settings", test_settings),
        patch("epic_task_manager.tools.review_tools.settings", test_settings),
        patch("epic_task_manager.tools.inspect_archived_artifact.settings", test_settings),
        patch("epic_task_manager.tools.get_task_summary.settings", test_settings),
        patch("epic_task_manager.resources.workflow_docs.settings", test_settings),
        patch("epic_task_manager.execution.prompter.settings", test_settings),
        patch("epic_task_manager.config.config_manager.settings", test_settings),
        # Patch singleton instances that capture settings paths at initialization
        patch("epic_task_manager.tools.initialize.config_manager", test_config_manager),
        patch("epic_task_manager.tools.initialize.state_manager", test_state_manager),
        patch("epic_task_manager.tools.task_tools.state_manager", test_state_manager),
        patch("epic_task_manager.tools.task_tools.artifact_manager", test_artifact_manager),
        patch("epic_task_manager.tools.task_tools.prompter", test_prompter),
        patch("epic_task_manager.tools.review_tools.state_manager", test_state_manager),
        patch("epic_task_manager.tools.review_tools.prompter", test_prompter),
        patch("epic_task_manager.config.config_manager.config_manager", test_config_manager),
    ]

    # Start all patches
    for p in patches:
        p.start()

    try:
        yield test_settings
    finally:
        # Stop all patches
        for p in patches:
            p.stop()


@pytest.fixture
def sample_task_id():
    """Standard test task ID."""
    return "TEST-123"


@pytest.fixture
def sample_task_data():
    """Sample task data for testing."""
    return {
        "task_summary": "Test Task Summary",
        "task_description": "This is a test task description for unit testing.",
        "acceptance_criteria": ["Criterion 1: Test functionality works", "Criterion 2: Error handling is proper", "Criterion 3: Documentation is complete"],
    }


@pytest.fixture(scope="function")
def initialized_project(isolated_epic_settings):
    """Create an initialized project for testing."""
    import asyncio

    from epic_task_manager.tools.initialize import initialize_project

    # Initialize with local provider
    result = asyncio.run(initialize_project(provider="local"))
    assert result.status == "success"

    return isolated_epic_settings
