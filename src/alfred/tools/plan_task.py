"""Plan task implementation."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.tool_factory import get_tool_handler
from src.alfred.constants import ToolName

# Get the handler from factory
plan_task_handler = get_tool_handler(ToolName.PLAN_TASK)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool."""
    return await plan_task_handler.execute(task_id)
