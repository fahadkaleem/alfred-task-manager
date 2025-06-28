"""
Generic state-advancing tool for submitting work artifacts.
"""

from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """
    Generic implementation for submitting work artifacts.
    
    This function:
    1. Looks up the active tool for the given task_id
    2. Determines the correct SM trigger based on current state
    3. Calls the trigger on the active tool's machine
    4. Persists the artifact to the scratchpad
    5. Generates and returns the prompt for the new state
    """
    # Look up the active tool for this task
    active_tool = orchestrator.active_tools.get(task_id)
    if not active_tool:
        error_msg = f"No active tool found for task {task_id}. Use plan_task or begin_task first."
        logger.error(error_msg)
        return ToolResponse(status="error", message=error_msg)
    
    # Get current state and determine the submit trigger
    current_state = active_tool.state
    if not current_state:
        error_msg = f"Active tool for task {task_id} has no current state."
        logger.error(error_msg)
        return ToolResponse(status="error", message=error_msg)
    
    # By convention, the trigger is "submit_{current_state}"
    submit_trigger = f"submit_{current_state}"
    
    try:
        # Check if the trigger exists on the machine and call it
        if not hasattr(active_tool.machine, submit_trigger):
            error_msg = f"Invalid state transition. No trigger '{submit_trigger}' available from state '{current_state}'."
            logger.error(error_msg)
            return ToolResponse(status="error", message=error_msg)
        
        # Call the trigger to advance the state machine
        trigger_method = getattr(active_tool.machine, submit_trigger)
        trigger_method()
        
        # Persist the artifact to the scratchpad
        # Note: Using a generic artifact type based on current state
        artifact_type = current_state
        artifact_manager.append_to_scratchpad(task_id, artifact_type, artifact, None)
        
        # Generate the prompt for the new state using the orchestrator's prompter
        # For now, using a simple success message and next state
        new_state = active_tool.state
        message = f"Work submitted successfully. Transitioned from '{current_state}' to '{new_state}'."
        
        # TODO: Integrate with proper prompter once available
        next_prompt = f"You are now in state '{new_state}'. Please review the submitted work and provide feedback."
        
        logger.info(f"Successfully submitted work for task {task_id}. State: {current_state} -> {new_state}")
        
        return ToolResponse(
            status="success",
            message=message,
            next_prompt=next_prompt
        )
        
    except Exception as e:
        error_msg = f"Failed to submit work for task {task_id}: {str(e)}"
        logger.error(error_msg)
        return ToolResponse(status="error", message=error_msg)