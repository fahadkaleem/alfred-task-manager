# src/alfred/tools/test_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, TestTaskTool, TestTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class TestTaskHandler(BaseToolHandler):
    """Handler for the test_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.TEST_TASK,
            tool_class=TestTaskTool,
            required_status=TaskStatus.READY_FOR_TESTING,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate TestTaskTool."""
        return TestTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Dispatches the tool to the 'testing' state."""
        if tool_instance.state == TestTaskState.DISPATCHING.value:
            # Load context from the original task definition for verification steps
            tool_instance.context_store["ac_verification_steps"] = getattr(task, "ac_verification_steps", [])

            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


test_task_handler = TestTaskHandler()
