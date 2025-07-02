from pathlib import Path
import json
from typing import Dict, Any
from src.alfred.state.manager import state_manager


class StateVerificationUtility:
    """Utility class for verifying Alfred state persistence and integrity."""

    def verify_task_status(self, task_id: str, expected_status: str) -> bool:
        """Verify that a task has the expected status."""
        try:
            current_state = self.get_current_task_state(task_id)
            if current_state is None:
                return False
            actual_status = current_state.get("status", "")
            return actual_status == expected_status
        except Exception:
            return False

    def verify_tool_state_exists(self, task_id: str) -> bool:
        """Check if a tool state exists for the given task."""
        try:
            tool_state = state_manager.get_tool_state(task_id)
            return tool_state is not None
        except Exception:
            return False

    def verify_state_file_exists(self, task_id: str) -> bool:
        """Check if the state file exists for the given task."""
        try:
            # Use state manager's internal path structure
            state_dir = Path(".alfred/state")
            task_state_file = state_dir / f"{task_id}.json"
            return task_state_file.exists()
        except Exception:
            return False

    def get_current_task_state(self, task_id: str) -> Dict[str, Any]:
        """Get the current state of a task from the state manager."""
        try:
            # Try to get task state from state manager
            task_state = state_manager.get_task_state(task_id)
            if task_state:
                return task_state

            # Fallback: try to read from state file directly
            state_dir = Path(".alfred/state")
            task_state_file = state_dir / f"{task_id}.json"

            if task_state_file.exists():
                with open(task_state_file, "r") as f:
                    return json.load(f)

            return {}
        except Exception as e:
            print(f"Error getting task state for {task_id}: {e}")
            return {}

    def get_tool_state(self, task_id: str) -> Dict[str, Any]:
        """Get the current tool state for a task."""
        try:
            tool_state = state_manager.get_tool_state(task_id)
            return tool_state if tool_state else {}
        except Exception as e:
            print(f"Error getting tool state for {task_id}: {e}")
            return {}

    def verify_state_consistency(self, task_id: str) -> Dict[str, bool]:
        """Run comprehensive state consistency checks."""
        results = {
            "task_state_exists": bool(self.get_current_task_state(task_id)),
            "tool_state_exists": self.verify_tool_state_exists(task_id),
            "state_file_exists": self.verify_state_file_exists(task_id),
        }

        # Additional consistency checks
        task_state = self.get_current_task_state(task_id)
        if task_state:
            results["has_valid_status"] = "status" in task_state
            results["has_task_id"] = task_state.get("task_id") == task_id

        return results
