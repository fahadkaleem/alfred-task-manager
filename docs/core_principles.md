------ docs/principles/configuration_management_principles.md ------
``````
# **ALFRED CONFIGURATION MANAGEMENT PRINCIPLES**

## **CORE PHILOSOPHY**
Configuration is **IMMUTABLE DATA, not RUNTIME VARIABLES**. Set once, trust forever. Changes require restarts.

## **THE GOLDEN RULES**

### **1. THREE-TIER HIERARCHY IS SACRED**
- **Tier 1**: Package defaults (built-in fallbacks)
- **Tier 2**: Global `settings` (environment-driven, immutable)
- **Tier 3**: Project `alfred.yml` (mutable, project-specific)
- This hierarchy is FROZEN. Do not add more tiers.

### **2. IMMUTABILITY ABOVE ALL**
- Global `settings` are loaded ONCE at startup
- No runtime modification of global configuration
- Project configs can change, but require explicit save operations
- Environment variables override everything (deployment-time decisions)

### **3. VALIDATION IS NON-NEGOTIABLE**
```python
Configuration validation requirements:
- All configs MUST use Pydantic models
- Invalid configs MUST fail fast at startup
- No silent fallbacks or default substitutions
- Provide actionable error messages with examples
```

### **4. ENVIRONMENT VARIABLES ARE SACRED**
```bash
Standard environment variable format:
ALFRED_DEBUG=true
ALFRED_LOG_LEVEL=debug
ALFRED_PROVIDER=jira
```
- All env vars use `ALFRED_` prefix
- Boolean values: `true/false` (lowercase)
- No env var can be overridden by file config

### **5. ATOMIC OPERATIONS ONLY**
- All config writes use temporary files + atomic move
- No partial config updates
- File locks prevent concurrent modifications
- Failed writes leave original config intact

### **6. FEATURE FLAGS ARE SIMPLE BOOLEANS**
```python
# GOOD - Simple boolean flags
feature_flags:
  enable_new_parser: true
  use_advanced_scoring: false

# BAD - Complex feature configuration
feature_flags:
  parser:
    version: "v2"
    settings: {...}
```

## **WHEN WORKING WITH CONFIGURATION**

### **DO:**
- ✅ Use Pydantic models for all config structures
- ✅ Validate configuration at startup
- ✅ Use atomic file operations for saves
- ✅ Provide clear error messages for invalid configs
- ✅ Document all configuration options in models
- ✅ Use environment variables for deployment settings

### **DON'T:**
- ❌ Modify global settings at runtime
- ❌ Add configuration caching or reloading
- ❌ Create dynamic configuration generation
- ❌ Use configuration for runtime state
- ❌ Add conditional configuration logic
- ❌ Create configuration inheritance chains

## **CONFIGURATION CATEGORIES**

### **Global Settings (Immutable)**
- Server configuration (ports, hosts)
- Logging levels and debug flags
- Provider selection and authentication
- Feature flags for system behavior

### **Project Configuration (Mutable)**
- Workflow customizations
- Project-specific provider settings
- Task templates and formats
- Local development overrides

### **"But I need runtime configuration!"**
No, you need runtime STATE. Use the state management system instead.

## **CONFIGURATION EXAMPLES**

### **GOOD Example - Proper structure:**
```python
class AlfredConfig(BaseModel):
    version: str = "1.0"
    providers: ProvidersConfig
    workflows: WorkflowConfig
    features: FeatureFlags
    
    @validator('version')
    def validate_version(cls, v):
        if v not in SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported version: {v}")
        return v
```

### **BAD Example - Runtime modification:**
```python
# NEVER DO THIS
def update_provider(new_provider):
    config.providers.default = new_provider  # NO!
    config.save()  # This breaks immutability!
```

## **TESTING CONFIGURATION**

Test configuration loading, not configuration content:

```python
def test_config_validation():
    # Test validation works
    with pytest.raises(ValidationError):
        AlfredConfig(version="invalid")
    
    # Test environment override
    with mock.patch.dict(os.environ, {"ALFRED_DEBUG": "true"}):
        config = load_config()
        assert config.debug is True
```

## **THE CONFIGURATION PLEDGE**

*"I will not modify configuration at runtime. I will not add configuration complexity. I will trust in immutability. When I think I need dynamic configuration, I will remember: I need dynamic STATE, not dynamic CONFIG. Configuration is for deployment decisions, not runtime decisions."*

## **ENFORCEMENT**

Any PR that:
- Modifies global settings at runtime → REJECTED
- Adds configuration reloading → REJECTED
- Creates dynamic config generation → REJECTED
- Bypasses validation → REJECTED
- Adds more than 3 tiers → REJECTED

Configuration is for deployment decisions. State is for runtime decisions. Do not confuse them.
``````
------ docs/principles/data_model_principles.md ------
``````
# **ALFRED DATA MODEL PRINCIPLES**

## **CORE PHILOSOPHY**
Data models are **IMMUTABLE CONTRACTS, not MUTABLE OBJECTS**. Models define structure, validation ensures integrity, serialization preserves consistency.

## **THE GOLDEN RULES**

### **1. PYDANTIC IS THE ONLY VALIDATION**
- All data models inherit from `BaseModel`
- No custom validation outside Pydantic
- No manual JSON serialization/deserialization
- Validation happens at model boundaries only

### **2. MODELS ARE VALUE OBJECTS**
```python
Value object requirements:
- Immutable after creation (no setters)
- Identity based on content, not memory
- No business logic in model classes
- Pure data containers with validation
```

### **3. ENUM-BASED TYPE SAFETY**
- All status fields use Enum types
- No string constants for state values
- Enum values are the source of truth
- No magic strings anywhere in the codebase

### **4. SERIALIZATION IS AUTOMATIC**
- Use `.model_dump()` for serialization
- Use `.model_validate()` for deserialization
- No custom `to_dict()` or `from_dict()` methods
- JSON serialization through Pydantic only

### **5. DOMAIN MODELS ARE SEPARATE**
```python
Model categories (NEVER MIX):
- Domain Models: Task, Subtask, User (business concepts)
- State Models: TaskState, WorkflowState (persistence)
- Config Models: AlfredConfig, ToolConfig (configuration)
- Response Models: ToolResponse, schemas (API)
```

### **6. NO MODEL INHERITANCE CHAINS**
- Maximum inheritance depth: 2 levels (BaseModel → DomainModel)
- No deep inheritance hierarchies
- Prefer composition over inheritance
- Mixins only for pure data (no behavior)

## **WHEN WORKING WITH DATA MODELS**

### **DO:**
- ✅ Use Pydantic `BaseModel` for all data structures
- ✅ Define validation with Pydantic validators
- ✅ Use Enum types for all status/type fields
- ✅ Keep models as pure data containers
- ✅ Use `model_dump()` and `model_validate()`
- ✅ Separate domain and persistence concerns

### **DON'T:**
- ❌ Add business logic to model classes
- ❌ Create deep inheritance hierarchies
- ❌ Use string constants for enum values
- ❌ Implement custom serialization methods
- ❌ Mix domain and state model concerns
- ❌ Create mutable model attributes

## **MODEL DEFINITION PATTERNS**

### **Domain Model Pattern**
```python
# GOOD - Pure domain model
class Task(BaseModel):
    task_id: str
    title: str
    context: str
    implementation_details: str
    acceptance_criteria: List[str]
    status: TaskStatus  # Enum type
    priority: TaskPriority  # Enum type
    created_at: datetime
    
    # Validation only, no business logic
    @field_validator('task_id')
    @classmethod
    def validate_task_id(cls, v: str) -> str:
        if not re.match(r'^[A-Z]+-\d+$', v):
            raise ValueError('Task ID must be format: ABC-123')
        return v

# BAD - Business logic in model
class Task(BaseModel):
    # ... fields ...
    
    def is_ready_for_development(self) -> bool:  # NO! Business logic
        return self.status == TaskStatus.READY_FOR_DEVELOPMENT
    
    def assign_to(self, user: str) -> None:  # NO! Mutation method
        self.assignee = user
```

### **State Model Pattern**
```python
# GOOD - Separate state model
class TaskState(BaseModel):
    task_id: str
    status: TaskStatus
    workflow_state: Dict[str, Any]
    artifacts: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def get_artifact(self, key: str) -> Optional[Any]:
        """Pure getter - no side effects"""
        return self.artifacts.get(key)
    
    def add_artifact(self, key: str, value: Any) -> 'TaskState':
        """Returns new instance - immutable"""
        new_artifacts = {**self.artifacts, key: value}
        return self.model_copy(update={
            'artifacts': new_artifacts,
            'updated_at': datetime.utcnow()
        })
```

