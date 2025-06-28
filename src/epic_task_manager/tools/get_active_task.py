# src/epic_task_manager/tools/get_active_task.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager


async def get_active_task() -> ToolResponse:
    """
    Gets the currently active task. If the active task is complete, it instructs
    the client to find the next available task.
    """
    if not settings.config_file.exists():
        return ToolResponse(status=STATUS_ERROR, message="Project not initialized. Please run 'initialize_project' first.")

    state_manager = StateManager()
    active_task_id = state_manager.get_active_task()

    if not active_task_id:
        # No active task exists. The correct next action is to find one.
        return ToolResponse(
            status=STATUS_SUCCESS,
            message="No active task found.",
            data={"active_task_id": None},
            next_prompt=(
                "<objective>Inform the user there is no active task and find available work.</objective>\n"
                "<instructions>Call the `list_available_tasks` tool to discover what to work on.</instructions>"
            ),
        )

    # An active task exists, we must check its state.
    machine = state_manager.get_machine(active_task_id)

    if machine and machine.state == "done":
        # The active task is complete. It should not be worked on. Find the next one.
        state_manager.deactivate_all_tasks()  # Clean up the invalid active state.
        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Active task {active_task_id} is already complete.",
            data={"active_task_id": active_task_id, "status": "done"},
            next_prompt=(
                "<objective>Inform the user the active task is complete and find the next one.</objective>\n"
                f"<instructions>1. Report to the user that task '{active_task_id}' is done.\n"
                "2. Call the `list_available_tasks` tool to discover what to work on next.</instructions>"
            ),
        )

    # The active task exists and is not done. Return its ID for work to be resumed.
    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Active task is {active_task_id}.",
        data={"active_task_id": active_task_id},
        next_prompt=(
            "<objective>Resume work on the active task.</objective>\n"
            f"<instructions>An active task, '{active_task_id}', was found. Call `begin_or_resume_task` to continue working on it.</instructions>"
        ),
    )
