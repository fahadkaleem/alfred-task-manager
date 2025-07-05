from alfred.state.manager import state_manager
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.tools.workflow_utils import get_phase_info, get_next_status
from alfred.lib.structured_logger import get_logger
from alfred.orchestration.orchestrator import orchestrator
from alfred.state.recovery import ToolRecovery

logger = get_logger(__name__)


def approve_and_advance_impl(task_id: str) -> ToolResponse:
    """Approve current phase and advance to next using centralized workflow config."""
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status

    # Check if there's an active workflow tool with sub-states
    active_tool = orchestrator.active_tools.get(task_id)
    if not active_tool:
        # Try to recover the tool
        active_tool = ToolRecovery.recover_tool(task_id)

    if active_tool:
        # Check if the tool has internal states that haven't completed
        tool_state = getattr(active_tool, "state", None)
        if tool_state:
            # Check if we're in a sub-state (not a main workflow phase)
            if hasattr(tool_state, "value"):
                state_value = tool_state.value
            else:
                state_value = str(tool_state)

            # If the state contains underscores or special suffixes, it's likely a sub-state
            if "_" in state_value or state_value.endswith("awaiting_ai_review") or state_value.endswith("awaiting_human_review"):
                return ToolResponse(
                    status="error",
                    message=f"Cannot use approve_and_advance while in sub-state '{state_value}'. "
                    f"The workflow tool '{active_tool.tool_name}' has internal states that must be completed first.\n\n"
                    f"**Next Action**: Call `alfred.approve_review(task_id='{task_id}')` to continue through the current workflow.\n\n"
                    f"**Note**: approve_and_advance is only for moving between major phases (e.g., implementation → review), "
                    f"not for approving sub-states within a workflow.",
                )

            # Check if the tool has a method to determine if it's complete
            if hasattr(active_tool, "get_final_work_state"):
                final_state = active_tool.get_final_work_state()
                if state_value != final_state:
                    return ToolResponse(
                        status="error",
                        message=f"The workflow tool '{active_tool.tool_name}' is not complete. "
                        f"Current state: '{state_value}', but needs to reach '{final_state}' before advancing phases. "
                        f"Use 'approve_review' or 'submit_work' to continue through the workflow.",
                    )

            # Additional check for specific workflow tools with known sub-states
            if active_tool.tool_name == "plan_task" and state_value not in ["verified", "validation"]:
                states_remaining = []
                if state_value == "discovery":
                    states_remaining = ["clarification", "contracts", "implementation_plan", "validation"]
                elif state_value == "clarification":
                    states_remaining = ["contracts", "implementation_plan", "validation"]
                elif state_value == "contracts":
                    states_remaining = ["implementation_plan", "validation"]
                elif state_value == "implementation_plan":
                    states_remaining = ["validation"]

                if states_remaining:
                    return ToolResponse(
                        status="error",
                        message=f"Cannot skip planning sub-states. Currently in '{state_value}' but still need to complete: {', '.join(states_remaining)}. "
                        f"Use 'submit_work' to submit artifacts and 'approve_review' to advance through each planning phase.",
                    )

    # Get next status using simplified workflow utilities
    next_status = get_next_status(current_status)
    if not next_status:
        return ToolResponse(status="error", message=f"No next status defined for '{current_status.value}'.")

    # Check if current status is terminal (cannot advance from DONE)
    if current_status == TaskStatus.DONE:
        return ToolResponse(status="error", message=f"Cannot advance from terminal status '{current_status.value}'.")

    # Note: Archiving is no longer needed with turn-based storage system
    # All artifacts are already stored as immutable turns

    # Advance to next status using direct status mapping
    state_manager.update_task_status(task_id, next_status)

    message = f"Phase '{current_status.value}' approved. Task '{task_id}' is now in status '{next_status.value}'."
    logger.info(message)

    if next_status == TaskStatus.DONE:
        message += "\n\nThe task is fully complete."
        return ToolResponse(status="success", message=message)

    return ToolResponse(status="success", message=message, next_prompt=f"To proceed, call `alfred.work_on(task_id='{task_id}')` to get the next action.")
