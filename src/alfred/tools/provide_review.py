# src/alfred/tools/provide_review.py
from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.constants import ToolName, ArtifactKeys
from src.alfred.core.prompter import prompter
from src.alfred.core.context_builder import ContextBuilder
from src.alfred.lib.logger import cleanup_task_logging, get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


def _is_ai_review_state(state: str) -> bool:
    """Check if the current state is an AI review state."""
    return state.endswith("_awaiting_ai_review")


def _is_human_review_state(state: str) -> bool:
    """Check if the current state is a human review state."""
    return state.endswith("_awaiting_human_review")


def _is_autonomous_mode_enabled() -> bool:
    """Check if autonomous mode is enabled in configuration."""
    config_manager = ConfigManager(settings.alfred_dir)
    config = config_manager.load()
    return config.features.autonomous_mode


def _handle_rejection(active_tool, current_state: str) -> str:
    """Handle review rejection by transitioning back to previous state."""
    logger.info(f"Review rejected, transitioning back from '{current_state}'")
    active_tool.request_revision()
    logger.info(f"After revision, new state is '{active_tool.state}'")
    return "Revision requested. Returning to previous step."


def _handle_ai_review_approval(active_tool, task_id: str) -> str:
    """Handle AI review approval, checking for autonomous mode."""
    active_tool.ai_approve()

    if _is_autonomous_mode_enabled():
        logger.info(f"Autonomous mode enabled. Bypassing human review for task {task_id}.")
        active_tool.human_approve()
        return "AI review approved. Autonomous mode bypassed human review."

    return "AI review approved. Awaiting human review."


def _handle_human_review_approval(active_tool) -> str:
    """Handle human review approval."""
    active_tool.human_approve()
    return "Human review approved. Proceeding to next step."


def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Processes review feedback, advancing the active tool's State Machine."""
    # Try to get active tool or recover it from state
    if task_id not in orchestrator.active_tools:
        # Try to recover the tool from persisted state
        from src.alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            logger.info(f"Recovered tool for task {task_id} from persisted state")
        else:
            return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info(f"Processing review for task {task_id} in state '{current_state}', approved={is_approved}")

    if not is_approved:
        message = _handle_rejection(active_tool, current_state)
    else:
        if _is_ai_review_state(current_state):
            message = _handle_ai_review_approval(active_tool, task_id)
        elif _is_human_review_state(current_state):
            message = _handle_human_review_approval(active_tool)
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{active_tool.state}'.")

    state_manager.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        # The tool's internal workflow is DONE. Its ONLY job now is to hand off.
        tool_name = active_tool.tool_name
        logger.info(f"[DEBUG] Tool {tool_name} reached terminal state for task {task_id}")

        # 1. Save the tool's final, most important artifact to the persistent TaskState.
        #    This makes it available for approve_and_advance to archive.
        task_state = state_manager.load_or_create(task_id)
        final_artifact_state = active_tool.get_final_work_state()
        # CRITICAL FIX: Use centralized key generation to ensure consistency
        final_artifact_key = ArtifactKeys.get_artifact_key(final_artifact_state)

        # Debug logging
        logger.info(f"[DEBUG] Final artifact state: {final_artifact_state}")
        logger.info(f"[DEBUG] Looking for key: {final_artifact_key}")
        logger.info(f"[DEBUG] Context store keys: {list(active_tool.context_store.keys())}")

        final_artifact = active_tool.context_store.get(final_artifact_key)

        if final_artifact:
            # Save the RAW artifact object directly. This is the key change.
            logger.info(f"[DEBUG] Found final artifact of type: {type(final_artifact)}")
            task_state.completed_tool_outputs[tool_name] = final_artifact
            state_manager.save_task_state(task_state)
            logger.info(f"Saved final output artifact from '{tool_name}' to persistent state for task {task_id}.")
        else:
            logger.warning(f"[DEBUG] Final artifact key '{final_artifact_key}' not found in context store!")

        # 2. Clean up the ephemeral tool instance.
        state_manager.clear_tool_state(task_id)
        del orchestrator.active_tools[task_id]
        cleanup_task_logging(task_id)

        # 3. Create the handoff prompt.
        handoff_message = (
            f"The '{tool_name}' workflow has completed successfully. "
            f"The final artifact has been generated and reviewed.\n\n"
            f"To formally approve this phase, archive the results, and advance the task, "
            f"you MUST now call `alfred.approve_and_advance(task_id='{task_id}')`."
        )

        logger.info(f"Tool '{tool_name}' for task {task_id} finished. Awaiting final approval via approve_and_advance.")

        return ToolResponse(status="success", message=f"'{tool_name}' completed. Awaiting final approval.", next_prompt=handoff_message)
    else:
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
                feedback_notes,
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
            additional_context=additional_context,
        )
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)
