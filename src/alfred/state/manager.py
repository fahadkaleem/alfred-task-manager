# src/alfred/state/manager.py
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from src.alfred.lib.fs_utils import file_lock
from src.alfred.lib.logger import get_logger
from src.alfred.models.state import TaskState
from src.alfred.state.unit_of_work import StateUnitOfWork
from src.alfred.models.schemas import TaskStatus

logger = get_logger(__name__)


class StateManager:
    """Manages the persistence layer for TaskState objects."""

    def _get_task_dir(self, task_id: str) -> Path:
        from src.alfred.config.settings import settings

        return settings.workspace_dir / task_id

    def _get_task_state_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "task_state.json"

    def _get_lock_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / ".state.lock"

    def _atomic_write(self, state: TaskState):
        """Internal atomic file write, assumes lock is held."""
        state_file = self._get_task_state_file(state.task_id)
        state.updated_at = datetime.utcnow().isoformat()

        # Create the complete workspace structure
        task_dir = state_file.parent
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create archive directory
        archive_dir = task_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        # Create empty scratchpad.md if it doesn't exist
        scratchpad_path = task_dir / "scratchpad.md"
        if not scratchpad_path.exists():
            scratchpad_path.touch(mode=0o600)  # Create with restricted permissions

        fd, temp_path_str = tempfile.mkstemp(dir=state_file.parent, prefix=".tmp_")
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(state.model_dump_json(indent=2))
            os.replace(temp_path, state_file)
        except Exception:
            if temp_path.exists():
                os.remove(temp_path)
            raise

    def load_or_create(self, task_id: str, lock: bool = True) -> TaskState:
        """Loads a task's state from disk, creating it if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)

        def _load():
            if not state_file.exists():
                logger.info(f"No state file for task {task_id}. Creating new state.")
                return TaskState(task_id=task_id)

            try:
                return TaskState.model_validate_json(state_file.read_text())
            except Exception as e:
                logger.error(f"Failed to load or validate state for task {task_id}, creating new. Error: {e}")
                return TaskState(task_id=task_id)

        if lock:
            with file_lock(self._get_lock_file(task_id)):
                return _load()
        return _load()

    @contextmanager
    def transaction(self):
        """Provides a transactional unit of work for state modifications."""
        uow = StateUnitOfWork(self)
        try:
            yield uow
            uow.commit()
        except Exception as e:
            logger.error(f"State transaction failed, rolling back. Error: {e}", exc_info=True)
            uow.rollback()
            raise

    # --- Thin Wrappers for Backward Compatibility ---
    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        with self.transaction() as uow:
            uow.update_task_status(task_id, new_status)

    def update_tool_state(self, task_id: str, tool: Any) -> None:
        with self.transaction() as uow:
            uow.update_tool_state(task_id, tool)

    def clear_tool_state(self, task_id: str) -> None:
        with self.transaction() as uow:
            uow.clear_tool_state(task_id)

    def add_completed_output(self, task_id: str, tool_name: str, artifact: Any) -> None:
        with self.transaction() as uow:
            uow.add_completed_output(task_id, tool_name, artifact)

    def load_or_create_task_state(self, task_id: str) -> TaskState:
        return self.load_or_create(task_id)

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        from src.alfred.constants import Paths

        archive_path = self._get_task_dir(task_id) / Paths.ARCHIVE_DIR
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
