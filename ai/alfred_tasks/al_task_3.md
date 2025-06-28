### **Task Directive: ALFRED-03 - Implement Work Submission**

**Objective:** To enable the submission of a work artifact, which will trigger a state transition within the active persona's HSM. This task implements the `submit_work` tool and the underlying logic to process it.

---

### **1. Create Artifact Model and Template**

First, define the data structure and presentation for the `git_setup` persona's artifact.

**File:** `src/alfred/models/artifacts.py`
```python
"""
Pydantic models for structured work artifacts.
"""
from pydantic import BaseModel, Field

class GitSetupArtifact(BaseModel):
    """
    Structured data artifact for the git_setup phase.
    """
    branch_name: str = Field(..., description="The name of the git branch created or used.")
    branch_status: str = Field(..., description="The status of the branch, e.g., 'clean'.")
    ready_for_work: bool = Field(..., description="Confirmation that the branch is ready for development.")
```

**File:** `src/alfred/templates/artifacts/git_setup.md`
```markdown
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: working
---

# Git Setup Complete: {{ task_id }}

## Branch Information

- **Branch Name:** `{{ artifact.branch_name }}`
- **Branch Status:** {{ artifact.branch_status }}
- **Ready for Work:** {{ artifact.ready_for_work }}

## Summary

The git environment has been successfully prepared for development work on the specified feature branch.
```

### **2. Enhance `PersonaRuntime` to Process Submissions**

Add a method to the `PersonaRuntime` class to handle an incoming work submission.

**File:** `src/alfred/orchestration/persona_runtime.py`
*(Add the following method inside the `PersonaRuntime` class)*
```python
    def submit_work(self, artifact_data: dict) -> tuple[bool, str]:
        """
        Processes a work submission, validates it, and triggers a state transition.

        Returns:
            A tuple of (success: bool, message: str)
        """
        # A more robust solution would map state to artifact model
        from src.alfred.models.artifacts import GitSetupArtifact
        try:
            # For now, we hardcode the GitSetupArtifact for this example.
            # A future implementation will need a mapping.
            if self.state == 'working':
                _ = GitSetupArtifact(**artifact_data)
        except Exception as e:
            return False, f"Artifact validation failed: {e}"

        # Trigger the state transition. This assumes a 'submit' trigger exists.
        try:
            self.submit() # This is the HSM trigger, e.g., model.submit()
            return True, f"Work submitted. New state is '{self.state}'."
        except Exception as e:
            # Handle cases where the transition is not allowed from the current state
            return False, f"Could not trigger submission from state '{self.state}': {e}"

```

### **3. Enhance `Orchestrator` to Route Submissions**

Add a method to the `Orchestrator` to route the `submit_work` call to the correct runtime.

**File:** `src/alfred/orchestration/orchestrator.py`
*(Add the following method inside the `Orchestrator` class)*
```python
    def submit_work_for_task(self, task_id: str, artifact_data: dict) -> tuple[str, str | None]:
        """
        Routes a work submission to the correct persona runtime.
        Returns: (message, next_prompt)
        """
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return ("Error: Task runtime not found.", None)

        success, message = runtime.submit_work(artifact_data)
        if not success:
            return (message, None)

        # If successful, save the new state and get the next prompt
        task_state = self._load_state().tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)

        next_prompt = runtime.get_current_prompt()
        return (message, next_prompt)
```

### **4. Implement and Expose the `submit_work` Tool**

Update the `task_tools.py` and `server.py` files.

**File:** `src/alfred/tools/task_tools.py`
*(Add the following function to the file)*
```python
def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a completed work artifact for the current phase of a task.
    """
    message, next_prompt = orchestrator.submit_work_for_task(task_id, artifact)

    if next_prompt is None:
        return ToolResponse(status="error", message=message)

    return ToolResponse(
        status="success",
        message=message,
        next_prompt=next_prompt,
    )
```

**File:** `src/alfred/server.py`
*(Add the new tool to the server)*
```python
"""
MCP Server for Alfred
"""
from fastmcp import FastMCP
from src.alfred.config.settings import settings
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.task_tools import begin_task as begin_task_impl
# New import
from src.alfred.tools.task_tools import submit_work as submit_work_impl

app = FastMCP(settings.server_name)

@app.tool()
async def initialize_project() -> ToolResponse:
    """
    Initializes the project for Alfred. Creates a .alfred directory with default
    configurations for personas and workflows. This must be the first tool

    called in a new project.
    """
    return initialize_project_impl()

@app.tool()
async def begin_task(task_id: str) -> ToolResponse:
    """
    Begins or resumes a task with the appropriate persona and state.
    """
    return begin_task_impl(task_id)

# New tool
@app.tool()
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step, triggering a
    state transition.
    """
    return submit_work_impl(task_id, artifact)


if __name__ == "__main__":
    app.run()
```

---
### **5. Validation**

After implementing the changes:
1.  Start a task with `begin_task(task_id='TEST-01')` to ensure it is in the `working` state.
2.  Call `submit_work(task_id='TEST-01', artifact={"branch_name": "feature/TEST-01", "branch_status": "clean", "ready_for_work": True})`.
3.  **Expected Output:**
    *   The tool should return a `ToolResponse` with `status: success`.
    *   The `message` should confirm that the work was submitted and the state has transitioned to `aireview`.
    *   The `next_prompt` should be the content of the `prompts/git_setup/ai_review.md` template.
4.  Check `.alfred/state.json`. The `persona_state` for `TEST-01` should now be `aireview`.
