# src/alfred/tools/progress.py
from typing import Optional, Any

from alfred.core.workflow import BaseWorkflowTool, ImplementTaskTool
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.constants import ToolName
from alfred.state.manager import state_manager
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class MarkSubtaskCompleteHandler(BaseToolHandler):
    """Handler for the mark_subtask_complete tool using stateless pattern."""

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

    async def execute(self, task_id: str = None, **kwargs: Any) -> ToolResponse:
        """Execute mark_subtask_complete using stateless pattern."""
        from alfred.lib.task_utils import load_task
        
        task = load_task(task_id)
        if not task:
            return ToolResponse(status="error", message=f"Task '{task_id}' not found.")
        
        # Load task state
        task_state = state_manager.load_or_create(task_id)
        
        # Check if we have an active workflow state
        if not task_state.active_tool_state:
            error_msg = f"""No active implementation workflow found for task '{task_id}'. 

**Current Status**: {task.task_status.value}

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

        workflow_state = task_state.active_tool_state
        
        # Ensure we are operating on an ImplementTaskTool
        if workflow_state.tool_name != ToolName.IMPLEMENT_TASK:
            return ToolResponse(status="error", message=f"Progress can only be marked during the '{ToolName.IMPLEMENT_TASK}' workflow.")

        # Execute the core logic
        return await self._execute_subtask_complete(task, task_state, workflow_state, **kwargs)

    async def _execute_subtask_complete(self, task: Task, task_state: TaskState, workflow_state: WorkflowState, **kwargs: Any) -> ToolResponse:
        """Core logic for marking subtask complete using stateless pattern."""
        subtask_id = kwargs.get("subtask_id")
        if not subtask_id:
            return ToolResponse(status="error", message="`subtask_id` is a required argument.")

        # Optional: Enforce task status validation
        if task.task_status != TaskStatus.IN_DEVELOPMENT:
            return ToolResponse(status="error", message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Progress can only be marked for tasks in 'in_development' status.")

        # Validate subtask_id against the plan
        execution_plan = workflow_state.context_store.get("artifact_content", {}).get("subtasks", [])
        valid_subtask_ids = {st["subtask_id"] for st in execution_plan}
        if subtask_id not in valid_subtask_ids:
            return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'. It does not exist in the execution plan.")

        # Update the list of completed subtasks
        completed_subtasks = set(workflow_state.context_store.get("completed_subtasks", []))
        if subtask_id in completed_subtasks:
            return ToolResponse(status="success", message=f"Subtask '{subtask_id}' was already marked as complete.")

        completed_subtasks.add(subtask_id)
        workflow_state.context_store["completed_subtasks"] = sorted(list(completed_subtasks))  # Store sorted for consistency

        # Persist the updated workflow state
        with state_manager.complex_update(task_id) as state:
            state.active_tool_state = workflow_state

        # Generate a progress report message
        completed_count = len(completed_subtasks)
        total_count = len(valid_subtask_ids)
        progress = (completed_count / total_count) * 100 if total_count > 0 else 0
        remaining = total_count - completed_count

        # Create an encouraging message based on progress
        if completed_count == total_count:
            message = (
                f"🎉 Excellent! Subtask '{subtask_id}' is complete. All {total_count} subtasks are now finished! "
                f"\n\n**Next Action**: Call `alfred.submit_work` with your ImplementationManifestArtifact to complete the implementation phase."
            )
        elif progress >= 80:
            message = (
                f"Great progress! Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%). "
                f"Almost there - only {remaining} subtask{'s' if remaining > 1 else ''} left!"
            )
        elif progress >= 50:
            message = f"Good work! Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%). You're over halfway done!"
        else:
            message = f"✓ Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%). Keep going - {remaining} subtasks remaining."

        logger.info(f"Subtask '{subtask_id}' marked complete for task {task.task_id}")

        # This tool does not return a next_prompt, as the AI should continue its work.
        return ToolResponse(status="success", message=message, data={"completed_count": completed_count, "total_count": total_count})

    # Legacy methods for BaseToolHandler compatibility - not used in stateless path
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Legacy setup method - not used in stateless path."""
        return None


mark_subtask_complete_handler = MarkSubtaskCompleteHandler()


# Keep the implementation function for decorator use
def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """Marks a specific subtask as complete during the implementation phase."""
    # Note: This synchronous wrapper calls the async handler
    import asyncio

    return asyncio.run(mark_subtask_complete_handler.execute(task_id, subtask_id=subtask_id))
