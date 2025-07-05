# src/alfred/tools/start_task.py
"""Implementation of the start_task logic."""

from alfred.lib.structured_logger import get_logger
from alfred.lib.task_utils import load_task
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.state.manager import state_manager

logger = get_logger(__name__)


def start_task_impl(task_id: str) -> ToolResponse:
    """
    Simple task start using stateless design.

    This function has been simplified to use the stateless workflow pattern.
    The actual workflow management is handled by GenericWorkflowHandler.
    """
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    task_state = state_manager.load_or_create(task_id)

    # Check if task is already started
    if task_state.active_tool_state:
        return ToolResponse(
            status="error",
            message=f"Task '{task_id}' already has an active workflow: {task_state.active_tool_state.tool_name}. Use `alfred.work_on_task('{task_id}')` to continue the current workflow.",
        )

    # Check task status
    if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
        return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. start_task can only be used on tasks with 'new' or 'planning' status.")

    # Note: The actual workflow creation is handled by the tool registry and GenericWorkflowHandler
    # This function just validates that the task can be started

    return ToolResponse(
        status="success",
        message=f"Task '{task_id}' is ready to start. Use the appropriate workflow tool to begin.",
        next_prompt=f"Call `alfred.work_on_task('{task_id}')` to begin working on this task.",
    )
