# **ALFRED ERROR HANDLING PRINCIPLES**

## **CORE PHILOSOPHY**
Error handling is **PREDICTABLE COMMUNICATION, not EXCEPTION CHAOS**. Errors are data, responses are uniform, users get actionable guidance.

## **THE GOLDEN RULES**

### **1. TOOLRESPONSE IS THE ONLY OUTPUT**
- All tool functions return `ToolResponse` objects
- Success: `ToolResponse.success(data, message)`
- Error: `ToolResponse.error(message, details)`
- No naked exceptions escaping tool boundaries

### **2. ERROR MESSAGES ARE USER-FACING**
```python
Error message requirements:
- Specific and actionable ("Missing file X" not "Invalid input")
- Include task/tool context ("Task AL-123 in plan_task")
- Suggest resolution steps when possible
- No internal implementation details exposed
```

### **3. EXCEPTION MAPPING IS SYSTEMATIC**
```python
Standard exception mapping:
- ValidationError → ToolResponse.error("Invalid data: {details}")
- FileNotFoundError → ToolResponse.error("Missing file: {path}")
- PermissionError → ToolResponse.error("Access denied: {resource}")
- TimeoutError → ToolResponse.error("Operation timed out: {operation}")
- Custom errors → Contextual ToolResponse.error()
```

### **4. ERROR CATEGORIES ARE FIXED**
```python
Error categories (NEVER ADD MORE):
- USER_ERROR: Invalid input, missing files, bad format
- SYSTEM_ERROR: Infrastructure, permissions, timeouts  
- VALIDATION_ERROR: Data validation, constraint violations
- STATE_ERROR: Invalid workflow state transitions
```

### **5. TRANSACTION LOGGING IS AUTOMATIC**
- All errors are logged via `TransactionLogger`
- Include full context: task_id, tool_name, error details
- Structured logging for analysis and debugging
- No duplicate logging in application code

### **6. FAIL FAST, FAIL CLEAR**
- Validate inputs immediately on entry
- No partial execution with invalid data
- Clear error messages at point of failure
- No silent failures or default substitutions

## **WHEN HANDLING ERRORS**

### **DO:**
- ✅ Return `ToolResponse.error()` for all failures
- ✅ Include specific, actionable error messages
- ✅ Log errors through `TransactionLogger`
- ✅ Validate inputs at function entry
- ✅ Map exceptions to user-friendly messages
- ✅ Include task/tool context in errors

### **DON'T:**
- ❌ Let exceptions escape tool boundaries
- ❌ Return None or empty responses for errors
- ❌ Add custom error response formats
- ❌ Expose internal implementation details
- ❌ Create error hierarchies or subtypes
- ❌ Log errors manually in application code

## **ERROR HANDLING PATTERNS**

### **Input Validation Pattern**
```python
# GOOD - Validate early, fail fast
@tool(name="example_tool")
async def example_tool_handler(task_id: str, data: dict) -> ToolResponse:
    # Validate inputs immediately
    if not task_id:
        return ToolResponse.error("Task ID is required")
    
    if not data or "required_field" not in data:
        return ToolResponse.error("Missing required field: required_field")
    
    try:
        # Business logic here
        result = process_data(data)
        return ToolResponse.success(result, "Processing completed")
        
    except ValidationError as e:
        return ToolResponse.error(f"Invalid data format: {e}")
    except FileNotFoundError as e:
        return ToolResponse.error(f"Missing required file: {e.filename}")
    except Exception as e:
        # Catch-all for unexpected errors
        return ToolResponse.error(f"Unexpected error in {task_id}: {str(e)}")

# BAD - Letting exceptions escape
@tool(name="bad_tool") 
async def bad_tool_handler(task_id: str) -> ToolResponse:
    data = load_file(task_id)  # FileNotFoundError escapes!
    return ToolResponse.success(data)
```

