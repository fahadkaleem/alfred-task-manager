"""
Initialization tool for Alfred.
"""

import shutil
from pathlib import Path

from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.models.alfred_config import AlfredConfig, ProviderConfig, TaskProvider
from src.alfred.models.schemas import ToolResponse


def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initializes the project workspace by creating the .alfred directory with
    provider-specific configuration.
    
    Args:
        provider: Provider choice ('jira', 'linear', or 'local'). If None, returns available choices.
        
    Returns:
        ToolResponse: Standardized response object.
    """
    alfred_dir = settings.alfred_dir
    
    # Check if already initialized
    if alfred_dir.exists() and (alfred_dir / "workflow.yml").exists():
        return ToolResponse(
            status="success", 
            message=f"Project already initialized at '{alfred_dir}'. No changes were made."
        )
    
    # Return choices if no provider specified
    if provider is None:
        return _get_provider_choices_response()
    
    try:
        # Validate provider choice
        provider_choice = _validate_provider_choice(provider)
        
        # Create base directory
        alfred_dir.mkdir(parents=True, exist_ok=True)

        # Copy default workflow file
        shutil.copyfile(settings.packaged_workflow_file, settings.workflow_file)

        # Copy default persona and template directories
        shutil.copytree(settings.packaged_personas_dir, alfred_dir / "personas")
        shutil.copytree(settings.packaged_templates_dir, alfred_dir / "templates")

        # Create configuration with selected provider
        config_manager = ConfigManager(alfred_dir)
        config = AlfredConfig(
            providers=ProviderConfig(task_provider=TaskProvider(provider_choice))
        )
        config_manager.save(config)
        
        # Setup provider-specific resources
        _setup_provider_resources(provider_choice, alfred_dir)

        return ToolResponse(
            status="success", 
            message=f"Successfully initialized Alfred project in '{alfred_dir}' with {provider_choice} provider."
        )
        
    except (OSError, shutil.Error) as e:
        return ToolResponse(
            status="error", 
            message=f"Failed to initialize project due to a file system error: {e}"
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
        raise ValueError(f"Invalid provider '{provider}'. Must be 'jira', 'linear', or 'local'.")
    return provider_choice


def _setup_provider_resources(provider: str, alfred_dir: Path) -> None:
    """Setup provider-specific resources."""
    if provider == "local":
        # Create tasks inbox for local provider
        tasks_dir = alfred_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        readme_path = tasks_dir / "README.md"
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

When you run `begin_task("TASK-ID")`, Alfred will read the corresponding file and start the workflow.
"""
        readme_path.write_text(readme_content, encoding="utf-8")