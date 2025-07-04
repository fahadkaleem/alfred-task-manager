# **ALFRED TOOL REGISTRATION PRINCIPLES**

## **CORE PHILOSOPHY**
Tool registration is **DECLARATIVE CONFIGURATION, not IMPERATIVE CODE**. Tools are data structures, not special snowflakes.

## **THE GOLDEN RULES**

### **1. ONE REGISTRY TO RULE THEM ALL**
- There is **EXACTLY ONE** tool registry: `ToolRegistry`
- All tools register through the `@tool` decorator
- Registration happens at module import time
- No manual registration or dynamic tool creation

### **2. TOOLS ARE CONFIGURATIONS, NOT CLASSES**
- Tools are defined by `ToolDefinition` data structures in `tool_definitions.py`
- Tool behavior comes from `ToolDefinition` entries
- A tool is just a name + configuration mapping
- If you're writing tool-specific code, you're doing it wrong

### **3. REGISTRATION IS IMMUTABLE**
```python
Tool registration requirements:
- Registration happens ONCE at startup
- No runtime tool registration or modification
- Tool conflicts are detected and fail fast
- No dynamic tool enabling/disabling
```

### **4. GENERIC HANDLER SUPREMACY**
- All workflow tools use `GenericWorkflowHandler`
- Tool-specific behavior comes from configuration
- No custom handler classes for new tools
- No special-case handling anywhere

### **5. CONTEXT LOADERS ARE PURE FUNCTIONS**
```python
# GOOD - Pure function context loader
def load_plan_context(task: Task, task_state: TaskState) -> dict:
    return {
        "execution_plan": task_state.get_artifact("execution_plan"),
        "requirements": task.implementation_details
    }

# BAD - Stateful or side-effect laden
def load_plan_context(task: Task, task_state: TaskState) -> dict:
    global_state.update(task.id)  # NO! Side effects forbidden
    return {...}
```

### **6. SACRED TOOL DEFINITION FIELDS**
```python
ToolDefinition fields (NEVER ADD NEW ONES):
- name                   # Tool identifier
- tool_class             # Workflow tool class
- description            # Tool description
- work_states            # List of work states for multi-step workflows
- dispatch_state         # Initial dispatch state for simple workflows
- terminal_state         # Final verified state
- initial_state          # Starting state
- entry_statuses         # Valid task statuses for entry
- exit_status            # Task status after tool execution
- required_status        # Specific status requirement (optional)
- dispatch_on_init       # Auto-dispatch behavior
- produces_artifacts     # Whether tool produces artifacts
- requires_artifact_from # Dependency validation
- context_loader         # Pure function for context
- custom_validator       # Custom validation function
```

## **WHEN ADDING A NEW TOOL**

### **DO:**
- ✅ Add entry to `TOOL_DEFINITIONS` dictionary in `tool_definitions.py`
- ✅ Create pure function context loader if needed (in same file)
- ✅ Use existing `GenericWorkflowHandler` (automatic via tool factory)
- ✅ Follow exact same pattern as existing tools
- ✅ Register with `@tool` decorator in server
- ✅ Validate `ToolDefinition` at startup

### **DON'T:**
- ❌ Create custom handler classes
- ❌ Add special-case logic anywhere
- ❌ Modify `GenericWorkflowHandler`
- ❌ Add new `ToolDefinition` fields
- ❌ Create stateful context loaders
- ❌ Think your tool is special

## **TOOL LIFECYCLE**

### **Registration Phase (Startup Only)**
1. Module imports trigger `@tool` decorators
2. `ToolRegistry` validates and stores tool definitions  
3. `TOOL_DEFINITIONS` loaded and validated at startup
4. Tool factory builds configuration lookup table from definitions

### **Execution Phase (Runtime)**
1. Tool request arrives via MCP
2. `ToolFactory.get_handler()` looks up `ToolDefinition`
3. `GenericWorkflowHandler` instantiated with configuration from definition
4. Handler executes using declarative configuration

### **"But my tool needs special behavior!"**
No, it needs special CONFIGURATION. Use the existing fields or rethink your approach.

## **TOOL REGISTRATION EXAMPLES**

### **GOOD Example - Standard registration:**
```python
# In server.py
@tool(
    name="implement_task",
    description="Execute implementation phase for a task"
)
async def implement_task_handler(task_id: str) -> ToolResponse:
    return await ToolFactory.get_handler("implement_task").execute(
        task_id=task_id
    )

# Configuration in tool_definitions.py
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

### **BAD Example - Custom handler:**
```python
# NEVER DO THIS
class SpecialImplementationHandler(BaseHandler):
    def execute(self, task_id: str):
        # Custom logic here... NO!
        pass

@tool(name="implement_task")  
async def implement_task_handler(task_id: str) -> ToolResponse:
    return await SpecialImplementationHandler().execute(task_id)
```

## **CONTEXT LOADER PATTERNS**

### **Simple Context (No Dependencies)**
```python
def load_simple_context(task: Task, task_state: TaskState) -> dict:
    return {
        "task_details": task.implementation_details,
        "acceptance_criteria": task.acceptance_criteria
    }
```

### **Artifact-Dependent Context**
```python
def load_dependent_context(task: Task, task_state: TaskState) -> dict:
    execution_plan = task_state.get_artifact("execution_plan")
    if not execution_plan:
        raise ValueError("Missing required artifact: execution_plan")
    
    return {
        "execution_plan": execution_plan,
        "task_context": task.context
    }
```

## **TESTING TOOL REGISTRATION**

Test registration, not implementation:

```python
def test_tool_registration():
    # Test tool is registered
    assert "implement_task" in ToolRegistry.get_all_tools()
    
    # Test definition exists
    tool_def = get_tool_definition("implement_task")
    assert tool_def.name == "implement_task"
    
    # Test definition validation
    tool_def.validate()
    
    # Test handler creation
    handler = ToolFactory.get_handler("implement_task")
    assert isinstance(handler, GenericWorkflowHandler)
```

## **THE TOOL REGISTRATION PLEDGE**

*"I will not create special tool handlers. I will not add custom registration logic. I will trust in declarative configuration. When I think my tool needs special treatment, I will remember: It doesn't. All tools are equal. All tools use the same handler. ToolDefinitions, not code, make tools different."*

## **ENFORCEMENT**

Any PR that:
- Creates custom handler classes → REJECTED
- Modifies `GenericWorkflowHandler` → REJECTED
- Adds new `ToolDefinition` fields → REJECTED
- Implements special-case logic → REJECTED
- Bypasses the registration system → REJECTED

Tools are configurations. Handlers are generic. The pattern is complete.