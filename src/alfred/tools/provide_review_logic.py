# src/alfred/tools/provide_review_logic.py
from alfred.core.prompter import generate_prompt
from alfred.lib.structured_logger import get_logger, cleanup_task_logging
from alfred.lib.task_utils import load_task
from alfred.lib.turn_manager import turn_manager
from alfred.models.schemas import ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.constants import Triggers, ToolName
from alfred.state.manager import state_manager
from alfred.constants import ArtifactKeys
from alfred.config.manager import ConfigManager
from alfred.config.settings import settings

logger = get_logger(__name__)


async def provide_review_logic(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Provide review logic using stateless WorkflowEngine pattern."""

    # Load task and task state
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    task_state = state_manager.load_or_create(task_id)

    # Check if we have an active workflow state
    if not task_state.active_tool_state:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    workflow_state = task_state.active_tool_state
    current_state = workflow_state.current_state

    # CRITICAL FIX: Override approval if feedback_notes is provided
    # If feedback is provided, treat it as a revision request regardless of is_approved flag
    if feedback_notes:
        logger.info("Feedback provided, overriding approval to revision request", task_id=task_id, original_is_approved=is_approved, feedback_length=len(feedback_notes))
        is_approved = False

    logger.info("Processing review", task_id=task_id, tool_name=workflow_state.tool_name, state=current_state, approved=is_approved)

    # Get tool definition and engine for state transitions (local import to avoid circular dependency)
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    tool_definition = TOOL_DEFINITIONS.get(workflow_state.tool_name)
    if not tool_definition:
        return ToolResponse(status="error", message=f"No tool definition found for {workflow_state.tool_name}")

    # Local import to avoid circular dependency
    from alfred.core.workflow_engine import WorkflowEngine

    engine = WorkflowEngine(tool_definition)

    if not is_approved:
        # Record revision request as a turn
        if feedback_notes:
            state_to_revise = current_state.replace("_awaiting_ai_review", "").replace("_awaiting_human_review", "")
            revision_turn = turn_manager.request_revision(task_id=task_id, state_to_revise=state_to_revise, feedback=feedback_notes, requested_by="human")
            # Store the revision turn number in context for next submission
            workflow_state.context_store["revision_turn_number"] = revision_turn.turn_number

        # Execute revision transition
        try:
            new_state = engine.execute_trigger(current_state, Triggers.REQUEST_REVISION)
            workflow_state.current_state = new_state
        except Exception as e:
            logger.error("Revision transition failed", task_id=task_id, error=str(e))
            return ToolResponse(status="error", message=f"Failed to process revision: {str(e)}")

        message = "Revision requested. Returning to previous step."
    else:
        # Clear any previous feedback when approving
        if "feedback_notes" in workflow_state.context_store:
            del workflow_state.context_store["feedback_notes"]

        # Determine the appropriate approval trigger
        if current_state.endswith("_awaiting_ai_review"):
            trigger = Triggers.AI_APPROVE
            message = "AI review approved. Awaiting human review."

            try:
                new_state = engine.execute_trigger(current_state, trigger)
                workflow_state.current_state = new_state

                # Check for autonomous mode to bypass human review
                try:
                    if ConfigManager(settings.alfred_dir).load().features.autonomous_mode:
                        logger.info("Autonomous mode enabled, bypassing human review", task_id=task_id, tool_name=workflow_state.tool_name)
                        # Execute another transition for human approve
                        new_state = engine.execute_trigger(workflow_state.current_state, Triggers.HUMAN_APPROVE)
                        workflow_state.current_state = new_state
                        message = "AI review approved. Autonomous mode bypassed human review."
                except FileNotFoundError:
                    logger.warning("Config file not found; autonomous mode unchecked.")

            except Exception as e:
                logger.error("AI approval transition failed", task_id=task_id, error=str(e))
                return ToolResponse(status="error", message=f"Failed to process AI approval: {str(e)}")

        elif current_state.endswith("_awaiting_human_review"):
            trigger = Triggers.HUMAN_APPROVE
            message = "Human review approved. Proceeding to next step."

            try:
                new_state = engine.execute_trigger(current_state, trigger)
                workflow_state.current_state = new_state
            except Exception as e:
                logger.error("Human approval transition failed", task_id=task_id, error=str(e))
                return ToolResponse(status="error", message=f"Failed to process human approval: {str(e)}")
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{current_state}'.")

    # Persist the updated workflow state
    with state_manager.complex_update(task_id) as state:
        state.active_tool_state = workflow_state

    # Check if we've reached a terminal state
    is_terminal = engine.is_terminal_state(workflow_state.current_state)

    if is_terminal:
        # Handle terminal state completion
        tool_name = workflow_state.tool_name

        # Create temporary tool instance to get final work state
        tool_class = tool_definition.tool_class
        temp_tool = tool_class(task_id=task_id)
        final_state = temp_tool.get_final_work_state()

        key = ArtifactKeys.get_artifact_key(final_state)
        artifact = workflow_state.context_store.get(key)

        if artifact:
            state_manager.add_completed_output(task_id, tool_name, artifact)

        # Clear active tool state
        with state_manager.complex_update(task_id) as state:
            state.active_tool_state = None

        cleanup_task_logging(task_id)

        # Import here to avoid circular dependency
        from alfred.models.schemas import TaskStatus
        from alfred.tools.workflow_utils import get_next_status

        # Update task status using workflow utilities for direct exit_status mapping
        current_task_status = task.task_status
        next_status = get_next_status(current_task_status)

        if next_status:
            state_manager.update_task_status(task_id, next_status)
            logger.info("Tool completed, status updated", task_id=task_id, tool_name=tool_name, old_status=current_task_status.value, new_status=next_status.value)

            if tool_name == ToolName.PLAN_TASK:
                handoff = f"""The planning workflow has completed successfully!

Task '{task_id}' is now ready for development.

**Next Action:**
Call `alfred.work_on_task(task_id='{task_id}')` to start implementation."""
            else:
                # Check if there's another active workflow tool (meaning we're transitioning between major phases)
                task_state_check = state_manager.load_or_create(task_id)
                if task_state_check.active_tool_state is None and next_status != TaskStatus.DONE:
                    # No active workflow - we're between major phases, approve_and_advance is appropriate
                    handoff = f"""The '{tool_name}' workflow has completed successfully! 

**Next Actions:**
1. Call `alfred.work_on_task(task_id='{task_id}')` to check the current status and see what phase comes next
2. Then use the suggested tool for the next phase (e.g., `review_task`, `test_task`, etc.)

**Quick Option:** Call `alfred.approve_and_advance(task_id='{task_id}')` to automatically advance to the next phase."""
                else:
                    # Still in a workflow or task is complete - don't suggest approve_and_advance
                    handoff = f"""The '{tool_name}' workflow has completed successfully! 

**Next Action:**
Call `alfred.work_on_task(task_id='{task_id}')` to check the current status and see what comes next."""
        else:
            # Fallback if no next status defined
            handoff = f"""The '{tool_name}' workflow has completed successfully! 

**Next Action:**
Call `alfred.work_on_task(task_id='{task_id}')` to check the current status."""

        return ToolResponse(status="success", message=f"'{tool_name}' completed.", next_prompt=handoff)

    if not is_approved and feedback_notes:
        # Store feedback in the workflow state's context for persistence
        workflow_state.context_store["feedback_notes"] = feedback_notes
        # Persist the updated workflow state with feedback
        with state_manager.complex_update(task_id) as state:
            state.active_tool_state = workflow_state

    # Always use the workflow state's context (which now includes feedback if present)
    ctx = workflow_state.context_store.copy()

    prompt = generate_prompt(
        task_id=task.task_id,
        tool_name=workflow_state.tool_name,
        state=workflow_state.current_state,
        task=task,
        additional_context=ctx,
    )
    return ToolResponse(status="success", message=message, next_prompt=prompt)
