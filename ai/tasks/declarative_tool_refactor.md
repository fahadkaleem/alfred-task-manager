# CRITICAL REFACTORING INSTRUCTION: Step 6 - Create Declarative Tool Definition System

**ATTENTION**: This is the sixth CRITICAL refactoring task. We need to replace the imperative tool registration scattered across multiple files with a single declarative tool definition system. This will make adding new tools trivial and eliminate the remaining registration duplication. Triple check that all tools remain fully functional.

## OBJECTIVE
Create a declarative tool definition system that combines tool configuration, registration, and handler creation into a single source of truth for each tool.

## CURRENT PROBLEM
Tool definitions are scattered across multiple files:
- Tool classes defined in `workflow.py`
- Handlers created in individual tool files
- Registration happens in `server.py` with decorators
- Configuration split between `workflow_config.py` and tool files
- Entry status mappings duplicated in multiple places

Adding a new tool requires changes in 5+ files and is error-prone.

## STEP-BY-STEP IMPLEMENTATION

### 1. Create Tool Definition System
**CREATE** a new file: `src/alfred/tools/tool_definitions.py`

```python
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
    PlanTaskTool, PlanTaskState,
    StartTaskTool, StartTaskState,
    ImplementTaskTool, ImplementTaskState,
    ReviewTaskTool, ReviewTaskState,
    TestTaskTool, TestTaskState,
    FinalizeTaskTool, FinalizeTaskState,
    CreateSpecTool, CreateSpecState,
    CreateTasksTool, CreateTasksState
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
        
        return {
            entry: self.exit_status
            for entry in self.entry_statuses
        }
    
    def get_all_states(self) -> List[str]:
        """Get all states including review states."""
        states = []
        
        # Add dispatch state if exists
        if self.dispatch_state:
            states.append(self.dispatch_state.value)
        
        # Add work states and their review states
        for state in self.work_states:
            state_value = state.value if hasattr(state, 'value') else str(state)
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
        raise ValueError(
            f"CRITICAL: Cannot start implementation. Execution plan from "
            f"'plan_task' not found for task '{task.task_id}'."
        )
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
        return (
            f"Task '{task.task_id}' has status '{task.task_status.value}'. "
            f"Planning can only start on a 'new' or resume a 'planning' task."
        )
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
    
    ToolName.CREATE_TASKS: ToolDefinition(
        name=ToolName.CREATE_TASKS,
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
```

### 2. Create Tool Factory
**CREATE** a new file: `src/alfred/tools/tool_factory.py`

```python
"""
Factory for creating tools from definitions.
"""
from typing import Dict, Any, Optional

from src.alfred.tools.tool_definitions import TOOL_DEFINITIONS, ToolDefinition
from src.alfred.tools.generic_handler import GenericWorkflowHandler
from src.alfred.tools.workflow_config import WorkflowToolConfig
from src.alfred.models.schemas import ToolResponse
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ToolFactory:
    """Factory for creating tool handlers from definitions."""
    
    @staticmethod
    def create_handler(tool_name: str) -> GenericWorkflowHandler:
        """Create a handler for the given tool."""
        definition = TOOL_DEFINITIONS.get(tool_name)
        if not definition:
            raise ValueError(f"No definition found for tool: {tool_name}")
        
        # Convert ToolDefinition to WorkflowToolConfig
        config = WorkflowToolConfig(
            tool_name=definition.name,
            tool_class=definition.tool_class,
            required_status=definition.required_status,
            entry_status_map=definition.get_entry_status_map(),
            dispatch_on_init=definition.dispatch_on_init,
            dispatch_state_attr=(
                definition.dispatch_state.value 
                if definition.dispatch_state and hasattr(definition.dispatch_state, 'value')
                else None
            ),
            context_loader=definition.context_loader,
            requires_artifact_from=definition.requires_artifact_from,
        )
        
        return GenericWorkflowHandler(config)
    
    @staticmethod
    async def execute_tool(tool_name: str, **kwargs) -> ToolResponse:
        """Execute a tool by name with the given arguments."""
        try:
            handler = ToolFactory.create_handler(tool_name)
            return await handler.execute(**kwargs)
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}", exc_info=True)
            return ToolResponse(
                status="error",
                message=f"Failed to execute tool {tool_name}: {str(e)}"
            )
    
    @staticmethod
    def get_tool_info(tool_name: str) -> Dict[str, Any]:
        """Get information about a tool."""
        definition = TOOL_DEFINITIONS.get(tool_name)
        if not definition:
            return {"error": f"Unknown tool: {tool_name}"}
        
        return {
            "name": definition.name,
            "description": definition.description,
            "entry_statuses": [s.value for s in definition.entry_statuses],
            "required_status": definition.required_status.value if definition.required_status else None,
            "produces_artifacts": definition.produces_artifacts,
            "work_states": [s.value for s in definition.work_states],
            "dispatch_on_init": definition.dispatch_on_init,
        }


# Create singleton handlers for backward compatibility
_tool_handlers: Dict[str, GenericWorkflowHandler] = {}


def get_tool_handler(tool_name: str) -> GenericWorkflowHandler:
    """Get or create a singleton handler for a tool."""
    if tool_name not in _tool_handlers:
        _tool_handlers[tool_name] = ToolFactory.create_handler(tool_name)
    return _tool_handlers[tool_name]
```

