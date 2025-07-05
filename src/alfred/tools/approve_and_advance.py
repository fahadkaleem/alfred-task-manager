from alfred.state.manager import state_manager
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.tools.workflow_utils import get_phase_info, get_next_status
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
def approve_and_advance_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for approve_and_advance compatible with GenericWorkflowHandler."""
    """Approve current phase and advance to next using centralized workflow config."""
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status

    # Check if there's an active workflow tool with sub-states
    workflow_state = task_state.active_tool_state
    if workflow_state:
        # Check if we're in a sub-state (not a main workflow phase)
        state_value = workflow_state.current_state

        # If the state contains underscores or special suffixes, it's likely a sub-state
        if "_" in state_value or state_value.endswith("awaiting_ai_review") or state_value.endswith("awaiting_human_review"):
            return ToolResponse(
                status="error",
                message=f"Cannot use approve_and_advance while in sub-state '{state_value}'. "
                f"The workflow tool '{workflow_state.tool_name}' has internal states that must be completed first.\n\n"
                f"**Next Action**: Call `alfred.approve_review(task_id='{task_id}')` to continue through the current workflow.\n\n"
                f"**Note**: approve_and_advance is only for moving between major phases (e.g., implementation → review), "
                f"not for approving sub-states within a workflow.",
            )

        # Check if we need to verify completion against known states
        # Import tool definitions to check if tool is complete
        from alfred.tools.tool_definitions import get_tool_definition

        tool_definition = get_tool_definition(workflow_state.tool_name)
        if tool_definition:
            # Local import to avoid circular dependency
            from alfred.core.workflow_engine import WorkflowEngine

            engine = WorkflowEngine(tool_definition)

            # Check if current state is terminal
            if not engine.is_terminal_state(state_value):
                # Create temporary tool instance to get final work state
                tool_class = tool_definition.tool_class
                temp_tool = tool_class(task_id=task_id)
                final_state = temp_tool.get_final_work_state()

                return ToolResponse(
                    status="error",
                    message=f"The workflow tool '{workflow_state.tool_name}' is not complete. "
                    f"Current state: '{state_value}', but needs to reach '{final_state}' before advancing phases. "
                    f"Use 'approve_review' or 'submit_work' to continue through the workflow.",
                )

            # Additional check for specific workflow tools with known sub-states
            if workflow_state.tool_name == "plan_task" and state_value not in ["verified", "validation"]:
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
