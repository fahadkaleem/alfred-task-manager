# File: src/epic_task_manager/tools/progress_tools.py

from pydantic import ValidationError

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.execution.exceptions import ArtifactNotFoundError, InvalidArtifactError
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.artifacts import ExecutionPlanArtifact
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
prompter = Prompter()
artifact_manager = ArtifactManager()


async def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """
    Marks a single step as complete, persists state, and returns the next step.
    This is the core checkpoint tool for resilient, multi-step phase execution.
    """
    if not settings.config_file.exists():
        return ToolResponse(status=STATUS_ERROR, message="Project not initialized.")

    model = state_manager.get_machine(task_id)
    if not model or getattr(model, "state", None) != "coding_working":
        current_state = "Not Found" if not model else getattr(model, "state", "Unknown")
        return ToolResponse(status=STATUS_ERROR, message=f"Invalid state: Tool can only be used in 'coding_working'. Current state: {current_state}")

    try:
        # --- START REFACTOR ---
        # REMOVE all old regex and parsing logic here.
        # REPLACE with direct JSON loading.

        # Load the execution plan DIRECTLY from the JSON artifact
        plan_data = artifact_manager.read_json_artifact(task_id, "planning")
        plan = ExecutionPlanArtifact(**plan_data)
        # --- END REFACTOR ---

        state_file = state_manager._load_state_file()
        task_state = state_file.tasks[task_id]

        # Validate step
        if task_state.current_step >= len(plan.execution_steps):
            return ToolResponse(status=STATUS_ERROR, message="All steps are already complete. You should call 'submit_for_review' now.")

        expected_step_id = plan.execution_steps[task_state.current_step].prompt_id
        if step_id != expected_step_id:
            return ToolResponse(status=STATUS_ERROR, message=f"Incorrect step ID. Expected '{expected_step_id}', but received '{step_id}'.")

        # Update state
        task_state.completed_steps.append(step_id)
        task_state.current_step += 1
        state_manager._save_state_file(state_file)

        # Check if all steps are complete
        if task_state.current_step == len(plan.execution_steps):
            next_prompt = (
                "# All Execution Steps Complete\n\n"
                "You have successfully executed all steps in the plan. The final action is to submit a lightweight completion manifest.\n\n"
                "Please call the `submit_for_review` tool now with the following structure:\n"
                '```json\n{\n  "implementation_summary": "string - High-level summary of what was implemented",\n  "execution_steps_completed": ["array of strings - should match the completed_steps list"],\n  "testing_notes": "string - Instructions for testing the implementation"\n}\n```'
            )
            message = f"Step '{step_id}' completed. All steps finished. Ready for final submission."
        else:
            # Generate prompt for the next step
            next_prompt = prompter.generate_prompt(task_id, getattr(model, "state", "coding_working"))
            message = f"Step '{step_id}' completed. Proceeding to next step."

        return ToolResponse(status=STATUS_SUCCESS, message=message, next_prompt=next_prompt)

    except (ArtifactNotFoundError, InvalidArtifactError, ValidationError, Exception) as e:
        return ToolResponse(status=STATUS_ERROR, message=f"An error occurred: {e}")
