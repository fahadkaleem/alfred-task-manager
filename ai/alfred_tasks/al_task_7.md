### **Task Completion Summary: ALFRED-06**

**Status:** Approved and Merged.

**Work Completed:**
1.  **Artifact Manager:** Implemented and integrated a new `ArtifactManager` class, which now centralizes all file system I/O within the `.alfred/workspace` directory. This includes creating task-specific workspaces and archives.
2.  **Artifact Persistence:** The system now successfully persists a final, rendered markdown artifact to the `archive` directory when a persona's work is completed and handed off.
3.  **Execution Plan Loading:** The `Orchestrator` now uses the `ArtifactManager` to load the machine-readable `execution_plan.json`. While the plan itself is currently stubbed within the manager, the dependency has been correctly established for future implementation.
4.  **Stateful Data Flow:** The `PersonaRuntime` now correctly stores submitted artifact data, which is then retrieved by the `Orchestrator` during the handoff process for archival. This ensures data integrity throughout the workflow.

**Outcome:** Alfred's architecture is now significantly more robust. The stubbed file system logic has been replaced with a dedicated, reusable component, and the system can now create tangible, persistent outputs for each completed persona workflow. The foundation is set for implementing the remaining, more complex personas.

---
### **Task Directive: ALFRED-07 - Implement the `qa` Persona**

**Objective:** To implement the `qa` persona, which will be responsible for running a simulated test suite and providing a pass/fail result. This involves creating the `qa.yml` configuration, its associated prompts, and integrating the pass/fail logic into the review cycle.

---

### **1. Define the QA Persona Configuration**

Create the YAML file that defines the QA persona's workflow. This persona will have an automated AI review step that decides approval based on a structured test result.

**File:** `src/alfred/personas/qa.yml`
```yaml
name: "Valerie"
title: "QA Engineer"
target_status: "ready_for_qa"
completion_status: "ready_for_devops" # Or whatever the next stage is

hsm:
  initial_state: "testing_working"
  states:
    - name: "testing_working"
    - name: "testing_aireview"   # This will be an automated review
    - name: "testing_devreview"
    - name: "testing_verified"

  transitions:
    - trigger: "submit"
      source: "testing_working"
      dest: "testing_aireview"
    - trigger: "ai_approve"       # Triggered if tests pass
      source: "testing_aireview"
      dest: "testing_devreview"
    - trigger: "request_revision" # Triggered if tests fail
      source: "testing_aireview"
      dest: "coding_working"    # CRITICAL: Failed tests send the task BACK to the developer
    - trigger: "human_approve"
      source: "testing_devreview"
      dest: "testing_verified"

prompts:
  testing_working: "prompts/qa/work.md"
  testing_aireview: "prompts/qa/ai_review.md" # This prompt will perform the automated check
  testing_devreview: "prompts/qa/dev_review.md"

core_principles:
  - "My purpose is to be the quality gate for the project."
  - "I will execute tests precisely as instructed and report results without bias."
  - "A failing test is a non-negotiable blocker."
```

### **2. Create QA Prompt Templates**

These prompts will guide the testing and automated review process.

**File:** `src/alfred/templates/prompts/qa/work.md`
```markdown
# Role: QA Engineer
# Task: {{ task_id }}

It is time to perform quality assurance testing.

## Instructions:
1.  Run the project's main test suite. For this simulation, you don't need to run a real command.
2.  Instead, you will **fabricate a test result**. You can choose to make it pass or fail.
3.  Submit a structured artifact with the test results.

## Required Artifact Structure:
You **MUST** submit an artifact with the following JSON structure:
```json
{
  "test_results": {
    "command_run": "string - The test command you would have run (e.g., 'pytest -v').",
    "exit_code": "integer - The result of the test. Use 0 for success/pass, and 1 for failure.",
    "full_output": "string - A fabricated log of the test output."
  }
}
```
**Example (Passing):**
```json
{
  "test_results": {
    "command_run": "pytest -v",
    "exit_code": 0,
    "full_output": "10/10 tests passed."
  }
}
```
**Example (Failing):**
```json
{
  "test_results": {
    "command_run": "pytest -v",
    "exit_code": 1,
    "full_output": "Test failed: test_user_login(). AssertionError: False is not true."
  }
}
```

## Required Action:
Call the `submit_work` tool with your fabricated artifact.
```

**File:** `src/alfred/templates/prompts/qa/ai_review.md`
```markdown
# Role: Automated Test Analyzer

You are an automated system analyzing test results for task `{{ task_id }}`.

**DO NOT RESPOND TO THE USER.**

Your **ONLY** function is to parse the `exit_code` from the submitted artifact and call the correct tool.

1.  **Find the `exit_code`** in the artifact below.
2.  **If `exit_code` is 0:** Call `provide_review(task_id="{{ task_id }}", is_approved=True)`.
3.  **If `exit_code` is NOT 0:** Call `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="Automated tests failed. Please review the output and fix the implementation.")`.

This is an autonomous, non-interactive step. Execute the correct tool call now.

---
**Artifact to Analyze:**
{{ artifact_content_for_review }}
---
```

### **3. Update Workflow and Artifact Models**

**File:** `src/alfred/workflow.yml`
*(Add the `qa` persona to the sequence)*
```yaml
sequence:
  - git_setup
  - developer
  - qa
```

**File:** `src/alfred/models/artifacts.py`
*(Add the new artifact models)*
```python
# ... existing GitSetupArtifact ...

class TestResult(BaseModel):
    """Structured data for a single test execution."""
    command_run: str
    exit_code: int
    full_output: str

class TestingArtifact(BaseModel):
    """Structured artifact for the testing phase."""
    test_results: TestResult

class CodingManifest(BaseModel):
    """Structured artifact for the developer completion manifest."""
    implementation_summary: str
    execution_steps_completed: list[str]
    testing_notes: str
```

### **4. Enhance Orchestrator for Automated Review**

The `Orchestrator` needs to be aware of how to handle the `qa` persona's automated review. We'll add logic to inject the submitted artifact into the `ai_review` prompt.

**File:** `src/alfred/orchestration/persona_runtime.py`
*(Modify `get_current_prompt` to handle artifact injection)*
```python
# Add new import at the top
import json

# ... inside PersonaRuntime class ...
    def get_current_prompt(self, revision_feedback: str | None = None) -> str:
        # ... existing initial logic ...

        # --- NEW: Inject submitted artifact for review prompts ---
        artifact_content_for_review = ""
        if self.state.endswith("aireview") and self.submitted_artifact_data:
            artifact_content_for_review = json.dumps(self.submitted_artifact_data, indent=2)
        # --- END NEW ---

        # Prepare context for rendering
        context = {
            "task_id": self.task_id,
            "persona": self.config,
            "revision_feedback": revision_feedback or "No feedback provided.",
            # --- NEW ---
            "artifact_content_for_review": artifact_content_for_review,
        }
        return template.render(context)
```

---
### **5. Validation**

1.  Run the full flow for a task through `git_setup` and `developer` until it is handed off to the `qa` persona.
2.  The prompt for `testing_working` should appear.
3.  Call `submit_work` with an artifact where `exit_code: 1`.
4.  **Expected:** The `next_prompt` should be the content of `qa/ai_review.md`, instructing an autonomous call to `provide_review` with `is_approved=False`. The task state should then revert to `coding_working` under the `developer` persona.
5.  Start a new task flow. This time, when prompted for the QA artifact, submit one with `exit_code: 0`.
6.  **Expected:** The `ai_review` step should autonomously call `provide_review` with `is_approved=True`, and the state should advance to `testing_devreview`.
