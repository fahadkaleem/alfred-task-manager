### **Task Directive: ALFRED-06 - Implement the Artifact Manager**

**Objective:** To create a centralized `ArtifactManager` responsible for all file system I/O within the `.alfred` workspace. This component is critical for persisting the outputs of each persona (e.g., the `git_setup` manifest, the final `developer` manifest) and for reading the machine-readable `execution_plan.json` required by the developer persona.

**CRITICAL INSTRUCTION:** This is a foundational component that removes stubbed logic. The implementation must be robust and handle all specified file operations precisely.

---

### **1. Create the Artifact Manager and Supporting Components**

This class will encapsulate all file I/O operations.

**File:** `src/alfred/lib/artifact_manager.py`
```python
"""
Manages reading and writing all artifacts and data within the .alfred workspace.
"""
import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.alfred.config.settings import settings

class ArtifactManager:
    """Handles all file system I/O for task artifacts."""

    def __init__(self):
        self.template_loader = FileSystemLoader(searchpath=str(settings.packaged_templates_dir))
        self.jinja_env = Environment(loader=self.template_loader)

    def _get_task_dir(self, task_id: str) -> Path:
        """Gets the directory for a specific task in the .alfred/workspace."""
        return settings.workspace_dir / task_id

    def _get_archive_dir(self, task_id: str) -> Path:
        """Gets the archive directory for a specific task."""
        return self._get_task_dir(task_id) / "archive"

    def create_task_workspace(self, task_id: str):
        """Creates the directory structure for a new task."""
        self._get_task_dir(task_id).mkdir(parents=True, exist_ok=True)
        self._get_archive_dir(task_id).mkdir(exist_ok=True)

    def write_artifact(self, task_id: str, persona_name: str, artifact: BaseModel, is_final: bool = False):
        """
        Writes a structured artifact to the filesystem.

        If is_final, it writes to the archive. Otherwise, to the live scratchpad.
        """
        # Determine filename and path
        # Simple naming for now. A more complex system could use versioning.
        filename = f"{persona_name}_artifact.md"
        archive_dir = self._get_archive_dir(task_id)

        # In a real scenario, we might use a live 'scratchpad.md'
        # For now, we'll write directly to the archive path for simplicity on finalization.
        if is_final:
            artifact_path = archive_dir / filename
        else:
            # Placeholder for live/scratchpad logic
            # For now, let's just log that we would write to a scratchpad
            print(f"INFO: Would write to scratchpad for task {task_id}")
            return

        # Get template
        template_path = f"artifacts/{persona_name}.md"
        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            print(f"ERROR: Could not find artifact template at {template_path}: {e}")
            return

        # Prepare context
        context = {
            "task_id": task_id,
            "artifact": artifact,
        }
        content = template.render(context)
        artifact_path.write_text(content, encoding="utf-8")
        print(f"INFO: Wrote artifact to {artifact_path}")

    def read_execution_plan(self, task_id: str) -> dict[str, Any] | None:
        """
        Reads the machine-readable execution plan from the planning phase.

        NOTE: This assumes a 'planning' persona has run and archived
        an 'execution_plan.json'. We will stub this for now.
        """
        # This path assumes a future 'planning' persona will create this file.
        plan_path = self._get_archive_dir(task_id) / "planning_execution_plan.json"
        if not plan_path.exists():
            # STUB: Return a default plan if one doesn't exist for testing purposes.
            print("WARN: execution_plan.json not found. Using stubbed plan.")
            return {"steps": [{"id": "STEP-001", "instruction": "Do the first thing."}, {"id": "STEP-002", "instruction": "Do the second thing."}]}

        try:
            with plan_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"ERROR: Failed to read or parse execution plan at {plan_path}: {e}")
            return None

# Singleton instance
artifact_manager = ArtifactManager()
```

### **2. Integrate the Artifact Manager into the Orchestrator**

Refactor the `Orchestrator` to use the new `ArtifactManager` instead of stubbed data.

