# src/alfred/tools/progress.py
from typing import Optional, Any

from alfred.core.workflow import BaseWorkflowTool, ImplementTaskTool
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.constants import ToolName
from alfred.state.manager import state_manager
from alfred.state.recovery import ToolRecovery
from alfred.lib.structured_logger import get_logger
from alfred.orchestration.orchestrator import orchestrator

logger = get_logger(__name__)


class MarkSubtaskCompleteHandler(BaseToolHandler):
    """Handler for the mark_subtask_complete tool."""

    def __init__(self):
        # This tool doesn't create a new workflow, it interacts with an existing one.
        # So, it doesn't need a tool_class or status maps.
        super().__init__(
            tool_name=ToolName.MARK_SUBTASK_COMPLETE,
            tool_class=None,  # Not a workflow-initiating tool
            required_status=None,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        # This should never be called for this type of tool.
        raise NotImplementedError("mark_subtask_complete does not create a new workflow tool.")

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """This is the core logic for the tool."""
        subtask_id = kwargs.get("subtask_id")
        if not subtask_id:
            return ToolResponse(status="error", message="`subtask_id` is a required argument.")

        # Ensure we are operating on an active ImplementTaskTool
        if not isinstance(tool_instance, ImplementTaskTool):
            return ToolResponse(status="error", message=f"Progress can only be marked during the '{ToolName.IMPLEMENT_TASK}' workflow.")

        # Optional: Enforce task status validation
        if task.task_status != TaskStatus.IN_DEVELOPMENT:
            return ToolResponse(status="error", message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Progress can only be marked for tasks in 'in_development' status.")

        # Validate subtask_id against the plan
        execution_plan = tool_instance.context_store.get("artifact_content", {}).get("subtasks", [])
        valid_subtask_ids = {st["subtask_id"] for st in execution_plan}
        if subtask_id not in valid_subtask_ids:
            return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'. It does not exist in the execution plan.")

        # Update the list of completed subtasks
        completed_subtasks = set(tool_instance.context_store.get("completed_subtasks", []))
        if subtask_id in completed_subtasks:
            return ToolResponse(status="success", message=f"Subtask '{subtask_id}' was already marked as complete.")

        completed_subtasks.add(subtask_id)
        tool_instance.context_store["completed_subtasks"] = sorted(list(completed_subtasks))  # Store sorted for consistency

        # Persist the updated tool state
        state_manager.update_tool_state(task.task_id, tool_instance)

        # Generate a progress report message
        completed_count = len(completed_subtasks)
        total_count = len(valid_subtask_ids)
        progress = (completed_count / total_count) * 100 if total_count > 0 else 0

        message = f"Acknowledged: Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%)."
        logger.info(message)

        # This tool does not return a next_prompt, as the AI should continue its work.
        return ToolResponse(status="success", message=message, data={"completed_count": completed_count, "total_count": total_count})

    def _get_or_create_tool(self, task_id: str, task: Task) -> BaseWorkflowTool | ToolResponse:
        """For this handler, we ONLY get an existing tool. We never create one."""
        if task_id in orchestrator.active_tools:
            return orchestrator.active_tools[task_id]

        # This tool requires an active workflow, so recovery is essential
        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            return recovered_tool

        # Provide helpful context about the task state
        from alfred.lib.task_utils import load_task
        task_info = load_task(task_id)
        task_status = task_info.task_status.value if task_info else "unknown"
        
        error_msg = f"""No active implementation workflow found for task '{task_id}'. 

**Current Status**: {task_status}

**Possible Reasons**:
- Implementation phase has already completed
- Task is in a different phase (planning, review, testing, etc.)
- No implementation workflow was started

**What to do**:
- If implementation is complete: Use `alfred.review_task('{task_id}')` to start code review
- If you need to restart implementation: Contact support (this shouldn't happen)
- To see current status: Use `alfred.work_on_task('{task_id}')`

Cannot mark subtask progress without an active implementation workflow."""
        
        return ToolResponse(status="error", message=error_msg)


mark_subtask_complete_handler = MarkSubtaskCompleteHandler()


# Keep the implementation function for decorator use
def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """Marks a specific subtask as complete during the implementation phase."""
    # Note: This synchronous wrapper calls the async handler
    import asyncio

    return asyncio.run(mark_subtask_complete_handler.execute(task_id, subtask_id=subtask_id))
