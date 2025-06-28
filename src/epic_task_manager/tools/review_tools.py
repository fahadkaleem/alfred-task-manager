# File: src/epic_task_manager/tools/review_tools.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
prompter = Prompter()


async def approve_or_request_changes(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """The single tool for all reviews (AI and Developer)."""

    if not settings.config_file.exists():
        return ToolResponse(
            status=STATUS_ERROR,
            message="Project not initialized. Please run the 'initialize_project' tool first.",
        )

    model = state_manager.get_machine(task_id)
    if not model:
        return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

    current_state = model.state
    trigger_attempted = ""
    try:
        if is_approved:
            if model.state.endswith("_aireview"):
                trigger_attempted = "ai_approves"
                model.ai_approves()
            elif model.state in ["planning_strategydevreview", "planning_solutiondesigndevreview", "planning_executionplandevreview"]:
                trigger_attempted = "human_approves"
                model.human_approves()
            else:
                return ToolResponse(
                    status=STATUS_ERROR,
                    message=f"Human approval from state '{current_state}' must be done via the 'approve_and_advance' tool.",
                )
        else:
            trigger_attempted = "request_revision"
            model.request_revision()

        state_manager.save_machine_state(task_id, model, feedback=feedback_notes)

        prompt = prompter.generate_prompt(task_id, model.state, revision_feedback=feedback_notes)

        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Review feedback submitted. State transitioned from '{current_state}' to '{model.state}'.",
            next_prompt=prompt,
        )
    except Exception as e:
        # A bit of a hack to get the underlying error from the transitions library
        if "Can't trigger event" in str(e):
            return ToolResponse(
                status=STATUS_ERROR,
                message=f"Invalid action from state '{current_state}'.",
                data={"error_details": {"type": "StateTransitionError", "current_state": current_state, "attempted_transition": trigger_attempted, "message": str(e)}},
            )
        return ToolResponse(status=STATUS_ERROR, message=f"Could not process feedback from state '{current_state}'. Error: {e}", data={"error_details": {"type": type(e).__name__, "message": str(e)}})
