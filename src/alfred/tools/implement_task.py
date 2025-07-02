"""Implement task implementation."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.tool_factory import get_tool_handler
from src.alfred.constants import ToolName

# Get the handler from factory
implement_task_handler = get_tool_handler(ToolName.IMPLEMENT_TASK)


async def implement_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the implement_task tool."""
    return await implement_task_handler.execute(task_id)
