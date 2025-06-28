# File: src/epic_task_manager/models/core.py

# Standard library imports
from typing import Any

# Third-party imports
from pydantic import BaseModel, Field

# Local application imports
# (none needed)


class TaskState(BaseModel):
    """Represents the persisted state of a single task"""

    task_id: str
    current_state: str
    # We will store the full state dictionary from the 'transitions' library
    machine_state: dict[str, Any] = Field(default_factory=dict)
    # Stores feedback notes during revision loops
    revision_feedback: str | None = None
    # Tracks if this task is currently active
    is_active: bool = Field(default=False)
    # The index of the next execution step to be processed in a multi-step phase
    current_step: int = Field(default=0, description="The index of the next execution step to be processed in a multi-step phase.")
    # A list of completed step IDs for the current phase
    completed_steps: list[str] = Field(default_factory=list, description="A list of completed step IDs for the current phase.")


class StateFile(BaseModel):
    """Represents the root state.json file"""

    tasks: dict[str, TaskState] = Field(default_factory=dict)
