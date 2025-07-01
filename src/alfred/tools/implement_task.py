# src/alfred/tools/implement_task.py
"""Implement task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
implement_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.IMPLEMENT_TASK])


async def implement_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the implement_task tool."""
    return await implement_task_handler.execute(task_id)
