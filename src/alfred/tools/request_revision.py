# src/alfred/tools/request_revision.py
from alfred.tools.provide_review_logic import provide_review_logic
from alfred.models.schemas import ToolResponse


# New logic function for GenericWorkflowHandler
async def request_revision_logic(task_id: str, feedback_notes: str, **kwargs) -> ToolResponse:
    """Logic function for request_revision compatible with GenericWorkflowHandler."""
    return await provide_review_logic(task_id=task_id, is_approved=False, feedback_notes=feedback_notes)


# Legacy request_revision_impl function removed - now using request_revision_logic with GenericWorkflowHandler
