"""
Declarative tool definition system for Alfred.

This module contains all tool definitions in a single place,
making it trivial to add new tools or modify existing ones.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Type, Optional, Callable, Any
from enum import Enum

from alfred.core.workflow import (
    BaseWorkflowTool,
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
)
from alfred.core.discovery_workflow import PlanTaskTool, PlanTaskState
from alfred.core.discovery_context import load_plan_task_context
from alfred.models.schemas import TaskStatus
from alfred.constants import ToolName

# Import logic functions for simple tools
from alfred.tools.get_next_task import get_next_task_logic
from alfred.tools.work_on import work_on_logic
from alfred.tools.create_task import create_task_logic
from alfred.tools.approve_review import approve_review_logic
from alfred.tools.request_revision import request_revision_logic
from alfred.tools.approve_and_advance import approve_and_advance_logic
from alfred.tools.initialize import initialize_project_logic
from alfred.tools.create_spec import create_spec_logic
from alfred.tools.create_tasks_from_spec import create_tasks_logic


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
        # Special cases for tools that need immediate status transitions
        if self.name == ToolName.IMPLEMENT_TASK:
            return {
                TaskStatus.READY_FOR_DEVELOPMENT: TaskStatus.IN_DEVELOPMENT,
                TaskStatus.IN_DEVELOPMENT: TaskStatus.IN_DEVELOPMENT
            }
        elif self.name == ToolName.REVIEW_TASK:
            return {
                TaskStatus.READY_FOR_REVIEW: TaskStatus.IN_REVIEW,
                TaskStatus.IN_REVIEW: TaskStatus.IN_REVIEW
            }
        elif self.name == ToolName.TEST_TASK:
            return {
                TaskStatus.READY_FOR_TESTING: TaskStatus.IN_TESTING,
                TaskStatus.IN_TESTING: TaskStatus.IN_TESTING
            }
        elif self.name == ToolName.FINALIZE_TASK:
            return {
                TaskStatus.READY_FOR_FINALIZATION: TaskStatus.IN_FINALIZATION,
                TaskStatus.IN_FINALIZATION: TaskStatus.IN_FINALIZATION
            }
        
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
        """Enhanced validation supporting simple tools."""
        # Case 1: Workflow tool (existing logic)
        if self.tool_class is not None:
            if self.dispatch_on_init and not self.dispatch_state:
                raise ValueError(f"Tool {self.name} has dispatch_on_init=True but no dispatch_state")

            if self.work_states and not self.terminal_state:
                raise ValueError(f"Tool {self.name} has work states but no terminal state")

            if self.entry_statuses and not self.exit_status:
                raise ValueError(f"Tool {self.name} has entry statuses but no exit status")

        # Case 2: Simple tool (new logic)
        elif self.tool_class is None:
            if self.context_loader is None:
                raise ValueError(f"Simple tool {self.name} must have context_loader as logic function")

            if any([self.work_states, self.dispatch_state, self.terminal_state, self.initial_state]):
                raise ValueError(f"Simple tool {self.name} cannot have workflow states")

            if self.dispatch_on_init:
                raise ValueError(f"Simple tool {self.name} cannot use dispatch_on_init")

        else:
            raise ValueError(f"Tool {self.name} must have either tool_class or context_loader")


# Context loaders
def load_execution_plan_context(task, task_state):
    """Load execution plan for implement_task."""
    from alfred.lib.turn_manager import turn_manager

    # Get the implementation_plan artifact from turns
    latest_artifacts = turn_manager.get_latest_artifacts_by_state(task.task_id)

    # Get the implementation_plan artifact specifically (which contains subtasks)
    implementation_plan = latest_artifacts.get("implementation_plan")
    if not implementation_plan:
        raise ValueError(f"CRITICAL: Cannot start implementation. Implementation plan not found for task '{task.task_id}'.")

    # Return the implementation plan with subtasks
    return {"artifact_content": implementation_plan}


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
        description="""
        Interactive planning with deep context discovery and conversational clarification.
        
        This tool implements a comprehensive planning workflow that mirrors how expert developers 
        actually approach complex tasks:
        
        1. DISCOVERY: Deep context gathering using all available tools in parallel
        2. CLARIFICATION: Conversational Q&A to resolve ambiguities  
        3. CONTRACTS: Interface-first design of all APIs and data models
        4. IMPLEMENTATION_PLAN: Self-contained subtask creation with full context
        5. VALIDATION: Final coherence check and human approval
        
        Features:
        - Context saturation before planning begins
        - Real human-AI conversation for ambiguity resolution
        - Contract-first design approach
        - Self-contained subtasks with no rediscovery needed
        - Re-planning support for changing requirements
        - Complexity adaptation (can skip contracts for simple tasks)
        """,
        work_states=[
            PlanTaskState.DISCOVERY,
            PlanTaskState.CLARIFICATION,
            PlanTaskState.CONTRACTS,
            PlanTaskState.IMPLEMENTATION_PLAN,
            PlanTaskState.VALIDATION,
        ],
        terminal_state=PlanTaskState.VERIFIED,
        initial_state=PlanTaskState.DISCOVERY,
        entry_statuses=[TaskStatus.NEW, TaskStatus.PLANNING, TaskStatus.TASKS_CREATED],
        exit_status=TaskStatus.READY_FOR_DEVELOPMENT,
        dispatch_on_init=False,
        context_loader=load_plan_task_context,
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
        exit_status=TaskStatus.READY_FOR_REVIEW,
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
        exit_status=TaskStatus.READY_FOR_TESTING,
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
        exit_status=TaskStatus.READY_FOR_FINALIZATION,
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
        exit_status=TaskStatus.DONE,
        required_status=TaskStatus.READY_FOR_FINALIZATION,
        dispatch_on_init=True,
        context_loader=load_finalize_context,
    ),
    ToolName.CREATE_SPEC: ToolDefinition(
        name=ToolName.CREATE_SPEC,
        tool_class=None,
        description="Create technical specification from PRD",
        context_loader=create_spec_logic,
    ),
    ToolName.CREATE_TASKS_FROM_SPEC: ToolDefinition(
        name=ToolName.CREATE_TASKS_FROM_SPEC,
        tool_class=None,
        description="Break down spec into actionable tasks",
        context_loader=create_tasks_logic,
    ),
    # Simple tools (tool_class=None, logic in context_loader)
    ToolName.GET_NEXT_TASK: ToolDefinition(
        name=ToolName.GET_NEXT_TASK,
        tool_class=None,
        description="Intelligently determines and recommends the next task to work on",
        context_loader=get_next_task_logic,
    ),
    ToolName.WORK_ON_TASK: ToolDefinition(
        name=ToolName.WORK_ON_TASK,
        tool_class=None,
        description="Primary entry point for working on any task - Smart Dispatch model",
        context_loader=work_on_logic,
    ),
    ToolName.CREATE_TASK: ToolDefinition(
        name=ToolName.CREATE_TASK,
        tool_class=None,
        description="Creates a new task in the Alfred system using standardized template format",
        context_loader=create_task_logic,
    ),
    ToolName.APPROVE_REVIEW: ToolDefinition(
        name=ToolName.APPROVE_REVIEW,
        tool_class=None,
        description="Approves the artifact in the current review step and advances the workflow",
        context_loader=approve_review_logic,
    ),
    ToolName.REQUEST_REVISION: ToolDefinition(
        name=ToolName.REQUEST_REVISION,
        tool_class=None,
        description="Rejects the artifact in the current review step and sends it back for revision",
        context_loader=request_revision_logic,
    ),
    ToolName.APPROVE_AND_ADVANCE: ToolDefinition(
        name=ToolName.APPROVE_AND_ADVANCE,
        tool_class=None,
        description="Approves the current phase and advances to the next phase in the workflow",
        context_loader=approve_and_advance_logic,
    ),
    ToolName.INITIALIZE_PROJECT: ToolDefinition(
        name=ToolName.INITIALIZE_PROJECT,
        tool_class=None,
        description="Initializes the project workspace for Alfred",
        context_loader=initialize_project_logic,
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
