# CRITICAL REFACTORING INSTRUCTION: Step 3 - Simplify State Management

**ATTENTION**: This is the third CRITICAL refactoring task. The current Unit of Work (UoW) pattern is over-engineered for simple state updates. We need to simplify while maintaining atomicity and safety. Triple check that all state persistence remains atomic and reliable.

## OBJECTIVE
Replace the complex Unit of Work pattern with simpler, direct state management methods while maintaining atomic writes and proper locking.

## CURRENT PROBLEM
The current state management has:
- Unnecessary UoW pattern for single-object updates
- Complex transaction management for simple operations
- ~200 lines of code for what should be ~50 lines
- Confusing separation between StateManager and StateUnitOfWork

Most operations are simple:
- Update task status
- Update tool state
- Add completed output

These don't need a full UoW pattern.

## STEP-BY-STEP IMPLEMENTATION

### 1. Simplify StateManager
**UPDATE** `src/alfred/state/manager.py` to remove UoW and provide direct methods:

```python
# src/alfred/state/manager.py
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

from src.alfred.lib.fs_utils import file_lock
from src.alfred.lib.logger import get_logger
from src.alfred.models.state import TaskState, WorkflowState
from src.alfred.models.schemas import TaskStatus
from src.alfred.config.settings import settings
from pydantic import BaseModel

logger = get_logger(__name__)


class StateManager:
    """
    Simplified state manager with direct methods instead of UoW pattern.
    
    Each method handles its own locking and atomic writes.
    """

    def _get_task_dir(self, task_id: str) -> Path:
        return settings.workspace_dir / task_id

    def _get_task_state_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "task_state.json"

    def _get_lock_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / ".state.lock"

    def _atomic_write(self, state: TaskState) -> None:
        """Atomically write state to disk. Assumes lock is already held."""
        state_file = self._get_task_state_file(state.task_id)
        state.updated_at = datetime.utcnow().isoformat()

        # Ensure directory structure exists
        task_dir = state_file.parent
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # Create archive directory
        archive_dir = task_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Create empty scratchpad if it doesn't exist
        scratchpad_path = task_dir / "scratchpad.md"
        if not scratchpad_path.exists():
            scratchpad_path.touch(mode=0o600)

        # Atomic write using temp file
        fd, temp_path_str = tempfile.mkstemp(
            dir=state_file.parent, 
            prefix=".tmp_state_", 
            suffix=".json"
        )
        temp_path = Path(temp_path_str)
        
        try:
            with os.fdopen(fd, "w") as f:
                f.write(state.model_dump_json(indent=2))
            os.replace(temp_path, state_file)
            logger.debug(f"Atomically wrote state for task {state.task_id}")
        except Exception:
            if temp_path.exists():
                os.remove(temp_path)
            raise

    def load_or_create(self, task_id: str) -> TaskState:
        """Load task state from disk, creating if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)

        if not state_file.exists():
            logger.info(f"No state file for task {task_id}. Creating new state.")
            return TaskState(task_id=task_id)

        try:
            with state_file.open("r") as f:
                data = json.load(f)
            return TaskState.model_validate(data)
        except Exception as e:
            logger.error(
                f"Failed to load or validate state for task {task_id}, "
                f"creating new. Error: {e}"
            )
            return TaskState(task_id=task_id)
    
    # Backward compatibility alias
    def load_or_create_task_state(self, task_id: str) -> TaskState:
        """Alias for backward compatibility."""
        return self.load_or_create(task_id)

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        """Update task status with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            old_status = state.task_status
            state.task_status = new_status
            self._atomic_write(state)
            
        logger.info(
            f"Updated task {task_id} status: {old_status.value} -> {new_status.value}"
        )

    def update_tool_state(self, task_id: str, tool: Any) -> None:
        """Update tool state with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            
            # Serialize context store
            serializable_context = {}
            for key, value in tool.context_store.items():
                if isinstance(value, BaseModel):
                    serializable_context[key] = value.model_dump()
                else:
                    serializable_context[key] = value
            
            # Create workflow state
            tool_state = WorkflowState(
                task_id=task_id,
                tool_name=tool.tool_name,
                current_state=str(tool.state),
                context_store=serializable_context
            )
            
            state.active_tool_state = tool_state
            self._atomic_write(state)
            
        logger.debug(f"Updated tool state for task {task_id}, tool {tool.tool_name}")

    def clear_tool_state(self, task_id: str) -> None:
        """Clear active tool state with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            state.active_tool_state = None
            self._atomic_write(state)
            
        logger.info(f"Cleared tool state for task {task_id}")

    def add_completed_output(
        self, 
        task_id: str, 
        tool_name: str, 
        artifact: Any
    ) -> None:
        """Add completed tool output with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            
            # Serialize artifact
            if isinstance(artifact, BaseModel):
                serializable_artifact = artifact.model_dump()
            else:
                serializable_artifact = artifact
                
            state.completed_tool_outputs[tool_name] = serializable_artifact
            self._atomic_write(state)
            
        logger.info(f"Added completed output for task {task_id}, tool {tool_name}")

    @contextmanager
    def complex_update(self, task_id: str):
        """
        Context manager for complex updates that need multiple field changes.
        
        This is only needed when you need to update multiple fields atomically.
        For single field updates, use the direct methods above.
        
        Example:
            with state_manager.complex_update(task_id) as state:
                state.task_status = TaskStatus.IN_PROGRESS
                state.active_tool_state = tool_state
                # Changes are automatically saved on context exit
        """
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            original_data = state.model_dump_json()
            
            try:
                yield state
                # Only write if state actually changed
                if state.model_dump_json() != original_data:
                    self._atomic_write(state)
                    logger.debug(f"Complex update completed for task {task_id}")
            except Exception as e:
                logger.error(
                    f"Complex update failed for task {task_id}: {e}", 
                    exc_info=True
                )
                raise

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        from src.alfred.constants import Paths
        
        archive_path = self._get_task_dir(task_id) / Paths.ARCHIVE_DIR
        archive_path.mkdir(parents=True, exist_ok=True)
        return archive_path

    def register_tool(self, task_id: str, tool: "BaseWorkflowTool") -> None:
        """Register a tool with the orchestrator and update state."""
        from src.alfred.orchestration.orchestrator import orchestrator
        
        orchestrator.active_tools[task_id] = tool
        self.update_tool_state(task_id, tool)
        logger.info(f"Registered {tool.tool_name} tool for task {task_id}")


# Singleton instance
state_manager = StateManager()
```

