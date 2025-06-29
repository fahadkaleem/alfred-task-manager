"""
Pydantic models for Alfred's state management.
"""

from datetime import datetime
from typing import Dict, Any, List
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


class WorkflowState(BaseModel):
    """
    Represents the complete state of a workflow tool.
    
    This model captures all necessary information to reconstruct
    a workflow tool after a crash or restart.
    """
    
    task_id: str
    tool_name: str
    current_state: str  # String representation of the state enum
    context_store: Dict[str, Any] = Field(default_factory=dict)
    persona_name: str
    artifact_map_states: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
