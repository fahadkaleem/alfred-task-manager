# src/alfred/tools/request_revision.py
from alfred.tools.provide_review_logic import provide_review_logic
from alfred.models.schemas import ToolResponse


async def request_revision_impl(task_id: str, feedback_notes: str) -> ToolResponse:
    """Requests revisions for the work in the current review step."""
    return await provide_review_logic(task_id=task_id, is_approved=False, feedback_notes=feedback_notes)
