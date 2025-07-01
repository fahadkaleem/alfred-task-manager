# src/alfred/tools/implement_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, ImplementTaskTool, ImplementTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ImplementTaskHandler(BaseToolHandler):
    """Handler for the implement_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.IMPLEMENT_TASK,
            tool_class=ImplementTaskTool,
            required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate ImplementTaskTool."""
        return ImplementTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Loads the execution plan and dispatches the tool to the 'implementing' state."""
        # Use the Enum for comparison
        if tool_instance.state == ImplementTaskState.DISPATCHING.value:
            task_state = state_manager.load_or_create(task.task_id)
            execution_plan = task_state.completed_tool_outputs.get(ToolName.PLAN_TASK)

            if not execution_plan:
                return ToolResponse(
                    status="error", message=f"CRITICAL: Cannot start implementation. Execution plan from 'plan_task' not found for task '{task.task_id}'. Please run 'plan_task' first."
                )

            # Store as artifact_content so the prompter can convert it to artifact_json for templates
            tool_instance.context_store["artifact_content"] = execution_plan

            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


implement_task_handler = ImplementTaskHandler()


# Keep the old implementation function for backward compatibility
async def implement_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the implement_task tool."""
    return await implement_task_handler.execute(task_id)
