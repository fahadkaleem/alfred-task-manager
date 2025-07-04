# src/alfred/state/manager.py
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Dict, TYPE_CHECKING

from alfred.lib.fs_utils import file_lock

if TYPE_CHECKING:
    from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.structured_logger import get_logger
from alfred.models.state import TaskState, WorkflowState
from alfred.models.schemas import TaskStatus
from alfred.config.settings import settings
from pydantic import BaseModel

logger = get_logger(__name__)


class StateManager:
    """
    Simplified state manager with direct methods instead of UoW pattern.

    Each method handles its own locking and atomic writes.
    """

    def _get_task_dir(self, task_id: str) -> Path:
        return settings.workspace_dir / task_id

    def _get_task_state_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "task_state.json"

    def _get_lock_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / ".state.lock"

    def _atomic_write(self, state: TaskState) -> None:
        """Atomically write state to disk. Assumes lock is already held."""
        state_file = self._get_task_state_file(state.task_id)
        state.updated_at = datetime.now(timezone.utc).isoformat()

        # Ensure directory structure exists
        task_dir = state_file.parent
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create empty scratchpad if it doesn't exist
        scratchpad_path = task_dir / "scratchpad.md"
        if not scratchpad_path.exists():
            scratchpad_path.touch(mode=0o600)

        # Atomic write using temp file
        fd, temp_path_str = tempfile.mkstemp(dir=state_file.parent, prefix=".tmp_state_", suffix=".json")
        temp_path = Path(temp_path_str)

        try:
            with os.fdopen(fd, "w") as f:
                f.write(state.model_dump_json(indent=2))
            os.replace(temp_path, state_file)
            logger.debug("Atomically wrote state", task_id=state.task_id)
        except Exception:
            if temp_path.exists():
                os.remove(temp_path)
            raise

    def load_or_create(self, task_id: str) -> TaskState:
        """Load task state from disk, creating if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)

        if not state_file.exists():
            logger.info("No state file found, creating new state", task_id=task_id)
            return TaskState(task_id=task_id)

        try:
            with state_file.open("r") as f:
                data = json.load(f)
            return TaskState.model_validate(data)
        except Exception as e:
            logger.error("Failed to load or validate state, creating new", task_id=task_id, error=str(e))
            return TaskState(task_id=task_id)

    # Backward compatibility alias
    def load_or_create_task_state(self, task_id: str) -> TaskState:
        """Alias for backward compatibility."""
        return self.load_or_create(task_id)

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        """Update task status with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            old_status = state.task_status
            state.task_status = new_status
            self._atomic_write(state)

        logger.info("Updated task status", task_id=task_id, old_status=old_status.value, new_status=new_status.value)

    def update_tool_state(self, task_id: str, tool: Any) -> None:
        """Update tool state with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)

            # Serialize context store
            serializable_context = {}
            for key, value in tool.context_store.items():
                if isinstance(value, BaseModel):
                    serializable_context[key] = value.model_dump()
                else:
                    serializable_context[key] = value

            # Create workflow state
            tool_state = WorkflowState(task_id=task_id, tool_name=tool.tool_name, current_state=str(tool.state), context_store=serializable_context)

            state.active_tool_state = tool_state
            self._atomic_write(state)

        logger.debug("Updated tool state", task_id=task_id, tool_name=tool.tool_name)

    def clear_tool_state(self, task_id: str) -> None:
        """Clear active tool state with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            state.active_tool_state = None
            self._atomic_write(state)

        logger.info("Cleared tool state", task_id=task_id)

    def add_completed_output(self, task_id: str, tool_name: str, artifact: Any) -> None:
        """Add completed tool output with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)

            # Serialize artifact
            if isinstance(artifact, BaseModel):
                serializable_artifact = artifact.model_dump()
            else:
                serializable_artifact = artifact

            state.completed_tool_outputs[tool_name] = serializable_artifact
            self._atomic_write(state)

        logger.info("Added completed output", task_id=task_id, tool_name=tool_name)

    @contextmanager
    def complex_update(self, task_id: str):
        """
        Context manager for complex updates that need multiple field changes.

        This is only needed when you need to update multiple fields atomically.
        For single field updates, use the direct methods above.

        Example:
            with state_manager.complex_update(task_id) as state:
                state.task_status = TaskStatus.IN_PROGRESS
                state.active_tool_state = tool_state
                # Changes are automatically saved on context exit
        """
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            original_data = state.model_dump_json()

            try:
                yield state
                # Only write if state actually changed
                if state.model_dump_json() != original_data:
                    self._atomic_write(state)
                    logger.debug("Complex update completed", task_id=task_id)
            except Exception as e:
                logger.error("Complex update failed", task_id=task_id, error=str(e), exc_info=True)
                raise

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        from alfred.constants import Paths

        archive_path = self._get_task_dir(task_id) / Paths.ARCHIVE_DIR
        archive_path.mkdir(parents=True, exist_ok=True)
        return archive_path

    def register_tool(self, task_id: str, tool: "BaseWorkflowTool") -> None:
        """Register a tool with the orchestrator and update state."""
        from alfred.orchestration.orchestrator import orchestrator

        orchestrator.active_tools[task_id] = tool
        self.update_tool_state(task_id, tool)
        logger.info("Registered tool", task_id=task_id, tool_name=tool.tool_name)


# Singleton instance
state_manager = StateManager()
