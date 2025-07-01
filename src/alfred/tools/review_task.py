# src/alfred/tools/review_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, ReviewTaskTool, ReviewTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ReviewTaskHandler(BaseToolHandler):
    """Handler for the review_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.REVIEW_TASK,
            tool_class=ReviewTaskTool,
            required_status=TaskStatus.READY_FOR_REVIEW,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate ReviewTaskTool."""
        return ReviewTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Dispatches the tool to the 'reviewing' state."""
        # Guard against incorrect status
        if task.task_status != TaskStatus.READY_FOR_REVIEW and tool_instance.state == ReviewTaskState.DISPATCHING.value:
            logger.warning(f"Task {task.task_id} is not in READY_FOR_REVIEW status. Current status: {task.task_status}")
            return ToolResponse(status="error", message=f"Task '{task.task_id}' must be in READY_FOR_REVIEW status to start review.")

        if tool_instance.state == ReviewTaskState.DISPATCHING.value:
            # Load context from the previous (implementation) phase
            task_state = state_manager.load_or_create(task.task_id)
            implementation_manifest = task_state.completed_tool_outputs.get(ToolName.IMPLEMENT_TASK)

            if not implementation_manifest:
                logger.warning(f"Implementation manifest not found for task '{task.task_id}'. Review may lack context.")

            tool_instance.context_store["implementation_manifest"] = implementation_manifest

            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


review_task_handler = ReviewTaskHandler()
