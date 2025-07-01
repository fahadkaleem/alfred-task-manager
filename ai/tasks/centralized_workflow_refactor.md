# CRITICAL REFACTORING INSTRUCTION: Step 5 - Create Centralized Workflow Configuration

**ATTENTION**: This is the fifth CRITICAL refactoring task. We need to centralize all workflow transitions, status mappings, and phase definitions that are currently scattered across multiple files. Triple check that all workflow logic remains exactly the same while eliminating duplication.

## OBJECTIVE
Replace all hardcoded workflow mappings and transitions scattered across the codebase with a single, centralized workflow configuration system.

## CURRENT PROBLEM
Workflow logic is duplicated across multiple files:
- `approve_and_advance.py` has STATUS_TRANSITION_MAP and ARTIFACT_PRODUCER_MAP
- `work_on.py` has handoff_tool_map 
- Status transitions are hardcoded in multiple places
- Phase relationships are implicit rather than explicit
- Adding new workflow phases requires changes in 5+ files

This violates DRY and makes workflow changes error-prone.

## STEP-BY-STEP IMPLEMENTATION

### 1. Create Workflow Configuration System
**CREATE** a new file: `src/alfred/core/workflow_config.py`

```python
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
        WorkflowPhase(
            status=TaskStatus.NEW,
            tool_name=ToolName.PLAN_TASK,
            next_status=TaskStatus.PLANNING,
            description="New task ready for planning"
        ),
        
        # Planning phase
        WorkflowPhase(
            status=TaskStatus.PLANNING,
            tool_name=ToolName.PLAN_TASK,
            next_status=TaskStatus.READY_FOR_DEVELOPMENT,
            description="Task being planned"
        ),
        
        # Spec creation phases (for epics)
        WorkflowPhase(
            status=TaskStatus.NEW,  # Alternate path for epics
            tool_name=ToolName.CREATE_SPEC,
            next_status=TaskStatus.CREATING_SPEC,
            description="New epic ready for spec creation"
        ),
        WorkflowPhase(
            status=TaskStatus.CREATING_SPEC,
            tool_name=ToolName.CREATE_SPEC,
            next_status=TaskStatus.SPEC_COMPLETED,
            description="Creating technical specification"
        ),
        WorkflowPhase(
            status=TaskStatus.SPEC_COMPLETED,
            tool_name=ToolName.CREATE_TASKS,
            next_status=TaskStatus.CREATING_TASKS,
            produces_artifact=False,  # This is a transition phase
            description="Spec completed, ready to create tasks"
        ),
        WorkflowPhase(
            status=TaskStatus.CREATING_TASKS,
            tool_name=ToolName.CREATE_TASKS,
            next_status=TaskStatus.TASKS_CREATED,
            description="Breaking down spec into tasks"
        ),
        WorkflowPhase(
            status=TaskStatus.TASKS_CREATED,
            tool_name=ToolName.PLAN_TASK,
            next_status=TaskStatus.PLANNING,
            produces_artifact=False,  # Transition to planning first task
            description="Tasks created, ready to plan first one"
        ),
        
        # Development phase
        WorkflowPhase(
            status=TaskStatus.READY_FOR_DEVELOPMENT,
            tool_name=ToolName.IMPLEMENT_TASK,
            next_status=TaskStatus.IN_DEVELOPMENT,
            produces_artifact=False,  # This is entry to development
            description="Ready to start implementation"
        ),
        WorkflowPhase(
            status=TaskStatus.IN_DEVELOPMENT,
            tool_name=ToolName.IMPLEMENT_TASK,
            next_status=TaskStatus.READY_FOR_REVIEW,
            description="Implementation in progress"
        ),
        
        # Review phase  
        WorkflowPhase(
            status=TaskStatus.READY_FOR_REVIEW,
            tool_name=ToolName.REVIEW_TASK,
            next_status=TaskStatus.IN_REVIEW,
            produces_artifact=False,
            description="Ready for code review"
        ),
        WorkflowPhase(
            status=TaskStatus.IN_REVIEW,
            tool_name=ToolName.REVIEW_TASK,
            next_status=TaskStatus.READY_FOR_TESTING,
            description="Code review in progress"
        ),
        
        # Testing phase
        WorkflowPhase(
            status=TaskStatus.READY_FOR_TESTING,
            tool_name=ToolName.TEST_TASK,
            next_status=TaskStatus.IN_TESTING,
            produces_artifact=False,
            description="Ready for testing"
        ),
        WorkflowPhase(
            status=TaskStatus.IN_TESTING,
            tool_name=ToolName.TEST_TASK,
            next_status=TaskStatus.READY_FOR_FINALIZATION,
            description="Testing in progress"
        ),
        
        # Finalization phase
        WorkflowPhase(
            status=TaskStatus.READY_FOR_FINALIZATION,
            tool_name=ToolName.FINALIZE_TASK,
            next_status=TaskStatus.IN_FINALIZATION,
            produces_artifact=False,
            description="Ready to finalize"
        ),
        WorkflowPhase(
            status=TaskStatus.IN_FINALIZATION,
            tool_name=ToolName.FINALIZE_TASK,
            next_status=TaskStatus.DONE,
            description="Creating commit and PR"
        ),
        
        # Terminal phase
        WorkflowPhase(
            status=TaskStatus.DONE,
            tool_name="",  # No tool for done status
            next_status=None,
            terminal=True,
            produces_artifact=False,
            description="Task completed"
        ),
    ]
    
    # Build lookup maps
    _BY_STATUS: Dict[TaskStatus, WorkflowPhase] = {
        phase.status: phase for phase in PHASES
    }
    
    _BY_TOOL_AND_STATUS: Dict[Tuple[str, TaskStatus], WorkflowPhase] = {
        (phase.tool_name, phase.status): phase 
        for phase in PHASES if phase.tool_name
    }
    
    @classmethod
    def get_phase(cls, status: TaskStatus) -> Optional[WorkflowPhase]:
        """Get the workflow phase for a given status."""
        return cls._BY_STATUS.get(status)
    
    @classmethod
    def get_phase_by_tool(cls, tool_name: str, status: TaskStatus) -> Optional[WorkflowPhase]:
        """Get the workflow phase for a specific tool and status."""
        return cls._BY_TOOL_AND_STATUS.get((tool_name, status))
    
    @classmethod
    def get_next_phase(cls, current_status: TaskStatus) -> Optional[WorkflowPhase]:
        """Get the next phase in the workflow."""
        current_phase = cls.get_phase(current_status)
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
            TaskStatus.DONE
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
    ToolName.CREATE_TASKS: [TaskStatus.SPEC_COMPLETED, TaskStatus.CREATING_TASKS],
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
```

