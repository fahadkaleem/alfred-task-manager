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