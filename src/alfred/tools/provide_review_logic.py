# src/alfred/tools/provide_review_logic.py
from alfred.core.prompter import generate_prompt
from alfred.lib.structured_logger import get_logger, cleanup_task_logging
from alfred.lib.task_utils import load_task
from alfred.lib.turn_manager import turn_manager
from alfred.models.schemas import ToolResponse
from alfred.constants import Triggers, ToolName
from alfred.orchestration.orchestrator import orchestrator
from alfred.state.manager import state_manager
from alfred.constants import ArtifactKeys
from alfred.config.manager import ConfigManager
from alfred.config.settings import settings

logger = get_logger(__name__)


async def provide_review_logic(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    if task_id not in orchestrator.active_tools:
        from alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if not recovered_tool:
            return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")
        orchestrator.active_tools[task_id] = recovered_tool

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info("Processing review", task_id=task_id, tool_name=active_tool.tool_name, state=current_state, approved=is_approved)

    if not is_approved:
        # Record revision request as a turn
        if feedback_notes:
            state_to_revise = current_state.replace("_awaiting_ai_review", "").replace("_awaiting_human_review", "")
            revision_turn = turn_manager.request_revision(task_id=task_id, state_to_revise=state_to_revise, feedback=feedback_notes, requested_by="human")
            # Store the revision turn number in context for next submission
            active_tool.context_store["revision_turn_number"] = revision_turn.turn_number

        active_tool.trigger(Triggers.REQUEST_REVISION)
        message = "Revision requested. Returning to previous step."
    else:
        # Clear any previous feedback when approving
        if "feedback_notes" in active_tool.context_store:
            del active_tool.context_store["feedback_notes"]

        if current_state.endswith("_awaiting_ai_review"):
            active_tool.trigger(Triggers.AI_APPROVE)
            message = "AI review approved. Awaiting human review."
            try:
                if ConfigManager(settings.alfred_dir).load().features.autonomous_mode:
                    logger.info("Autonomous mode enabled, bypassing human review", task_id=task_id, tool_name=active_tool.tool_name)
                    active_tool.trigger(Triggers.HUMAN_APPROVE)
                    message = "AI review approved. Autonomous mode bypassed human review."
            except FileNotFoundError:
                logger.warning("Config file not found; autonomous mode unchecked.")
        elif current_state.endswith("_awaiting_human_review"):
            active_tool.trigger(Triggers.HUMAN_APPROVE)
            message = "Human review approved. Proceeding to next step."
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{current_state}'.")

    state_manager.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        tool_name = active_tool.tool_name
        final_state = active_tool.get_final_work_state()
        key = ArtifactKeys.get_artifact_key(final_state)
        artifact = active_tool.context_store.get(key)

        if artifact:
            state_manager.add_completed_output(task_id, tool_name, artifact)
        state_manager.clear_tool_state(task_id)

        orchestrator.active_tools.pop(task_id, None)
        cleanup_task_logging(task_id)

        # Import here to avoid circular dependency
        from alfred.models.schemas import TaskStatus
        from alfred.core.workflow_config import WorkflowConfiguration

        # Update task status based on the tool that just completed
        current_task_status = task.task_status
        if tool_name == ToolName.PLAN_TASK and current_task_status == TaskStatus.PLANNING:
            # Planning completed, update to READY_FOR_DEVELOPMENT
            state_manager.update_task_status(task_id, TaskStatus.READY_FOR_DEVELOPMENT)
            logger.info("Planning completed, status updated", task_id=task_id, tool_name=tool_name, new_status="READY_FOR_DEVELOPMENT")
            handoff = f"""The planning workflow has completed successfully!

Task '{task_id}' is now ready for development.

**Next Action:**
Call `alfred.work_on_task(task_id='{task_id}')` to start implementation."""
        else:
            # For other tools, provide the standard handoff message
            handoff = f"""The '{tool_name}' workflow has completed successfully! 

**Next Action Required:**
Call `alfred.approve_and_advance(task_id='{task_id}')` to:
- Archive the completed work
- Advance to the next phase  
- Update task status

**Alternative:** If you need to review the work first, call `alfred.work_on_task(task_id='{task_id}')` to see current status."""

        return ToolResponse(status="success", message=f"'{tool_name}' completed.", next_prompt=handoff)

    if not is_approved and feedback_notes:
        # Store feedback in the tool's context for persistence
        active_tool.context_store["feedback_notes"] = feedback_notes
        # Persist the updated tool state with feedback
        state_manager.update_tool_state(task_id, active_tool)

    # Always use the tool's context (which now includes feedback if present)
    ctx = active_tool.context_store.copy()

    prompt = generate_prompt(
        task_id=task.task_id,
        tool_name=active_tool.tool_name,
        state=active_tool.state,
        task=task,
        additional_context=ctx,
    )
    return ToolResponse(status="success", message=message, next_prompt=prompt)
