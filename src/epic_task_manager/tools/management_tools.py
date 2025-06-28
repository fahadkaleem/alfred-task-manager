# File: src/epic_task_manager/tools/management_tools.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager

state_manager = StateManager()
prompter = Prompter()


async def inspect_and_manage_task(task_id: str, force_transition: str | None = None) -> ToolResponse:
    """
    Inspects a task's state and valid triggers, or forces a state transition.
    This is a powerful tool for recovering stuck tasks.
    """
    if not settings.config_file.exists():
        return ToolResponse(status=STATUS_ERROR, message="Project not initialized.")

    model = state_manager.get_machine(task_id)
    if not model:
        return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

    current_state = model.state

    # --- CORRECTED LOGIC ---
    # Use the library's built-in method to get a list of valid triggers for the current state.
    valid_trigger_names = model.get_triggers(current_state)
    # --- END CORRECTION ---

    if force_transition is None:
        # --- Inspection Mode ---
        data = {
            "task_id": task_id,
            "current_state": current_state,
            "valid_triggers": valid_trigger_names,
        }
        message = "Task state inspected. See data for available triggers."
        return ToolResponse(status=STATUS_SUCCESS, message=message, data=data)
    # --- Management (Force Transition) Mode ---
    if force_transition not in valid_trigger_names:
        error_message = f"Invalid transition '{force_transition}' from state '{current_state}'. Valid triggers are: {valid_trigger_names}"
        return ToolResponse(status=STATUS_ERROR, message=error_message)

    try:
        # Dynamically call the trigger method on the model (e.g., model.advance())
        trigger_func = getattr(model, force_transition)
        trigger_func()

        # Persist the new state
        state_manager.save_machine_state(task_id, model)

        # Get the prompt for the new state
        next_prompt = prompter.generate_prompt(task_id, model.state)

        message = f"Successfully forced transition '{force_transition}'. Task '{task_id}' is now in state '{model.state}'."
        return ToolResponse(status=STATUS_SUCCESS, message=message, next_prompt=next_prompt)

    except Exception as e:
        # Catch any other errors during the transition process
        return ToolResponse(
            status=STATUS_ERROR,
            message=f"Failed to force transition '{force_transition}': {e}",
        )