## **ENUM PATTERNS**

### **Status Enums**
```python
class TaskStatus(str, Enum):
    NEW = "new"
    PLANNING = "planning"
    READY_FOR_DEVELOPMENT = "ready_for_development"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    READY_FOR_TESTING = "ready_for_testing"
    READY_FOR_FINALIZATION = "ready_for_finalization"
    COMPLETED = "completed"

# Usage - always use enum values
if task.status == TaskStatus.IN_PROGRESS:  # GOOD
if task.status == "in_progress":  # BAD - magic string
```

### **Priority Enums**
```python
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"
    CRITICAL = "critical"
    
    @property
    def value(self) -> int:
        """Numeric value for sorting"""
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[self.value]
```

## **VALIDATION PATTERNS**

### **Field Validation**
```python
class Task(BaseModel):
    title: str
    context: str
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title too long (max 200 chars)')
        return v.strip()
    
    @field_validator('context')
    @classmethod
    def validate_context(cls, v: str) -> str:
        if len(v) < 10:
            raise ValueError('Context too short (min 10 chars)')
        return v
```

### **Model Validation**
```python
class Subtask(BaseModel):
    subtask_id: str
    description: str
    estimated_hours: int
    
    @model_validator(mode='after')
    def validate_subtask(self) -> 'Subtask':
        if self.estimated_hours > 40:
            raise ValueError('Subtask too large (max 40 hours)')
        return self
```

## **SERIALIZATION PATTERNS**

### **Standard Serialization**
```python
# GOOD - Use Pydantic methods
def save_task(task: Task) -> None:
    data = task.model_dump()  # Pydantic serialization
    with open(f"{task.task_id}.json", 'w') as f:
        json.dump(data, f, indent=2)

def load_task(task_id: str) -> Task:
    with open(f"{task_id}.json", 'r') as f:
        data = json.load(f)
    return Task.model_validate(data)  # Pydantic deserialization

# BAD - Custom serialization
def save_task(task: Task) -> None:
    data = {  # NO! Manual serialization
        'id': task.task_id,
        'title': task.title,
        # ...
    }
```

### **API Response Models**
```python
class TaskResponse(BaseModel):
    success: bool
    task: Optional[Task] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Usage
response = TaskResponse(
    success=True,
    task=task,
    message="Task created successfully"
)
return response.model_dump()
```

## **TESTING DATA MODELS**

Test validation, not implementation:

```python
def test_task_validation():
    # Test valid task creation
    task = Task(
        task_id="AL-123",
        title="Test Task",
        context="Test context for the task",
        implementation_details="Test implementation",
        acceptance_criteria=["Criterion 1"],
        status=TaskStatus.NEW,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow()
    )
    assert task.task_id == "AL-123"
    
    # Test validation failures
    with pytest.raises(ValidationError):
        Task(task_id="invalid")  # Bad format
    
    with pytest.raises(ValidationError):
        Task(title="")  # Empty title
```

## **MODEL EVOLUTION**

### **Adding New Fields**
```python
class Task(BaseModel):
    # Existing fields...
    
    # New optional field (backward compatible)
    assignee: Optional[str] = None
    
    # New required field (needs migration)
    workspace_id: str = Field(..., description="Workspace identifier")
```

### **Deprecating Fields**
```python
class Task(BaseModel):
    # Current fields...
    
    # Deprecated field (keep for compatibility)
    old_field: Optional[str] = Field(None, deprecated=True)
    
    @field_validator('old_field')
    @classmethod
    def validate_old_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            warnings.warn("old_field is deprecated", DeprecationWarning)
        return v
```

## **THE DATA MODEL PLEDGE**

*"I will not add business logic to models. I will not create deep inheritance chains. I will trust in Pydantic validation. When I think I need complex models, I will remember: Models are contracts, not implementations. Simple models are reliable models. Validation at boundaries prevents corruption throughout."*

## **ENFORCEMENT**

Any PR that:
- Adds business logic to model classes → REJECTED
- Creates custom serialization methods → REJECTED
- Uses string constants instead of enums → REJECTED
- Creates deep inheritance hierarchies → REJECTED
- Mixes domain and state concerns → REJECTED

Models are data contracts. Validation is automatic. Serialization is standard. Keep it simple.
``````
------ docs/principles/error_handling_principles.md ------
``````
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
``````
------ docs/principles/handler_principles.md ------
``````
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
``````
------ docs/principles/logging_debugging_principles.md ------
``````
# **ALFRED LOGGING & DEBUGGING PRINCIPLES**

## **CORE PHILOSOPHY**
Logging is **STRUCTURED OBSERVABILITY, not CONSOLE SPAM**. Logs are data for analysis, debugging is guided investigation, both serve specific purposes.

## **THE GOLDEN RULES**

### **1. CONSOLIDATE THE DUAL SYSTEMS**
- **ELIMINATE**: Basic Python logging in `lib/logger.py`
- **KEEP ONLY**: `TransactionLogger` for all logging needs
- One logging system, one format, one destination
- No mixing of logging approaches

### **2. TRANSACTION LOGGING IS AUTOMATIC**
```python
Transaction logging happens automatically:
- Tool calls logged on entry with parameters
- Tool responses logged on exit with results
- Errors logged with full stack traces
- All logs include task_id, tool_name, timestamp
```

### **3. STRUCTURED DATA ONLY**
- All logs in JSONL format for analysis
- No plain text log messages
- Consistent field names across all logs
- Machine-readable timestamps (ISO 8601)

### **4. TASK-BASED LOG ORGANIZATION**
```
Debug log structure:
.alfred/debug/
├── transactions.jsonl     # All tool transactions
├── {task_id}/            # Task-specific logs  
│   ├── tool_calls.jsonl  # Tool calls for this task
│   └── state_changes.jsonl # State transitions
```

### **5. LOG LEVELS ARE SIMPLE**
```python
Only three log levels:
- INFO: Normal operations (tool calls, state changes)
- ERROR: Failures and exceptions 
- DEBUG: Detailed tracing (only when debug=true)
```

### **6. NO PERFORMANCE IMPACT IN PRODUCTION**
- Async logging to avoid blocking
- Log rotation to prevent disk bloat
- Debug logging disabled by default
- Structured logging with minimal overhead

## **WHEN WORKING WITH LOGGING**

### **DO:**
- ✅ Use `TransactionLogger` for all logging
- ✅ Log structured data with consistent fields
- ✅ Include task_id in all relevant logs
- ✅ Use async logging for performance
- ✅ Organize logs by task for easy debugging
- ✅ Rotate logs to prevent disk issues

### **DON'T:**
- ❌ Use Python's standard logging module
- ❌ Log plain text messages
- ❌ Create custom logging formats
- ❌ Log sensitive data (passwords, tokens)
- ❌ Add manual logging in tool handlers
- ❌ Create nested logging hierarchies

## **TRANSACTION LOGGING PATTERNS**

### **Automatic Tool Logging**
```python
# This happens automatically via decorators
@tool(name="implement_task")
async def implement_task_handler(task_id: str) -> ToolResponse:
    # Entry log: {"event": "tool_start", "tool": "implement_task", "task_id": "AL-123"}
    
    result = perform_implementation(task_id)
    
    # Exit log: {"event": "tool_end", "tool": "implement_task", "result": "success"}
    return ToolResponse.success(result)
```

### **State Change Logging**
```python
# In StateManager
def save_state(self, task_id: str, state: TaskState) -> None:
    old_status = self.load_state(task_id).status if self.exists(task_id) else None
    
    # Save state atomically
    self._atomic_save(task_id, state)
    
    # Log state change
    TransactionLogger.log_state_change(
        task_id=task_id,
        old_status=old_status,
        new_status=state.status,
        timestamp=datetime.utcnow()
    )
```

## **LOG STRUCTURE STANDARDS**

### **Tool Transaction Log Entry**
```json
{
  "event": "tool_call",
  "task_id": "AL-123",
  "tool_name": "implement_task",
  "parameters": {"task_id": "AL-123"},
  "timestamp": "2024-01-15T10:30:45.123Z",
  "duration_ms": 1250,
  "success": true,
  "response_size": 1024
}
```

