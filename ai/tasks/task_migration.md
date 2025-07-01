# CRITICAL REFACTORING INSTRUCTION: Step 1 - Consolidate Tool Handlers

**ATTENTION**: This is a CRITICAL refactoring task. You must be EXTREMELY careful to ensure ALL functionality is preserved while eliminating duplication. Double and triple check every change. Missing even a small detail could break the entire workflow system.

## OBJECTIVE
Replace all individual tool handler classes (PlanTaskHandler, ImplementTaskHandler, ReviewTaskHandler, TestTaskHandler, FinalizeTaskHandler) with a single, configurable GenericWorkflowHandler class.

## CURRENT PROBLEM
We have 5+ nearly identical handler classes with only minor variations:
- PlanTaskHandler
- ImplementTaskHandler  
- ReviewTaskHandler
- TestTaskHandler
- FinalizeTaskHandler

Each has ~50 lines of code that are 90% identical. This violates DRY principles.

## STEP-BY-STEP IMPLEMENTATION

### 1. Create New Configuration Classes
**CREATE** a new file: `src/alfred/tools/workflow_config.py`

```python
"""
Workflow tool configuration system for eliminating handler duplication.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Type, Callable, Any
from enum import Enum

from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.models.schemas import TaskStatus
from src.alfred.state.manager import state_manager


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
    PlanTaskTool, PlanTaskState,
    ImplementTaskTool, ImplementTaskState,
    ReviewTaskTool, ReviewTaskState,
    TestTaskTool, TestTaskState,
    FinalizeTaskTool, FinalizeTaskState
)

WORKFLOW_TOOL_CONFIGS = {
    ToolName.PLAN_TASK: WorkflowToolConfig(
        tool_name=ToolName.PLAN_TASK,
        tool_class=PlanTaskTool,
        required_status=None,  # Special validation in setup
        entry_status_map={
            TaskStatus.NEW: TaskStatus.PLANNING,
            TaskStatus.PLANNING: TaskStatus.PLANNING,
        },
        dispatch_on_init=False,  # Plan task doesn't auto-dispatch
    ),
    
    ToolName.IMPLEMENT_TASK: WorkflowToolConfig(
        tool_name=ToolName.IMPLEMENT_TASK,
        tool_class=ImplementTaskTool,
        required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        entry_status_map={
            TaskStatus.READY_FOR_DEVELOPMENT: TaskStatus.IN_DEVELOPMENT,
            TaskStatus.IN_DEVELOPMENT: TaskStatus.IN_DEVELOPMENT,
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
            TaskStatus.READY_FOR_REVIEW: TaskStatus.IN_REVIEW,
            TaskStatus.IN_REVIEW: TaskStatus.IN_REVIEW,
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
            TaskStatus.READY_FOR_TESTING: TaskStatus.IN_TESTING,
            TaskStatus.IN_TESTING: TaskStatus.IN_TESTING,
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
            TaskStatus.READY_FOR_FINALIZATION: TaskStatus.IN_FINALIZATION,
            TaskStatus.IN_FINALIZATION: TaskStatus.IN_FINALIZATION,
        },
        dispatch_on_init=True,
        dispatch_state_attr=FinalizeTaskState.DISPATCHING.value,
        context_loader=load_finalize_context,
    ),
}
```

### 2. Create the Generic Handler
**CREATE** a new file: `src/alfred/tools/generic_handler.py`

```python
"""
Generic workflow handler that replaces all individual tool handlers.
"""
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.tools.workflow_config import WorkflowToolConfig
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class GenericWorkflowHandler(BaseToolHandler):
    """
    A single, configurable handler that replaces all individual workflow tool handlers.
    
    This handler uses configuration to determine behavior, eliminating the need for
    separate handler classes for each tool.
    """
    
    def __init__(self, config: WorkflowToolConfig):
        """Initialize with a workflow configuration."""
        super().__init__(
            tool_name=config.tool_name,
            tool_class=config.tool_class,
            required_status=config.required_status,
        )
        self.config = config
    
    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method using the configured tool class."""
        return self.config.tool_class(task_id=task_id)
    
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """
        Generic setup logic driven by configuration.
        
        This method handles:
        1. Special validation (e.g., plan_task status check)
        2. Context loading from previous phases
        3. Auto-dispatch if configured
        4. State persistence
        """
        # Special validation for plan_task
        if self.config.tool_name == "plan_task":
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task.task_id}' has status '{task.task_status.value}'. "
                            f"Planning can only start on a 'new' or resume a 'planning' task.",
                )
        
        # Check if we should dispatch on initialization
        if self.config.dispatch_on_init and tool_instance.state == self.config.dispatch_state_attr:
            # Load task state for context
            task_state = state_manager.load_or_create(task.task_id)
            
            # Load context using configured loader
            if self.config.context_loader:
                try:
                    context = self.config.context_loader(task, task_state)
                    tool_instance.context_store.update(context)
                except ValueError as e:
                    # Context loader can raise ValueError for missing dependencies
                    return ToolResponse(status="error", message=str(e))
                except Exception as e:
                    logger.error(f"Context loader failed for {self.config.tool_name}: {e}")
                    return ToolResponse(
                        status="error",
                        message=f"Failed to load required context for {self.config.tool_name}: {str(e)}"
                    )
            
            # Dispatch to next state
            dispatch_method = getattr(tool_instance, self.config.target_state_method)
            dispatch_method()
            
            # Persist the state change
            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)
            
            logger.info(
                f"Dispatched '{self.config.tool_name}' for task {task.task_id} "
                f"to state '{tool_instance.state}'."
            )
        
        return None
```

