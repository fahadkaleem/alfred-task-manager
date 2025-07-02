"""Review task implementation."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.tool_factory import get_tool_handler
from src.alfred.constants import ToolName

# Get the handler from factory
review_task_handler = get_tool_handler(ToolName.REVIEW_TASK)


async def review_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the review_task tool."""
    return await review_task_handler.execute(task_id)
