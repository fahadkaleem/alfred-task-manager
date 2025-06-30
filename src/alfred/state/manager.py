# src/alfred/state/manager.py
"""
State management for Alfred.
Provides atomic state persistence for the TaskState object.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from src.alfred.config.settings import settings
from src.alfred.constants import Paths
from src.alfred.lib.logger import get_logger
from src.alfred.models.schemas import TaskStatus
from src.alfred.models.state import TaskState, WorkflowState

logger = get_logger(__name__)


class StateManager:
    """Manages the persistent state for a single task via task_state.json."""

    def _get_task_state_file(self, task_id: str) -> Path:
        """Gets the path to the unified state file for a task."""
        return settings.workspace_dir / task_id / "task_state.json"

    def load_or_create(self, task_id: str) -> TaskState:
        """Loads a task's unified state from disk, or creates it if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)
        if not state_file.exists():
            logger.info(f"No state file found for task {task_id}. Creating new state.")
            new_state = TaskState(task_id=task_id)
            self.save_task_state(new_state)
            return new_state

        try:
            state_json = state_file.read_text()
            state_data = TaskState.model_validate_json(state_json)
            tool_name = state_data.active_tool_state.tool_name if state_data.active_tool_state else "None"
            logger.info(f"Loaded state for task {task_id}. Status: {state_data.task_status.value}, Active Tool: {tool_name}.")
            return state_data
        except Exception as e:
            logger.error(f"Failed to load or validate state for task {task_id}, creating new state. Error: {e}")
            new_state = TaskState(task_id=task_id)
            self.save_task_state(new_state)
            return new_state

    def save_task_state(self, state: TaskState) -> None:
        """Atomically saves the entire unified state for a task."""
        from src.alfred.lib.artifact_manager import artifact_manager

        state.updated_at = datetime.utcnow().isoformat()
        state_file = self._get_task_state_file(state.task_id)

        # Ensure the complete workspace structure is created (including archive dir)
        if not state_file.parent.exists():
            artifact_manager.create_task_workspace(state.task_id)

        temp_file = state_file.with_suffix(Paths.JSON_EXTENSION + Paths.TMP_EXTENSION)
        try:
            temp_file.write_text(state.model_dump_json(indent=2))
            temp_file.replace(state_file)
            logger.info(f"Successfully saved state for task {state.task_id}.")
        except Exception as e:
            logger.error(f"Failed to save state for task {state.task_id}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> TaskState:
        """Loads, updates the task_status, and saves the state."""
        state = self.load_or_create(task_id)
        state.task_status = new_status
        self.save_task_state(state)
        logger.info(f"Updated task {task_id} status to {new_status.value}")
        return state

    def update_tool_state(self, task_id: str, tool: "BaseWorkflowTool") -> TaskState:
        """Loads, updates the tool state portion, and saves."""
        state = self.load_or_create(task_id)

        serializable_context = {}
        if tool.context_store:
            for key, value in tool.context_store.items():
                if isinstance(value, BaseModel):
                    serializable_context[key] = value.model_dump()
                else:
                    serializable_context[key] = value

        tool_state_data = WorkflowState(
            task_id=task_id,
            tool_name=tool.tool_name,
            current_state=str(tool.state),
            context_store=serializable_context,
            updated_at=datetime.utcnow().isoformat(),
        )
        state.active_tool_state = tool_state_data
        self.save_task_state(state)
        return state

    def clear_tool_state(self, task_id: str) -> TaskState:
        """Loads, clears the active tool state, and saves."""
        state = self.load_or_create(task_id)
        if state.active_tool_state:
            logger.info(f"Clearing active tool state for task {task_id}.")
            state.active_tool_state = None
            self.save_task_state(state)
        return state

    def load_or_create_task_state(self, task_id: str) -> TaskState:
        return self.load_or_create(task_id)

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        archive_path = settings.workspace_dir / task_id / Paths.ARCHIVE_DIR
        archive_path.mkdir(parents=True, exist_ok=True)
        return archive_path

    def register_tool(self, task_id: str, tool: "BaseWorkflowTool") -> None:
        """Register a tool with the orchestrator and update state."""
        from src.alfred.orchestration.orchestrator import orchestrator

        orchestrator.active_tools[task_id] = tool
        self.update_tool_state(task_id, tool)
        logger.info(f"Registered {tool.tool_name} tool for task {task_id}")


# Singleton instance
state_manager = StateManager()
