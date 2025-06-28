"""
Pydantic models for Alfred's state management.
"""

from pydantic import BaseModel, Field


class TaskState(BaseModel):
    """Represents the persisted state of a single task."""

    task_id: str
    workflow_step: int = 0
    persona_state: str | None = None
    is_active: bool = False
    execution_plan: dict | None = None  # Holds the active plan for stepwise personas
    current_step: int = 0
    completed_steps: list[str] = Field(default_factory=list)
    revision_feedback: str | None = None


class StateFile(BaseModel):
    """Represents the root state.json file."""

    tasks: dict[str, TaskState] = Field(default_factory=dict)
