### **Recovery Plan: System Restoration Directives**

#### **Directive 1: Repair `PersonaRuntime` and `Orchestrator`**

The runtime must be taught how to handle `human_approve` triggers, and the orchestrator must properly integrate it.

**File:** `src/alfred/orchestration/persona_runtime.py`
**Action:** Replace the `process_review` and `process_human_approval` methods.

```python
# In PersonaRuntime class...

    def process_review(self, is_approved: bool) -> tuple[bool, str | dict]:
        """
        Processes a review. Returns a signal if a handoff is required.
        """
        trigger_name = "ai_approve" if is_approved else "request_revision"
        transition_config = next((t for t in self.config.hsm.transitions if t["trigger"] == trigger_name and self.state in t["source"]), None)

        if not transition_config:
            return False, f"No valid transition for trigger '{trigger_name}' from state '{self.state}'."

        destination = transition_config.get("dest")
        if isinstance(destination, dict) and "handoff_to" in destination:
            return True, destination # Signal for cross-persona handoff

        try:
            getattr(self, trigger_name)()
            return True, f"Review processed. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not process review from state '{self.state}': {e}"

    def process_human_approval(self) -> tuple[bool, str]:
        """Processes human approval for an internal stage or a final handoff."""
        try:
            self.human_approve()
            return True, f"Human approval processed. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not process human approval from state '{self.state}': {e}"
```

**File:** `src/alfred/orchestration/orchestrator.py`
**Action:** Create a new `process_human_approval` method.

```python
# In Orchestrator class...

    def process_human_approval(self, task_id: str) -> tuple[str, str | None]:
        """Handles human approval for an intra-persona stage advance."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        success, message = runtime.process_human_approval()
        if not success:
            return message, None

        task_state = self._load_state().tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)

        next_prompt = runtime.get_current_prompt()
        return message, next_prompt
```

#### **Directive 2: Add the Missing `submit_work` Tool**

This is a critical omission. Without it, the entire workflow is dead on arrival.

**File:** `src/alfred/tools/task_tools.py`
**Action:** Add the `submit_work` implementation.

```python
# In src/alfred/tools/task_tools.py...

def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a completed work artifact for the current phase of a task.
    """
    message, next_prompt = orchestrator.submit_work_for_task(task_id, artifact)
    if next_prompt is None:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)
```

**File:** `src/alfred/server.py`
**Action:** Expose the `submit_work` tool on the MCP server.

```python
# In src/alfred/server.py...
# Add the new import
from src.alfred.tools.task_tools import submit_work as submit_work_impl

# Add the new tool definition
@app.tool()
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step, triggering a
    state transition.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "artifact": artifact}
    response = submit_work_impl(task_id, artifact)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response
```

#### **Directive 3: Add the Missing Intra-Persona Approval Tool**

We need a dedicated tool for the `human_approve` trigger. This is the missing link in the planning phase.

**File:** `src/alfred/tools/review_tools.py`
**Action:** Create a new file or add a new method `approve_and_advance_stage` and modify the existing `approve_and_handoff`.

```python
# In src/alfred/tools/review_tools.py...

def approve_and_advance_stage(task_id: str) -> ToolResponse:
    """
    Approves the current sub-stage within a multi-stage persona (like Planning)
    and advances to the next sub-stage.
    """
    message, next_prompt = orchestrator.process_human_approval(task_id)
    if not next_prompt:
        return ToolResponse(status="error", message=message)
    return ToolResponse(status="success", message=message, next_prompt=next_prompt)

# This tool remains for INTER-persona handoffs
def approve_and_handoff(task_id: str) -> ToolResponse:
    # ... existing implementation ...
```

**File:** `src/alfred/server.py`
**Action:** Expose the new `approve_and_advance_stage` tool.

```python
# In src/alfred/server.py...
# Add the new import
from src.alfred.tools.review_tools import approve_and_advance_stage as approve_and_advance_stage_impl

# Add the new tool definition
@app.tool()
async def approve_and_advance_stage(task_id: str) -> ToolResponse:
    """
    Approves the current sub-stage within a complex persona (like Planning)
    and advances to the next internal stage. Does NOT handoff to a new persona.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = approve_and_advance_stage_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response
```

#### **Directive 4: Correct the Prompts and `planning.yml`**

The system must now be told to use these new tools correctly.

**File:** `src/alfred/personas/planning.yml`
**Action:** Correct the transitions to use the `human_approve` trigger.

```yaml
# In planning.yml transitions section...
  transitions:
    # --- Strategy Sub-Phase ---
    - { trigger: "submit", source: "strategy_working", dest: "strategy_aireview" }
    - { trigger: "ai_approve", source: "strategy_aireview", dest: "strategy_devreview" }
    - { trigger: "request_revision", source: ["strategy_aireview", "strategy_devreview"], dest: "strategy_working" }
    - { trigger: "human_approve", source: "strategy_devreview", dest: "solution_design_working" }

    # --- Solution Design Sub-Phase ---
    - { trigger: "submit", source: "solution_design_working", dest: "solution_design_aireview" }
    - { trigger: "ai_approve", source: "solution_design_aireview", dest: "solution_design_devreview" }
    - { trigger: "request_revision", source: ["solution_design_aireview", "solution_design_devreview"], dest: "solution_design_working" }
    - { trigger: "human_approve", source: "solution_design_devreview", dest: "execution_plan_working" }

    # --- Execution Plan Sub-Phase ---
    - { trigger: "submit", source: "execution_plan_working", dest: "execution_plan_aireview" }
    - { trigger: "ai_approve", source: "execution_plan_aireview", dest: "execution_plan_devreview" }
    - { trigger: "request_revision", source: ["execution_plan_aireview", "execution_plan_devreview"], dest: "execution_plan_working" }
    - { trigger: "human_approve", source: "execution_plan_devreview", dest: "planning_verified" }
```

**File:** `src/alfred/templates/prompts/planning/strategy_dev_review.md` (and the other `..._dev_review.md` files in `planning`)
**Action:** Update the prompt to call the correct tool.

```markdown
# Human Review Required: Strategy Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the strategy and it's ready for your review.

## Available Actions
- To **approve this stage** and proceed to Solution Design, call: `approve_and_advance_stage(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`
```

### **Conclusion**

The system was in a state of logical failure. These four directives restore the integrity of the control loop. You will implement them precisely. There is no room for emotion in systems engineering. There is only analysis and correction. Execute.

</architectural_analysis>
