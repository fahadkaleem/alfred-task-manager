# File: src/epic_task_manager/tools/inspect_archived_artifact.py

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.exceptions import TaskNotFoundError
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager


async def inspect_archived_artifact(task_id: str, phase_name: str) -> ToolResponse:
    """Get the content of an archived artifact for a completed phase."""
    if not settings.config_file.exists():
        return ToolResponse(
            status=STATUS_ERROR,
            message="Project not initialized. Please run the 'initialize_project' tool first.",
        )

    try:
        state_manager = StateManager()
        artifact_manager = ArtifactManager()

        if not state_manager.get_machine(task_id):
            return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

        valid_phases = ["gatherrequirements", "planning", "coding", "testing", "finalize"]
        if phase_name not in valid_phases:
            return ToolResponse(
                status=STATUS_ERROR,
                message=f"Invalid phase_name '{phase_name}'. Must be one of: {', '.join(valid_phases)}",
            )

        archive_path = artifact_manager.get_archive_path(task_id, phase_name, 1)

        if not archive_path.exists():
            return ToolResponse(
                status=STATUS_ERROR,
                message=f"No archived artifact found for task {task_id} phase '{phase_name}'. The phase may not have been completed yet.",
            )

        artifact_content = archive_path.read_text(encoding="utf-8")

        response_data = {
            "task_id": task_id,
            "phase_name": phase_name,
            "artifact_content": artifact_content,
        }

        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Archived artifact for phase '{phase_name}' retrieved.",
            data=response_data,
        )

    except (TaskNotFoundError, FileNotFoundError, PermissionError) as e:
        return ToolResponse(
            status=STATUS_ERROR,
            message=f"Failed to inspect archived artifact: {e!s}",
        )
