# File: src/epic_task_manager/tools/get_task_summary.py

import json

import yaml

from epic_task_manager.config.settings import settings
from epic_task_manager.constants import STATUS_ERROR, STATUS_SUCCESS
from epic_task_manager.exceptions import StateFileError, TaskNotFoundError
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.manager import StateManager


async def get_task_summary(task_id: str) -> ToolResponse:
    """Get a lightweight summary of a task's current status."""
    if not settings.config_file.exists():
        return ToolResponse(
            status=STATUS_ERROR,
            message="Project not initialized. Please run the 'initialize_project' tool first.",
        )

    try:
        state_manager = StateManager()
        artifact_manager = ArtifactManager()

        model = state_manager.get_machine(task_id)
        if not model:
            return ToolResponse(status=STATUS_ERROR, message=f"Task {task_id} not found.")

        current_state = model.state
        artifact_status = "unknown"
        try:
            artifact_content = artifact_manager.read_artifact(task_id)
            if artifact_content:
                metadata, _ = artifact_manager.parse_artifact(artifact_content)
                artifact_status = metadata.get("status", "unknown")
            else:
                artifact_status = "missing"
        except (yaml.YAMLError, json.JSONDecodeError, UnicodeDecodeError):
            artifact_status = "invalid_format"

        summary_data = {
            "task_id": task_id,
            "current_state": current_state,
            "artifact_status": artifact_status,
            "is_active": state_manager.get_active_task() == task_id,
        }

        return ToolResponse(
            status=STATUS_SUCCESS,
            message="Task summary retrieved successfully.",
            data=summary_data,
        )

    except (TaskNotFoundError, StateFileError, FileNotFoundError, PermissionError) as e:
        return ToolResponse(status=STATUS_ERROR, message=f"Failed to get task summary: {e!s}")
