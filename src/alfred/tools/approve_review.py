# src/alfred/tools/approve_review.py
from alfred.tools.provide_review_logic import provide_review_logic
from alfred.models.schemas import ToolResponse


async def approve_review_impl(task_id: str) -> ToolResponse:
    """Approves the work for the current review step."""
    return await provide_review_logic(task_id=task_id, is_approved=True)