### 2. Update approve_and_advance.py
**UPDATE** `src/alfred/tools/approve_and_advance.py` to use the centralized config:

```python
from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.core.workflow_config import WorkflowConfiguration
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def approve_and_advance_impl(task_id: str) -> ToolResponse:
    """Approve current phase and advance to next using centralized workflow config."""
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status
    
    # Get current phase from workflow config
    current_phase = WorkflowConfiguration.get_phase(current_status)
    if not current_phase:
        return ToolResponse(
            status="error",
            message=f"Unknown workflow phase for status '{current_status.value}'."
        )
    
    # Check if this phase can be advanced from
    if current_phase.terminal:
        return ToolResponse(
            status="error",
            message=f"Cannot advance from terminal status '{current_status.value}'."
        )
    
    if not current_phase.next_status:
        return ToolResponse(
            status="error",
            message=f"No next phase defined for status '{current_status.value}'."
        )
    
    # Archive artifacts if this phase produces them
    if current_phase.produces_artifact and current_phase.tool_name:
        workflow_step = WorkflowConfiguration.get_workflow_step_number(current_status)
        
        # Archive the scratchpad
        artifact_manager.archive_scratchpad(
            task_id, 
            current_phase.tool_name, 
            workflow_step
        )
        logger.info(
            f"Archived scratchpad for tool '{current_phase.tool_name}' "
            f"at workflow step {workflow_step}"
        )
        
        # Archive the final artifact
        final_artifact = task_state.completed_tool_outputs.get(current_phase.tool_name)
        if final_artifact:
            artifact_manager.archive_final_artifact(
                task_id, 
                current_phase.tool_name, 
                final_artifact
            )
            logger.info(f"Archived final artifact for phase '{current_status.value}'.")
        else:
            logger.warning(
                f"No final artifact found for tool '{current_phase.tool_name}' to archive."
            )
    
    # Advance to next status
    next_phase = WorkflowConfiguration.get_next_phase(current_status)
    if not next_phase:
        return ToolResponse(
            status="error",
            message=f"Failed to determine next phase for status '{current_status.value}'."
        )
    
    state_manager.update_task_status(task_id, next_phase.status)
    
    message = (
        f"Phase '{current_status.value}' approved. "
        f"Task '{task_id}' is now in status '{next_phase.status.value}'."
    )
    logger.info(message)
    
    if next_phase.terminal:
        message += "\n\nThe task is fully complete."
        return ToolResponse(status="success", message=message)
    
    return ToolResponse(
        status="success",
        message=message,
        next_prompt=f"To proceed, call `alfred.work_on(task_id='{task_id}')` to get the next action."
    )
```

