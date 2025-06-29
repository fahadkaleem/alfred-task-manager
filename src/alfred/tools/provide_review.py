# src/alfred/tools/provide_review.py
from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.constants import ToolName
from src.alfred.core.prompter import prompter
from src.alfred.core.workflow import ReviewState
from src.alfred.core.context_builder import ContextBuilder
from src.alfred.lib.logger import cleanup_task_logging, get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)

# Force server reload marker - AL-09 implementation active

def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Processes review feedback, advancing the active tool's State Machine."""
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info(f"Processing review for task {task_id} in state '{current_state}', approved={is_approved}")
    
    if not is_approved:
        logger.info(f"Review rejected, transitioning back from '{current_state}'")
        active_tool.request_revision()
        message = "Revision requested. Returning to previous step."
        logger.info(f"After revision, new state is '{active_tool.state}'")
    else:
        if current_state == ReviewState.AWAITING_AI_REVIEW.value:
            active_tool.ai_approve()
            config_manager = ConfigManager(settings.alfred_dir)
            config = config_manager.load()
            if config.features.autonomous_mode:
                logger.info(f"Autonomous mode enabled. Bypassing human review for task {task_id}.")
                active_tool.human_approve()
                message = "AI review approved. Autonomous mode bypassed human review."
            else:
                message = "AI review approved. Awaiting human review."
        elif current_state == ReviewState.AWAITING_HUMAN_REVIEW.value:
            active_tool.human_approve()
            message = "Human review approved. Proceeding to next step."
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{active_tool.state}'.")

    state_manager.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        # --- ADD THIS LOGIC ---
        if active_tool.tool_name == ToolName.START_TASK:
            final_task_status = TaskStatus.PLANNING
            handoff_message = f"Setup for task {task_id} is complete. The task is now '{final_task_status.value}'. Call 'plan_task' to begin planning."
        # --- END ADDED LOGIC ---
        elif active_tool.tool_name == ToolName.PLAN_TASK:
            final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
            handoff_message = f"Planning for task {task_id} is complete. The task is now '{final_task_status.value}'. To begin implementation, use the 'implement_task' tool."
        else:
            final_task_status = TaskStatus.DONE # Default fallback
            handoff_message = f"Tool '{active_tool.tool_name}' for task {task_id} completed."

        state_manager.update_task_status(task_id, final_task_status)
        state_manager.clear_tool_state(task_id)
        del orchestrator.active_tools[task_id]
        cleanup_task_logging(task_id)
        logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")
        
        return ToolResponse(status="success", message=message, next_prompt=handoff_message)
    else:
        persona_config = load_persona(active_tool.persona_name)
        
        # CRITICAL: Force visible logging to verify code execution
        logger.warning(f"[AL-09 VERIFICATION] Building context for state '{active_tool.state}', is_approved={is_approved}")
        
        # Build proper context based on transition type
        if not is_approved:
            # Rejection: returning to work state, need feedback context
            logger.info(f"[FEEDBACK LOOP] Building feedback context for rejection flow")
            logger.info(f"[FEEDBACK LOOP] State: '{active_tool.state}', Feedback: {feedback_notes[:100]}")
            additional_context = ContextBuilder.build_feedback_context(
                active_tool,
                active_tool.state,  # Current state after revision
                feedback_notes
            )
            logger.info(f"[FEEDBACK LOOP] Context keys after building: {list(additional_context.keys())}")
            logger.info(f"[FEEDBACK LOOP] Has feedback_notes: {'feedback_notes' in additional_context}")
            logger.info(f"[FEEDBACK LOOP] Has context_artifact: {'context_artifact' in additional_context}")
        else:
            # Approval: moving forward, standard context
            logger.info(f"[FEEDBACK LOOP] Building standard context for approval flow")
            additional_context = ContextBuilder.build_standard_context(active_tool)
            
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=active_tool.state,
            persona_config=persona_config,
            additional_context=additional_context,
        )
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)