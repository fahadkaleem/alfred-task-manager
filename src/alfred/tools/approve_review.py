# src/alfred/tools/approve_review.py
from alfred.tools.provide_review_logic import provide_review_logic
from alfred.models.schemas import ToolResponse


# New logic function for GenericWorkflowHandler
async def approve_review_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for approve_review compatible with GenericWorkflowHandler."""
    return await provide_review_logic(task_id=task_id, is_approved=True)


# Legacy approve_review_impl function removed - now using approve_review_logic with GenericWorkflowHandler
