"""
Workflow utility functions using TOOL_DEFINITIONS.

This module provides workflow resolution functions that replace the obsolete
WorkflowConfiguration system with direct TOOL_DEFINITIONS lookups.
"""

from typing import Optional, Dict, Any

from alfred.models.schemas import TaskStatus


def get_tool_for_status(task_status: TaskStatus) -> Optional[str]:
    """Find tool that handles the given task status.

    Args:
        task_status: The current task status

    Returns:
        Tool name that can handle this status, or None if no tool found
    """
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    for tool_name, tool_def in TOOL_DEFINITIONS.items():
        if task_status in tool_def.entry_statuses:
            return tool_name
    return None


def get_phase_info(task_status: TaskStatus) -> Optional[Dict[str, Any]]:
    """Get phase information for a status from ToolDefinition.

    Args:
        task_status: The current task status

    Returns:
        Dictionary with phase info (status, tool_name, description, exit_status)
        or None if no matching tool found
    """
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    tool_def = next((td for td in TOOL_DEFINITIONS.values() if task_status in td.entry_statuses), None)
    if tool_def:
        return {"status": task_status, "tool_name": tool_def.name, "description": tool_def.description.strip(), "exit_status": tool_def.exit_status}
    return None


def is_terminal_status(task_status: TaskStatus) -> bool:
    """Check if status is terminal (TaskStatus.DONE).

    Args:
        task_status: The task status to check

    Returns:
        True if status is TaskStatus.DONE, False otherwise
    """
    return task_status == TaskStatus.DONE


def get_next_status(current_status: TaskStatus) -> Optional[TaskStatus]:
    """Get next status from current tool's exit_status.

    Args:
        current_status: The current task status

    Returns:
        Next TaskStatus from tool's exit_status, or None if no tool found
    """
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    tool_def = next((td for td in TOOL_DEFINITIONS.values() if current_status in td.entry_statuses), None)
    return tool_def.exit_status if tool_def else None
