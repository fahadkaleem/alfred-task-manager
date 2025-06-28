"""
Tools for handling the review cycle of a persona's work.
"""

from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator


def provide_review(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Approves or requests revisions on a work artifact, advancing the
    internal review state of the active persona.
    """
    message, next_prompt = orchestrator.process_review(task_id, is_approved, feedback_notes)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)


def approve_and_advance_stage(task_id: str) -> ToolResponse:
    """
    Approves the current sub-stage within a multi-stage persona (like Planning)
    and advances to the next sub-stage.
    """
    message, next_prompt = orchestrator.process_human_approval(task_id)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)


def approve_and_handoff(task_id: str) -> ToolResponse:
    """
    Gives final approval for a persona's work and hands the task off
    to the next persona in the workflow sequence.
    """
    message, next_prompt = orchestrator.process_handoff(task_id)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)
