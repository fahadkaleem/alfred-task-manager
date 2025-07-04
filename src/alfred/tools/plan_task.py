"""Discovery planning tool implementation."""

from typing import Optional, Dict, Any
from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName


async def plan_task_impl(task_id: str, restart_context: Optional[Dict[str, Any]] = None) -> ToolResponse:
    """Implementation logic for the discovery planning tool.

    Args:
        task_id: The unique identifier for the task to plan
        restart_context: Optional context for re-planning scenarios

    Returns:
        ToolResponse with next action guidance
    """
    # Get the handler from factory (uses GenericWorkflowHandler)
    handler = get_tool_handler(ToolName.PLAN_TASK)

    # Execute with restart context if provided
    if restart_context:
        return await handler.execute(task_id=task_id, restart_context=restart_context)
    else:
        return await handler.execute(task_id=task_id)
