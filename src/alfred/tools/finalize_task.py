from typing import Optional, Any

from src.alfred.models.schemas import ToolResponse, TaskStatus, Task
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import BaseWorkflowTool, FinalizeTaskTool, FinalizeTaskState
from src.alfred.core.prompter import generate_prompt
from src.alfred.constants import ToolName
from src.alfred.tools.base_tool_handler import BaseToolHandler

logger = get_logger(__name__)


class FinalizeTaskHandler(BaseToolHandler):
    """Handler for the finalize_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.FINALIZE_TASK,
            tool_class=FinalizeTaskTool,
            required_status=TaskStatus.READY_FOR_FINALIZATION,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate FinalizeTaskTool."""
        return FinalizeTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Loads test results and dispatches the tool to the 'finalizing' state."""
        if tool_instance.state == FinalizeTaskState.DISPATCHING.value:
            task_state = state_manager.load_or_create(task.task_id)

            # Load test results if available
            test_results = task_state.completed_tool_outputs.get(ToolName.TEST_TASK)
            if test_results:
                tool_instance.context_store["test_results"] = test_results

            # Dispatch to finalizing state
            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


finalize_task_handler = FinalizeTaskHandler()


async def finalize_task_impl(task_id: str) -> ToolResponse:
    """Finalize task entry point - handles the completion phase"""
    return await finalize_task_handler.execute(task_id)
