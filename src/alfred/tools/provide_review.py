# src/alfred/tools/provide_review.py
import json
from src.alfred.models.schemas import ToolResponse, Task, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.lib.logger import get_logger, cleanup_task_logging
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)

def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Processes review feedback, advancing the active tool's State Machine.
    Handles both mid-workflow reviews and final tool completion.
    
    IMPORTANT: This implementation uses atomic state transitions to prevent
    state corruption if prompt generation fails.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # Determine the trigger
    trigger = "ai_approve" if is_approved else "request_revision"
    if not hasattr(active_tool, trigger):
        return ToolResponse(status="error", message=f"Invalid action: cannot trigger '{trigger}' from state '{active_tool.state}'.")
    
    # Save current state for potential rollback
    original_state = active_tool.state
    original_context = active_tool.context_store.copy()
    
    try:
        # PHASE 1: Prepare everything that could fail
        # Calculate what the next state will be
        next_transitions = active_tool.machine.get_transitions(
            source=active_tool.state,
            trigger=trigger
        )
        if not next_transitions:
            return ToolResponse(
                status="error", 
                message=f"No valid transition for trigger '{trigger}' from state '{active_tool.state}'."
            )
        
        next_state = next_transitions[0].dest
        
        # Check if the next state will be terminal
        will_be_terminal = (next_state == "verified")  # Hardcoded for now, could be made more flexible
        
        if will_be_terminal:
            # Prepare completion logic
            final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
            handoff_message = (
                f"Planning for task {task_id} is complete and verified. "
                f"The task is now '{final_task_status.value}'.\n\n"
                f"To begin implementation, run `alfred.implement_task(task_id='{task_id}')`."
            )
            next_prompt = handoff_message
        else:
            # Prepare mid-workflow logic
            try:
                persona_config = load_persona(active_tool.persona_name)
            except FileNotFoundError as e:
                return ToolResponse(status="error", message=str(e))
            
            # Always provide feedback_notes in additional_context
            additional_context = active_tool.context_store.copy()
            additional_context["feedback_notes"] = feedback_notes or ""
            
            # Generate prompt for the NEXT state (most likely to fail)
            next_prompt = prompter.generate_prompt(
                task=task,
                tool_name=active_tool.tool_name,
                state=next_state,  # Use the calculated next state
                persona_config=persona_config,
                additional_context=additional_context
            )
        
        # PHASE 2: Commit - only if everything succeeded
        # Now do the actual state transition
        getattr(active_tool, trigger)()
        logger.info(f"Task {task_id}: State transitioned via trigger '{trigger}' to '{active_tool.state}'.")
        
        # Persist the new state immediately
        state_manager.save_tool_state(task_id, active_tool)
        
        # Handle terminal state cleanup
        if active_tool.is_terminal:
            update_task_status(task_id, final_task_status)
            state_manager.clear_tool_state(task_id)  # Clean up persisted state
            del orchestrator.active_tools[task_id]
            cleanup_task_logging(task_id)
            logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")
            
            return ToolResponse(
                status="success",
                message=f"Tool '{active_tool.tool_name}' completed successfully.",
                next_prompt=next_prompt
            )
        else:
            message = "Review approved. Proceeding to next step." if is_approved else "Revision requested."
            return ToolResponse(status="success", message=message, next_prompt=next_prompt)
            
    except Exception as e:
        # Rollback on any failure
        logger.error(f"State transition failed for task {task_id}: {e}")
        active_tool.state = original_state
        active_tool.context_store = original_context
        
        # Save the rolled-back state
        try:
            state_manager.save_tool_state(task_id, active_tool)
        except:
            pass  # Don't fail the error response if state save fails
        
        return ToolResponse(
            status="error",
            message=f"Failed to process review: {str(e)}"
        )