### **State Validation Pattern**
```python
# GOOD - Validate state transitions
def validate_tool_entry(task: Task, required_status: List[TaskStatus]) -> Optional[ToolResponse]:
    if task.status not in required_status:
        valid_statuses = [s.value for s in required_status]
        return ToolResponse.error(
            f"Task {task.task_id} has status {task.status.value}. "
            f"Required status: {', '.join(valid_statuses)}"
        )
    return None  # No error

# Usage in tools
async def implement_task_handler(task_id: str) -> ToolResponse:
    task = get_task(task_id)
    
    # Validate state first
    error = validate_tool_entry(task, [TaskStatus.READY_FOR_DEVELOPMENT])
    if error:
        return error
    
    # Continue with business logic...
```

## **ERROR MESSAGE GUIDELINES**

### **GOOD Error Messages**
```python
# Specific and actionable
"Task AL-123 not found. Check task ID and try again."
"Missing required artifact: execution_plan. Run plan_task first."
"Invalid task format: Title is required but missing."
"File .alfred/tasks/AL-123.md is locked. Try again in a few seconds."

# Include context and resolution
"Task AL-123 has status COMPLETED. Cannot implement completed tasks."
"Planning phase requires status NEW or PLANNING. Current status: IN_PROGRESS."
```

### **BAD Error Messages**
```python
# Vague and unhelpful
"Error occurred"
"Invalid input" 
"Something went wrong"
"Task not found"

# Too technical or internal
"ValidationError in pydantic model field validation"
"JSONDecodeError at line 42, column 18"
"Thread lock acquisition timeout in StateManager._acquire_lock()"
```

## **TRANSACTION LOGGING PATTERN**

```python
# Automatic error logging (built into tool decorators)
@tool(name="example_tool")
async def example_tool_handler(task_id: str) -> ToolResponse:
    try:
        # Business logic
        return ToolResponse.success(result)
    except Exception as e:
        # Error automatically logged by decorator
        return ToolResponse.error(f"Failed to process {task_id}: {e}")

# Manual logging only for additional context
def complex_operation(task_id: str) -> dict:
    try:
        return perform_operation()
    except SpecificError as e:
        # Log additional context before re-raising
        logger.info(f"Operation failed for {task_id}, retrying with fallback")
        return perform_fallback_operation()
```

## **ERROR RESPONSE STRUCTURE**

### **Standard Error Response**
```python
ToolResponse.error(
    message="User-facing error description",
    details={
        "error_type": "VALIDATION_ERROR",
        "task_id": task_id,
        "tool_name": "implement_task", 
        "timestamp": datetime.utcnow().isoformat(),
        "context": {"additional": "debugging info"}
    }
)
```

### **Success Response for Reference**
```python
ToolResponse.success(
    data={"result": "operation completed"},
    message="Task AL-123 implementation started successfully"
)
```

## **TESTING ERROR HANDLING**

Test error conditions explicitly:

```python
def test_error_handling():
    # Test invalid inputs
    response = tool_handler("invalid-task-id")
    assert not response.success
    assert "not found" in response.message
    
    # Test state validation
    task = Task(task_id="TEST", status=TaskStatus.COMPLETED)
    response = tool_handler(task.task_id)
    assert not response.success
    assert "COMPLETED" in response.message
    
    # Test exception mapping
    with mock.patch('tool.load_file', side_effect=FileNotFoundError):
        response = tool_handler("valid-task-id")
        assert not response.success
        assert "Missing" in response.message
```

## **THE ERROR HANDLING PLEDGE**

*"I will not let exceptions escape tool boundaries. I will not create custom error formats. I will trust in ToolResponse uniformity. When I think I need complex error handling, I will remember: Simple error handling is reliable error handling. Users need clarity, not complexity. Every error is an opportunity to guide the user toward success."*

## **ENFORCEMENT**

Any PR that:
- Lets exceptions escape tool boundaries → REJECTED
- Creates custom error response formats → REJECTED
- Adds manual error logging in tools → REJECTED
- Returns None/empty for error conditions → REJECTED
- Exposes internal implementation details → REJECTED

Errors are data. ToolResponse is the container. Consistency is the goal.