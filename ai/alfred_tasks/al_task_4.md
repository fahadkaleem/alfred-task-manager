### **Task Completion Summary: ALFRED-03**

**Status:** Approved and Merged.

**Work Completed:**
1.  **Artifact Modeling:** Created the `GitSetupArtifact` Pydantic model and its corresponding Jinja2 artifact template (`git_setup.md`).
2.  **Work Submission Logic:** Enhanced `PersonaRuntime` with a `submit_work` method to validate incoming artifacts and trigger state transitions on its internal HSM.
3.  **Orchestration Routing:** Enhanced the `Orchestrator` with a `submit_work_for_task` method that correctly routes the submission to the active persona runtime for the specified task.
4.  **Tool Exposure:** Implemented and exposed the `submit_work` tool via `task_tools.py` and the main `server.py`, making it accessible to the MCP client.

**Outcome:** The Alfred application can now process work. A user can begin a task, receive a prompt for work, and submit a structured artifact. The system will validate this artifact, advance the internal state machine of the active persona, and prepare to deliver the next prompt.

---
### **Task Directive: ALFRED-04 - Implement Review and Handoff**

**Objective:** To implement the review cycle (`ai_review`, `dev_review`) and the final handoff mechanism that transitions a task from one persona to the next. This will complete the entire lifecycle for the `git_setup` persona.

---

### **1. Update Persona Configuration**

The `git_setup.yml` needs to be expanded to include the full review lifecycle states and their corresponding prompts.

**File:** `src/alfred/personas/git_setup.yml`
*(Replace the entire file with this content)*
```yaml
name: "Branch Manager"
title: "Git Setup Specialist"
target_status: "ready_for_setup"
completion_status: "ready_for_dev"

hsm:
  initial_state: "working"
  states:
    - "working"
    - "aireview"
    - "devreview"
    - "verified" # Terminal state for this persona

  transitions:
    - trigger: "submit"
      source: "working"
      dest: "aireview"
    - trigger: "ai_approve"
      source: "aireview"
      dest: "devreview"
    - trigger: "human_approve"
      source: "devreview"
      dest: "verified"
    - trigger: "request_revision"
      source: ["aireview", "devreview"]
      dest: "working"

prompts:
  working: "prompts/git_setup/work.md"
  aireview: "prompts/git_setup/ai_review.md"
  devreview: "prompts/git_setup/dev_review.md"
  verified: "prompts/git_setup/verified.md"

core_principles:
  - "My sole focus is ensuring the Git repository is in a clean, correct state."
  - "I will be interactive. I will not proceed if the repository is dirty without explicit user instruction."
```

### **2. Create New Prompt Templates**

Create the prompt templates for the review states.

**File:** `src/alfred/templates/prompts/git_setup/ai_review.md`
```markdown
# Role: QA Reviewer - Git Setup Validation

You are reviewing the git setup artifact for task `{{ task_id }}` to ensure it is safe to proceed with development.

**Artifact to Review:**
*(The orchestrator will need to inject the artifact content here in a future task)*

## Review Criteria:
1.  **`ready_for_work` MUST be `true`**.
2.  **`branch_name` MUST follow the convention `feature/{{ task_id }}`.**
3.  **`branch_status` MUST be `"clean"`**.

## Required Action:
Call `provide_review(task_id="{{ task_id }}", is_approved=True)` if all criteria are met. Otherwise, call with `is_approved=False` and provide specific `feedback_notes`.
```

**File:** `src/alfred/templates/prompts/git_setup/dev_review.md`
```markdown
# Human Review Required

The git setup for task `{{ task_id }}` has been validated by the AI. Please review the artifact and the repository state.

## Next Step:
Use the `approve_and_handoff(task_id="{{ task_id }}")` tool to approve this work and handoff the task to the next persona (Developer).

Or, use `provide_review` to request revisions.
```

### **3. Implement Review and Handoff Logic**

Create a new `review_tools.py` file and enhance the `Orchestrator` and `PersonaRuntime`.

