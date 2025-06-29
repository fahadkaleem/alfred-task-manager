# src/alfred/tools/progress.py
"""
Progress tracking tools for Alfred workflow system.
"""
from src.alfred.lib.logger import get_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """Marks a specific subtask as complete during the implementation phase."""
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    execution_plan_artifact = active_tool.context_store.get("execution_plan_artifact")
    if not execution_plan_artifact:
        return ToolResponse(status="error", message="No execution plan found in context.")

    # Note: Pydantic models in context are stored as dicts after deserialization
    execution_plan = execution_plan_artifact.get("subtasks", [])
    valid_subtask_ids = {subtask["subtask_id"] for subtask in execution_plan}
    if subtask_id not in valid_subtask_ids:
        return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'.")

    completed_subtasks = set(active_tool.context_store.get("completed_subtasks", []))
    if subtask_id in completed_subtasks:
        return ToolResponse(status="success", message=f"Subtask '{subtask_id}' already marked complete.")

    completed_subtasks.add(subtask_id)
    active_tool.context_store["completed_subtasks"] = list(completed_subtasks)

    # --- THIS IS THE FIX ---
    # Use the correct, unified state manager method.
    state_manager.update_tool_state(task_id, active_tool)
    # --- END FIX ---

    completed_count = len(completed_subtasks)
    total_subtasks = len(valid_subtask_ids)
    progress = (completed_count / total_subtasks) * 100 if total_subtasks > 0 else 0
    message = f"Acknowledged: Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_subtasks} ({progress:.0f}%)."
    logger.info(message)

    return ToolResponse(
        status="success",
        message=message,
        data={
            "completed_count": completed_count,
            "total_count": total_subtasks,
            "progress_percentage": progress,
        },
    )