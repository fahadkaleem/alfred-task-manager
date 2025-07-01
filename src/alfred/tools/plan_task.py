# src/alfred/tools/plan_task.py
"""Plan task implementation using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
plan_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.PLAN_TASK])


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool."""
    return await plan_task_handler.execute(task_id)
