# src/alfred/tools/progress.py
"""
Progress tracking tools for Alfred workflow system.

Provides functionality to track subtask completion during implementation phase.
"""

from typing import Set

from src.alfred.lib.logger import get_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.core.workflow import BaseWorkflowTool

logger = get_logger(__name__)


def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """
    Marks a specific subtask as complete during the implementation phase.

    This function:
    1. Verifies an active tool exists for the task
    2. Checks if the subtask_id is valid for the current execution plan
    3. Tracks completed subtasks in the tool's context_store
    4. Persists the updated state

    Args:
        task_id: The unique identifier for the task
        subtask_id: The subtask identifier to mark as complete (e.g., "subtask-1")

    Returns:
        ToolResponse: Success/error status with appropriate message
    """
    # Check if there's an active tool for this task
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'. Cannot mark subtask complete.")

    active_tool = orchestrator.active_tools[task_id]

    # Get the execution plan from context store if available
    execution_plan = active_tool.context_store.get("execution_plan_artifact")
    if not execution_plan:
        # Try alternative key names
        execution_plan = active_tool.context_store.get("generate_subtasks_artifact")

    if not execution_plan:
        return ToolResponse(status="error", message="No execution plan found in the active tool's context. Cannot validate subtask.")

    # Validate the subtask_id exists in the execution plan
    valid_subtask_ids = {subtask.subtask_id for subtask in execution_plan.subtasks}
    if subtask_id not in valid_subtask_ids:
        return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'. Valid subtask IDs are: {', '.join(sorted(valid_subtask_ids))}")

    # Initialize completed_subtasks set if it doesn't exist
    if "completed_subtasks" not in active_tool.context_store:
        active_tool.context_store["completed_subtasks"] = set()

    # Ensure completed_subtasks is a set (handle deserialization from JSON)
    completed_subtasks = active_tool.context_store["completed_subtasks"]
    if isinstance(completed_subtasks, list):
        completed_subtasks = set(completed_subtasks)
        active_tool.context_store["completed_subtasks"] = completed_subtasks

    # Check if already marked complete
    if subtask_id in completed_subtasks:
        return ToolResponse(status="success", message=f"Subtask '{subtask_id}' was already marked as complete.")

    # Mark the subtask as complete
    completed_subtasks.add(subtask_id)

    # Calculate progress
    total_subtasks = len(valid_subtask_ids)
    completed_count = len(completed_subtasks)
    progress_percentage = (completed_count / total_subtasks) * 100

    # Save the updated state
    try:
        state_manager.save_tool_state(task_id, active_tool)
        logger.info(f"Task {task_id}: Marked subtask '{subtask_id}' as complete. Progress: {completed_count}/{total_subtasks} ({progress_percentage:.1f}%)")

        # Build progress summary
        remaining_subtasks = valid_subtask_ids - completed_subtasks
        progress_message = f"Successfully marked subtask '{subtask_id}' as complete.\n\nProgress: {completed_count}/{total_subtasks} subtasks completed ({progress_percentage:.1f}%)\n"

        if remaining_subtasks:
            progress_message += f"Remaining subtasks: {', '.join(sorted(remaining_subtasks))}"
        else:
            progress_message += "All subtasks completed! 🎉"

        return ToolResponse(
            status="success",
            message=progress_message,
            data={
                "completed_count": completed_count,
                "total_count": total_subtasks,
                "progress_percentage": progress_percentage,
                "completed_subtasks": sorted(list(completed_subtasks)),
                "remaining_subtasks": sorted(list(remaining_subtasks)),
            },
        )

    except Exception as e:
        logger.error(f"Failed to save progress for task {task_id}: {e}")
        # Remove the subtask from completed set since save failed
        completed_subtasks.discard(subtask_id)

        return ToolResponse(status="error", message=f"Failed to save progress: {str(e)}")
