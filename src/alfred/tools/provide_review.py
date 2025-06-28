"""
Generic state-advancing tool for providing review feedback.
"""

from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Generic implementation for providing review feedback.
    
    This function:
    1. Looks up the active tool for the given task_id
    2. Determines the correct SM trigger based on approval status
    3. Calls the trigger on the active tool's machine
    4. Checks if the new state is terminal (VERIFIED)
    5. If terminal, performs tool completion logic
    6. If not terminal, generates and returns the prompt for the new state
    """
    # Look up the active tool for this task
    active_tool = orchestrator.active_tools.get(task_id)
    if not active_tool:
        error_msg = f"No active tool found for task {task_id}. Use plan_task or begin_task first."
        logger.error(error_msg)
        return ToolResponse(status="error", message=error_msg)
    
    # Get current state
    current_state = active_tool.state
    if not current_state:
        error_msg = f"Active tool for task {task_id} has no current state."
        logger.error(error_msg)
        return ToolResponse(status="error", message=error_msg)
    
    # Determine the trigger based on approval status
    if is_approved:
        trigger_name = "ai_approve"
    else:
        trigger_name = "request_revision"
    
    try:
        # Check if the trigger exists on the machine and call it
        if not hasattr(active_tool.machine, trigger_name):
            error_msg = f"Invalid state transition. No trigger '{trigger_name}' available from state '{current_state}'."
            logger.error(error_msg)
            return ToolResponse(status="error", message=error_msg)
        
        # Call the trigger to advance the state machine
        trigger_method = getattr(active_tool.machine, trigger_name)
        trigger_method()
        
        new_state = active_tool.state
        
        # Check if the new state is a terminal state
        if active_tool.is_terminal:
            # Tool completion logic
            message = f"Tool completed successfully. Final state: '{new_state}'"
            
            # Remove the tool from active tools
            del orchestrator.active_tools[task_id]
            
            # TODO: Update master task status and return handoff prompt
            # For now, return a completion message
            next_prompt = "Task planning phase completed. Ready for next phase."
            
            logger.info(f"Tool completed for task {task_id}. Removed from active tools.")
            
            return ToolResponse(
                status="success",
                message=message,
                next_prompt=next_prompt
            )
        else:
            # Not a terminal state, generate prompt for new state
            if is_approved:
                message = f"Review approved. Advanced from '{current_state}' to '{new_state}'."
            else:
                message = f"Review requested revisions. Returned from '{current_state}' to '{new_state}'."
                message += f" Feedback: {feedback_notes}" if feedback_notes else ""
            
            # TODO: Integrate with proper prompter once available
            next_prompt = f"You are now in state '{new_state}'. Please continue with the required work."
            if not is_approved and feedback_notes:
                next_prompt += f" Address the following feedback: {feedback_notes}"
            
            logger.info(f"Review processed for task {task_id}. State: {current_state} -> {new_state}")
            
            return ToolResponse(
                status="success",
                message=message,
                next_prompt=next_prompt
            )
            
    except Exception as e:
        error_msg = f"Failed to process review for task {task_id}: {str(e)}"
        logger.error(error_msg)
        return ToolResponse(status="error", message=error_msg)