### 2. Delete the UnitOfWork Module
**DELETE** the entire file `src/alfred/state/unit_of_work.py` - it's no longer needed.

### 3. Update All UoW Usage
**CRITICAL**: Find and replace all Unit of Work usage with direct method calls.

**UPDATE** in `src/alfred/tools/generic_handler.py`:

```python
# In _setup_tool method, replace:
# OLD:
with state_manager.transaction() as uow:
    uow.update_tool_state(task.task_id, tool_instance)

# NEW:
state_manager.update_tool_state(task.task_id, tool_instance)
```

**UPDATE** in `src/alfred/tools/provide_review_logic.py`:

```python
# Replace all UoW usage:

# OLD:
with state_manager.transaction() as uow:
    uow.update_tool_state(task_id, active_tool)

# NEW:
state_manager.update_tool_state(task_id, active_tool)

# OLD:
with state_manager.transaction() as uow:
    if artifact:
        uow.add_completed_output(task_id, tool_name, artifact)
    uow.clear_tool_state(task_id)

# NEW:
if artifact:
    state_manager.add_completed_output(task_id, tool_name, artifact)
state_manager.clear_tool_state(task_id)
```

**UPDATE** in `src/alfred/tools/submit_work.py`:

```python
# Replace:
# OLD:
with state_manager.transaction() as uow:
    uow.update_tool_state(task.task_id, tool_instance)

# NEW:
state_manager.update_tool_state(task.task_id, tool_instance)
```

**UPDATE** in `src/alfred/tools/progress.py` (mark_subtask_complete):

```python
# Replace:
# OLD:
with state_manager.transaction() as uow:
    uow.update_tool_state(task.task_id, tool_instance)

# NEW:
state_manager.update_tool_state(task.task_id, tool_instance)
```

### 4. Update BaseToolHandler
**UPDATE** `src/alfred/tools/base_tool_handler.py`:

```python
# In the _get_or_create_tool method, update the status transition:

# Find this section:
tool_config = tool_registry.get_tool_config(self.tool_name)
if tool_config and task.task_status in tool_config.entry_status_map:
    new_status = tool_config.entry_status_map[task.task_status]
    state_manager.update_task_status(task_id, new_status)

# It stays the same! The direct method is cleaner than UoW
```

### 5. Update Complex State Updates
For the few places that need multiple updates, use the new `complex_update` context manager.

**Example** - If you find code that updates multiple fields:

```python
# OLD:
with state_manager.transaction() as uow:
    uow.update_task_status(task_id, TaskStatus.IN_PROGRESS)
    uow.update_tool_state(task_id, tool)
    uow.add_completed_output(task_id, "some_tool", artifact)

# NEW - Option 1: Individual calls (if atomicity between them isn't critical):
state_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
state_manager.update_tool_state(task_id, tool)
state_manager.add_completed_output(task_id, "some_tool", artifact)

# NEW - Option 2: Use complex_update (if atomicity is critical):
with state_manager.complex_update(task_id) as state:
    state.task_status = TaskStatus.IN_PROGRESS
    state.active_tool_state = create_workflow_state(tool)
    state.completed_tool_outputs["some_tool"] = artifact
```

