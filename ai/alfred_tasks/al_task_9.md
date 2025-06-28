### **Task Directive: ALFRED-09 - Implement Observability Framework**

**Objective:** To instrument the Alfred application with a robust, task-specific logging and transaction tracing framework. This will create a detailed audit trail for every operation, enabling effective debugging and analysis. This framework must be gated by a new configuration flag.

**CRITICAL INSTRUCTION:** This is an architectural enhancement. Adhere to the specified class designs and integration points precisely. The goal is to create a clean, centralized system, not to sprinkle `print` statements throughout the code.

---

### **1. Update Configuration**

Add a `debugging_mode` flag to the application settings. This will control the entire observability framework.

**File:** `src/alfred/config/settings.py`
*(Add the new field to the `Settings` class)*
```python
class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_prefix="ALFRED_", case_sensitive=False)

    # NEW: Debugging flag
    debugging_mode: bool = True

    # Server configuration
    # ... rest of the file
```

### **2. Implement Centralized Logging**

Create a new library module for logging. This will be responsible for setting up and managing file-based log handlers for each task.

**File:** `src/alfred/lib/logger.py`
```python
"""
Centralized logging configuration for Alfred.
"""
import logging
from pathlib import Path

from src.alfred.config.settings import settings

# A dictionary to hold task-specific handlers to avoid duplication
_task_handlers = {}

def get_logger(name: str) -> logging.Logger:
    """Gets a logger instance with the specified name."""
    return logging.getLogger(name)

def setup_task_logging(task_id: str):
    """
    Sets up a specific file handler for a given task ID.
    This function is idempotent.
    """
    if not settings.debugging_mode or task_id in _task_handlers:
        return

    # Create the debug directory for the task
    debug_dir = settings.alfred_dir / "debug" / task_id
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / "logs.txt"

    # Create a file handler
    handler = logging.FileHandler(log_file, mode='a')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the root logger to capture logs from all modules
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO) # Set a base level

    _task_handlers[task_id] = handler
    print(f"INFO: Task-specific logging enabled for {task_id} at {log_file}")

def cleanup_task_logging(task_id: str):
    """Removes a task-specific log handler."""
    if task_id in _task_handlers:
        handler = _task_handlers.pop(task_id)
        logging.getLogger().removeHandler(handler)
        handler.close()
```

### **3. Implement MCP Transaction Logger**

Create a new library module for logging the request/response cycle of every tool call. We will use the JSON Lines format (`.jsonl`) as it is ideal for append-only logging.

**File:** `src/alfred/lib/transaction_logger.py`
```python
"""
Logs MCP tool requests and responses for debugging and analysis.
"""
import json
from datetime import datetime, timezone

from src.alfred.config.settings import settings
from src.alfred.models.schemas import ToolResponse

class TransactionLogger:
    """Logs a single transaction to a task-specific .jsonl file."""

    def log(self, task_id: str, tool_name: str, request_data: dict, response: ToolResponse):
        """Appends a transaction record to the log."""
        if not settings.debugging_mode:
            return

        if not task_id:
            # Handle transactions that don't have a task_id (like initialize_project)
            task_id = "SYSTEM"

        # Create the debug directory for the task
        debug_dir = settings.alfred_dir / "debug" / task_id
        debug_dir.mkdir(parents=True, exist_ok=True)
        log_file = debug_dir / "transactions.jsonl"

        log_entry = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "tool_name": tool_name,
            "request": request_data,
            "response": response.model_dump(mode='json'),
        }

        try:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except IOError as e:
            print(f"ERROR: Failed to write to transaction log for task {task_id}: {e}")

# Singleton instance
transaction_logger = TransactionLogger()
```

### **4. Integrate Observability into the Application**

Now, wire the new components into the main application logic.

**File:** `src/alfred/orchestration/orchestrator.py`
*(Add logging to key methods)*
```python
# Add new imports at the top
from src.alfred.lib.logger import get_logger, setup_task_logging

# Get a logger instance for this module
logger = get_logger(__name__)

# ... inside the Orchestrator class ...
    def begin_task(self, task_id: str) -> tuple[str, str | None]:
        """
        Begins or resumes a task, returning an initial prompt.
        """
        # --- NEW: Setup logging for this task ---
        setup_task_logging(task_id)
        logger.info(f"Orchestrator beginning/resuming task {task_id}.")
        # --- END NEW ---

        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            logger.error(f"Failed to get or create runtime for task {task_id}.")
            return ("Error: Could not create or find a runtime for this task. Check workflow/persona configuration.", None)
        # ... rest of the method
```

**File:** `src/alfred/server.py`
*(Modify ALL tool definitions to log transactions)*
```python
# Add new imports
from src.alfred.lib.transaction_logger import transaction_logger
import inspect

# ... existing imports ...

# --- REFACTOR ALL TOOLS TO LOG TRANSACTIONS ---
# This is the new pattern that must be applied to every tool.

@app.tool()
async def initialize_project() -> ToolResponse:
    # ... (docstring) ...
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {} # No parameters for this tool
    response = initialize_project_impl()
    transaction_logger.log(task_id=None, tool_name=tool_name, request_data=request_data, response=response)
    return response

@app.tool()
async def begin_task(task_id: str) -> ToolResponse:
    # ... (docstring) ...
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = begin_task_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response

# ... APPLY THE SAME PATTERN TO ALL OTHER TOOLS ...
# (submit_work, provide_review, approve_and_handoff, mark_step_complete)

@app.tool()
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "artifact": artifact}
    response = submit_work_impl(task_id, artifact)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response

# (And so on for the rest of the tools)
```

---
### **5. Validation**

1.  Delete the `.alfred` directory. Run `initialize_project()`.
2.  **Expected:** A `.alfred/debug/SYSTEM/transactions.jsonl` file should be created, containing one JSON object for the `initialize_project` call.
3.  Call `begin_task(task_id='DEBUG-01')`.
4.  **Expected:**
    *   A new directory `.alfred/debug/DEBUG-01/` is created.
    *   Inside, a `logs.txt` file is created. It should contain at least one log entry from the `Orchestrator`.
    *   Inside, a `transactions.jsonl` file is created. It should contain one JSON object for the `begin_task` call.
5.  Call `submit_work(...)` for the same task.
6.  **Expected:** A new line is appended to `.alfred/debug/DEBUG-01/transactions.jsonl` containing the details of the `submit_work` call.
