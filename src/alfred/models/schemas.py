"""
Pydantic models for Alfred tool responses and core workflow data models.
"""

from typing import Any, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """The standardized response object for all Alfred tools."""

    status: str = Field(description="The status of the operation, typically 'success' or 'error'.")
    message: str = Field(description="A clear, human-readable message describing the result.")
    data: dict[str, Any] | None = Field(default=None)
    next_prompt: str | None = Field(default=None)


class TaskStatus(str, Enum):
    """Enumeration for the high-level status of a Task."""
    NEW = "new"
    PLANNING = "planning"
    READY_FOR_DEVELOPMENT = "ready_for_development"
    IN_DEVELOPMENT = "in_development"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    REVISIONS_REQUESTED = "revisions_requested"
    READY_FOR_TESTING = "ready_for_testing"
    IN_TESTING = "in_testing"
    READY_FOR_FINALIZATION = "ready_for_finalization"
    DONE = "done"


class OperationType(str, Enum):
    """Enumeration for the type of file system operation in a SLOT."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    REVIEW = "review"  # For tasks that only involve reviewing code, not changing it.


class Task(BaseModel):
    """Represents a single, well-defined unit of work (a user story or engineering task)."""
    task_id: str = Field(description="The unique identifier, e.g., 'TS-01'.")
    title: str = Field(description="A short, human-readable title for the task.")
    context: str = Field(description="The background for this task, explaining the 'why'.")
    implementation_details: str = Field(description="A high-level overview of the proposed 'how'.")
    dev_notes: Optional[str] = Field(None, description="Optional notes for the developer.")
    acceptance_criteria: List[str] = Field(default_factory=list)
    ac_verification_steps: List[str] = Field(default_factory=list)
    task_status: TaskStatus = Field(default=TaskStatus.NEW)


class Taskflow(BaseModel):
    """Defines the step-by-step procedure and verification for a SLOT."""
    procedural_steps: List[str] = Field(description="Sequential steps for the AI to execute.")
    verification_steps: List[str] = Field(description="Checks or tests to verify the SLOT is complete.")


class SLOT(BaseModel):
    """The core, self-contained, and atomic unit of technical work."""
    slot_id: str = Field(description="A unique ID for this SLOT, e.g., 'slot_1.1'.")
    title: str = Field(description="A short, human-readable title for the SLOT.")
    spec: str = Field(description="The detailed specification for this change.")
    location: str = Field(description="The primary file path or directory for the work.")
    operation: OperationType = Field(description="The type of file system operation.")
    taskflow: Taskflow = Field(description="The detailed workflow for execution and testing.")
