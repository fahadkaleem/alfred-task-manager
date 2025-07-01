# src/alfred/state/unit_of_work.py
from __future__ import annotations
import json
import os
import tempfile
from typing import Any, Dict, TYPE_CHECKING

from pydantic import BaseModel

from src.alfred.lib.fs_utils import file_lock
from src.alfred.lib.logger import get_logger
from src.alfred.models.state import TaskState, WorkflowState

if TYPE_CHECKING:
    from src.alfred.core.workflow import BaseWorkflowTool
    from src.alfred.models.schemas import TaskStatus
    from src.alfred.state.manager import StateManager

logger = get_logger(__name__)


class StateUnitOfWork:
    """Implements the Unit of Work pattern for atomic state updates."""

    def __init__(self, state_manager: "StateManager"):
        self.state_manager = state_manager
        self._pending_changes: Dict[str, TaskState] = {}
        self._loaded_states: Dict[str, TaskState] = {}

    def _get_current_state(self, task_id: str) -> TaskState:
        """Gets the current state, loading it from disk or cache if necessary."""
        if task_id in self._pending_changes:
            return self._pending_changes[task_id]
        if task_id in self._loaded_states:
            return self._loaded_states[task_id]

        state = self.state_manager.load_or_create(task_id, lock=False)
        self._loaded_states[task_id] = state
        return state

    def update_task_status(self, task_id: str, status: "TaskStatus"):
        """Stage a status update."""
        state = self._get_current_state(task_id)
        state.task_status = status
        self._pending_changes[task_id] = state

    def update_tool_state(self, task_id: str, tool: "BaseWorkflowTool"):
        """Stage a tool state update."""
        state = self._get_current_state(task_id)
        serializable_context = {key: value.model_dump() if isinstance(value, BaseModel) else value for key, value in tool.context_store.items()}
        tool_state_data = WorkflowState(task_id=task_id, tool_name=tool.tool_name, current_state=str(tool.state), context_store=serializable_context)
        state.active_tool_state = tool_state_data
        self._pending_changes[task_id] = state

    def clear_tool_state(self, task_id: str):
        """Stage the clearing of a tool state."""
        state = self._get_current_state(task_id)
        state.active_tool_state = None
        self._pending_changes[task_id] = state

    def add_completed_output(self, task_id: str, tool_name: str, artifact: Any):
        """Stage the addition of a completed tool's output."""
        state = self._get_current_state(task_id)
        serializable_artifact = artifact.model_dump() if isinstance(artifact, BaseModel) else artifact
        state.completed_tool_outputs[tool_name] = serializable_artifact
        self._pending_changes[task_id] = state

    def commit(self):
        """Atomically commit all pending changes for all tasks."""
        if not self._pending_changes:
            logger.debug("No pending state changes to commit.")
            return

        for task_id, state in self._pending_changes.items():
            lock_file = self.state_manager._get_lock_file(task_id)
            with file_lock(lock_file):
                self.state_manager._atomic_write(state)

        logger.info(f"Committed state changes for tasks: {list(self._pending_changes.keys())}")
        self._pending_changes.clear()
        self._loaded_states.clear()

    def rollback(self):
        """Discard all pending changes."""
        if self._pending_changes:
            logger.warning(f"Rolling back pending state changes for tasks: {list(self._pending_changes.keys())}")
        self._pending_changes.clear()
        self._loaded_states.clear()
