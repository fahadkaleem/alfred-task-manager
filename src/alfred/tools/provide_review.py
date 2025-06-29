# src/alfred/tools/provide_review.py
import json

from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.task_utils import load_task
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.lib.logger import get_logger, cleanup_task_logging
from src.alfred.state.manager import state_manager
from src.alfred.constants import ToolName, Paths, PlanTaskStates, ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Processes review feedback, advancing the active tool's State Machine."""
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id))

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.TASK_NOT_FOUND.format(task_id=task_id))

    trigger = Triggers.AI_APPROVE if is_approved else Triggers.REQUEST_REVISION
    if not hasattr(active_tool, trigger):
        return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot trigger '{trigger}' from state '{active_tool.state}'.")

    getattr(active_tool, trigger)()
    logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))
    state_manager.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
        state_manager.update_task_status(task_id, final_task_status)
        state_manager.clear_tool_state(task_id)

        del orchestrator.active_tools[task_id]
        cleanup_task_logging(task_id)
        logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")
        
        handoff_message = f"Planning for task {task_id} is complete. The task is now '{final_task_status.value}'. To begin implementation, use the 'implement_task' tool."
        return ToolResponse(status=ResponseStatus.SUCCESS, message=f"Tool '{active_tool.tool_name}' completed successfully.", next_prompt=handoff_message)
    else:
        persona_config = load_persona(active_tool.persona_name)
        additional_context = active_tool.context_store.copy()
        additional_context["feedback_notes"] = feedback_notes or ""
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=active_tool.state,
            persona_config=persona_config,
            additional_context=additional_context,
        )
        message = "Review approved. Proceeding to next step." if is_approved else "Revision requested."
        return ToolResponse(status=ResponseStatus.SUCCESS, message=message, next_prompt=next_prompt)