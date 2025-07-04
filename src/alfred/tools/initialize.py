"""
Initialization tool for Alfred.

This module provides the interactive initialize_project tool that sets up the
.alfred directory with provider-specific configuration.
"""

import logging
from pathlib import Path
import shutil

from alfred.config.manager import ConfigManager
from alfred.config.settings import settings
from alfred.constants import ResponseStatus
from alfred.models.alfred_config import TaskProvider
from alfred.models.schemas import ToolResponse

logger = logging.getLogger(__name__)


def initialize_project(provider: str | None = None, test_dir: Path | None = None) -> ToolResponse:
    """Initialize Alfred with provider selection.

    Args:
        provider: Provider choice ('jira', 'linear', or 'local'). If None, returns available choices.
        test_dir: Optional test directory for testing purposes. If provided, will use this instead of settings.alfred_dir.

    Returns:
        ToolResponse: Standardized response object.
    """
    alfred_dir = test_dir if test_dir is not None else settings.alfred_dir

    # Check if already initialized
    if _is_already_initialized(alfred_dir):
        return _create_already_initialized_response(alfred_dir)

    # Return choices if no provider specified
    if provider is None:
        return _get_provider_choices_response()

    try:
        # Validate and perform initialization
        provider_choice = _validate_provider_choice(provider)
        return _perform_initialization(provider_choice, alfred_dir)

    except KeyboardInterrupt:
        return ToolResponse(status=ResponseStatus.ERROR, message="Initialization cancelled by user.")
    except (OSError, shutil.Error, ValueError) as e:
        return ToolResponse(
            status=ResponseStatus.ERROR,
            message=f"Failed to initialize project. Error: {e}",
        )


def _is_already_initialized(alfred_dir: Path) -> bool:
    """Check if project is already initialized."""
    return alfred_dir.exists() and (alfred_dir / "config.yml").exists()


def _create_already_initialized_response(alfred_dir: Path) -> ToolResponse:
    """Create response for already initialized project."""
    return ToolResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Project already initialized at '{alfred_dir}'. No changes were made.",
    )


def _get_provider_choices_response() -> ToolResponse:
    """Return provider choices for client to prompt user."""
    choices_data = {
        "choices": [
            {
                "value": "jira",
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
    if provider_choice not in ["jira", "linear", "local"]:
        msg = f"Invalid provider '{provider}'. Must be 'jira', 'linear', or 'local'."
        raise ValueError(msg)
    return provider_choice


def _perform_initialization(provider_choice: str, alfred_dir: Path) -> ToolResponse:
    """Perform the actual initialization setup."""
    # Create directories
    _create_project_directories(alfred_dir)

    # Copy default config file
    _copy_config_file(alfred_dir)

    # Setup provider-specific configuration
    result = _setup_provider_configuration(provider_choice, alfred_dir)
    if result["status"] == ResponseStatus.ERROR:
        return ToolResponse(status=ResponseStatus.ERROR, message=result["message"])

    return ToolResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Successfully initialized Alfred project in '{alfred_dir}' with {provider_choice} provider.",
    )


def _create_project_directories(alfred_dir: Path) -> None:
    """Create the necessary project directories."""
    alfred_dir.mkdir(parents=True, exist_ok=True)
    (alfred_dir / "workspace").mkdir(exist_ok=True)
    (alfred_dir / "specs").mkdir(exist_ok=True)
    (alfred_dir / "tasks").mkdir(exist_ok=True)
    logger.info(f"Created project directories at {alfred_dir}")


def _copy_config_file(alfred_dir: Path) -> None:
    """Copy the default config file."""
    config_file = alfred_dir / settings.config_filename
    shutil.copyfile(settings.packaged_config_file, config_file)
    logger.info(f"Copied config file to {config_file}")


def _setup_provider_configuration(provider_choice: str, alfred_dir: Path) -> dict:
    """Setup provider-specific configuration."""
    config_manager = ConfigManager(alfred_dir)

    if provider_choice == "jira":
        return _setup_jira_provider(config_manager, alfred_dir)
    if provider_choice == "linear":
        return _setup_linear_provider(config_manager, alfred_dir)
    if provider_choice == "local":
        return _setup_local_provider(config_manager, alfred_dir)

    return {"status": ResponseStatus.ERROR, "message": f"Unknown provider: {provider_choice}"}


def _setup_jira_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup Jira provider with MCP connectivity check."""
    if _validate_mcp_connectivity("jira"):
        config = config_manager.create_default()
        config.provider.type = TaskProvider.JIRA
        config_manager.save(config)
        _setup_provider_resources("jira", alfred_dir)
        logger.info("Configured Jira provider")
        return {"status": ResponseStatus.SUCCESS}
    return {
        "status": ResponseStatus.ERROR,
        "message": "Could not connect to the Atlassian MCP server. Please ensure it is running and accessible.",
    }


def _setup_linear_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup Linear provider with MCP connectivity check."""
    if _validate_mcp_connectivity("linear"):
        config = config_manager.create_default()
        config.provider.type = TaskProvider.LINEAR
        config_manager.save(config)
        _setup_provider_resources("linear", alfred_dir)
        logger.info("Configured Linear provider")
        return {"status": ResponseStatus.SUCCESS}
    return {
        "status": ResponseStatus.ERROR,
        "message": "Could not connect to the Linear MCP server. Please ensure it is running and accessible.",
    }


def _setup_local_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup local provider with tasks inbox and README."""
    # Create configuration
    config = config_manager.create_default()
    config.provider.type = TaskProvider.LOCAL
    config_manager.save(config)

    # Setup provider resources
    _setup_provider_resources("local", alfred_dir)

    logger.info("Configured local provider")
    return {"status": ResponseStatus.SUCCESS}


def _setup_provider_resources(provider: str, alfred_dir: Path) -> None:
    """Setup provider-specific resources."""
    # Always create tasks directory for cache-first architecture
    tasks_dir = alfred_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    # Create README with provider-specific content
    readme_path = tasks_dir / "README.md"

    if provider == "local":
        readme_content = """# Local Task Files

This directory is your task inbox for Alfred.

## Creating Tasks

Create markdown files in this directory with the following format:

```markdown
# TASK-ID

## Summary
Brief summary of the task

## Description
Detailed description of what needs to be done

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

When you run `work_on("TASK-ID")`, Alfred will read the corresponding file and start the workflow.
"""
    else:
        # For Jira/Linear providers
        readme_content = f"""# Alfred Task Cache

This directory contains the local markdown representation of all tasks Alfred is aware of.

Since you're using the **{provider}** provider, this directory acts as a local cache. Tasks are fetched from {provider.capitalize()} and stored here before being worked on.

## Task Format

All cached tasks follow the same markdown format:

```markdown
# TASK-ID

## Summary
Brief summary of the task

## Description
Detailed description of what needs to be done

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

Tasks will be automatically cached here when you work on them using `work_on("TASK-ID")`.
"""

    readme_path.write_text(readme_content, encoding="utf-8")
    logger.info(f"Created {provider} provider resources at {tasks_dir}")


def _validate_mcp_connectivity(provider: str) -> bool:
    """Check if required MCP tools are available for the given provider.

    This is a placeholder for actual MCP connectivity validation.
    In a production system, this would attempt to call MCP tools
    to verify they are available and responding.
    """
    # TODO: Implement actual MCP tool availability check
    # For now, we'll simulate the check and return True
    logger.info(f"Simulating MCP connectivity check for {provider} provider")
    return True
