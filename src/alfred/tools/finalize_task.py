"""Finalize task implementation."""

from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName

# Get the handler from factory
finalize_task_handler = get_tool_handler(ToolName.FINALIZE_TASK)


async def finalize_task_impl(task_id: str) -> ToolResponse:
    """Finalize task entry point - handles the completion phase"""
    return await finalize_task_handler.execute(task_id)
