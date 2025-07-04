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