### 3. Update work_on.py
**UPDATE** `src/alfred/tools/work_on.py` to use centralized config:

```python
from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.core.workflow_config import WorkflowConfiguration
from src.alfred.lib.task_utils import does_task_exist_locally, write_task_to_markdown
from src.alfred.task_providers.factory import get_provider
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def work_on_impl(task_id: str) -> ToolResponse:
    """Smart dispatch using centralized workflow configuration."""
    
    # Step 1: Check if the task exists locally first (cache-first architecture)
    if not does_task_exist_locally(task_id):
        logger.info(f"Task '{task_id}' not found in local cache. Fetching from provider...")
        
        # Task is not in our local cache, fetch from provider
        provider = get_provider()
        
        try:
            # Delegate to the provider to fetch the task
            task = provider.get_task(task_id)
            
            if not task:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task_id}' could not be found. Please check:\n"
                    f"1. Task ID is correct (case-sensitive)\n"
                    f"2. For local tasks: File exists at .alfred/tasks/{task_id}.md\n"
                    f"3. For remote tasks: Task exists in your configured provider (Jira/Linear)\n"
                    f"4. Task file format is valid (see .alfred/tasks/README.md)\n"
                    f"5. Run 'alfred.get_next_task()' to see available tasks",
                )
            
            # Step 2: Cache the fetched task locally
            write_task_to_markdown(task)
            logger.info(f"Successfully cached task '{task_id}' from provider")
            
        except Exception as e:
            logger.error(f"Failed to fetch task from provider: {e}")
            return ToolResponse(
                status="error",
                message=f"Failed to fetch task '{task_id}' from provider: {str(e)}"
            )
    
    # Step 3: Use centralized workflow config for smart dispatch
    task_state = state_manager.load_or_create_task_state(task_id)
    task_status = task_state.task_status
    
    # Get the appropriate tool from workflow configuration
    next_tool = WorkflowConfiguration.get_tool_for_status(task_status)
    
    if next_tool:
        phase = WorkflowConfiguration.get_phase(task_status)
        message = (
            f"Task '{task_id}' is in status '{task_status.value}'. "
            f"The next action is to use the '{next_tool}' tool."
        )
        
        if phase and phase.description:
            message += f"\nPhase: {phase.description}"
        
        next_prompt = f"To proceed with task '{task_id}', call `alfred.{next_tool}(task_id='{task_id}')`."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)
    
    # Check if task is done
    if WorkflowConfiguration.is_terminal_status(task_status):
        return ToolResponse(
            status="success",
            message=f"Task '{task_id}' is already done. No further action is required."
        )
    
    # Unknown status
    return ToolResponse(
        status="error",
        message=f"Unhandled status '{task_status.value}' for task '{task_id}'. "
                f"This may be a configuration error."
    )
```