### 3. Update Individual Tool Files
Now update each tool file to use the factory. This makes them much simpler:

**UPDATE** `src/alfred/tools/plan_task.py`:
```python
"""Plan task implementation."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.tool_factory import get_tool_handler
from src.alfred.constants import ToolName

# Get the handler from factory
plan_task_handler = get_tool_handler(ToolName.PLAN_TASK)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool."""
    return await plan_task_handler.execute(task_id)
```

**UPDATE** all other tool files similarly:
- `implement_task.py`
- `review_task.py`
- `test_task.py`
- `finalize_task.py`
- `create_spec.py`
- `create_tasks.py`

They all follow the same pattern - just get handler from factory.

### 4. Update Server Registration
**UPDATE** `src/alfred/server.py` to use the declarative definitions:

```python
# At the top, add import
from src.alfred.tools.tool_definitions import TOOL_DEFINITIONS, get_tool_definition
from src.alfred.tools.tool_factory import get_tool_handler

# Create a helper function to register tools
def register_tool_from_definition(app: FastMCP, tool_name: str):
    """Register a tool using its definition."""
    definition = get_tool_definition(tool_name)
    handler = get_tool_handler(tool_name)
    
    @tool_registry.register(
        name=tool_name,
        handler_class=lambda: handler,
        tool_class=definition.tool_class,
        entry_status_map=definition.get_entry_status_map()
    )
    async def tool_impl(**kwargs):
        return await handler.execute(**kwargs)
    
    return tool_impl

# Then for each tool, replace the registration with:

# Plan Task
@app.tool()
async def plan_task(task_id: str) -> ToolResponse:
    """
    Initiates the detailed technical planning for a specific task.
    
    [KEEP ENTIRE EXISTING DOCSTRING]
    """
    handler = get_tool_handler(ToolName.PLAN_TASK)
    return await handler.execute(task_id)

# Register with tool registry
register_tool_from_definition(app, ToolName.PLAN_TASK)

# Repeat for all other tools, keeping their docstrings intact
```

### 5. Delete Obsolete Files
**DELETE** `src/alfred/tools/workflow_config.py` - replaced by tool_definitions.py

### 6. Update Tool Registry Initialization
**UPDATE** `src/alfred/state/recovery.py` to use definitions:

```python
# Update the TOOL_REGISTRY initialization
from src.alfred.tools.tool_definitions import TOOL_DEFINITIONS

class ToolRecovery:
    """Handles recovery of workflow tools from persisted state."""
    
    # Build registry from definitions
    TOOL_REGISTRY: Dict[str, Type[BaseWorkflowTool]] = {
        name: definition.tool_class
        for name, definition in TOOL_DEFINITIONS.items()
    }
```

### 7. Create Tool Management Commands
**CREATE** `src/alfred/tools/tool_commands.py`:

```python
"""
Utility commands for tool management.
"""
from typing import List, Dict, Any

from src.alfred.tools.tool_definitions import TOOL_DEFINITIONS
from src.alfred.tools.tool_factory import ToolFactory


def list_tools() -> List[Dict[str, Any]]:
    """List all available tools with their information."""
    return [
        ToolFactory.get_tool_info(name)
        for name in sorted(TOOL_DEFINITIONS.keys())
    ]


def validate_tools() -> Dict[str, List[str]]:
    """Validate all tool definitions and return any issues."""
    issues = {}
    
    for name, definition in TOOL_DEFINITIONS.items():
        tool_issues = []
        
        # Check for common issues
        if not definition.description:
            tool_issues.append("Missing description")
        
        if definition.work_states and not definition.terminal_state:
            tool_issues.append("Has work states but no terminal state")
        
        if definition.entry_statuses and not definition.exit_status:
            tool_issues.append("Has entry statuses but no exit status")
        
        # Try to create handler
        try:
            ToolFactory.create_handler(name)
        except Exception as e:
            tool_issues.append(f"Handler creation failed: {e}")
        
        if tool_issues:
            issues[name] = tool_issues
    
    return issues


def generate_tool_documentation() -> str:
    """Generate markdown documentation for all tools."""
    lines = ["# Alfred Tools Documentation\n"]
    
    for name in sorted(TOOL_DEFINITIONS.keys()):
        definition = TOOL_DEFINITIONS[name]
        info = ToolFactory.get_tool_info(name)
        
        lines.append(f"## {name}\n")
        lines.append(f"{definition.description}\n")
        lines.append(f"- **Entry Statuses**: {', '.join(info['entry_statuses'])}")
        lines.append(f"- **Required Status**: {info['required_status'] or 'None'}")
        lines.append(f"- **Work States**: {', '.join(info['work_states'])}")
        lines.append(f"- **Auto-dispatch**: {info['dispatch_on_init']}")
        lines.append("")
    
    return "\n".join(lines)
```

