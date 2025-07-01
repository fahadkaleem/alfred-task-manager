# src/alfred/tools/review_task.py
"""Review task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
review_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.REVIEW_TASK])


async def review_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the review_task tool."""
    return await review_task_handler.execute(task_id)