**File:** `src/alfred/orchestration/orchestrator.py`
*(Make the following changes)*
```python
# Add new import at the top
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.models.artifacts import GitSetupArtifact # Add this import

# In the Orchestrator class, modify _get_or_create_runtime
# ...
        if not task_state:
            # This is a new task
            task_state = TaskState(task_id=task_id)
            # --- CHANGE: Create the task workspace ---
            artifact_manager.create_task_workspace(task_id)
            # --- END CHANGE ---
            if not self.workflow_sequence:
# ...

# In the Orchestrator class, modify process_handoff
# ...
        # --- CHANGE: Archive the artifact ---
        # This requires knowing the artifact type for the completed persona.
        # We will need a more robust way to handle this mapping.
        # For now, we'll handle git_setup as a special case.
        if runtime.config.name == 'git_setup' and runtime.state == 'verified':
            # This is where we would fetch the submitted artifact data from a temp store
            # and write it. Since we don't have that, we'll create a dummy one.
            final_artifact = GitSetupArtifact(
                branch_name=f"feature/{task_id}",
                branch_status="clean",
                ready_for_work=True
            )
            artifact_manager.write_artifact(task_id, 'git_setup', final_artifact, is_final=True)
        # --- END CHANGE ---

        # 2. Update master state
# ...

# In the Orchestrator class, modify process_step_completion
# ...
        # --- CHANGE: Load execution plan from the artifact manager ---
        execution_plan = artifact_manager.read_execution_plan(task_id)
        if not execution_plan or "steps" not in execution_plan:
            return "Error: Failed to load a valid execution plan.", None
        # --- END CHANGE ---

        if task_state.current_step >= len(execution_plan["steps"]):
# ...
```

### **3. Refactor Work Submission to Store Artifact Data**

The current `submit_work` flow doesn't store the artifact data anywhere. We need to temporarily hold it so it can be archived during the handoff.

**File:** `src/alfred/orchestration/persona_runtime.py`
*(Add a new attribute to the `__init__` method)*
```python
    def __init__(self, task_id: str, config: PersonaConfig):
        # ... existing init code ...
        self.submitted_artifact_data: dict | None = None
```*(Modify the `submit_work` method)*
```python
    def submit_work(self, artifact_data: dict) -> tuple[bool, str]:
        """
        Processes a work submission, validates it, and triggers a state transition.
        """
        # ... existing validation logic ...

        # --- CHANGE: Store the artifact data on the runtime ---
        self.submitted_artifact_data = artifact_data
        # --- END CHANGE ---

        # Trigger the state transition. This assumes a 'submit' trigger exists.
        # ... existing trigger logic ...
```

**File:** `src/alfred/orchestration/orchestrator.py`
*(Modify the `process_handoff` method again to use the stored data)*
```python
# In process_handoff, replace the "Archive the artifact" block with this:
        # --- CHANGE: Archive the artifact ---
        if runtime.config.name == 'git_setup' and runtime.state == 'verified':
            if runtime.submitted_artifact_data:
                final_artifact = GitSetupArtifact(**runtime.submitted_artifact_data)
                artifact_manager.write_artifact(task_id, 'git_setup', final_artifact, is_final=True)
            else:
                print(f"WARN: No submitted artifact data found for task {task_id} on handoff.")
        # --- END CHANGE ---
```

---
### **4. Validation**

1.  Run the full flow for `TEST-01`: `begin_task`, `submit_work`, `provide_review`, `approve_and_handoff`.
2.  **Expected Output:**
    *   The `developer` persona should activate as before.
    *   The console should log a `WARN` message about the `execution_plan.json` not being found and that a stub is being used. This is correct for this task.
    *   Check the project directory. There should now be a `.alfred/workspace/TEST-01/archive/git_setup_artifact.md` file.
3.  Inspect the content of `git_setup_artifact.md`. It should be correctly rendered with the data provided during the `submit_work` call.
