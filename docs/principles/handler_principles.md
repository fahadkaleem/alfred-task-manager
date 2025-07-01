# **ALFRED HANDLER SYSTEM PRINCIPLES**

## **CORE PHILOSOPHY**
Handlers are **CONFIGURATION, not CODE**. One generic handler rules them all. Duplication is the enemy.

## **THE GOLDEN RULES**

### **1. ONE HANDLER TO RULE THEM ALL**
- There is **EXACTLY ONE** workflow handler class: `GenericWorkflowHandler`
- All workflow tools use this SAME handler with different configurations
- If you think you need a new handler class, YOU ARE WRONG

### **2. CONFIGURATION IS IMMUTABLE**
- Tool configurations are defined ONCE in `workflow_config.py`
- Configuration is DATA, not logic
- Never add conditional logic to configurations
- If behavior differs, it goes in the configuration, not in a new handler

### **3. HANDLER LOGIC IS FROZEN**
- The `GenericWorkflowHandler` logic is COMPLETE
- Do NOT add new methods to handle "special cases"
- Do NOT add if-statements for specific tools
- If you need different behavior, use the configuration

### **4. SACRED CONFIGURATION FIELDS**
```python
WorkflowToolConfig fields (NEVER ADD NEW ONES):
- tool_name              # The tool's identifier
- tool_class            # The workflow tool class to instantiate
- required_status       # Status requirement (can be None)
- entry_status_map      # Status transitions on entry
- dispatch_on_init      # Whether to auto-dispatch
- dispatch_state_attr   # State to check for dispatch
- target_state_method   # Method to call (always "dispatch")
- context_loader        # Function to load context
- requires_artifact_from # Dependency validation
```

### **5. CONTEXT LOADERS ARE PURE FUNCTIONS**
- Context loaders take `(task, task_state)` and return a dict
- They do NOT modify state
- They do NOT have side effects
- They raise `ValueError` for missing dependencies
- They are defined in `workflow_config.py` ONLY

### **6. NO SPECIAL SNOWFLAKES**
- Every workflow tool follows the SAME pattern
- No tool is "special" enough to need its own handler
- Plan task is NOT special (its validation goes in configuration)
- If a tool seems special, you're thinking about it wrong

## **WHEN ADDING A NEW TOOL**

### **DO:**
- ✅ Add a configuration entry to `WORKFLOW_TOOL_CONFIGS`
- ✅ Create a context loader if needed (pure function)
- ✅ Use the existing `GenericWorkflowHandler`
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
- It's handled in the EXISTING handler via configuration
- The validation is simple and remains in `_setup_tool`
- This is the ONLY special case, and it's already handled

### **"But I need different dispatch logic!"**
- No, you need different configuration
- Use `dispatch_on_init`, `dispatch_state_attr`
- The dispatch logic itself NEVER changes

## **TESTING HANDLERS**

When testing handler changes:

```python
# This is ALL you should need for a new tool
def test_new_tool():
    config = WorkflowToolConfig(
        tool_name="new_tool",
        tool_class=NewToolClass,
        required_status=TaskStatus.SOME_STATUS,
        # ... other config
    )
    handler = GenericWorkflowHandler(config)
    # Should work immediately
```

## **THE HANDLER PLEDGE**

*"I will not create new handler classes. I will not add special logic. I will trust in configuration. When I think I need a new handler, I will remember: I am wrong. The GenericWorkflowHandler is sufficient. Complexity is the enemy. Configuration is the way."*