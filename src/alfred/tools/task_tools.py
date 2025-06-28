"""
Tools for core task management, like starting and stopping tasks.
"""

from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator


def begin_task(task_id: str) -> ToolResponse:
    """
    Initializes a new task in the Alfred workflow or resumes an existing task
    from its current state.
    """
    message, next_prompt = orchestrator.begin_task(task_id)

    if next_prompt is None:
        return ToolResponse(status="error", message=message)

    return ToolResponse(
        status="success",
        message=message,
        next_prompt=next_prompt,
    )


def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a completed work artifact for the current phase of a task.
    """
    message, next_prompt = orchestrator.submit_work_for_task(task_id, artifact)

    if next_prompt is None:
        return ToolResponse(status="error", message=message)

    return ToolResponse(
        status="success",
        message=message,
        next_prompt=next_prompt,
    )