**File:** `src/alfred/tools/review_tools.py`
```python
"""
Tools for handling the review cycle of a persona's work.
"""
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator

def provide_review(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Approves or requests revisions on a work artifact, advancing the
    internal review state of the active persona.
    """
    message, next_prompt = orchestrator.process_review(task_id, is_approved, feedback_notes)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)

def approve_and_handoff(task_id: str) -> ToolResponse:
    """
    Gives final approval for a persona's work and hands the task off
    to the next persona in the workflow sequence.
    """
    message, next_prompt = orchestrator.process_handoff(task_id)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)
```

**File:** `src/alfred/orchestration/persona_runtime.py`
*(Add these methods to the `PersonaRuntime` class)*
```python
    def process_review(self, is_approved: bool) -> tuple[bool, str]:
        """Processes a review, triggering ai_approve or request_revision."""
        try:
            if is_approved:
                self.ai_approve()
            else:
                self.request_revision()
            return True, f"Review processed. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not process review from state '{self.state}': {e}"

    def process_human_approval(self) -> tuple[bool, str]:
        """Processes the final human approval for the persona's work."""
        try:
            self.human_approve()
            return True, f"Human approval processed. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not process human approval from state '{self.state}': {e}"
```

**File:** `src/alfred/orchestration/orchestrator.py`
*(Add these methods to the `Orchestrator` class)*
```python
    def process_review(self, task_id: str, is_approved: bool, feedback: str) -> tuple[str, str | None]:
        """Routes a review to the correct runtime."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        success, message = runtime.process_review(is_approved)
        if not success:
            return message, None

        task_state = self._load_state().tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            task_state.revision_feedback = feedback if not is_approved else None
            self._save_task_state(task_state)

        next_prompt = runtime.get_current_prompt(revision_feedback=task_state.revision_feedback)
        return message, next_prompt

    def process_handoff(self, task_id: str) -> tuple[str, str | None]:
        """Processes final approval and hands off to the next persona."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        # 1. Finalize the current persona
        success, message = runtime.process_human_approval()
        if not success or runtime.state != 'verified':
            return f"Error: Cannot handoff task. Persona not in 'verified' state. Message: {message}", None

        # 2. Update master state
        task_state = self._load_state().tasks.get(task_id)
        if not task_state:
            return "Error: Cannot find task state to update.", None

        task_state.workflow_step += 1
        if task_state.workflow_step >= len(self.workflow_sequence):
            # This is the end of the entire workflow
            return "Workflow complete! No more personas.", "Task is fully complete."

        # 3. Destroy old runtime and create the next one
        self.active_runtimes.pop(task_id, None)
        next_runtime = self._get_or_create_runtime(task_id)
        if not next_runtime:
            return "Error: Could not create runtime for the next persona.", None

        next_prompt = next_runtime.get_current_prompt()
        return f"Handoff complete. Task is now with persona '{next_runtime.config.name}'.", next_prompt
```

### **4. Update Server to Expose New Tools**

**File:** `src/alfred/server.py`
*(Add the new tools to the server)*
```python
# ... existing imports
from src.alfred.tools.review_tools import provide_review as provide_review_impl
from src.alfred.tools.review_tools import approve_and_handoff as approve_and_handoff_impl

# ... existing tool definitions

@app.tool()
async def provide_review(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Provides feedback (approval or revision) on a work artifact."""
    return provide_review_impl(task_id, is_approved, feedback_notes)

@app.tool()
async def approve_and_handoff(task_id: str) -> ToolResponse:
    """Gives final approval and hands off the task to the next persona."""
    return approve_and_handoff_impl(task_id)
```

---
### **5. Validation**

After implementing the changes:
1.  Run the full flow for `TEST-01`:
2.  `begin_task(...)` -> `submit_work(...)`
3.  You should be in `aireview`. Call `provide_review(task_id='TEST-01', is_approved=True)`.
4.  **Expected:** State transitions to `devreview`. The `next_prompt` should be the `dev_review.md` content.
5.  Call `approve_and_handoff(task_id='TEST-01')`.
6.  **Expected:**
    *   The `git_setup` persona is finalized.
    *   The `TaskState` `workflow_step` should now be `1`.
    *   A new `PersonaRuntime` for the `developer` persona should be created.
    *   The `next_prompt` should be the initial prompt for the `developer` persona (`prompts/developer/work.md`).