### **Error Log Entry**
```json
{
  "event": "error",
  "task_id": "AL-123", 
  "tool_name": "plan_task",
  "error_type": "ValidationError",
  "error_message": "Missing required field: task_context",
  "stack_trace": "...",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

### **State Change Log Entry**
```json
{
  "event": "state_change",
  "task_id": "AL-123",
  "old_status": "planning",
  "new_status": "ready_for_development", 
  "tool_name": "plan_task",
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

## **DEBUGGING WORKFLOW PATTERNS**

### **Task-Specific Debugging**
```python
def debug_task_workflow(task_id: str) -> dict:
    """Get comprehensive debug info for a task"""
    logs_dir = Path(f".alfred/debug/{task_id}")
    
    # Load all logs for this task
    tool_calls = load_jsonl(logs_dir / "tool_calls.jsonl")
    state_changes = load_jsonl(logs_dir / "state_changes.jsonl")
    
    return {
        "task_id": task_id,
        "tool_calls": tool_calls,
        "state_changes": state_changes,
        "current_state": StateManager.load_state(task_id),
        "timeline": merge_and_sort_by_timestamp(tool_calls, state_changes)
    }
```

### **Error Analysis**
```python
def analyze_recent_errors(hours: int = 24) -> list:
    """Find all errors in recent timeframe"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    errors = []
    for log_entry in read_transaction_logs():
        if (log_entry.get("event") == "error" and 
            log_entry.get("timestamp") > cutoff.isoformat()):
            errors.append(log_entry)
    
    return sorted(errors, key=lambda x: x["timestamp"])
```

## **LOG MANAGEMENT PATTERNS**

### **Log Rotation Configuration**
```python
class TransactionLogger:
    @classmethod
    def configure_rotation(cls):
        """Set up log rotation to prevent disk bloat"""
        # Rotate daily, keep 30 days
        rotation_config = {
            "when": "midnight",
            "interval": 1,
            "backup_count": 30,
            "encoding": "utf-8"
        }
        return rotation_config
```

### **Log Cleanup**
```python
def cleanup_old_logs(days_to_keep: int = 30):
    """Remove logs older than specified days"""
    cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
    
    debug_dir = Path(".alfred/debug")
    for task_dir in debug_dir.iterdir():
        if task_dir.is_dir():
            # Remove old task directories
            if task_dir.stat().st_mtime < cutoff.timestamp():
                shutil.rmtree(task_dir)
```

## **DEBUG MODE FEATURES**

### **Enhanced Debug Logging**
```python
# When settings.debug = True
class TransactionLogger:
    @classmethod
    def log_debug_info(cls, **kwargs):
        """Enhanced logging for debug mode"""
        if not settings.debug:
            return
        
        debug_entry = {
            "event": "debug",
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        cls._write_log(debug_entry)
```

### **Debug Context Manager**
```python
@contextmanager
def debug_trace(operation: str, task_id: str):
    """Trace operation execution in debug mode"""
    if settings.debug:
        TransactionLogger.log_debug_info(
            operation=f"{operation}_start",
            task_id=task_id
        )
    
    start_time = time.time()
    try:
        yield
    finally:
        if settings.debug:
            duration = time.time() - start_time
            TransactionLogger.log_debug_info(
                operation=f"{operation}_end",
                task_id=task_id,
                duration_ms=duration * 1000
            )
```

## **TESTING LOGGING BEHAVIOR**

### **Test Log Generation**
```python
def test_transaction_logging(tmp_path):
    """Test that tool calls are logged properly"""
    # Configure temporary log directory
    TransactionLogger.configure(log_dir=tmp_path)
    
    # Execute tool
    response = await implement_task_handler("TEST-123")
    
    # Verify log entry exists
    log_file = tmp_path / "transactions.jsonl"
    assert log_file.exists()
    
    logs = list(read_jsonl(log_file))
    assert len(logs) >= 1
    assert logs[0]["tool_name"] == "implement_task"
    assert logs[0]["task_id"] == "TEST-123"
```

### **Test Debug Mode**
```python
def test_debug_mode_logging():
    """Test enhanced logging in debug mode"""
    with mock.patch('settings.debug', True):
        with debug_trace("test_operation", "TEST-123"):
            # Operation here
            pass
    
    # Verify debug logs created
    logs = list(read_transaction_logs())
    debug_logs = [l for l in logs if l.get("event") == "debug"]
    assert len(debug_logs) >= 2  # start and end
```

## **MIGRATION STRATEGY**

### **Phase 1: Consolidation (IMMEDIATE)**
- Remove all usage of standard Python logging
- Migrate to TransactionLogger everywhere
- Consolidate log formats to JSONL

### **Phase 2: Enhancement (NEXT)**
- Add task-specific log organization
- Implement log rotation and cleanup
- Add debug mode enhancements

### **Phase 3: Analysis Tools (FUTURE)**
- Build log analysis dashboard
- Add automated error detection
- Create performance monitoring

## **THE LOGGING & DEBUGGING PLEDGE**

*"I will not create multiple logging systems. I will not log unstructured data. I will trust in transaction-based logging. When I think I need custom logging, I will remember: Consistency enables analysis. Structure enables automation. One logging system is better than two. Logs are for machines first, humans second."*

## **ENFORCEMENT**

Any PR that:
- Uses standard Python logging → REJECTED
- Creates custom log formats → REJECTED
- Adds manual logging in tool handlers → REJECTED
- Logs unstructured text messages → REJECTED
- Creates multiple logging systems → REJECTED

Logging is data collection. Structure enables analysis. One system serves all needs.
``````
------ docs/principles/mcp_client_principles.md ------
``````
# MCP Client Interface Principles

## Core Philosophy
MCP clients are **external users without source code access**. They rely entirely on tool descriptions and prompts to understand how to use our tools correctly.

## The Golden Rules

### 1. PROMPTS MUST BE SELF-DOCUMENTING
- Every data structure mentioned in a prompt MUST include its complete schema
- Never assume clients can "figure out" field names or types
- If you mention an object type, show its JSON structure immediately

### 2. EXAMPLES ARE MANDATORY
- Every complex data structure needs at least one complete, valid example
- Include both GOOD (correct) and BAD (wrong) examples
- Annotate examples with comments explaining key points

### 3. ENUM VALUES MUST BE LISTED
- Never just say "integration_type enum" - list ALL valid values
- Include descriptions of when to use each value
- Group related values with explanatory headers

### 4. ERROR MESSAGES MUST GUIDE
- Don't just say what's wrong - show what's right
- Include partial examples in error messages
- Suggest the closest valid option for invalid inputs

### 5. VALIDATION SHOULD TEACH
- Validation errors should educate, not just reject
- Show the expected format alongside what was provided
- Explain WHY something is invalid, not just that it is

## Required Sections for Tool Prompts

### Schema Documentation Section
```markdown
## Schema Documentation

### ObjectName
\```json
{
  "field_name": "type",        // Description of field
  "enum_field": "enum",        // MUST be one of: VALUE1, VALUE2, VALUE3
  "array_field": ["type"],     // Array of elements (note the brackets!)
  "nested_object": {           // Nested object structure
    "sub_field": "type"
  }
}
\```
```

### Examples Section
```markdown
## Examples

### Good Example (CORRECT)
\```json
{
  "field": "value",            // Why this is correct
  "enum": "VALID_VALUE"        // Using proper enum
}
\```

### Bad Example (WRONG)  
\```json
{
  "field": value,              // WRONG: Missing quotes
  "enum": "invalid"            // WRONG: Not a valid enum value
}
\```
```

## Common Patterns

### For Enum Fields
```markdown
"integration_type": "enum",      // MUST be one of the following values:
  // External integrations:
  // - "API_ENDPOINT"           // For REST API endpoints
  // - "DATABASE"               // For database operations
  
  // Code structure integrations:
  // - "DATA_MODEL_EXTENSION"   // Adding fields to existing models
  // - "PARSER_EXTENSION"       // Extending parser functionality
```

### For Array Fields
```markdown
"examples": ["string"]          // List of examples (MUST be array!)
// CORRECT: ["example1", "example2"]
// WRONG: "example1"            // Single string not allowed
```

### For Complex Objects
```markdown
### Complete Structure
\```json
{
  "simple_field": "string",
  "complex_field": {
    "nested": "value"
  },
  "array_field": [
    {"item": "value"}
  ]
}
\```
```

## Testing MCP Interfaces

Before releasing any MCP tool:

1. **Black Box Test**: Test without looking at source code
2. **Schema Completeness**: Verify all mentioned types are documented
3. **Example Validity**: Ensure all examples actually work
4. **Error Helpfulness**: Trigger errors and check if messages guide to solution

## Anti-Patterns to Avoid

### ❌ Vague Type References
```markdown
Create a ContextDiscoveryArtifact with:
- integration_points: List of IntegrationPoint objects
```

### ✅ Complete Type Documentation
```markdown
Create a ContextDiscoveryArtifact with:
- integration_points: List of IntegrationPoint objects, where each has:
  - component_name: string
  - integration_type: one of ["PARSER_EXTENSION", "DATA_MODEL_EXTENSION", ...]
  - examples: array of strings (e.g., ["example1", "example2"])
```

### ❌ Enum Without Values
```markdown
"complexity_assessment": enum based on scope
```

### ✅ Enum With All Values
```markdown
"complexity_assessment": "enum", // MUST be: "LOW", "MEDIUM", or "HIGH"
```

## The MCP Client Promise

*"As an MCP tool developer, I promise that my tools will be fully usable by someone who has never seen my source code. My prompts will teach, my errors will guide, and my examples will illuminate the path to success."*

---

Remember: Your MCP client might be an AI agent, a human developer, or an automated system. They all deserve clear, complete, and helpful interfaces.
``````
------ docs/principles/mcp_server_principles.md ------
``````
# **ALFRED MCP SERVER INTEGRATION PRINCIPLES**

## **CORE PHILOSOPHY**
MCP integration is **TRANSPARENT PROTOCOL BRIDGING, not CUSTOM FRAMEWORK**. The server exposes tools cleanly, handles protocol details automatically, stays out of business logic.

## **THE GOLDEN RULES**

### **1. FASTMCP IS THE ONLY FRAMEWORK**
- All MCP server functionality through FastMCP
- No custom MCP protocol implementation
- No manual message handling or transport
- Let FastMCP handle protocol details automatically

### **2. TOOL DECORATORS ARE SACRED**
```python
Tool registration pattern (NEVER CHANGE):
@tool(name="tool_name", description="Clear description")
async def tool_handler(param: type) -> ToolResponse:
    return ToolResponse.success(data, message)
```

### **3. SERVER LIFECYCLE IS AUTOMATIC**
- Server startup/shutdown handled by FastMCP
- Lifespan context managers for initialization
- No manual server state management
- Transaction logging automatic on all tools

### **4. TOOL ISOLATION IS MANDATORY**
- Each tool is completely independent
- No shared state between tool calls
- No tool-to-tool communication
- Tools communicate only through state persistence

### **5. PROTOCOL ABSTRACTION IS COMPLETE**
- Business logic never sees MCP protocol details
- No raw MCP message handling in application code
- Tools work identically whether called via MCP or direct
- Protocol concerns isolated in server layer

### **6. ASYNC IS UNIVERSAL**
- All tool handlers are async functions
- Use `async/await` throughout the stack
- No blocking operations in tool handlers
- Concurrent tool execution supported

## **WHEN WORKING WITH MCP INTEGRATION**

### **DO:**
- ✅ Use `@tool` decorator for all exposed functions
- ✅ Return `ToolResponse` objects from all tools
- ✅ Keep tool handlers async and stateless
- ✅ Use FastMCP lifespan for initialization
- ✅ Let transaction logging happen automatically
- ✅ Validate inputs at tool entry points

### **DON'T:**
- ❌ Handle MCP protocol details manually
- ❌ Create custom MCP message handlers
- ❌ Share state between tool calls
- ❌ Block in async tool handlers
- ❌ Expose internal implementation via MCP
- ❌ Create tool interdependencies

## **SERVER SETUP PATTERNS**

### **Standard Server Configuration**
```python
# GOOD - Clean FastMCP setup
from fastmcp import FastMCP

app = FastMCP("Alfred Task Manager")

@app.lifespan
async def lifespan():
    """Initialization and cleanup"""
    # Initialize logging
    TransactionLogger.initialize()
    
    # Load configuration
    settings = load_settings()
    
    yield  # Server runs here
    
    # Cleanup if needed
    pass

# Tool registration happens via decorators
@app.tool(name="get_next_task")
async def get_next_task_handler() -> ToolResponse:
    # Business logic here
    pass

# BAD - Manual MCP handling
class CustomMCPServer:
    def handle_tool_call(self, message):  # NO! Let FastMCP handle this
        pass
```

### **Tool Registration Pattern**
```python
# GOOD - Standard tool pattern
@tool(
    name="implement_task",
    description="Execute implementation phase for a task that has completed planning"
)
async def implement_task_handler(task_id: str) -> ToolResponse:
    """
    Clear docstring explaining tool purpose and usage.
    
    Args:
        task_id: The unique identifier for the task
        
    Returns:
        ToolResponse with success/error and appropriate data
    """
    try:
        # Delegate to business logic
        handler = ToolFactory.get_handler("implement_task")
        return await handler.execute(task_id=task_id)
        
    except Exception as e:
        return ToolResponse.error(f"Failed to execute implement_task: {e}")

# BAD - Direct business logic in MCP handler
@tool(name="implement_task")
async def implement_task_handler(task_id: str) -> ToolResponse:
    # NO! Business logic belongs in handlers
    task = load_task(task_id)
    state_machine = create_state_machine()
    # ... complex logic here
```

## **TOOL PARAMETER PATTERNS**

### **Simple Parameters**
```python
@tool(name="get_task")
async def get_task_handler(task_id: str) -> ToolResponse:
    """Get a single task by ID"""
    if not task_id:
        return ToolResponse.error("Task ID is required")
    
    # Delegate to provider
    provider = ProviderFactory.create_provider()
    try:
        task = provider.get_task(task_id)
        return ToolResponse.success(task.model_dump(), f"Retrieved task {task_id}")
    except TaskNotFoundError:
        return ToolResponse.error(f"Task {task_id} not found")
```

### **Complex Parameters**
```python
@tool(name="submit_work")
async def submit_work_handler(task_id: str, artifact: dict) -> ToolResponse:
    """Submit work artifact for current workflow step"""
    if not task_id:
        return ToolResponse.error("Task ID is required")
    
    if not artifact:
        return ToolResponse.error("Artifact data is required")
    
    # Validate and delegate
    handler = ToolFactory.get_handler("submit_work")
    return await handler.execute(task_id=task_id, artifact=artifact)
```

## **ERROR HANDLING IN MCP CONTEXT**

### **Protocol Error Isolation**
```python
@tool(name="example_tool")
async def example_tool_handler(param: str) -> ToolResponse:
    """Always return ToolResponse - never let exceptions escape"""
    try:
        # Business logic
        result = perform_operation(param)
        return ToolResponse.success(result, "Operation completed")
        
    except ValidationError as e:
        # Map domain errors to user-friendly messages
        return ToolResponse.error(f"Invalid input: {e}")
        
    except Exception as e:
        # Catch all unexpected errors
        logger.exception(f"Unexpected error in {example_tool.__name__}")
        return ToolResponse.error(f"Internal error: {str(e)}")
```

### **No Protocol Details in Errors**
```python
# GOOD - User-friendly error
return ToolResponse.error("Task AL-123 not found. Check task ID and try again.")

# BAD - Protocol details exposed
return ToolResponse.error("MCP tool call failed: JSON-RPC error -32601")
```

## **TRANSACTION LOGGING INTEGRATION**

### **Automatic Logging Setup**
```python
# Transaction logging happens automatically via decorators
@tool(name="plan_task")
async def plan_task_handler(task_id: str) -> ToolResponse:
    # Logging happens automatically:
    # - Tool call logged on entry
    # - Parameters logged (sanitized)
    # - Response logged on exit
    # - Errors logged with stack traces
    
    handler = ToolFactory.get_handler("plan_task")
    return await handler.execute(task_id=task_id)
```

## **TESTING MCP INTEGRATION**

### **Test Tool Registration**
```python
def test_tool_registration():
    """Test that tools are properly registered with MCP server"""
    # Test tool is available
    assert "implement_task" in app.tools
    
    # Test tool metadata
    tool_info = app.tools["implement_task"]
    assert tool_info.name == "implement_task"
    assert "task_id" in tool_info.parameters
```

### **Test Tool Execution**
```python
@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool execution returns proper ToolResponse"""
    # Test successful execution
    response = await implement_task_handler("AL-123")
    assert isinstance(response, ToolResponse)
    
    # Test error handling
    response = await implement_task_handler("")
    assert not response.success
    assert "required" in response.message.lower()
```

## **SERVER CONFIGURATION**

### **Standard Configuration**
```python
# main.py - Server entry point
if __name__ == "__main__":
    # FastMCP handles everything
    app.run(
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.log_level
    )
```

### **Development vs Production**
```python
# Development
app.run(debug=True, reload=True)

# Production  
app.run(
    host="0.0.0.0",
    port=8000,
    workers=1,  # MCP is single-threaded by design
    debug=False
)
```

## **PERFORMANCE CONSIDERATIONS**

### **Async Best Practices**
```python
# GOOD - Non-blocking operations
@tool(name="example_tool")
async def example_tool_handler(task_id: str) -> ToolResponse:
    # Use async file operations
    async with aiofiles.open(f"{task_id}.json") as f:
        content = await f.read()
    
    # Use async HTTP clients
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/api/tasks/{task_id}")
    
    return ToolResponse.success(content)

# BAD - Blocking operations
@tool(name="example_tool") 
async def example_tool_handler(task_id: str) -> ToolResponse:
    # Blocking file I/O
    with open(f"{task_id}.json") as f:  # Blocks event loop!
        content = f.read()
    
    # Blocking HTTP
    response = requests.get(f"/api/tasks/{task_id}")  # Blocks!
    
    return ToolResponse.success(content)
```

## **THE MCP SERVER PLEDGE**

*"I will not handle MCP protocol details manually. I will not create custom server logic. I will trust in FastMCP abstraction. When I think I need MCP customization, I will remember: The server is a tool transport, not business logic. Tools are independent, stateless functions. Protocol complexity belongs in the framework, not the application."*

## **ENFORCEMENT**

Any PR that:
- Implements custom MCP protocol handling → REJECTED
- Creates stateful tool handlers → REJECTED
- Adds manual transaction logging → REJECTED
- Exposes protocol details in business logic → REJECTED
- Creates tool interdependencies → REJECTED

MCP is transport. Tools are functions. FastMCP handles the rest.
``````
------ docs/principles/prompt_builder_principles.md ------
``````
# **ALFRED PROMPT BUILDER PRINCIPLES**

## **CORE PHILOSOPHY**
Prompt building is **DETERMINISTIC ASSEMBLY, not DYNAMIC GENERATION**. Templates are data, context is data, prompts are predictable combinations.

## **THE GOLDEN RULES**

### **1. CONSOLIDATION OVER DUPLICATION**
- **ONE SYSTEM ONLY**: File-based templates with `PromptLibrary`
- Kill the class-based template system completely
- All prompts come from `.md` files in `prompts/` directory
- No exceptions, no fallbacks, no dual systems

### **2. TEMPLATE RESOLUTION IS EXPLICIT**
```python
Template path formula (NEVER CHANGE):
prompts/{tool_name}/{state}.md

Examples:
- prompts/plan_task/contextualize.md
- prompts/implement_task/dispatching.md
- prompts/review_task/working.md
```

### **3. VARIABLE SUBSTITUTION IS SIMPLE**
- Use `string.Template` for variable substitution
- Variables follow `${variable_name}` format
- No Jinja2, no complex templating logic
- No conditional rendering, no loops

### **4. CONTEXT BUILDERS ARE PURE FUNCTIONS**
```python
Context builder requirements:
- Take (task, task_state, **kwargs) → return dict
- No side effects or state mutations
- No external API calls or file operations
- Deterministic output for same inputs
```

### **5. TEMPLATE CACHING IS TRANSPARENT**
- Templates loaded once at startup
- Cache invalidation only on restart
- No hot-reloading in production
- File changes require server restart

### **6. VARIABLE VALIDATION IS MANDATORY**
- All template variables must be provided
- Missing variables cause immediate failure
- No default substitutions or silent failures
- Clear error messages with variable names

## **WHEN WORKING WITH PROMPTS**

### **DO:**
- ✅ Use `PromptLibrary.render_template()` for all prompts
- ✅ Create pure function context builders
- ✅ Follow exact template path formula
- ✅ Validate all required variables provided
- ✅ Use simple `${variable}` substitution
- ✅ Fail fast on missing templates or variables

### **DON'T:**
- ❌ Create class-based templates
- ❌ Add complex templating logic
- ❌ Implement dynamic template paths
- ❌ Cache context data
- ❌ Add fallback template systems
- ❌ Use conditional template rendering

## **PROMPT BUILDING PATTERNS**

### **Simple Template Rendering**
```python
# GOOD - Standard template rendering
def build_planning_prompt(task: Task, state: TaskState) -> str:
    context = {
        "task_id": task.task_id,
        "task_title": task.title,
        "task_context": task.context,
        "current_state": "contextualize"
    }
    
    return PromptLibrary.render_template(
        tool_name="plan_task",
        state="contextualize", 
        context=context
    )

# BAD - Dynamic template selection
def build_planning_prompt(task: Task, state: TaskState) -> str:
    template_name = f"planning_{task.priority.lower()}"  # NO!
    if task.complexity > 5:
        template_name += "_complex"  # NO!
    return PromptLibrary.render_template(template_name, context)
```

### **Context Builder Pattern**
```python
# GOOD - Pure context builder
def build_implementation_context(task: Task, task_state: TaskState) -> dict:
    execution_plan = task_state.get_artifact("execution_plan")
    if not execution_plan:
        raise ValueError("Missing required artifact: execution_plan")
    
    return {
        "task_id": task.task_id,
        "execution_plan": json.dumps(execution_plan, indent=2),
        "task_context": task.context,
        "implementation_details": task.implementation_details
    }

# BAD - Stateful context builder
def build_implementation_context(task: Task, task_state: TaskState) -> dict:
    global last_context  # NO! No global state
    cache.set(task.task_id, task_state)  # NO! No side effects
    return {...}
```

## **TEMPLATE STRUCTURE ENFORCEMENT**

### **Required Template Sections**
Every template MUST have these sections:
```markdown
# CONTEXT
# OBJECTIVE  
# BACKGROUND
# INSTRUCTIONS
# CONSTRAINTS
# OUTPUT
# EXAMPLES
```

### **Variable Documentation**
Every template MUST start with this header:
```markdown
<!--
Template: {tool_name}.{state}
Purpose: [Description]
Variables:
  - task_id: Task identifier
  - task_title: Task title
  - [All other variables]
-->
```

## **ERROR HANDLING PATTERNS**

### **Template Not Found**
```python
# Clear, actionable error messages
try:
    template = PromptLibrary.get_template("plan_task", "contextualize")
except TemplateNotFoundError:
    raise ToolResponse.error(
        f"Missing template: prompts/plan_task/contextualize.md"
    )
```

### **Missing Variables**
```python
# Fail fast with specific missing variables
try:
    prompt = template.substitute(context)
except KeyError as e:
    missing_var = e.args[0]
    raise ToolResponse.error(
        f"Missing required variable: {missing_var}"
    )
```

## **PROMPT LIBRARY INTERFACE**

### **Core Methods (ONLY these exist)**
```python
class PromptLibrary:
    @classmethod
    def render_template(cls, tool_name: str, state: str, context: dict) -> str:
        """Render template with context - main interface"""
    
    @classmethod  
    def get_template(cls, tool_name: str, state: str) -> Template:
        """Get raw template object - for testing only"""
        
    @classmethod
    def reload_templates(cls) -> None:
        """Reload all templates - development only"""
```

### **"But I need custom prompt logic!"**
No, you need a different template. Create a new template file instead of adding logic.

## **TESTING PROMPT BUILDING**

Test rendering, not template content:

```python
def test_prompt_rendering():
    context = {
        "task_id": "TEST-1",
        "task_title": "Test Task", 
        "task_context": "Test context",
        "current_state": "contextualize"
    }
    
    # Test successful rendering
    prompt = PromptLibrary.render_template(
        "plan_task", "contextualize", context
    )
    assert "TEST-1" in prompt
    assert "Test Task" in prompt
    
    # Test missing variable error
    del context["task_id"]
    with pytest.raises(KeyError):
        PromptLibrary.render_template("plan_task", "contextualize", context)
```

## **TEMPLATE MIGRATION STRATEGY**

### **Phase 1: Consolidation (IMMEDIATE)**
- Remove all class-based template code
- Migrate remaining templates to file-based
- Update all prompt building to use `PromptLibrary`

### **Phase 2: Validation (NEXT)**
- Add template variable validation
- Implement template header checking
- Create template testing utilities

## **THE PROMPT BUILDER PLEDGE**

*"I will not create complex templating systems. I will not add dynamic template logic. I will trust in simple substitution. When I think I need template complexity, I will remember: Complexity in templates leads to debugging nightmares. Simple templates are predictable templates. Predictable templates are maintainable templates."*

## **ENFORCEMENT**

Any PR that:
- Adds class-based templates → REJECTED
- Implements dynamic template paths → REJECTED
- Adds complex templating logic → REJECTED
- Creates template fallback systems → REJECTED
- Bypasses `PromptLibrary` → REJECTED

Templates are data files. Context is data. Prompts are deterministic assembly. Keep it simple.
``````
------ docs/principles/state_machine_principles.md ------
``````
# **ALFRED STATE MACHINE PRINCIPLES**

## **CORE PHILOSOPHY**
State machines are **DECLARATIVE WORKFLOWS, not IMPERATIVE CODE**. Use the builder. Trust the builder. The builder is complete.

## **THE GOLDEN RULES**

### **1. THE BUILDER IS COMPLETE**
- `WorkflowStateMachineBuilder` handles ALL workflow patterns
- It has TWO methods: `build_workflow_with_reviews` and `build_simple_workflow`
- These two methods cover EVERY use case
- Do NOT add new builder methods

### **2. STATE MACHINES ARE DECLARATIVE**
- You declare states in `ToolDefinition` and the builder creates the machine
- You do NOT manually create transitions
- You do NOT manually create review states
- The builder handles ALL of this
- All behavior is configuration-driven through `ToolDefinition`

### **3. REVIEW PATTERNS ARE SACRED**
```
Every review cycle follows this EXACT pattern:
1. work_state → work_state_awaiting_ai_review
2. ai_review → work_state_awaiting_human_review
3. human_review → next_work_state
Plus revision paths back to work_state
```
This pattern is FROZEN. Do not modify it.

### **4. TWO PATTERNS ONLY**

**Pattern 1: Multi-step with reviews** (Discovery Planning)
```python
# In ToolDefinition:
work_states=[
    PlanTaskState.DISCOVERY,
    PlanTaskState.CLARIFICATION,
    PlanTaskState.CONTRACTS,
    PlanTaskState.IMPLEMENTATION_PLAN,
    PlanTaskState.VALIDATION
],
terminal_state=PlanTaskState.VERIFIED,
initial_state=PlanTaskState.DISCOVERY
```

**Pattern 2: Simple dispatch-work-done** (Implementation, Review, Test, Finalize)
```python
# In ToolDefinition:
work_states=[ImplementTaskState.IMPLEMENTING],
dispatch_state=ImplementTaskState.DISPATCHING,
terminal_state=ImplementTaskState.VERIFIED
```

THERE ARE NO OTHER PATTERNS.

### **5. STATE NAMING IS AUTOMATIC**
- Work states: As defined in your enum
- AI review: `{work_state}_awaiting_ai_review`
- Human review: `{work_state}_awaiting_human_review`
- The builder creates these names. You do NOT.

### **6. NO CUSTOM TRANSITIONS**
- The builder creates ALL transitions
- You do NOT add custom transitions
- You do NOT modify transition logic
- If you think you need a custom transition, redesign your states

## **WHEN CREATING A NEW WORKFLOW TOOL**

### **DO:**
- ✅ Add entry to `TOOL_DEFINITIONS` in `tool_definitions.py`
- ✅ Define your state enum
- ✅ Choose Pattern 1 or Pattern 2 in your `ToolDefinition`
- ✅ Define your artifact_map in your tool class
- ✅ Trust the builder completely

### **DON'T:**
- ❌ Create transitions manually
- ❌ Add custom state machine logic
- ❌ Modify the builder
- ❌ Create "special" patterns
- ❌ Think your workflow is unique

## **CHOOSING YOUR PATTERN**

### **Use Pattern 1 when:**
- Multiple sequential work states requiring deep interaction
- Each state needs AI and human review
- Example: plan_task (discovery → clarification → contracts → implementation_plan → validation)

### **Use Pattern 2 when:**
- Single work state
- Dispatch → Work → Done
- Example: implement_task, review_task, test_task

### **"But my workflow is different!"**
No, it's not. Pick Pattern 1 or Pattern 2.

## **STATE MACHINE EXAMPLES**

### **GOOD Example - Declarative tool definition:**
```python
# In tool_definitions.py
ToolName.MY_TOOL: ToolDefinition(
    name=ToolName.MY_TOOL,
    tool_class=MyWorkflowTool,
    description="My workflow tool",
    work_states=[MyState.WORKING],
    dispatch_state=MyState.DISPATCHING,
    terminal_state=MyState.VERIFIED,
    entry_statuses=[TaskStatus.READY],
    exit_status=TaskStatus.IN_PROGRESS,
    dispatch_on_init=True
)

# Tool class uses the builder automatically
class MyWorkflowTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        # Builder is called automatically by tool_factory
        super().__init__(task_id, ToolName.MY_TOOL)
```

### **BAD Example - Manual construction:**
```python
# NEVER DO THIS
states = ["dispatching", "working", "working_awaiting_ai_review", ...]
transitions = [
    {"trigger": "dispatch", "source": "dispatching", ...},
    # NO! Use the builder!
]
```

## **TESTING STATE MACHINES**

Test ONLY the outcomes, not the implementation:

```python
def test_state_machine():
    tool = MyWorkflowTool("test-1")
    
    # Test the behavior, not the structure
    assert tool.state == "initial_state"
    tool.submit_work()  # or whatever trigger
    assert tool.state == "expected_next_state"
```

## **THE STATE MACHINE PLEDGE**

*"I will not create custom state machines. I will not add special transitions. The builder provides all I need. When I think my workflow is special, I will remember: It is not. It fits Pattern 1 or Pattern 2. Complexity is the path to madness. The builder is the way."*

## **ENFORCEMENT**

Any PR that:
- Adds a new handler class → REJECTED
- Modifies GenericWorkflowHandler → REJECTED  
- Adds custom state machine logic → REJECTED
- Creates transitions manually → REJECTED
- Adds "special case" handling → REJECTED

The patterns are complete. Trust them.
``````
------ docs/principles/state_management_principles.md ------
``````
# **ALFRED STATE MANAGEMENT PRINCIPLES**

## **CORE PHILOSOPHY**
State is **ATOMIC TRUTH, not EVENTUAL CONSISTENCY**. Write once, trust forever. No partial updates.

## **THE GOLDEN RULES**

### **1. ATOMICITY IS NON-NEGOTIABLE**
- All state changes are atomic operations
- Use file locking for concurrent access protection
- Temporary files + `os.replace()` for atomic writes
- Failed operations leave original state intact

### **2. SINGLE SOURCE OF TRUTH**
- `TaskState` is the definitive state container
- No state duplication across files
- No caching of state data
- State lives in `.alfred/state/{task_id}.json`

### **3. IMMUTABLE STATE TRANSITIONS**
```python
State modification requirements:
- Load state → Modify copy → Atomic save
- No in-place mutations of loaded state
- All changes go through StateManager
- Context managers for complex updates
```

### **4. FILE LOCKING IS SACRED**
- Every state access acquires file lock
- Read operations get shared locks
- Write operations get exclusive locks
- Locks are ALWAYS released (use context managers)

### **5. SERIALIZATION IS PYDANTIC-ONLY**
- All state uses Pydantic models for serialization
- JSON format with proper validation
- No custom serialization logic
- Backward compatibility through model validation

### **6. NO STATE CACHING**
- State is always read from disk
- No in-memory state caches
- Fresh load for every access
- File system is the cache

## **WHEN WORKING WITH STATE**

### **DO:**
- ✅ Use `StateManager` for all state operations
- ✅ Acquire locks for every state access
- ✅ Use context managers for updates
- ✅ Validate state with Pydantic models
- ✅ Handle concurrent access gracefully
- ✅ Use atomic operations for writes

### **DON'T:**
- ❌ Cache state in memory
- ❌ Bypass file locking
- ❌ Make partial state updates
- ❌ Access state files directly
- ❌ Implement custom serialization
- ❌ Create state singletons

## **STATE OPERATION PATTERNS**

### **Simple State Read**
```python
# GOOD - Always through StateManager
def get_task_status(task_id: str) -> TaskStatus:
    state = StateManager.load_state(task_id)
    return state.status if state else TaskStatus.NEW

# BAD - Direct file access
def get_task_status(task_id: str) -> TaskStatus:
    with open(f".alfred/state/{task_id}.json") as f:  # NO!
        data = json.load(f)
        return TaskStatus(data["status"])
```

### **Atomic State Update**
```python
# GOOD - Atomic update with context manager
def update_task_status(task_id: str, new_status: TaskStatus):
    with StateManager.get_state_lock(task_id):
        state = StateManager.load_state(task_id)
        state.status = new_status
        StateManager.save_state(task_id, state)

# BAD - Non-atomic update
def update_task_status(task_id: str, new_status: TaskStatus):
    state = StateManager.load_state(task_id)  # Race condition!
    state.status = new_status
    StateManager.save_state(task_id, state)   # Lost updates!
```

### **Complex State Transaction**
```python
# GOOD - Transactional update
def complete_workflow_step(task_id: str, artifact: dict):
    with StateManager.update_state(task_id) as state:
        state.add_artifact("result", artifact)
        state.workflow_state.advance_step()
        # Automatic atomic save on context exit
```

## **CONCURRENCY HANDLING**

### **Lock Acquisition Patterns**
- **Read locks**: Multiple readers allowed
- **Write locks**: Exclusive access required
- **Timeout handling**: 30-second default timeout
- **Deadlock prevention**: Consistent lock ordering

### **Error Recovery**
- Failed writes preserve original state
- Lock timeouts raise clear exceptions
- Partial updates are impossible
- Consistent state guaranteed

## **STATE STRUCTURE**

### **TaskState Components**
```python
TaskState:
- task_id: str              # Immutable identifier
- status: TaskStatus        # Current workflow status  
- workflow_state: dict      # Tool-specific state data
- artifacts: dict           # Work products and results
- created_at: datetime      # Immutable creation time
- updated_at: datetime      # Last modification time
```

### **Artifact Management**
- Artifacts are versioned by workflow step
- No artifact overwriting (append-only)
- JSON-serializable data only
- Artifact keys follow consistent naming

## **TESTING STATE MANAGEMENT**

Test behavior, not implementation:

```python
def test_atomic_state_update():
    task_id = "test-123"
    
    # Concurrent updates should be safe
    def update_status():
        with StateManager.get_state_lock(task_id):
            state = StateManager.load_state(task_id)
            state.status = TaskStatus.IN_PROGRESS
            StateManager.save_state(task_id, state)
    
    # Both updates should succeed atomically
    thread1 = Thread(target=update_status)
    thread2 = Thread(target=update_status)
    
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    
    # Final state should be consistent
    final_state = StateManager.load_state(task_id)
    assert final_state.status == TaskStatus.IN_PROGRESS
```

## **ERROR HANDLING**

### **Lock Timeout Errors**
```python
try:
    with StateManager.get_state_lock(task_id, timeout=30):
        # State operations
        pass
except LockTimeoutError:
    # Clear error handling
    raise ToolResponse.error("State locked by another operation")
```

### **Validation Errors**
```python
try:
    state = StateManager.load_state(task_id)
except ValidationError as e:
    # State corruption detected
    raise ToolResponse.error(f"Invalid state format: {e}")
```

## **THE STATE MANAGEMENT PLEDGE**

*"I will not cache state. I will not bypass locks. I will trust in atomicity. When I think I need performance optimization, I will remember: Correctness first, performance second. Consistent state is more valuable than fast state. Atomic operations are the foundation of reliability."*

## **ENFORCEMENT**

Any PR that:
- Bypasses file locking → REJECTED
- Caches state in memory → REJECTED
- Makes non-atomic updates → REJECTED
- Accesses state files directly → REJECTED
- Implements custom serialization → REJECTED

State operations are atomic or they don't exist. There is no middle ground.
``````
------ docs/principles/task_provider_principles.md ------
``````
# **ALFRED TASK PROVIDER PRINCIPLES**

## **CORE PHILOSOPHY**
Task providers are **UNIFORM ADAPTERS, not SPECIAL INTEGRATIONS**. One interface, many backends. Behavior is consistent regardless of source.

## **THE GOLDEN RULES**

### **1. ONE INTERFACE TO RULE THEM ALL**
- All providers implement `BaseTaskProvider` interface
- **EXACTLY FOUR METHODS**: `get_task`, `get_all_tasks`, `create_task`, `get_next_task`
- No provider-specific methods or extensions
- Uniform behavior across all implementations

### **2. PROVIDER FACTORY IS IMMUTABLE**
- Provider selection happens through configuration
- Factory creates providers based on `settings.provider`
- No runtime provider switching
- Provider instances are stateless

### **3. DATA NORMALIZATION IS SACRED**
```python
Task data normalization requirements:
- All tasks conform to standard Task model
- Provider-specific data goes in metadata fields
- Status values map to standard TaskStatus enum
- No provider-specific task properties exposed
```

### **4. ERROR HANDLING IS UNIFORM**
- All providers raise same exception types
- Error messages are provider-agnostic
- Network/API errors become `ProviderError`
- Data format errors become `ValidationError`

### **5. TASK RANKING IS PROVIDER-INDEPENDENT**
- All providers use AL-61 algorithm for `get_next_task`
- Ranking considers: status, priority, age, dependencies
- No provider-specific ranking logic
- Recommendations include clear reasoning

### **6. NO PROVIDER LEAKAGE**
- Provider implementation details never exposed
- No conditional logic based on provider type
- Tools work identically regardless of provider
- Provider switching is transparent

## **WHEN ADDING A NEW PROVIDER**

### **DO:**
- ✅ Inherit from `BaseTaskProvider`
- ✅ Implement all four required methods
- ✅ Normalize data to standard Task model
- ✅ Use consistent error handling
- ✅ Follow AL-61 ranking algorithm
- ✅ Add configuration to provider factory

### **DON'T:**
- ❌ Add provider-specific methods
- ❌ Expose provider implementation details
- ❌ Create custom task models
- ❌ Implement custom ranking logic
- ❌ Add conditional provider behavior
- ❌ Cache provider data

## **PROVIDER INTERFACE CONTRACT**

### **Required Methods (ALL must be implemented)**
```python
class BaseTaskProvider:
    def get_task(self, task_id: str) -> Task:
        """Get single task by ID - MUST raise TaskNotFoundError if missing"""
        
    def get_all_tasks(self) -> List[Task]:
        """Get all tasks - MUST return empty list if none exist"""
        
    def create_task(self, task_content: str) -> Task:
        """Create new task - MUST validate format and return created task"""
        
    def get_next_task(self) -> Optional[Task]:
        """Get recommended next task - MUST use AL-61 algorithm"""
```

### **"But my provider needs special methods!"**
No, it doesn't. If the standard interface doesn't cover your use case, the interface is incomplete, not your provider.

## **DATA NORMALIZATION EXAMPLES**

### **GOOD Example - Proper normalization:**
```python
def _normalize_jira_task(self, jira_issue: dict) -> Task:
    return Task(
        task_id=jira_issue["key"],
        title=jira_issue["fields"]["summary"],
        context=jira_issue["fields"]["description"],
        status=self._map_jira_status(jira_issue["fields"]["status"]),
        priority=self._map_jira_priority(jira_issue["fields"]["priority"]),
        # Provider-specific data in metadata
        metadata={"jira_id": jira_issue["id"], "project": jira_issue["project"]}
    )
```

### **BAD Example - Provider-specific properties:**
```python
# NEVER DO THIS
class JiraTask(Task):
    jira_id: str        # NO! Provider-specific properties
    project_key: str    # NO! Use metadata instead

def get_task(self, task_id: str) -> JiraTask:  # NO! Return Task, not subclass
    pass
```

## **ERROR HANDLING PATTERNS**

### **Standard Error Mapping**
```python
try:
    response = jira_client.get_issue(task_id)
except JiraAPIError as e:
    if e.status_code == 404:
        raise TaskNotFoundError(f"Task {task_id} not found")
    else:
        raise ProviderError(f"Failed to fetch task: {e}")
except ValidationError as e:
    raise ProviderError(f"Invalid task data: {e}")
```

### **Consistent Error Messages**
```python
# GOOD - Provider-agnostic errors
raise TaskNotFoundError(f"Task {task_id} not found")
raise ProviderError("Failed to create task: Invalid format")

# BAD - Provider-specific errors  
raise JiraAPIError("JIRA-123 not found in project ABC")
raise LinearAPIError("GraphQL mutation failed")
```

## **TASK RANKING IMPLEMENTATION**

All providers MUST use the AL-61 algorithm:

```python
def get_next_task(self) -> Optional[Task]:
    tasks = self.get_all_tasks()
    
    # AL-61 algorithm (standardized)
    ready_tasks = [t for t in tasks if t.status in READY_STATUSES]
    
    if not ready_tasks:
        return None
    
    # Scoring: priority + age_bonus - dependency_penalty
    scored_tasks = []
    for task in ready_tasks:
        score = (
            task.priority.value * 10 +
            self._age_bonus(task) -
            self._dependency_penalty(task)
        )
        scored_tasks.append((score, task))
    
    # Return highest scoring task
    return max(scored_tasks, key=lambda x: x[0])[1]
```

## **TESTING TASK PROVIDERS**

Test interface compliance, not implementation:

```python
def test_provider_interface():
    provider = MyTaskProvider()
    
    # Test all required methods exist
    assert hasattr(provider, 'get_task')
    assert hasattr(provider, 'get_all_tasks')
    assert hasattr(provider, 'create_task')
    assert hasattr(provider, 'get_next_task')
    
    # Test error handling
    with pytest.raises(TaskNotFoundError):
        provider.get_task("nonexistent")
    
    # Test data normalization
    task = provider.get_task("existing-id")
    assert isinstance(task, Task)  # Not provider-specific subclass
```

## **PROVIDER CONFIGURATION**

### **Factory Registration**
```python
# GOOD - Clean factory registration
PROVIDER_CLASSES = {
    "local": LocalTaskProvider,
    "jira": JiraTaskProvider,
    "linear": LinearTaskProvider
}

def create_provider(provider_type: str) -> BaseTaskProvider:
    if provider_type not in PROVIDER_CLASSES:
        raise ValueError(f"Unknown provider: {provider_type}")
    return PROVIDER_CLASSES[provider_type]()
```

## **THE TASK PROVIDER PLEDGE**

*"I will not expose provider implementation details. I will not create provider-specific extensions. I will trust in uniform interfaces. When I think my provider needs special behavior, I will remember: The interface is the contract. All providers are equal. All tasks are normalized. Consistency across providers is more valuable than provider-specific features."*

## **ENFORCEMENT**

Any PR that:
- Adds provider-specific methods → REJECTED
- Exposes provider implementation details → REJECTED
- Creates custom task models → REJECTED
- Bypasses data normalization → REJECTED
- Implements custom ranking logic → REJECTED

Providers are adapters. Adapters are uniform. The interface is sacred.
``````
------ docs/principles/template_system_principles.md ------
``````
# **ALFRED TEMPLATE SYSTEM PRINCIPLES**

## **CORE PHILOSOPHY**
Templates are **DATA, not CODE**. They should be as static and predictable as possible.

## **THE GOLDEN RULES**

### **1. NEVER MODIFY TEMPLATE STRUCTURE**
- Templates follow a **STRICT SECTION FORMAT** - do not add, remove, or reorder sections
- The sections are: CONTEXT → OBJECTIVE → BACKGROUND → INSTRUCTIONS → CONSTRAINTS → OUTPUT → EXAMPLES
- If a section doesn't apply, leave it empty - DO NOT REMOVE IT

### **2. TEMPLATES ARE WRITE-ONCE**
- Once a template file is created, its **variables** are FROZEN
- You can edit the text content, but NEVER add new `${variables}`
- If you need new data, pass it through existing variables or create a NEW template

### **3. ONE FILE = ONE PURPOSE**
- Each template file serves **exactly one** state/purpose
- No conditional logic inside templates
- No dynamic content generation
- If you need different content for different scenarios, create separate template files

### **4. VARIABLE NAMING IS SACRED**
```
Standard variables (NEVER RENAME THESE):
- ${task_id}          - The task identifier
- ${tool_name}        - Current tool name  
- ${current_state}    - Current workflow state
- ${task_title}       - Task title
- ${task_context}     - Task goal/context
- ${implementation_details} - Implementation overview
- ${acceptance_criteria}    - Formatted AC list
- ${artifact_json}    - JSON representation of artifacts
- ${feedback}         - Review feedback
```

### **5. NO LOGIC IN TEMPLATES**
- **FORBIDDEN**: `{% if %}`, `{% for %}`, complex Jinja2
- **ALLOWED**: Simple `${variable}` substitution only
- If you need logic, handle it in Python and pass the result as a variable

### **6. EXPLICIT PATHS ONLY**
- Template location = `prompts/{tool_name}/{state}.md`
- No dynamic path construction
- No fallback chains
- If a template doesn't exist, it's an ERROR - don't silently fall back

## **WHEN WORKING WITH TEMPLATES**

### **DO:**
- ✅ Edit prompt text to improve AI behavior
- ✅ Clarify instructions within existing structure  
- ✅ Add examples in the EXAMPLES section
- ✅ Improve formatting for readability
- ✅ Fix typos and grammar

### **DON'T:**
- ❌ Add new variables to existing templates
- ❌ Create dynamic template paths
- ❌ Add conditional logic
- ❌ Merge multiple templates into one
- ❌ Create "smart" template loading logic
- ❌ Mix templates with code generation

## **ADDING NEW FUNCTIONALITY**

### **Need a new prompt?**
1. Create a new file at the correct path: `prompts/{tool_name}/{state}.md`
2. Use ONLY the standard variables listed above
3. Follow the EXACT section structure
4. Test that it renders with standard context

### **Need new data in a prompt?**
1. **STOP** - Can you use existing variables?
2. If absolutely necessary, document the new variable in the template header
3. Update the PromptBuilder to provide this variable
4. Update THIS DOCUMENT with the new standard variable

### **Need conditional behavior?**
1. Create separate template files for each condition
2. Handle the logic in Python code
3. Choose which template to load based on the condition

## **TEMPLATE HEADER REQUIREMENT**

Every template MUST start with this header:

```markdown
<!--
Template: {tool_name}.{state}
Purpose: [One line description]
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  [List ALL variables used in this template]
-->
```

## **TESTING TEMPLATES**

Before committing ANY template change:

1. **Variable Check**: List all `${variables}` in the template
2. **Render Test**: Ensure it renders with standard context
3. **No Logic Check**: Confirm no `{% %}` tags exist
4. **Structure Check**: Verify all sections are present

```python
# Test snippet to include in your tests
def verify_template(template_path):
    content = template_path.read_text()
    
    # No Jinja2 logic
    assert '{%' not in content, "No logic allowed in templates"
    
    # Has all sections
    required_sections = ['# CONTEXT', '# OBJECTIVE', '# BACKGROUND', 
                        '# INSTRUCTIONS', '# CONSTRAINTS', '# OUTPUT']
    for section in required_sections:
        assert section in content, f"Missing {section}"
    
    # Extract variables
    import re
    variables = re.findall(r'\$\{(\w+)\}', content)
    
    # All variables are standard
    standard_vars = {'task_id', 'tool_name', 'current_state', 'task_title',
                    'task_context', 'implementation_details', 'acceptance_criteria',
                    'artifact_json', 'feedback'}
    
    unknown_vars = set(variables) - standard_vars
    assert not unknown_vars, f"Unknown variables: {unknown_vars}"
```

## **ERROR MESSAGES**

When templates fail, the error should be:
- **SPECIFIC**: "Missing required variable 'task_id' in template plan_task.contextualize"
- **ACTIONABLE**: Show what variables were provided vs required
- **TRACEABLE**: Include the template file path

Never:
- Silently fall back to a default
- Generate templates dynamically
- Guess at missing variables

## **THE MAINTENANCE PLEDGE**

*"I will treat templates as immutable contracts. I will not add complexity to make them 'smarter'. I will keep logic in code and content in templates. When in doubt, I will create a new template rather than make an existing one more complex."*

---

**Remember**: Every time you add logic to a template, somewhere a production system breaks at 3 AM. Keep templates simple, predictable, and boring. Boring templates are reliable templates.
``````
------ docs/principles/tool_registration_principles.md ------
``````
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
``````
------ docs/principles/workflow_configuration_principles.md ------
``````
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
``````
