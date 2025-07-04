# **ALFRED HANDLER SYSTEM PRINCIPLES**

## **CORE PHILOSOPHY**
Handlers are **CONFIGURATION, not CODE**. One generic handler rules them all. Duplication is the enemy.

## **THE GOLDEN RULES**

### **1. ONE HANDLER TO RULE THEM ALL**
- There is **EXACTLY ONE** workflow handler class: `GenericWorkflowHandler`
- All workflow tools use this SAME handler with different `ToolDefinition` configurations
- If you think you need a new handler class, YOU ARE WRONG

### **2. CONFIGURATION IS IMMUTABLE**
- Tool configurations are defined ONCE in `tool_definitions.py` as `ToolDefinition` objects
- Configuration is DATA, not logic
- Never add conditional logic to configurations
- If behavior differs, it goes in the `ToolDefinition`, not in a new handler

### **3. HANDLER LOGIC IS FROZEN**
- The `GenericWorkflowHandler` logic is COMPLETE
- Do NOT add new methods to handle "special cases"
- Do NOT add if-statements for specific tools
- If you need different behavior, use the `ToolDefinition` configuration

### **4. SACRED TOOL DEFINITION FIELDS**
```python
ToolDefinition fields (NEVER ADD NEW ONES):
- name                   # The tool's identifier
- tool_class            # The workflow tool class to instantiate
- description           # Tool description
- work_states           # List of work states for multi-step workflows
- dispatch_state        # Initial dispatch state for simple workflows
- terminal_state        # Final verified state
- initial_state         # Starting state (usually first work state or dispatch)
- entry_statuses        # Valid task statuses for entry
- exit_status           # Task status after tool execution
- required_status       # Specific status requirement (optional)
- dispatch_on_init      # Whether to auto-dispatch on initialization
- produces_artifacts    # Whether tool produces artifacts (default: True)
- requires_artifact_from # Dependency on another tool's output
- context_loader        # Function to load context
- custom_validator      # Custom validation function
```

### **5. CONTEXT LOADERS ARE PURE FUNCTIONS**
- Context loaders take `(task, task_state)` and return a dict
- They do NOT modify state
- They do NOT have side effects
- They raise `ValueError` for missing dependencies
- They are defined in `tool_definitions.py` ONLY

### **6. NO SPECIAL SNOWFLAKES**
- Every workflow tool follows the SAME pattern
- No tool is "special" enough to need its own handler
- Plan task is NOT special (its validation goes in configuration)
- If a tool seems special, you're thinking about it wrong

## **WHEN ADDING A NEW TOOL**

### **DO:**
- ✅ Add a `ToolDefinition` entry to `TOOL_DEFINITIONS` 
- ✅ Create a context loader if needed (pure function)
- ✅ Use the existing `GenericWorkflowHandler` (automatically used by tool factory)
- ✅ Follow the established patterns exactly
- ✅ Keep it simple and configuration-driven

### **DON'T:**
- ❌ Create a new handler class
- ❌ Modify `GenericWorkflowHandler`
- ❌ Add special case logic anywhere
- ❌ Create "helper" handler classes
- ❌ Think your tool is special

## **HANDLING "SPECIAL" REQUIREMENTS**

### **"But my tool needs X!"**
1. Can it be expressed as configuration? → Add to config
2. Can it be a context loader? → Write a pure function
3. Can it use existing patterns? → Use them
4. None of the above? → You're wrong, rethink it

### **"But plan_task has special validation!"**
- It's handled in the EXISTING handler via `custom_validator` in `ToolDefinition`
- The validation is simple and remains in `_setup_tool`
- This is the ONLY special case, and it's already handled via configuration

### **"But I need different dispatch logic!"**
- No, you need different configuration
- Use `dispatch_on_init` and state configuration in `ToolDefinition`
- The dispatch logic itself NEVER changes

## **TESTING HANDLERS**

When testing handler changes:

```python
# This is ALL you should need for a new tool
def test_new_tool():
    tool_def = ToolDefinition(
        name="new_tool",
        tool_class=NewToolClass,
        description="New tool description",
        work_states=[NewState.WORKING],
        dispatch_state=NewState.DISPATCHING,
        terminal_state=NewState.VERIFIED,
        entry_statuses=[TaskStatus.READY],
        exit_status=TaskStatus.IN_PROGRESS,
        dispatch_on_init=True
    )
    # Handler created automatically by tool factory
    # Should work immediately with no custom code
```

## **THE HANDLER PLEDGE**

*"I will not create new handler classes. I will not add special logic. I will trust in configuration. When I think I need a new handler, I will remember: I am wrong. The GenericWorkflowHandler is sufficient. Complexity is the enemy. Configuration is the way."*