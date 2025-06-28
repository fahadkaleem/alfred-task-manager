"""
Tools for managing progress within a multi-step persona workflow.
"""

from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator


def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """
    Marks a single execution step as complete and returns the prompt for the next step.
    This is the core checkpoint tool for the developer persona.
    """
    message, next_prompt = orchestrator.process_step_completion(task_id, step_id)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)
