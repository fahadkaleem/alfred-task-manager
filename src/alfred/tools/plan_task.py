# src/alfred/tools/plan_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, PlanTaskTool, PlanTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager


class PlanTaskHandler(BaseToolHandler):
    """Handler for the plan_task tool."""

    def __init__(self):
        # THIS IS THE FIX for Blocker #1
        super().__init__(
            tool_name=ToolName.PLAN_TASK,
            tool_class=PlanTaskTool,
            required_status=None,  # Validation is handled in _setup_tool
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate PlanTaskTool."""
        # PlanTaskTool does not require special args for its __init__
        return PlanTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Validate status and handle initial dispatch."""
        if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
            return ToolResponse(
                status="error",
                message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task.",
            )

        # Status update is now handled by BaseToolHandler via ToolRegistry

        # This is the crucial fix for Blocker #1.
        # If the tool is in its initial state, we perform no action,
        # as the initial prompt is already correct. The user will call
        # `submit_work` to advance it.
        if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value:
            # No dispatch needed, we are already in the correct starting state.
            pass

        return None


plan_task_handler = PlanTaskHandler()


# Keep the old implementation function for backward compatibility
async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool with unified state."""
    return await plan_task_handler.execute(task_id)
