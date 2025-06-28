# Standard library imports
import json

# Third-party imports
from transitions.extensions.factory import HierarchicalMachine

# Local application imports
from epic_task_manager.config.settings import settings
from epic_task_manager.models.core import StateFile, TaskState

from .machine import INITIAL_STATE, states, transitions


class TaskAlreadyExistsError(ValueError):
    """Raised when attempting to create a task that already exists."""


class TaskNotFoundError(ValueError):
    """Raised when attempting to access a non-existent task."""


class TaskModel:
    """A simple model class for the state machine to bind to."""


class StateManager:
    """Manages loading, saving, and interacting with the Task HSM."""

    def __init__(self):
        self.state_file_path = settings.state_file

    def _load_state_file(self) -> StateFile:
        """Always load fresh state from disk to avoid caching issues."""
        if not self.state_file_path.exists():
            return StateFile()
        try:
            data = json.loads(self.state_file_path.read_text())
            return StateFile(**data)
        except (json.JSONDecodeError, FileNotFoundError):
            return StateFile()

    def _save_state_file(self, state: StateFile) -> None:
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_file_path.write_text(state.model_dump_json(indent=2))

    def get_machine(self, task_id: str) -> TaskModel | None:
        """Loads and returns the HSM for a specific task."""
        state_file = self._load_state_file()
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            return None

        model = TaskModel()
        HierarchicalMachine(
            model=model,
            states=states,
            transitions=transitions,
            initial=task_state.current_state,
        )
        return model

    def create_machine(self, task_id: str) -> TaskModel:
        """Creates a new task and its HSM."""
        state_file = self._load_state_file()
        if task_id in state_file.tasks:
            raise TaskAlreadyExistsError

        task_state = TaskState(task_id=task_id, current_state=INITIAL_STATE)
        state_file.tasks[task_id] = task_state

        model = TaskModel()
        HierarchicalMachine(model=model, states=states, transitions=transitions, initial=INITIAL_STATE)
        self._save_state_file(state_file)

        return model

    def save_machine_state(self, task_id: str, model: TaskModel, feedback: str | None = None) -> None:
        """Saves the current state of a task's HSM."""
        state_file = self._load_state_file()
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            raise TaskNotFoundError

        task_state.current_state = model.state
        task_state.revision_feedback = feedback

        state_file.tasks[task_id] = task_state
        self._save_state_file(state_file)

    def set_active_task(self, task_id: str) -> None:
        """Mark a task as active and deactivate all others."""
        state_file = self._load_state_file()
        if task_id not in state_file.tasks:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Deactivate all tasks
        for task in state_file.tasks.values():
            task.is_active = False

        # Activate the specified task
        state_file.tasks[task_id].is_active = True
        self._save_state_file(state_file)

    def get_active_task(self) -> str | None:
        """Get the currently active task ID, if any."""
        state_file = self._load_state_file()
        for task_id, task_state in state_file.tasks.items():
            if task_state.is_active:
                return task_id
        return None

    def deactivate_all_tasks(self) -> None:
        """Deactivate all tasks."""
        state_file = self._load_state_file()
        for task in state_file.tasks.values():
            task.is_active = False
        self._save_state_file(state_file)
