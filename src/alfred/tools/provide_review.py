# src/alfred/tools/provide_review.py
import json
from src.alfred.models.schemas import ToolResponse, Task, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.lib.logger import get_logger, cleanup_task_logging

logger = get_logger(__name__)

def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Processes review feedback, advancing the active tool's State Machine.
    Handles both mid-workflow reviews and final tool completion.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # Determine the trigger and advance the state machine
    trigger = "ai_approve" if is_approved else "request_revision"
    if not hasattr(active_tool, trigger):
        return ToolResponse(status="error", message=f"Invalid action: cannot trigger '{trigger}' from state '{active_tool.state}'.")
    
    getattr(active_tool, trigger)()
    logger.info(f"Task {task_id}: State transitioned via trigger '{trigger}' to '{active_tool.state}'.")

    # Check if the new state is the tool's terminal state
    if active_tool.is_terminal:
        # --- TOOL COMPLETION LOGIC ---
        # This logic must be extensible for different tools in the future.
        # For now, we hardcode the outcome for plan_task.
        final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
        handoff_message = (
            f"Planning for task {task_id} is complete and verified. "
            f"The task is now '{final_task_status.value}'.\n\n"
            f"To begin implementation, run `alfred.implement_task(task_id='{task_id}')`."
        )
        
        update_task_status(task_id, final_task_status)
        del orchestrator.active_tools[task_id]
        
        # --- ADD LOGGING CLEANUP ---
        cleanup_task_logging(task_id)
        
        logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")

        return ToolResponse(
            status="success",
            message=f"Tool '{active_tool.tool_name}' completed successfully.",
            next_prompt=handoff_message
        )
    else:
        # --- MID-WORKFLOW REVIEW LOGIC ---
        try:
            persona_config = load_persona(active_tool.persona_name)
        except FileNotFoundError as e:
            return ToolResponse(status="error", message=str(e))
        
        additional_context = {"feedback_notes": feedback_notes} if not is_approved and feedback_notes else {}
        
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=active_tool.state,
            persona_config=persona_config,
            additional_context=additional_context
        )
        
        message = "Review approved. Proceeding to next step." if is_approved else "Revision requested."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)