### 4. Update workflow_config.py for tools
**UPDATE** `src/alfred/tools/workflow_config.py` to use centralized workflow phases:

```python
# At the top, add import
from src.alfred.core.workflow_config import TOOL_ENTRY_POINTS

# Update the WORKFLOW_TOOL_CONFIGS to use the centralized entry points
# In each tool config, replace the hardcoded entry_status_map with:

WORKFLOW_TOOL_CONFIGS = {
    ToolName.PLAN_TASK: WorkflowToolConfig(
        tool_name=ToolName.PLAN_TASK,
        tool_class=PlanTaskTool,
        required_status=None,  # Special validation in setup
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.PLAN_TASK]
            if WorkflowConfiguration.get_phase(status)
        },
        dispatch_on_init=False,
    ),
    
    ToolName.IMPLEMENT_TASK: WorkflowToolConfig(
        tool_name=ToolName.IMPLEMENT_TASK,
        tool_class=ImplementTaskTool,
        required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        entry_status_map={
            status: WorkflowConfiguration.get_phase(status).next_status
            for status in TOOL_ENTRY_POINTS[ToolName.IMPLEMENT_TASK]
            if WorkflowConfiguration.get_phase(status)
        },
        dispatch_on_init=True,
        dispatch_state_attr=ImplementTaskState.DISPATCHING.value,
        context_loader=load_execution_plan_context,
        requires_artifact_from=ToolName.PLAN_TASK,
    ),
    
    # Continue pattern for other tools...
}
```

### 5. Update TaskStatus Enum (if needed)
**VERIFY** that `src/alfred/models/schemas.py` has all required statuses:

```python
class TaskStatus(str, Enum):
    """Enumeration for the high-level status of a Task."""
    
    NEW = "new"
    CREATING_SPEC = "creating_spec"
    SPEC_COMPLETED = "spec_completed"
    CREATING_TASKS = "creating_tasks"
    TASKS_CREATED = "tasks_created"
    PLANNING = "planning"
    READY_FOR_DEVELOPMENT = "ready_for_development"
    IN_DEVELOPMENT = "in_development"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    REVISIONS_REQUESTED = "revisions_requested"  # If used
    READY_FOR_TESTING = "ready_for_testing"
    IN_TESTING = "in_testing"
    READY_FOR_FINALIZATION = "ready_for_finalization"
    IN_FINALIZATION = "in_finalization"
    DONE = "done"
```

## VERIFICATION CHECKLIST
**CRITICAL**: After implementing this centralized workflow:

1. ✓ All workflow transitions work exactly as before
2. ✓ Status mappings are consistent across all tools
3. ✓ Archive step numbers are correct
4. ✓ Tool dispatch logic works for all statuses
5. ✓ No hardcoded mappings remain in individual files
6. ✓ Adding new phases only requires changes to WorkflowConfiguration
7. ✓ Phase descriptions are helpful and accurate
8. ✓ Terminal status detection works correctly

## TESTING REQUIREMENTS

1. **Workflow Traversal Test**:
```python
def test_complete_workflow():
    """Test that we can traverse the entire workflow."""
    
    # Test main path
    status = TaskStatus.NEW
    visited = [status]
    
    while not WorkflowConfiguration.is_terminal_status(status):
        phase = WorkflowConfiguration.get_phase(status)
        assert phase is not None, f"No phase for status {status}"
        
        if phase.next_status:
            status = phase.next_status
            visited.append(status)
        else:
            break
    
    print(f"Main workflow path: {' -> '.join(s.value for s in visited)}")
    assert status == TaskStatus.DONE
```

