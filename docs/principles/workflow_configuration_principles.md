# **ALFRED WORKFLOW CONFIGURATION PRINCIPLES**

## **CORE PHILOSOPHY**
Workflow configuration is **DECLARATIVE BLUEPRINTS, not IMPERATIVE LOGIC**. Workflows are data structures that drive behavior, not code that implements behavior.

## **THE GOLDEN RULES**

### **1. TWO-TIER ARCHITECTURE IS SACRED**
- **Tier 1**: High-level workflow phases (`WorkflowConfiguration`)
- **Tier 2**: Tool-specific state machines (built by `WorkflowStateMachineBuilder`)
- Each tier has distinct responsibilities
- No cross-tier dependencies or leakage

### **2. WORKFLOW PHASES ARE IMMUTABLE**
```python
Standard workflow phases (NEVER MODIFY):
1. PLANNING     → plan_task (Discovery → Clarification → Contracts → Implementation_Plan → Validation)
2. DEVELOPMENT  → implement_task  
3. REVIEW       → review_task
4. TESTING      → test_task
5. FINALIZATION → finalize_task
```
This sequence is FROZEN. No reordering, no additions, no removals.
Note: PLANNING phase internally uses discovery workflow but still maps to same external interface.

### **3. ENTRY POINTS ARE EXPLICIT**
- Each phase has specific entry requirements
- Status validation happens at phase boundaries
- No implicit phase transitions
- Clear error messages for invalid transitions

### **4. TOOL DEFINITIONS ARE DATA**
```python
ToolDefinition structure (IMMUTABLE):
- name                   # Unique identifier
- tool_class            # Class to instantiate
- description           # Tool description
- work_states           # List of work states for multi-step workflows
- dispatch_state        # Initial dispatch state for simple workflows
- terminal_state        # Final verified state
- initial_state         # Starting state
- entry_statuses        # Valid task statuses for entry
- exit_status           # Task status after tool execution
- required_status       # Specific status requirement (optional)
- dispatch_on_init      # Auto-dispatch behavior
- produces_artifacts    # Whether tool produces artifacts
- requires_artifact_from # Dependency validation
- context_loader        # Pure function reference
- custom_validator      # Custom validation function
```

### **5. CONTEXT LOADERS ARE PURE FUNCTIONS**
- Context loaders take `(task, task_state)` → return `dict`
- No side effects, no state mutations
- No external calls or file operations
- Deterministic for same inputs

### **6. DEPENDENCY VALIDATION IS AUTOMATIC**
- `requires_artifact_from` enforces tool dependencies
- Missing artifacts cause immediate failure
- No partial execution with missing dependencies
- Clear error messages for missing requirements

## **WHEN WORKING WITH WORKFLOW CONFIGURATION**

### **DO:**
- ✅ Add new tools to `TOOL_DEFINITIONS` in `tool_definitions.py`
- ✅ Use immutable `ToolDefinition` data structures
- ✅ Create pure function context loaders
- ✅ Validate entry requirements explicitly via `entry_statuses`
- ✅ Follow two-tier architecture strictly
- ✅ Use standard workflow phases

### **DON'T:**
- ❌ Modify workflow phase sequence
- ❌ Add new `ToolDefinition` fields
- ❌ Create stateful context loaders
- ❌ Bypass entry point validation via `entry_statuses`
- ❌ Mix tool and workflow concerns
- ❌ Add conditional configuration logic

## **WORKFLOW PHASE DEFINITIONS**

### **Phase Entry Requirements**
```python
PLANNING:     status in [NEW, PLANNING]
DEVELOPMENT:  status == READY_FOR_DEVELOPMENT  
REVIEW:       status == READY_FOR_REVIEW
TESTING:      status == READY_FOR_TESTING
FINALIZATION: status == READY_FOR_FINALIZATION
```

### **Phase Responsibilities**
- **PLANNING**: Create execution plan and subtasks
- **DEVELOPMENT**: Implement planned changes
- **REVIEW**: Validate implementation quality
- **TESTING**: Verify functionality and acceptance criteria
- **FINALIZATION**: Create commits and pull requests

### **"But I need a custom workflow!"**
No, you need better task breakdown. The workflow is complete and covers all development scenarios.

## **TOOL CONFIGURATION PATTERNS**

