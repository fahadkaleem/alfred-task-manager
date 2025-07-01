# src/alfred/tools/provide_review_logic.py
from src.alfred.core.prompter import generate_prompt
from src.alfred.lib.logger import get_logger, cleanup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import ToolResponse
from src.alfred.constants import Triggers
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.constants import ArtifactKeys
from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings

logger = get_logger(__name__)


async def provide_review_logic(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    if task_id not in orchestrator.active_tools:
        from src.alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if not recovered_tool:
            return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")
        orchestrator.active_tools[task_id] = recovered_tool

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info(f"Processing review for task {task_id} in state '{current_state}', approved={is_approved}")

    if not is_approved:
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
                    logger.info(f"Autonomous mode enabled. Bypassing human review for task {task_id}.")
                    active_tool.trigger(Triggers.HUMAN_APPROVE)
                    message = "AI review approved. Autonomous mode bypassed human review."
            except FileNotFoundError:
                logger.warning("Config file not found; autonomous mode unchecked.")
        elif current_state.endswith("_awaiting_human_review"):
            active_tool.trigger(Triggers.HUMAN_APPROVE)
            message = "Human review approved. Proceeding to next step."
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{current_state}'.")

    with state_manager.transaction() as uow:
        uow.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        tool_name = active_tool.tool_name
        final_state = active_tool.get_final_work_state()
        key = ArtifactKeys.get_artifact_key(final_state)
        artifact = active_tool.context_store.get(key)

        with state_manager.transaction() as uow:
            if artifact:
                uow.add_completed_output(task_id, tool_name, artifact)
            uow.clear_tool_state(task_id)

        orchestrator.active_tools.pop(task_id, None)
        cleanup_task_logging(task_id)

        handoff = f"The '{tool_name}' workflow has completed successfully. To formally approve this phase, call `alfred.approve_and_advance(task_id='{task_id}')`."
        return ToolResponse(status="success", message=f"'{tool_name}' completed. Awaiting final approval.", next_prompt=handoff)

    if not is_approved and feedback_notes:
        # Store feedback in the tool's context for persistence
        active_tool.context_store["feedback_notes"] = feedback_notes
        # Persist the updated tool state with feedback
        with state_manager.transaction() as uow:
            uow.update_tool_state(task_id, active_tool)

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