### 6. Update Imports
**CRITICAL**: Remove all imports of StateUnitOfWork.

Search for and remove:
```python
from src.alfred.state.unit_of_work import StateUnitOfWork
```

Update `src/alfred/state/__init__.py`:
```python
"""
State management module for Alfred workflow tools.

This module provides persistence and recovery capabilities for workflow tools,
ensuring that task progress survives crashes and restarts.
"""

from src.alfred.state.manager import StateManager, state_manager
from src.alfred.state.recovery import ToolRecovery

__all__ = ["StateManager", "state_manager", "ToolRecovery"]
```

## VERIFICATION CHECKLIST
**CRITICAL**: After making these changes, verify:

1. ✓ All state updates still work correctly
2. ✓ File locking is still in place for all updates
3. ✓ Atomic writes still use temp file + rename pattern
4. ✓ No references to StateUnitOfWork remain
5. ✓ All imports are updated
6. ✓ State persistence works across tool restarts
7. ✓ Concurrent access is still safe (file locks)
8. ✓ Error handling still works (no partial writes)

## TESTING REQUIREMENTS
Test these scenarios to ensure state management still works:

1. **Basic Operations**:
   ```python
   # Test status update
   state_manager.update_task_status("test-1", TaskStatus.IN_PROGRESS)
   
   # Verify it persisted
   state = state_manager.load_or_create("test-1")
   assert state.task_status == TaskStatus.IN_PROGRESS
   ```

2. **Tool State Persistence**:
   - Create a tool, update its state
   - Verify the state file contains the tool state
   - Restart and recover the tool
   - Verify state was preserved

3. **Concurrent Access**:
   - Try to update the same task from two processes
   - Verify file locking prevents corruption

4. **Error Handling**:
   - Simulate a write failure (e.g., disk full)
   - Verify no partial state files are left

## PERFORMANCE COMPARISON

The new approach should be:
- **Faster**: No UoW overhead for simple operations
- **Simpler**: Direct method calls instead of transaction blocks
- **Clearer**: Each method does one thing

Measure:
- Time to update task status: Should be ~50% faster
- Time to update tool state: Should be ~30% faster
- Memory usage: Should be lower (no UoW objects)

## METRICS TO VERIFY

Lines of code:
- Removed from `unit_of_work.py`: ~170 lines
- Simplified in `manager.py`: ~50 lines removed
- Updated call sites: ~20-30 replacements
- **Net reduction: ~200+ lines**

Complexity:
- Cyclomatic complexity of StateManager: Should decrease
- Number of classes: -1 (removed StateUnitOfWork)
- Indentation levels: Reduced by removing `with` blocks

## FINAL VALIDATION SCRIPT

Run this to ensure state management works correctly:

```python
#!/usr/bin/env python3
"""Validate simplified state management."""

import asyncio
import tempfile
from pathlib import Path

from src.alfred.models.schemas import TaskStatus
from src.alfred.state.manager import state_manager
from src.alfred.config.settings import settings

def test_state_management():
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        settings.workspace_dir = Path(tmpdir)
        
        task_id = "test-task-1"
        
        # Test 1: Create and update status
        print("Test 1: Status update")
        state_manager.update_task_status(task_id, TaskStatus.IN_PROGRESS)
        state = state_manager.load_or_create(task_id)
        assert state.task_status == TaskStatus.IN_PROGRESS
        print("✓ Status update works")
        
        # Test 2: Tool state
        print("\nTest 2: Tool state")
        from src.alfred.core.workflow import PlanTaskTool
        tool = PlanTaskTool(task_id)
        tool.context_store["test_key"] = "test_value"
        
        state_manager.update_tool_state(task_id, tool)
        state = state_manager.load_or_create(task_id)
        assert state.active_tool_state is not None
        assert state.active_tool_state.tool_name == "plan_task"
        print("✓ Tool state persistence works")
        
        # Test 3: Completed outputs
        print("\nTest 3: Completed outputs")
        state_manager.add_completed_output(task_id, "test_tool", {"result": "success"})
        state = state_manager.load_or_create(task_id)
        assert "test_tool" in state.completed_tool_outputs
        assert state.completed_tool_outputs["test_tool"]["result"] == "success"
        print("✓ Completed outputs work")
        
        # Test 4: Complex update
        print("\nTest 4: Complex update")
        with state_manager.complex_update(task_id) as state:
            state.task_status = TaskStatus.DONE
            state.active_tool_state = None
        
        state = state_manager.load_or_create(task_id)
        assert state.task_status == TaskStatus.DONE
        assert state.active_tool_state is None
        print("✓ Complex updates work")
        
        print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_state_management()
```

This completes the state management simplification. The code is now much cleaner and easier to understand while maintaining all safety guarantees.