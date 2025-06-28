### **Task Completion Summary: ALFRED-04**

**Status:** Approved and Merged.

**Work Completed:**
1.  **Full Persona Lifecycle:** Implemented the complete `working` -> `aireview` -> `devreview` -> `verified` lifecycle for the `git_setup` persona, defined within its `git_setup.yml` configuration.
2.  **Review Tooling:** Created and exposed the `provide_review` tool, which allows the AI client to drive the internal review states of a persona.
3.  **Handoff Mechanism:** Created and exposed the `approve_and_handoff` tool. This tool successfully finalizes the current persona's work and orchestrates the transition to the next persona in the `workflow.yml` sequence.
4.  **Orchestration Logic:** The `Orchestrator` is now equipped with the logic to process reviews and manage the destruction of the old persona's runtime and the instantiation of the new one during a handoff, ensuring a clean context switch.

**Outcome:** The core engine of Alfred is now feature-complete for managing workflows. It can guide a task through a persona's entire state machine and successfully transition it to the next persona, replicating the phase-based advancement of the original ETM system.

---
### **Task Directive: ALFRED-05 - Implement the Developer Persona**

**Objective:** To port the complex logic of the ETM `coding` phase into the new, self-contained `developer` persona. This involves creating its YAML definition, implementing the checkpoint-based execution loop, and ensuring it activates correctly after the `git_setup` handoff.

**CRITICAL INSTRUCTION:** The logic you implement MUST match the specification precisely. The YAML structure, file paths, and class methods are not suggestions. They are directives. Adhere to them without deviation.

---

### **1. Define the Developer Persona Configuration**

This YAML file defines the multi-step `coding` and `testing` workflow that the developer persona will execute.

**File:** `src/alfred/personas/developer.yml`
*(Replace the entire file with this content)*
```yaml
name: "James"
title: "Full Stack Developer"
target_status: "ready_for_dev"
completion_status: "ready_for_qa"

hsm:
  initial_state: "coding_working"
  states:
    - name: "coding_working"  # AI executes one step at a time
    - name: "coding_submission" # AI submits a final manifest
    - name: "coding_aireview"
    - name: "coding_devreview"
    - name: "coding_verified"   # Terminal state for this persona

  transitions:
    # Note: The coding loop is managed by the orchestrator, not HSM transitions.
    # The HSM transitions only handle the final submission and review.
    - trigger: "submit_manifest"
      source: "coding_submission"
      dest: "coding_aireview"
    - trigger: "ai_approve"
      source: "coding_aireview"
      dest: "coding_devreview"
    - trigger: "human_approve"
      source: "coding_devreview"
      dest: "coding_verified"
    - trigger: "request_revision"
      source: ["coding_aireview", "coding_devreview"]
      dest: "coding_working" # Revisions send it back to the start of the coding loop

prompts:
  coding_working: "prompts/developer/coding_step.md"
  coding_submission: "prompts/developer/coding_submission.md"
  coding_aireview: "prompts/developer/ai_review.md"
  coding_devreview: "prompts/developer/dev_review.md"

core_principles:
  - "My focus is to implement the approved execution plan with perfect fidelity."
  - "I will execute one step at a time and report completion before proceeding."
  - "Code quality and adherence to the plan are paramount."
```

### **2. Create Developer Prompt Templates**

These templates will guide the AI through the coding process.

**File:** `src/alfred/templates/prompts/developer/coding_step.md`
```markdown
# Role: Software Developer
# Task: {{ task_id }} | Step {{ step_number }} of {{ total_steps }}

You MUST execute the following single, atomic step from the execution plan.

---
### **Step ID: `{{ step_id }}`**
---

### **Instruction:**
```
{{ step_instruction }}
```
---

## Required Action

Upon successful completion of this single step, you **MUST** immediately call the `mark_step_complete` tool with the exact `step_id` from this prompt. This is non-negotiable.

**Tool Call:**
`mcp_alfred_mark_step_complete(task_id="{{ task_id }}", step_id="{{ step_id }}")`
```

