# src/alfred/models/state.py
"""
Pydantic models for Alfred's state management.
This module defines the single source of truth for task state.
"""
from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

from src.alfred.models.schemas import TaskStatus


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
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UnifiedTaskState(BaseModel):
    """
    The single, unified state object for a task.
    This is the schema for the new `task_state.json` file.
    """

    task_id: str
    task_status: TaskStatus = Field(default=TaskStatus.NEW)
    active_tool_state: Optional[WorkflowState] = Field(default=None)
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())