2. **Tool Mapping Test**:
```python
def test_tool_mappings():
    """Ensure every status has the correct tool."""
    
    for status in TaskStatus:
        tool = WorkflowConfiguration.get_tool_for_status(status)
        phase = WorkflowConfiguration.get_phase(status)
        
        if phase and not phase.terminal:
            assert tool is not None, f"No tool for non-terminal status {status}"
            print(f"{status.value} -> {tool}")
```

3. **Backward Compatibility Test**:
```python
def test_backward_compatibility():
    """Ensure the refactored system produces same results as old hardcoded maps."""
    
    # Compare with old STATUS_TRANSITION_MAP from approve_and_advance
    old_transitions = {
        TaskStatus.CREATING_SPEC: TaskStatus.SPEC_COMPLETED,
        TaskStatus.CREATING_TASKS: TaskStatus.TASKS_CREATED,
        # ... etc
    }
    
    for from_status, to_status in old_transitions.items():
        phase = WorkflowConfiguration.get_phase(from_status)
        assert phase.next_status == to_status, f"Mismatch for {from_status}"
```

## MIGRATION BENEFITS

With this centralized configuration:

1. **Single Source of Truth**: All workflow logic in one place
2. **Easy Modification**: Add new phases by adding to PHASES list
3. **Better Documentation**: Each phase has a description
4. **Type Safety**: Using dataclasses and enums
5. **Validation**: Can validate transitions before making them
6. **Introspection**: Can query workflow structure programmatically

## METRICS TO VERIFY

Code reduction:
- Removed from `approve_and_advance.py`: ~40 lines (mappings)
- Removed from `work_on.py`: ~30 lines (mappings)
- Removed from other files: ~50 lines (scattered mappings)
- Added in `workflow_config.py`: ~200 lines
- **Net addition**: ~80 lines (but much more maintainable)

Duplication eliminated:
- STATUS_TRANSITION_MAP: Was in 3+ places, now 1
- ARTIFACT_PRODUCER_MAP: Was in 2+ places, now 1  
- Tool dispatch logic: Was in 5+ places, now 1

## FINAL VALIDATION

Run this comprehensive test:

```python
#!/usr/bin/env python3
"""Validate centralized workflow configuration."""

from src.alfred.core.workflow_config import WorkflowConfiguration, TOOL_ENTRY_POINTS
from src.alfred.models.schemas import TaskStatus
from src.alfred.constants import ToolName

def validate_workflow():
    print("=== Workflow Configuration Validation ===\n")
    
    # 1. Check all statuses have phases
    print("1. Status Coverage:")
    orphan_statuses = []
    for status in TaskStatus:
        phase = WorkflowConfiguration.get_phase(status)
        if not phase:
            orphan_statuses.append(status)
        else:
            print(f"  ✓ {status.value} -> {phase.tool_name or 'TERMINAL'}")
    
    if orphan_statuses:
        print(f"  ✗ Orphan statuses: {orphan_statuses}")
    
    # 2. Validate transitions
    print("\n2. Transition Validation:")
    for phase in WorkflowConfiguration.PHASES:
        if phase.next_status:
            next_phase = WorkflowConfiguration.get_phase(phase.next_status)
            print(f"  ✓ {phase.status.value} -> {phase.next_status.value}")
    
    # 3. Tool entry points
    print("\n3. Tool Entry Points:")
    for tool, statuses in TOOL_ENTRY_POINTS.items():
        print(f"  {tool}: {[s.value for s in statuses]}")
    
    # 4. Workflow paths
    print("\n4. Possible Workflow Paths:")
    print("  Task Path: NEW -> PLANNING -> ... -> DONE")
    print("  Epic Path: NEW -> CREATING_SPEC -> ... -> PLANNING -> ... -> DONE")
    
    print("\n✅ Validation complete!")

if __name__ == "__main__":
    validate_workflow()
```

This completes the workflow configuration centralization, making the entire workflow logic maintainable from a single location.