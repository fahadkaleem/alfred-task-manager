"""
State management for Alfred workflow tools.

Provides atomic state persistence and recovery capabilities.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.constants import Paths

logger = get_logger(__name__)


class StateManager:
    """
    Manages persistent state for workflow tools.

    This class provides:
    - Atomic state persistence with temp file + rename
    - State recovery from disk
    - Cleanup of completed tool states
    """

    def __init__(self):
        """Initialize the state manager with the workspace directory."""
        self.state_dir = settings.alfred_dir / "workspace"

    def get_task_state_file(self, task_id: str) -> Path:
        """
        Get the state file path for a task.

        Args:
            task_id: The task identifier

        Returns:
            Path to the tool state file
        """
        return self.state_dir / task_id / Paths.TOOL_STATE_FILE

    def save_tool_state(self, task_id: str, tool: Any) -> None:
        """
        Atomically save tool state to disk.

        This method ensures state is persisted safely using a temp file
        and atomic rename operation.

        Args:
            task_id: The task identifier
            tool: The workflow tool instance to persist
        """
        logger.info(f"[STATE_MANAGER] save_tool_state called for task {task_id}")
        logger.info(f"[STATE_MANAGER] Tool info - name: {tool.tool_name}, state: {tool.state}, context_keys: {list(tool.context_store.keys())}")

        from src.alfred.models.state import WorkflowState

        # Create the state data
        # Convert any Pydantic models in context_store to dicts
        serializable_context = {}
        for key, value in tool.context_store.items():
            if hasattr(value, "model_dump"):
                # It's a Pydantic model, convert to dict
                serializable_context[key] = value.model_dump()
            else:
                serializable_context[key] = value

        state_data = WorkflowState(
            task_id=task_id,
            tool_name=tool.tool_name,
            current_state=str(tool.state),  # Convert enum to string
            context_store=serializable_context,
            persona_name=tool.persona_name,
            artifact_map_states=[str(state) for state in tool.artifact_map.keys()],
            updated_at=datetime.utcnow().isoformat(),
        )

        # Ensure directory exists
        state_file = self.get_task_state_file(task_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[STATE_MANAGER] Writing state to {state_file}")

        # Atomic write with temp file
        temp_file = state_file.with_suffix(".tmp")
        try:
            temp_file.write_text(state_data.model_dump_json(indent=2))
            temp_file.replace(state_file)
            logger.info(f"[STATE_MANAGER] Successfully saved tool state for task {task_id} in state {tool.state}")
        except Exception as e:
            logger.error(f"[STATE_MANAGER] Failed to save tool state for task {task_id}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def load_tool_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load persisted tool state from disk.

        Args:
            task_id: The task identifier

        Returns:
            WorkflowState dict if found, None otherwise
        """
        state_file = self.get_task_state_file(task_id)
        if not state_file.exists():
            logger.debug(f"No persisted state found for task {task_id}")
            return None

        try:
            from src.alfred.models.state import WorkflowState

            state_json = state_file.read_text()
            state_data = WorkflowState.model_validate_json(state_json)
            logger.info(f"Loaded tool state for task {task_id}: {state_data.tool_name} in state {state_data.current_state}")
            return state_data.model_dump()
        except Exception as e:
            logger.error(f"Failed to load tool state for task {task_id}: {e}")
            return None

    def clear_tool_state(self, task_id: str) -> None:
        """
        Remove tool state when a workflow completes.

        Args:
            task_id: The task identifier
        """
        state_file = self.get_task_state_file(task_id)
        if state_file.exists():
            try:
                state_file.unlink()
                logger.debug(f"Cleared tool state for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to clear tool state for task {task_id}: {e}")

    def has_persisted_state(self, task_id: str) -> bool:
        """
        Check if a task has persisted state.

        Args:
            task_id: The task identifier

        Returns:
            True if state file exists, False otherwise
        """
        return self.get_task_state_file(task_id).exists()


# Singleton instance
state_manager = StateManager()
