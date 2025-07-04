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