### 3. Update Each Tool Implementation
**CRITICAL**: Now update each tool file to use the generic handler.

**UPDATE** `src/alfred/tools/plan_task.py`:
```python
# src/alfred/tools/plan_task.py
"""Plan task implementation using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
plan_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.PLAN_TASK])


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool."""
    return await plan_task_handler.execute(task_id)
```

**UPDATE** `src/alfred/tools/implement_task.py`:
```python
# src/alfred/tools/implement_task.py
"""Implement task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
implement_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.IMPLEMENT_TASK])


async def implement_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the implement_task tool."""
    return await implement_task_handler.execute(task_id)
```

**UPDATE** `src/alfred/tools/review_task.py`:
```python
# src/alfred/tools/review_task.py
"""Review task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
review_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.REVIEW_TASK])
```

**UPDATE** `src/alfred/tools/test_task.py`:
```python
# src/alfred/tools/test_task.py
"""Test task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
test_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.TEST_TASK])
```

**UPDATE** `src/alfred/tools/finalize_task.py`:
```python
# src/alfred/tools/finalize_task.py
"""Finalize task using generic handler."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS
from src.alfred.constants import ToolName

# Create the handler instance
finalize_task_handler = GenericWorkflowHandler(WORKFLOW_TOOL_CONFIGS[ToolName.FINALIZE_TASK])


async def finalize_task_impl(task_id: str) -> ToolResponse:
    """Finalize task entry point - handles the completion phase"""
    return await finalize_task_handler.execute(task_id)
```

### 4. Update server.py Tool Registrations
**CRITICAL**: Update server.py to use the new handlers while preserving ALL docstrings exactly as they are.

**UPDATE** the tool decorator sections in `src/alfred/server.py`:

```python
# For plan_task - PRESERVE THE ENTIRE DOCSTRING
@app.tool()
@tool_registry.register(
    name=ToolName.PLAN_TASK,
    handler_class=lambda: plan_task_handler,  # Use lambda to get instance
    tool_class=PlanTaskTool,
    entry_status_map=WORKFLOW_TOOL_CONFIGS[ToolName.PLAN_TASK].entry_status_map
)
async def plan_task(task_id: str) -> ToolResponse:
    """
    Initiates the detailed technical planning for a specific task.
    
    [PRESERVE ENTIRE EXISTING DOCSTRING - DO NOT MODIFY]
    """
    return await plan_task_handler.execute(task_id)

# Similar updates for implement_task, review_task, test_task, finalize_task
# CRITICAL: Keep ALL docstrings EXACTLY as they are
```

### 5. Remove Old Handler Classes
**DELETE** the following classes from their respective files:
- `PlanTaskHandler` class from `plan_task.py`
- `ImplementTaskHandler` class from `implement_task.py`
- `ReviewTaskHandler` class from `review_task.py`
- `TestTaskHandler` class from `test_task.py`
- `FinalizeTaskHandler` class from `finalize_task.py`

### 6. Update Tool Registry
**UPDATE** `src/alfred/tools/registry.py` to handle handler instances:

```python
@dataclass(frozen=True)
class ToolConfig:
    """Immutable configuration for a registered tool."""
    name: str
    handler_class: Any  # Can be Type or Callable returning instance
    tool_class: Type[BaseWorkflowTool]
    entry_status_map: Dict[TaskStatus, TaskStatus]
    implementation: Callable[..., Coroutine[Any, Any, ToolResponse]]
    
    def get_handler(self):
        """Get handler instance, handling both class and instance cases."""
        if callable(self.handler_class):
            return self.handler_class()
        return self.handler_class
```

## VERIFICATION CHECKLIST
**CRITICAL**: After making these changes, verify:

1. ✓ All 5 workflow tools still function exactly as before
2. ✓ All docstrings in server.py are preserved EXACTLY
3. ✓ Tool registry still works with the new handler instances
4. ✓ State transitions work correctly for each tool
5. ✓ Context loading works for tools that need it
6. ✓ Special validation (like plan_task status check) still works
7. ✓ All imports are updated correctly
8. ✓ No orphaned imports from deleted handler classes

## TESTING REQUIREMENTS
First stop and ask user to restart the mcp server and then Run these exact test scenarios:
1. Create a new task and run through entire workflow
2. Resume a task in each possible state
3. Test error cases (missing artifacts, wrong status)
4. Verify state persistence works correctly

## EXPECTED OUTCOME
- Reduce ~250 lines of duplicated handler code to ~100 lines of generic handler
- All functionality preserved exactly
- Easier to add new workflow tools (just add config)
- Single place to fix bugs in handler logic

**FINAL CHECK**: Count the lines of code removed vs added. You should remove at least 150 lines net.