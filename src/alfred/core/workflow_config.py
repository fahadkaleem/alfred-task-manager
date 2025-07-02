"""
Centralized workflow configuration system.

This module defines the complete workflow lifecycle and all transitions
in a single place, eliminating duplication across the codebase.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

from src.alfred.models.schemas import TaskStatus
from src.alfred.constants import ToolName


@dataclass(frozen=True)
class WorkflowPhase:
    """
    Represents a single phase in the task workflow.

    A phase is a combination of status and the tool used to process it.
    """

    status: TaskStatus
    tool_name: str
    next_status: Optional[TaskStatus] = None
    produces_artifact: bool = True
    terminal: bool = False
    description: str = ""

    @property
    def is_entry_point(self) -> bool:
        """Check if this phase can be an entry point for its tool."""
        return self.status in TOOL_ENTRY_POINTS.get(self.tool_name, [])


@dataclass(frozen=True)
class WorkflowTransition:
    """Represents a transition between workflow phases."""

    from_status: TaskStatus
    to_status: TaskStatus
    trigger: str = "approve"  # Default trigger
    condition: Optional[str] = None  # Optional condition for transition


class WorkflowConfiguration:
    """
    Central configuration for the entire Alfred workflow.

    This class defines:
    - All workflow phases and their relationships
    - Valid status transitions
    - Tool entry points
    - Phase metadata
    """

    # Define all workflow phases in order
    PHASES: List[WorkflowPhase] = [
        # Initial phase
        WorkflowPhase(status=TaskStatus.NEW, tool_name=ToolName.PLAN_TASK, next_status=TaskStatus.PLANNING, description="New task ready for planning"),
        # Planning phase
        WorkflowPhase(status=TaskStatus.PLANNING, tool_name=ToolName.PLAN_TASK, next_status=TaskStatus.READY_FOR_DEVELOPMENT, description="Task being planned"),
        # Spec creation phases (for epics)
        WorkflowPhase(
            status=TaskStatus.NEW,  # Alternate path for epics
            tool_name=ToolName.CREATE_SPEC,
            next_status=TaskStatus.CREATING_SPEC,
            description="New epic ready for spec creation",
        ),
        WorkflowPhase(status=TaskStatus.CREATING_SPEC, tool_name=ToolName.CREATE_SPEC, next_status=TaskStatus.SPEC_COMPLETED, description="Creating technical specification"),
        WorkflowPhase(
            status=TaskStatus.SPEC_COMPLETED,
            tool_name=ToolName.CREATE_TASKS_FROM_SPEC,
            next_status=TaskStatus.CREATING_TASKS,
            produces_artifact=False,  # This is a transition phase
            description="Spec completed, ready to create tasks",
        ),
        WorkflowPhase(status=TaskStatus.CREATING_TASKS, tool_name=ToolName.CREATE_TASKS_FROM_SPEC, next_status=TaskStatus.TASKS_CREATED, description="Breaking down spec into tasks"),
        WorkflowPhase(
            status=TaskStatus.TASKS_CREATED,
            tool_name=ToolName.PLAN_TASK,
            next_status=TaskStatus.PLANNING,
            produces_artifact=False,  # Transition to planning first task
            description="Tasks created, ready to plan first one",
        ),
        # Development phase
        WorkflowPhase(
            status=TaskStatus.READY_FOR_DEVELOPMENT,
            tool_name=ToolName.IMPLEMENT_TASK,
            next_status=TaskStatus.IN_DEVELOPMENT,
            produces_artifact=False,  # This is entry to development
            description="Ready to start implementation",
        ),
        WorkflowPhase(status=TaskStatus.IN_DEVELOPMENT, tool_name=ToolName.IMPLEMENT_TASK, next_status=TaskStatus.READY_FOR_REVIEW, description="Implementation in progress"),
        # Review phase
        WorkflowPhase(status=TaskStatus.READY_FOR_REVIEW, tool_name=ToolName.REVIEW_TASK, next_status=TaskStatus.IN_REVIEW, produces_artifact=False, description="Ready for code review"),
        WorkflowPhase(status=TaskStatus.IN_REVIEW, tool_name=ToolName.REVIEW_TASK, next_status=TaskStatus.READY_FOR_TESTING, description="Code review in progress"),
        # Testing phase
        WorkflowPhase(status=TaskStatus.READY_FOR_TESTING, tool_name=ToolName.TEST_TASK, next_status=TaskStatus.IN_TESTING, produces_artifact=False, description="Ready for testing"),
        WorkflowPhase(status=TaskStatus.IN_TESTING, tool_name=ToolName.TEST_TASK, next_status=TaskStatus.READY_FOR_FINALIZATION, description="Testing in progress"),
        # Finalization phase
        WorkflowPhase(status=TaskStatus.READY_FOR_FINALIZATION, tool_name=ToolName.FINALIZE_TASK, next_status=TaskStatus.IN_FINALIZATION, produces_artifact=False, description="Ready to finalize"),
        WorkflowPhase(status=TaskStatus.IN_FINALIZATION, tool_name=ToolName.FINALIZE_TASK, next_status=TaskStatus.DONE, description="Creating commit and PR"),
        # Revision handling phase
        WorkflowPhase(
            status=TaskStatus.REVISIONS_REQUESTED,
            tool_name="",  # No specific tool, depends on context
            next_status=None,  # Depends on which phase requested revisions
            produces_artifact=False,
            description="Revisions requested, awaiting fixes",
        ),
        # Terminal phase
        WorkflowPhase(
            status=TaskStatus.DONE,
            tool_name="",  # No tool for done status
            next_status=None,
            terminal=True,
            produces_artifact=False,
            description="Task completed",
        ),
    ]

    # Build lookup maps
    _BY_STATUS: Dict[TaskStatus, List[WorkflowPhase]] = {}
    _BY_TOOL_AND_STATUS: Dict[Tuple[str, TaskStatus], WorkflowPhase] = {}

    @classmethod
    def _build_lookups(cls):
        """Build lookup maps from phases."""
        if not cls._BY_STATUS:  # Only build once
            for phase in cls.PHASES:
                if phase.status not in cls._BY_STATUS:
                    cls._BY_STATUS[phase.status] = []
                cls._BY_STATUS[phase.status].append(phase)

                if phase.tool_name:
                    cls._BY_TOOL_AND_STATUS[(phase.tool_name, phase.status)] = phase

    @classmethod
    def get_phase(cls, status: TaskStatus, tool_name: Optional[str] = None) -> Optional[WorkflowPhase]:
        """Get the workflow phase for a given status, optionally filtered by tool."""
        cls._build_lookups()

        phases = cls._BY_STATUS.get(status, [])
        if not phases:
            return None

        if tool_name:
            # Filter by tool if specified
            for phase in phases:
                if phase.tool_name == tool_name:
                    return phase
            return None

        # Return the first phase for this status
        return phases[0]

    @classmethod
    def get_phase_by_tool(cls, tool_name: str, status: TaskStatus) -> Optional[WorkflowPhase]:
        """Get the workflow phase for a specific tool and status."""
        cls._build_lookups()
        return cls._BY_TOOL_AND_STATUS.get((tool_name, status))

    @classmethod
    def get_next_phase(cls, current_status: TaskStatus, tool_name: Optional[str] = None) -> Optional[WorkflowPhase]:
        """Get the next phase in the workflow."""
        current_phase = cls.get_phase(current_status, tool_name)
        if current_phase and current_phase.next_status:
            return cls.get_phase(current_phase.next_status)
        return None

    @classmethod
    def get_tool_for_status(cls, status: TaskStatus) -> Optional[str]:
        """Get the tool that handles a given status."""
        phase = cls.get_phase(status)
        return phase.tool_name if phase and phase.tool_name else None

    @classmethod
    def get_artifact_producer(cls, status: TaskStatus) -> Optional[str]:
        """Get the tool that produces artifacts for a given status."""
        phase = cls.get_phase(status)
        if phase and phase.produces_artifact and phase.tool_name:
            return phase.tool_name
        return None

    @classmethod
    def get_phases_for_tool(cls, tool_name: str) -> List[WorkflowPhase]:
        """Get all phases handled by a specific tool."""
        return [p for p in cls.PHASES if p.tool_name == tool_name]

    @classmethod
    def is_terminal_status(cls, status: TaskStatus) -> bool:
        """Check if a status is terminal."""
        phase = cls.get_phase(status)
        return phase.terminal if phase else False

    @classmethod
    def get_workflow_step_number(cls, status: TaskStatus) -> int:
        """Get the step number in the workflow (for archiving)."""
        # Define the main workflow sequence
        main_sequence = [
            TaskStatus.NEW,
            TaskStatus.CREATING_SPEC,
            TaskStatus.CREATING_TASKS,
            TaskStatus.PLANNING,
            TaskStatus.IN_DEVELOPMENT,
            TaskStatus.IN_REVIEW,
            TaskStatus.IN_TESTING,
            TaskStatus.IN_FINALIZATION,
            TaskStatus.DONE,
        ]

        try:
            # Find closest matching status in sequence
            if status in main_sequence:
                return main_sequence.index(status) + 1

            # Handle intermediate statuses
            if status == TaskStatus.SPEC_COMPLETED:
                return main_sequence.index(TaskStatus.CREATING_SPEC) + 1
            elif status == TaskStatus.TASKS_CREATED:
                return main_sequence.index(TaskStatus.CREATING_TASKS) + 1
            elif status == TaskStatus.READY_FOR_DEVELOPMENT:
                return main_sequence.index(TaskStatus.PLANNING) + 1
            elif status == TaskStatus.READY_FOR_REVIEW:
                return main_sequence.index(TaskStatus.IN_DEVELOPMENT) + 1
            elif status == TaskStatus.READY_FOR_TESTING:
                return main_sequence.index(TaskStatus.IN_REVIEW) + 1
            elif status == TaskStatus.READY_FOR_FINALIZATION:
                return main_sequence.index(TaskStatus.IN_TESTING) + 1

            return 0  # Unknown status
        except ValueError:
            return 0


# Tool entry points - which statuses can start each tool
TOOL_ENTRY_POINTS: Dict[str, List[TaskStatus]] = {
    ToolName.CREATE_SPEC: [TaskStatus.NEW, TaskStatus.CREATING_SPEC],
    ToolName.CREATE_TASKS_FROM_SPEC: [TaskStatus.SPEC_COMPLETED, TaskStatus.CREATING_TASKS],
    ToolName.PLAN_TASK: [TaskStatus.NEW, TaskStatus.PLANNING, TaskStatus.TASKS_CREATED],
    ToolName.IMPLEMENT_TASK: [TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.IN_DEVELOPMENT],
    ToolName.REVIEW_TASK: [TaskStatus.READY_FOR_REVIEW, TaskStatus.IN_REVIEW],
    ToolName.TEST_TASK: [TaskStatus.READY_FOR_TESTING, TaskStatus.IN_TESTING],
    ToolName.FINALIZE_TASK: [TaskStatus.READY_FOR_FINALIZATION, TaskStatus.IN_FINALIZATION],
}


# Status transition validation
VALID_TRANSITIONS: Dict[TaskStatus, List[TaskStatus]] = {
    TaskStatus.NEW: [TaskStatus.CREATING_SPEC, TaskStatus.PLANNING],
    TaskStatus.CREATING_SPEC: [TaskStatus.SPEC_COMPLETED],
    TaskStatus.SPEC_COMPLETED: [TaskStatus.CREATING_TASKS],
    TaskStatus.CREATING_TASKS: [TaskStatus.TASKS_CREATED],
    TaskStatus.TASKS_CREATED: [TaskStatus.PLANNING],
    TaskStatus.PLANNING: [TaskStatus.READY_FOR_DEVELOPMENT],
    TaskStatus.READY_FOR_DEVELOPMENT: [TaskStatus.IN_DEVELOPMENT],
    TaskStatus.IN_DEVELOPMENT: [TaskStatus.READY_FOR_REVIEW],
    TaskStatus.READY_FOR_REVIEW: [TaskStatus.IN_REVIEW],
    TaskStatus.IN_REVIEW: [TaskStatus.READY_FOR_TESTING, TaskStatus.IN_DEVELOPMENT],  # Can go back for revisions
    TaskStatus.READY_FOR_TESTING: [TaskStatus.IN_TESTING],
    TaskStatus.IN_TESTING: [TaskStatus.READY_FOR_FINALIZATION, TaskStatus.IN_DEVELOPMENT],  # Can go back
    TaskStatus.READY_FOR_FINALIZATION: [TaskStatus.IN_FINALIZATION],
    TaskStatus.IN_FINALIZATION: [TaskStatus.DONE],
    TaskStatus.DONE: [],  # Terminal state
}


def validate_transition(from_status: TaskStatus, to_status: TaskStatus) -> bool:
    """Validate if a status transition is allowed."""
    valid_next = VALID_TRANSITIONS.get(from_status, [])
    return to_status in valid_next
