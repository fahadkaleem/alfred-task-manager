from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.core.workflow_config import WorkflowConfiguration
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def approve_and_advance_impl(task_id: str) -> ToolResponse:
    """Approve current phase and advance to next using centralized workflow config."""
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status
    
    # Get current phase from workflow config
    current_phase = WorkflowConfiguration.get_phase(current_status)
    if not current_phase:
        return ToolResponse(
            status="error",
            message=f"Unknown workflow phase for status '{current_status.value}'."
        )
    
    # Check if this phase can be advanced from
    if current_phase.terminal:
        return ToolResponse(
            status="error",
            message=f"Cannot advance from terminal status '{current_status.value}'."
        )
    
    if not current_phase.next_status:
        return ToolResponse(
            status="error",
            message=f"No next phase defined for status '{current_status.value}'."
        )
    
    # Archive artifacts if this phase produces them
    if current_phase.produces_artifact and current_phase.tool_name:
        workflow_step = WorkflowConfiguration.get_workflow_step_number(current_status)
        
        # Archive the scratchpad
        artifact_manager.archive_scratchpad(
            task_id, 
            current_phase.tool_name, 
            workflow_step
        )
        logger.info(
            f"Archived scratchpad for tool '{current_phase.tool_name}' "
            f"at workflow step {workflow_step}"
        )
        
        # Archive the final artifact
        final_artifact = task_state.completed_tool_outputs.get(current_phase.tool_name)
        if final_artifact:
            artifact_manager.archive_final_artifact(
                task_id, 
                current_phase.tool_name, 
                final_artifact
            )
            logger.info(f"Archived final artifact for phase '{current_status.value}'.")
        else:
            logger.warning(
                f"No final artifact found for tool '{current_phase.tool_name}' to archive."
            )
    
    # Advance to next status
    next_phase = WorkflowConfiguration.get_next_phase(current_status)
    if not next_phase:
        return ToolResponse(
            status="error",
            message=f"Failed to determine next phase for status '{current_status.value}'."
        )
    
    state_manager.update_task_status(task_id, next_phase.status)
    
    message = (
        f"Phase '{current_status.value}' approved. "
        f"Task '{task_id}' is now in status '{next_phase.status.value}'."
    )
    logger.info(message)
    
    if next_phase.terminal:
        message += "\n\nThe task is fully complete."
        return ToolResponse(status="success", message=message)
    
    return ToolResponse(
        status="success",
        message=message,
        next_prompt=f"To proceed, call `alfred.work_on(task_id='{task_id}')` to get the next action."
    )
