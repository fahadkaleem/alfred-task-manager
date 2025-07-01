"""
Workflow tool configuration system for eliminating handler duplication.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Type, Callable, Any
from enum import Enum

from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.models.schemas import TaskStatus
from src.alfred.state.manager import state_manager
from src.alfred.core.workflow_config import TOOL_ENTRY_POINTS, WorkflowConfiguration


@dataclass
class WorkflowToolConfig:
    """Configuration for a workflow tool, replacing individual handlers."""

    # Basic configuration
    tool_name: str
    tool_class: Type[BaseWorkflowTool]
    required_status: Optional[TaskStatus] = None

    # Entry status mapping (for status transitions on tool creation)
    entry_status_map: Dict[TaskStatus, TaskStatus] = None

    # Dispatch configuration
    dispatch_on_init: bool = False
    dispatch_state_attr: Optional[str] = None  # e.g., "DISPATCHING"
    target_state_method: str = "dispatch"  # method to call for state transition

    # Context loading configuration
    context_loader: Optional[Callable[[Any, Any], Dict[str, Any]]] = None

    # Validation
    requires_artifact_from: Optional[str] = None  # e.g., ToolName.PLAN_TASK

    def __post_init__(self):
        """Validate configuration consistency."""
        if self.dispatch_on_init and not self.dispatch_state_attr:
            raise ValueError(f"Tool {self.tool_name} has dispatch_on_init=True but no dispatch_state_attr")

        if self.entry_status_map is None:
            self.entry_status_map = {}


# Define all tool configurations
def load_execution_plan_context(task, task_state):
    """Context loader for implement_task."""
    from src.alfred.constants import ToolName

    execution_plan = task_state.completed_tool_outputs.get(ToolName.PLAN_TASK)
    if not execution_plan:
        raise ValueError(f"CRITICAL: Cannot start implementation. Execution plan from 'plan_task' not found for task '{task.task_id}'.")

    return {"artifact_content": execution_plan}


def load_implementation_context(task, task_state):
    """Context loader for review_task."""
    from src.alfred.constants import ToolName

    implementation_manifest = task_state.completed_tool_outputs.get(ToolName.IMPLEMENT_TASK)
    return {"implementation_manifest": implementation_manifest}


def load_test_context(task, task_state):
    """Context loader for test_task."""
    return {"ac_verification_steps": getattr(task, "ac_verification_steps", [])}


def load_finalize_context(task, task_state):
    """Context loader for finalize_task."""
    from src.alfred.constants import ToolName

    test_results = task_state.completed_tool_outputs.get(ToolName.TEST_TASK)
    context = {}
    if test_results:
        context["test_results"] = test_results
    return context


# Tool Configuration Registry
from src.alfred.constants import ToolName
from src.alfred.core.workflow import (
    PlanTaskTool,
    PlanTaskState,
    ImplementTaskTool,
    ImplementTaskState,
    ReviewTaskTool,
    ReviewTaskState,
    TestTaskTool,
    TestTaskState,
    FinalizeTaskTool,
    FinalizeTaskState,
)

WORKFLOW_TOOL_CONFIGS = {
    ToolName.PLAN_TASK: WorkflowToolConfig(
        tool_name=ToolName.PLAN_TASK,
        tool_class=PlanTaskTool,
        required_status=None,  # Special validation in setup
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.PLAN_TASK]
            if WorkflowConfiguration.get_phase(status) and WorkflowConfiguration.get_phase(status).next_status
        },
        dispatch_on_init=False,  # Plan task doesn't auto-dispatch
    ),
    ToolName.IMPLEMENT_TASK: WorkflowToolConfig(
        tool_name=ToolName.IMPLEMENT_TASK,
        tool_class=ImplementTaskTool,
        required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.IMPLEMENT_TASK]
            if WorkflowConfiguration.get_phase(status) and WorkflowConfiguration.get_phase(status).next_status
        },
        dispatch_on_init=True,
        dispatch_state_attr=ImplementTaskState.DISPATCHING.value,
        context_loader=load_execution_plan_context,
        requires_artifact_from=ToolName.PLAN_TASK,
    ),
    ToolName.REVIEW_TASK: WorkflowToolConfig(
        tool_name=ToolName.REVIEW_TASK,
        tool_class=ReviewTaskTool,
        required_status=TaskStatus.READY_FOR_REVIEW,
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.REVIEW_TASK]
            if WorkflowConfiguration.get_phase(status) and WorkflowConfiguration.get_phase(status).next_status
        },
        dispatch_on_init=True,
        dispatch_state_attr=ReviewTaskState.DISPATCHING.value,
        context_loader=load_implementation_context,
    ),
    ToolName.TEST_TASK: WorkflowToolConfig(
        tool_name=ToolName.TEST_TASK,
        tool_class=TestTaskTool,
        required_status=TaskStatus.READY_FOR_TESTING,
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.TEST_TASK]
            if WorkflowConfiguration.get_phase(status) and WorkflowConfiguration.get_phase(status).next_status
        },
        dispatch_on_init=True,
        dispatch_state_attr=TestTaskState.DISPATCHING.value,
        context_loader=load_test_context,
    ),
    ToolName.FINALIZE_TASK: WorkflowToolConfig(
        tool_name=ToolName.FINALIZE_TASK,
        tool_class=FinalizeTaskTool,
        required_status=TaskStatus.READY_FOR_FINALIZATION,
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.FINALIZE_TASK]
            if WorkflowConfiguration.get_phase(status) and WorkflowConfiguration.get_phase(status).next_status
        },
        dispatch_on_init=True,
        dispatch_state_attr=FinalizeTaskState.DISPATCHING.value,
        context_loader=load_finalize_context,
    ),
}
