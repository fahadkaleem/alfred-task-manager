### **Task Directive: ALFRED-08 - Implement the DevOps Persona and Finalize Workflow**

**Objective:** To implement the final `devops` persona and complete the v1 workflow sequence. This involves creating the `devops.yml` persona, its artifact model and templates, and ensuring the workflow correctly terminates after the final handoff.

---

### **1. Define the DevOps Persona Configuration**

Create the YAML file for the `devops` persona. This persona will simulate the final steps of merging code and creating a pull request.

**File:** `src/alfred/personas/devops.yml`
```yaml
name: "Commander"
title: "DevOps Engineer"
target_status: "ready_for_devops"
completion_status: "done" # The final status

hsm:
  initial_state: "working"
  states:
    - "working"
    - "aireview"
    - "devreview"
    - "verified" # Terminal state for this persona

  transitions:
    - { trigger: "submit", source: "working", dest: "aireview" }
    - { trigger: "ai_approve", source: "aireview", dest: "devreview" }
    - { trigger: "human_approve", source: "devreview", dest: "verified" }
    - { trigger: "request_revision", source: ["aireview", "devreview"], dest: "working" }

prompts:
  working: "prompts/devops/work.md"
  aireview: "prompts/devops/ai_review.md"
  devreview: "prompts/devops/dev_review.md"

artifacts:
  - state: "working"
    model_path: "src.alfred.models.artifacts.FinalizeArtifact"
```

### **2. Create DevOps Artifact Model and Templates**

**File:** `src/alfred/models/artifacts.py`
*(Add the new `FinalizeArtifact` model)*
```python
# ... existing models ...
class FinalizeArtifact(BaseModel):
    """Structured data for the finalize phase artifact."""
    commit_hash: str = Field(..., description="Git commit hash from the final commit")
    pull_request_url: str = Field(..., description="URL of the created pull request")
```

**File:** `src/alfred/templates/artifacts/devops.md`
```markdown
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Task Finalization Complete: {{ task_id }}

## Git Workflow Summary

The feature has been successfully pushed and a Pull Request has been created.

### Final Receipt

- **Commit Hash:** `{{ artifact.commit_hash }}`
- **Pull Request URL:** [{{ artifact.pull_request_url }}]({{ artifact.pull_request_url }})

The Alfred workflow for this task is now complete!
```

**File:** `src/alfred/templates/prompts/devops/work.md`
```markdown
# Role: DevOps Engineer
# Task: {{ task_id }}

The task has passed all previous stages and is ready for finalization.

## Instructions:
Simulate the final git workflow by fabricating a commit hash and a pull request URL.

## Required Artifact Structure:
You **MUST** submit an artifact with the following JSON structure:
```json
{
  "commit_hash": "string - A fabricated 40-character hexadecimal git commit hash.",
  "pull_request_url": "string - A fabricated GitHub pull request URL."
}
```
**Example:**
```json
{
  "commit_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
  "pull_request_url": "https://github.com/example/repo/pull/123"
}
```
## Required Action:
Call the `submit_work` tool with your fabricated artifact.
```

### **3. Update Workflow Configuration**

Add the `devops` persona to the main workflow sequence.

**File:** `src/alfred/workflow.yml`
```yaml
sequence:
  - git_setup
  - developer
  - qa
  - devops
```

---
### **4. Validation**

1.  Run a task through the entire workflow sequence: `git_setup` -> `developer` -> `qa`.
2.  After approving the `qa` persona's work, `approve_and_handoff` should be called.
3.  **Expected:** The task should now be handed off to the `devops` persona. The `next_prompt` should be the content of `prompts/devops/work.md`.
4.  Submit a valid `FinalizeArtifact` for the `devops` persona.
5.  Proceed through the `devops` review cycle until `approve_and_handoff` is called on the final `devreview` state.
6.  **Expected:** The `Orchestrator.process_handoff` method should recognize that this is the final step in the sequence.
    *   It should set the task's status to `done`.
    *   It should return the message "Workflow complete! No more personas." and a final confirmation prompt.
    *   The `active_runtimes` dictionary for the task should be cleared.
    *   Any subsequent call to `begin_task` for this ID should gracefully report that the task is already complete.
