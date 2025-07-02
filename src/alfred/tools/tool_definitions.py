"""
Declarative tool definition system for Alfred.

This module contains all tool definitions in a single place,
making it trivial to add new tools or modify existing ones.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Type, Optional, Callable, Any
from enum import Enum

from src.alfred.core.workflow import (
    BaseWorkflowTool,
    PlanTaskTool,
    PlanTaskState,
    StartTaskTool,
    StartTaskState,
    ImplementTaskTool,
    ImplementTaskState,
    ReviewTaskTool,
    ReviewTaskState,
    TestTaskTool,
    TestTaskState,
    FinalizeTaskTool,
    FinalizeTaskState,
    CreateSpecTool,
    CreateSpecState,
    CreateTasksTool,
    CreateTasksState,
)
from src.alfred.models.schemas import TaskStatus
from src.alfred.constants import ToolName


@dataclass
class ToolDefinition:
    """Complete definition of a workflow tool."""

    # Basic info
    name: str
    tool_class: Type[BaseWorkflowTool]
    description: str

    # States
    work_states: List[Enum] = field(default_factory=list)
    dispatch_state: Optional[Enum] = None
    terminal_state: Optional[Enum] = None
    initial_state: Optional[Enum] = None

    # Status mapping
    entry_statuses: List[TaskStatus] = field(default_factory=list)
    exit_status: Optional[TaskStatus] = None
    required_status: Optional[TaskStatus] = None

    # Behavior flags
    dispatch_on_init: bool = False
    produces_artifacts: bool = True
    requires_artifact_from: Optional[str] = None

    # Context loading
    context_loader: Optional[Callable[[Any, Any], Dict[str, Any]]] = None

    # Validation
    custom_validator: Optional[Callable[[Any], Optional[str]]] = None

    def get_entry_status_map(self) -> Dict[TaskStatus, TaskStatus]:
        """Build entry status map from definition."""
        if not self.exit_status:
            return {}

        return {entry: self.exit_status for entry in self.entry_statuses}

    def get_all_states(self) -> List[str]:
        """Get all states including review states."""
        states = []

        # Add dispatch state if exists
        if self.dispatch_state:
            states.append(self.dispatch_state.value)

        # Add work states and their review states
        for state in self.work_states:
            state_value = state.value if hasattr(state, "value") else str(state)
            states.append(state_value)
            states.append(f"{state_value}_awaiting_ai_review")
            states.append(f"{state_value}_awaiting_human_review")

        # Add terminal state
        if self.terminal_state:
            states.append(self.terminal_state.value)

        return states

    def validate(self) -> None:
        """Validate the tool definition for consistency."""
        if self.dispatch_on_init and not self.dispatch_state:
            raise ValueError(f"Tool {self.name} has dispatch_on_init=True but no dispatch_state")

        if self.work_states and not self.terminal_state:
            raise ValueError(f"Tool {self.name} has work states but no terminal state")

        if self.entry_statuses and not self.exit_status:
            raise ValueError(f"Tool {self.name} has entry statuses but no exit status")


# Context loaders
def load_execution_plan_context(task, task_state):
    """Load execution plan for implement_task."""
    execution_plan = task_state.completed_tool_outputs.get(ToolName.PLAN_TASK)
    if not execution_plan:
        raise ValueError(f"CRITICAL: Cannot start implementation. Execution plan from 'plan_task' not found for task '{task.task_id}'.")
    return {"artifact_content": execution_plan}


def load_implementation_context(task, task_state):
    """Load implementation manifest for review_task."""
    manifest = task_state.completed_tool_outputs.get(ToolName.IMPLEMENT_TASK)
    return {"implementation_manifest": manifest}


def load_test_context(task, task_state):
    """Load test context from task."""
    return {"ac_verification_steps": getattr(task, "ac_verification_steps", [])}


def load_finalize_context(task, task_state):
    """Load test results for finalize_task."""
    test_results = task_state.completed_tool_outputs.get(ToolName.TEST_TASK)
    return {"test_results": test_results} if test_results else {}


def load_spec_context(task, task_state):
    """Load technical spec for create_tasks."""
    # This is loaded from archive, not task state
    return {}  # Handled specially in create_tasks_impl


# Custom validators
def validate_plan_task_status(task) -> Optional[str]:
    """Validate that task is in correct status for planning."""
    if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
        return f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task."
    return None


# Define all tools declaratively
TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
    ToolName.PLAN_TASK: ToolDefinition(
        name=ToolName.PLAN_TASK,
        tool_class=PlanTaskTool,
        description="Create detailed execution plan for a task",
        work_states=[
            PlanTaskState.CONTEXTUALIZE,
            PlanTaskState.STRATEGIZE,
            PlanTaskState.DESIGN,
            PlanTaskState.GENERATE_SUBTASKS,
        ],
        terminal_state=PlanTaskState.VERIFIED,
        initial_state=PlanTaskState.CONTEXTUALIZE,
        entry_statuses=[TaskStatus.NEW, TaskStatus.PLANNING, TaskStatus.TASKS_CREATED],
        exit_status=TaskStatus.PLANNING,
        dispatch_on_init=False,
        custom_validator=validate_plan_task_status,
    ),
    ToolName.START_TASK: ToolDefinition(
        name=ToolName.START_TASK,
        tool_class=StartTaskTool,
        description="Setup git environment for task",
        work_states=[
            StartTaskState.AWAITING_GIT_STATUS,
            StartTaskState.AWAITING_BRANCH_CREATION,
        ],
        terminal_state=StartTaskState.VERIFIED,
        initial_state=StartTaskState.AWAITING_GIT_STATUS,
        entry_statuses=[TaskStatus.NEW, TaskStatus.PLANNING],
        exit_status=TaskStatus.PLANNING,
        dispatch_on_init=False,
    ),
    ToolName.IMPLEMENT_TASK: ToolDefinition(
        name=ToolName.IMPLEMENT_TASK,
        tool_class=ImplementTaskTool,
        description="Execute the planned implementation",
        work_states=[ImplementTaskState.IMPLEMENTING],
        dispatch_state=ImplementTaskState.DISPATCHING,
        terminal_state=ImplementTaskState.VERIFIED,
        initial_state=ImplementTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.IN_DEVELOPMENT],
        exit_status=TaskStatus.IN_DEVELOPMENT,
        required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        dispatch_on_init=True,
        requires_artifact_from=ToolName.PLAN_TASK,
        context_loader=load_execution_plan_context,
    ),
    ToolName.REVIEW_TASK: ToolDefinition(
        name=ToolName.REVIEW_TASK,
        tool_class=ReviewTaskTool,
        description="Perform code review",
        work_states=[ReviewTaskState.REVIEWING],
        dispatch_state=ReviewTaskState.DISPATCHING,
        terminal_state=ReviewTaskState.VERIFIED,
        initial_state=ReviewTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_REVIEW, TaskStatus.IN_REVIEW],
        exit_status=TaskStatus.IN_REVIEW,
        required_status=TaskStatus.READY_FOR_REVIEW,
        dispatch_on_init=True,
        context_loader=load_implementation_context,
    ),
    ToolName.TEST_TASK: ToolDefinition(
        name=ToolName.TEST_TASK,
        tool_class=TestTaskTool,
        description="Run and validate tests",
        work_states=[TestTaskState.TESTING],
        dispatch_state=TestTaskState.DISPATCHING,
        terminal_state=TestTaskState.VERIFIED,
        initial_state=TestTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_TESTING, TaskStatus.IN_TESTING],
        exit_status=TaskStatus.IN_TESTING,
        required_status=TaskStatus.READY_FOR_TESTING,
        dispatch_on_init=True,
        context_loader=load_test_context,
    ),
    ToolName.FINALIZE_TASK: ToolDefinition(
        name=ToolName.FINALIZE_TASK,
        tool_class=FinalizeTaskTool,
        description="Create commit and pull request",
        work_states=[FinalizeTaskState.FINALIZING],
        dispatch_state=FinalizeTaskState.DISPATCHING,
        terminal_state=FinalizeTaskState.VERIFIED,
        initial_state=FinalizeTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_FINALIZATION, TaskStatus.IN_FINALIZATION],
        exit_status=TaskStatus.IN_FINALIZATION,
        required_status=TaskStatus.READY_FOR_FINALIZATION,
        dispatch_on_init=True,
        context_loader=load_finalize_context,
    ),
    ToolName.CREATE_SPEC: ToolDefinition(
        name=ToolName.CREATE_SPEC,
        tool_class=CreateSpecTool,
        description="Create technical specification from PRD",
        work_states=[CreateSpecState.DRAFTING_SPEC],
        dispatch_state=CreateSpecState.DISPATCHING,
        terminal_state=CreateSpecState.VERIFIED,
        initial_state=CreateSpecState.DISPATCHING,
        entry_statuses=[TaskStatus.NEW, TaskStatus.CREATING_SPEC],
        exit_status=TaskStatus.CREATING_SPEC,
        dispatch_on_init=True,
    ),
    ToolName.CREATE_TASKS_FROM_SPEC: ToolDefinition(
        name=ToolName.CREATE_TASKS_FROM_SPEC,
        tool_class=CreateTasksTool,
        description="Break down spec into actionable tasks",
        work_states=[CreateTasksState.DRAFTING_TASKS],
        dispatch_state=CreateTasksState.DISPATCHING,
        terminal_state=CreateTasksState.VERIFIED,
        initial_state=CreateTasksState.DISPATCHING,
        entry_statuses=[TaskStatus.SPEC_COMPLETED, TaskStatus.CREATING_TASKS],
        exit_status=TaskStatus.CREATING_TASKS,
        required_status=TaskStatus.SPEC_COMPLETED,
        dispatch_on_init=True,
        context_loader=load_spec_context,
    ),
}


# Validate all definitions on module load
for tool_def in TOOL_DEFINITIONS.values():
    tool_def.validate()


def get_tool_definition(tool_name: str) -> ToolDefinition:
    """Get tool definition by name."""
    if tool_name not in TOOL_DEFINITIONS:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_DEFINITIONS[tool_name]


def get_all_tool_names() -> List[str]:
    """Get all registered tool names."""
    return sorted(TOOL_DEFINITIONS.keys())
