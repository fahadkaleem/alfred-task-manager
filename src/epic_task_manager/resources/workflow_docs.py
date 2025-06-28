"""
Workflow documentation resource
"""

from typing import Any

from epic_task_manager.config.settings import settings


async def get_workflow_documentation() -> dict[str, Any]:
    """
    Provide documentation about the workflow phases
    """
    return {
        "workflow_phases": settings.workflow_phases,
        "transitions": settings.phase_transitions,
        "description": {
            "retrieved": "Task has been fetched from Jira and is ready for planning",
            "planning": "Creating implementation plan and design decisions",
            "coding": "Implementing the solution according to the plan",
            "review": "Code review and quality checks",
            "complete": "Task is done and deployed",
        },
    }