## VERIFICATION CHECKLIST
**CRITICAL**: After implementing the declarative system:

1. ✓ All tools work exactly as before
2. ✓ Tool definitions are validated on module load
3. ✓ Adding a new tool only requires one entry in TOOL_DEFINITIONS
4. ✓ All tool configuration is centralized
5. ✓ No tool configuration remains in individual files
6. ✓ Server registration works correctly
7. ✓ Tool recovery works with the new system
8. ✓ All imports are updated correctly

## TESTING REQUIREMENTS

1. **Tool Creation Test**:
```python
def test_all_tools_creatable():
    """Ensure all defined tools can be created."""
    from src.alfred.tools.tool_factory import ToolFactory
    
    for tool_name in TOOL_DEFINITIONS:
        print(f"Testing {tool_name}...")
        handler = ToolFactory.create_handler(tool_name)
        assert handler is not None
        assert handler.config.tool_name == tool_name
        print(f"  ✓ Created successfully")
```

2. **Definition Validation Test**:
```python
def test_tool_definitions_valid():
    """Validate all tool definitions."""
    from src.alfred.tools.tool_commands import validate_tools
    
    issues = validate_tools()
    if issues:
        print("Tool definition issues found:")
        for tool, tool_issues in issues.items():
            print(f"  {tool}:")
            for issue in tool_issues:
                print(f"    - {issue}")
    else:
        print("✓ All tool definitions valid")
```

3. **Documentation Generation Test**:
```python
def test_generate_docs():
    """Generate tool documentation."""
    from src.alfred.tools.tool_commands import generate_tool_documentation
    
    docs = generate_tool_documentation()
    print(docs)
    
    # Save to file
    with open("docs/tools.md", "w") as f:
        f.write(docs)
```

## ADDING A NEW TOOL

With this system, adding a new tool is trivial. Just add to TOOL_DEFINITIONS:

```python
ToolName.MY_NEW_TOOL: ToolDefinition(
    name=ToolName.MY_NEW_TOOL,
    tool_class=MyNewTool,
    description="Does something new",
    work_states=[MyToolState.WORKING],
    terminal_state=MyToolState.VERIFIED,
    initial_state=MyToolState.WORKING,
    entry_statuses=[TaskStatus.SOME_STATUS],
    exit_status=TaskStatus.NEXT_STATUS,
    dispatch_on_init=False,
),
```

That's it! The tool is now:
- Registered in the system
- Has a handler created automatically
- Can be executed via ToolFactory
- Is documented automatically
- Works with state recovery

## METRICS TO VERIFY

Code reduction:
- Removed from individual tool files: ~200 lines
- Removed workflow_config.py: ~150 lines
- Added tool_definitions.py: ~300 lines
- Added tool_factory.py: ~100 lines
- **Net reduction: ~50 lines**

But more importantly:
- Tool configuration in ONE place
- Adding tools is now trivial (10 lines vs 50+)
- No duplication of configuration
- Self-documenting system
- Validation built-in

## FINAL VALIDATION

Run this comprehensive test:

```python
#!/usr/bin/env python3
"""Validate declarative tool system."""

import asyncio
from src.alfred.tools.tool_definitions import TOOL_DEFINITIONS, get_all_tool_names
from src.alfred.tools.tool_factory import ToolFactory
from src.alfred.tools.tool_commands import list_tools, validate_tools

async def validate_tool_system():
    print("=== Tool Definition System Validation ===\n")
    
    # 1. List all tools
    print("1. Registered Tools:")
    for tool_info in list_tools():
        print(f"  - {tool_info['name']}: {tool_info['description']}")
    
    # 2. Validate definitions
    print("\n2. Definition Validation:")
    issues = validate_tools()
    if not issues:
        print("  ✓ All definitions valid")
    else:
        for tool, tool_issues in issues.items():
            print(f"  ✗ {tool}: {', '.join(tool_issues)}")
    
    # 3. Test execution
    print("\n3. Execution Test:")
    test_task_id = "TEST-001"
    
    # Test plan_task (doesn't require specific status)
    try:
        result = await ToolFactory.execute_tool(ToolName.PLAN_TASK, task_id=test_task_id)
        print(f"  ✓ plan_task execution: {result.status}")
    except Exception as e:
        print(f"  ✗ plan_task failed: {e}")
    
    print("\n✅ Validation complete!")

if __name__ == "__main__":
    asyncio.run(validate_tool_system())
```

This completes the declarative tool definition system, making tool management much simpler and more maintainable.