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