### **Simple Tool Configuration**
```python
ToolName.IMPLEMENT_TASK: ToolDefinition(
    name=ToolName.IMPLEMENT_TASK,
    tool_class=ImplementTaskTool,
    description="Execute the planned implementation",
    work_states=[ImplementTaskState.IMPLEMENTING],
    dispatch_state=ImplementTaskState.DISPATCHING,
    terminal_state=ImplementTaskState.VERIFIED,
    entry_statuses=[TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.IN_DEVELOPMENT],
    exit_status=TaskStatus.IN_DEVELOPMENT,
    required_status=TaskStatus.READY_FOR_DEVELOPMENT,
    dispatch_on_init=True,
    requires_artifact_from=ToolName.PLAN_TASK,
    context_loader=load_execution_plan_context
)
```

### **Multi-Step Configuration (Discovery Planning)**
```python
ToolName.PLAN_TASK: ToolDefinition(
    name=ToolName.PLAN_TASK,
    tool_class=PlanTaskTool,
    description="Interactive planning with deep context discovery",
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
    exit_status=TaskStatus.PLANNING,
    dispatch_on_init=False,  # Manual progression through discovery states
    context_loader=load_plan_task_context,
    custom_validator=validate_plan_task_status,
)
```

## **CONTEXT LOADER EXAMPLES**

### **GOOD Example - Pure function:**
```python
def load_plan_task_context(task: Task, task_state: TaskState) -> dict:
    return {
        "task_title": task.title,
        "task_context": task.context,
        "implementation_details": task.implementation_details,
        "acceptance_criteria": task.acceptance_criteria,
        "autonomous_mode": False  # Can be overridden by tool
    }
```

### **BAD Example - Stateful loader:**
```python
def load_planning_context(task: Task, task_state: TaskState) -> dict:
    # NO! Side effects forbidden
    cache.store(task.task_id, task_state)
    global_context.update(task=task)
    
    # NO! External calls forbidden  
    external_data = api_client.get_requirements(task.task_id)
    
    return {...}
```

## **WORKFLOW VALIDATION**

### **Entry Point Validation**
```python
def validate_workflow_entry(tool_name: str, task: Task) -> None:
    tool_def = get_tool_definition(tool_name)
    
    if task.status not in tool_def.entry_statuses:
        valid_statuses = [s.value for s in tool_def.entry_statuses]
        raise ToolResponse.error(
            f"Task {task.task_id} has status {task.status.value}. "
            f"Required: {valid_statuses}"
        )
```

### **Dependency Validation**
```python
def validate_dependencies(tool_name: str, task_state: TaskState) -> None:
    tool_def = get_tool_definition(tool_name)
    
    if tool_def.requires_artifact_from:
        required_artifact = f"{tool_def.requires_artifact_from}_result"
        if not task_state.get_artifact(required_artifact):
            raise ToolResponse.error(
                f"Missing required artifact: {required_artifact}"
            )
```

## **TESTING WORKFLOW CONFIGURATION**

Test configuration validity, not tool behavior:

```python
def test_workflow_configuration():
    # Test all tools have valid definitions
    for tool_name, tool_def in TOOL_DEFINITIONS.items():
        assert tool_def.name == tool_name
        assert tool_def.tool_class is not None
        assert tool_def.entry_statuses is not None
        
        # Test context loader is callable
        if tool_def.context_loader:
            assert callable(tool_def.context_loader)
        
        # Test tool definition validation
        tool_def.validate()
    
    # Test workflow phase coverage
    phases = WorkflowConfiguration.get_all_phases()
    assert len(phases) == 5  # PLANNING through FINALIZATION
```

## **CONFIGURATION EVOLUTION**

### **Adding New Tools**
1. Add entry to `TOOL_DEFINITIONS` in `tool_definitions.py`
2. Create context loader if needed (in same file)
3. Ensure tool follows existing patterns (Pattern 1 or 2)
4. Update tests and documentation

### **"But I need to modify the workflow!"**
No, you need to modify your tasks. The workflow is universal and complete.

## **THE WORKFLOW CONFIGURATION PLEDGE**

*"I will not modify workflow phases. I will not add configuration complexity. I will trust in declarative blueprints. When I think I need workflow customization, I will remember: The workflow is universal. Tasks are variable. Configuration drives behavior, code does not. Declarative is better than imperative."*

## **ENFORCEMENT**

Any PR that:
- Modifies workflow phase sequence → REJECTED
- Adds new `ToolDefinition` fields → REJECTED  
- Creates stateful context loaders → REJECTED
- Bypasses entry point validation → REJECTED
- Mixes workflow and tool concerns → REJECTED

Workflows are blueprints. Tools are implementations. ToolDefinitions are the bridge between them.