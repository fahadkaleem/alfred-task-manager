"""
Initialization tool for Epic Task Manager.

This module provides the interactive initialize_project tool that sets up the
.epictaskmanager directory with provider-specific configuration.
"""

from pathlib import Path
import shutil

from epic_task_manager.config.config_manager import ConfigManager
from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.exceptions import InitializationError
from epic_task_manager.models.config import TaskSource
from epic_task_manager.models.core import StateFile
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
config_manager = ConfigManager()


async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initialize Epic Task Manager with provider selection.

    Args:
        provider: Provider choice ('atlassian', 'linear', or 'local'). If None, returns available choices.

    Returns:
        ToolResponse: Standardized response object.
    """
    # Check if already initialized
    if _is_already_initialized():
        return _create_already_initialized_response()

    # Return choices if no provider specified
    if provider is None:
        return _get_provider_choices_response()

    try:
        # Validate and perform initialization
        provider_choice = _validate_provider_choice(provider)
        return await _perform_initialization(provider_choice)

    except KeyboardInterrupt:
        return ToolResponse(status=STATUS_ERROR, message="Initialization cancelled by user.")
    except (InitializationError, FileNotFoundError, PermissionError, OSError) as e:
        return ToolResponse(
            status=STATUS_ERROR,
            message=f"Failed to initialize project. Error: {e}",
        )


def _is_already_initialized() -> bool:
    """Check if project is already initialized."""
    etm_dir = settings.epic_task_manager_dir
    return etm_dir.exists() and settings.config_file.exists()


def _create_already_initialized_response() -> ToolResponse:
    """Create response for already initialized project."""
    etm_dir = settings.epic_task_manager_dir
    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Project already initialized at '{etm_dir}'. No changes were made.",
    )


def _get_provider_choices_response() -> ToolResponse:
    """Return provider choices for client to prompt user."""
    choices_data = {
        "choices": [
            {
                "value": "atlassian",
                "label": "Jira (requires Atlassian MCP server)",
                "description": "Connect to Jira for task management via MCP",
            },
            {
                "value": "linear",
                "label": "Linear (requires Linear MCP server)",
                "description": "Connect to Linear for task management via MCP",
            },
            {
                "value": "local",
                "label": "Local markdown files",
                "description": "Use local .md files for task definitions",
            },
        ],
        "prompt": "How will you be sourcing your tasks?",
    }
    return ToolResponse(
        status="choices_needed",
        message="Please select a task source provider.",
        data=choices_data,
    )


def _validate_provider_choice(provider: str) -> str:
    """Validate and normalize provider choice."""
    provider_choice = provider.lower()
    if provider_choice not in ["atlassian", "linear", "local"]:
        raise InitializationError(f"Invalid provider '{provider}'. Must be 'atlassian', 'linear', or 'local'.")
    return provider_choice


async def _perform_initialization(provider_choice: str) -> ToolResponse:
    """Perform the actual initialization setup."""
    # Create directories
    _create_project_directories()

    # Copy default templates to user workspace
    _copy_default_templates()

    # Setup provider-specific configuration
    if provider_choice == "atlassian":
        result = _setup_jira_provider()
        if not result["success"]:
            return ToolResponse(status=STATUS_ERROR, message=result["message"])
    elif provider_choice == "linear":
        result = _setup_linear_provider()
        if not result["success"]:
            return ToolResponse(status=STATUS_ERROR, message=result["message"])
    elif provider_choice == "local":
        _setup_local_provider()

    # Create initial state
    state_manager._save_state_file(StateFile())

    etm_dir = settings.epic_task_manager_dir
    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Successfully initialized Epic Task Manager project in '{etm_dir}' with {provider_choice} provider.",
    )


def _create_project_directories() -> None:
    """Create the necessary project directories."""
    etm_dir = settings.epic_task_manager_dir
    etm_dir.mkdir(exist_ok=True)
    settings.workspace_dir.mkdir(exist_ok=True)

    # Create the architectural documentation README
    _create_workspace_readme(etm_dir)


def _copy_default_templates() -> None:
    """Copy default templates to user workspace for customization."""
    source_dir = settings.templates_dir
    dest_dir = settings.prompts_dir

    try:
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
    except (OSError, shutil.Error) as e:
        raise InitializationError(f"Failed to copy templates: {e}")


def _setup_jira_provider() -> dict:
    """Setup Jira provider with MCP connectivity check"""
    if config_manager.validate_mcp_availability(TaskSource.ATLASSIAN):
        config_manager.setup_provider_config(TaskSource.ATLASSIAN, {"connection_method": "mcp"})
        return {"success": True}
    return {
        "success": False,
        "message": "Could not connect to the Atlassian MCP server. Please ensure it is running and accessible.",
    }


def _setup_linear_provider() -> dict:
    """Setup Linear provider with MCP connectivity check"""
    if config_manager.validate_mcp_availability(TaskSource.LINEAR):
        config_manager.setup_provider_config(TaskSource.LINEAR, {"connection_method": "mcp"})
        return {"success": True}
    return {
        "success": False,
        "message": "Could not connect to the Linear MCP server. Please ensure it is running and accessible.",
    }


def _setup_local_provider() -> None:
    """Setup local provider with tasks inbox and README"""
    settings.tasks_inbox_dir.mkdir(exist_ok=True)
    readme_path = settings.tasks_inbox_dir / "README.md"
    readme_content = "# Local Task Files\n\nThis directory is your task inbox for Epic Task Manager."
    readme_path.write_text(readme_content, encoding="utf-8")
    config_manager.setup_provider_config(TaskSource.LOCAL)


def _create_workspace_readme(etm_dir: Path) -> None:
    """Create architectural documentation README in the workspace root."""
    readme_path = etm_dir / "README.md"
    readme_content = """# Epic Task Manager Workspace

This directory contains all data for the Epic Task Manager.

## Directory Structure

- **`workspace/`**: Contains the live, work-in-progress data for each active task.
  - **`{task_id}/`**: A dedicated directory for each task.
  - **`{task_id}/scratchpad.md`**: The live "whiteboard" for the current phase. All work is appended here.
  - **`{task_id}/archive/`**: The immutable, historical record of a task. Once a phase is completed, its final artifact is stored here.

- **`tasks/`**: (For "local" mode only) The inbox for new task definitions written in Markdown.

- **`prompts/`**: Contains local overrides for the AI's prompt templates. You can customize these files to change the AI's behavior and personality.

- **`config.json`**: The main configuration file for the project.

- **`state.json`**: The internal state file for all tasks. **Do not edit this file manually unless you are recovering from a critical error.**

## The `03-planning.json` Artifact

You may notice a `03-planning.json` file in the `archive` directory alongside the standard `.md` files. This is intentional and critical for system stability.

-   The `03-planning.md` file is the **human-readable** log of the planning process.
-   The `03-planning.json` file is the **machine-readable** final execution plan.

The `coding` phase reads this `.json` file directly to ensure that it executes the approved plan with perfect fidelity. This prevents errors that could arise from misinterpreting the markdown file.
"""
    readme_path.write_text(readme_content, encoding="utf-8")