**File:** `src/alfred/templates/prompts/developer/coding_submission.md`
```markdown
# Role: Software Developer
# Task: {{ task_id }} | All Steps Complete

You have successfully executed all steps in the plan. The final action is to submit a lightweight completion manifest.

## Required Action

You **MUST** call the `submit_work` tool now with a structured artifact. The required structure is:
```json
{
  "implementation_summary": "string - A high-level summary of what was implemented.",
  "execution_steps_completed": ["array of strings - A list of all completed step IDs."],
  "testing_notes": "string - Instructions for the QA persona on how to test this implementation."
}
```
**CRITICAL:** Do not proceed until you have called `submit_work`.
```

### **3. Implement Checkpoint Logic in Orchestrator and Tools**

This requires a new `mark_step_complete` tool and enhanced logic in the `Orchestrator` to manage the coding loop.

**File:** `src/alfred/tools/progress_tools.py`
```python
"""
Tools for managing progress within a multi-step persona workflow.
"""
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator

def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """
    Marks a single execution step as complete and returns the prompt for the next step.
    This is the core checkpoint tool for the developer persona.
    """
    message, next_prompt = orchestrator.process_step_completion(task_id, step_id)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)
```

**File:** `src/alfred/orchestration/orchestrator.py`
*(Add the following method to the `Orchestrator` class)*```python
    def process_step_completion(self, task_id: str, step_id: str) -> tuple[str, str | None]:
        """
        Processes a step completion for the developer persona's coding loop.
        This logic lives here because it's managing the loop, not just a single state transition.
        """
        # For now, we assume this is only for the developer persona.
        # A more robust implementation would check the active persona type.
        task_state = self._load_state().tasks.get(task_id)
        if not task_state:
            return "Error: Task state not found.", None

        # Load the machine-readable execution plan (this assumes it's been created and archived)
        # This part requires an artifact manager, which we will stub for now.
        # TODO: Implement a real artifact manager in a future task.
        execution_plan = {"steps": [{"id": "STEP-001", "instruction": "Do the first thing."}, {"id": "STEP-002", "instruction": "Do the second thing."}]} # Stubbed plan

        if task_state.current_step >= len(execution_plan["steps"]):
            return "Error: All steps already completed.", None

        expected_step_id = execution_plan["steps"][task_state.current_step]["id"]
        if step_id != expected_step_id:
            return f"Error: Incorrect step ID. Expected '{expected_step_id}', got '{step_id}'.", None

        # Update state
        task_state.completed_steps.append(step_id)
        task_state.current_step += 1
        self._save_task_state(task_state)

        # Check if all steps are now complete
        if task_state.current_step >= len(execution_plan["steps"]):
            # Transition the HSM to the submission state
            runtime = self._get_or_create_runtime(task_id)
            runtime.state = "coding_submission" # Manually set state for submission
            task_state.persona_state = "coding_submission"
            self._save_task_state(task_state)
            message = "All steps complete. Ready for final manifest submission."
            next_prompt = runtime.get_current_prompt()
        else:
            # Get prompt for the next step
            runtime = self._get_or_create_runtime(task_id)
            next_step = execution_plan["steps"][task_state.current_step]
            # This is a simplified prompt generation. We will need to enhance the prompter.
            # TODO: Enhance get_current_prompt to handle step-specific context.
            next_prompt = f"Execute Step {task_state.current_step + 1}: {next_step['instruction']}"
            message = f"Step '{step_id}' complete."

        return message, next_prompt
```

### **4. Update Server to Expose New Tool**

**File:** `src/alfred/server.py`
*(Add the new tool)*
```python
# ... existing imports
from src.alfred.tools.progress_tools import mark_step_complete as mark_step_complete_impl

# ... existing tool definitions

@app.tool()
async def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    """Marks a single coding step as complete."""
    return mark_step_complete_impl(task_id, step_id)
```

---
### **5. Validation**

1.  Handoff a task to the `developer` persona. The initial prompt should be for the first coding step.
2.  Call `mark_step_complete(task_id='...', step_id='STEP-001')`.
3.  **Expected:** The `state.json` should be updated (`current_step: 1`). The prompt for the second step should be returned.
4.  Call `mark_step_complete(task_id='...', step_id='STEP-002')`.
5.  **Expected:** The state should transition to `coding_submission`. The prompt should be the content of `coding_submission.md`, instructing the AI to call `submit_work`.
6.  Call `submit_work` with the required manifest structure.
7.  **Expected:** The state transitions to `coding_aireview`. The workflow is now ready for the review cycle.
