### **Task Directive: ALFRED-17 - Integrate Execution Plan into Task State**

**Objective:** To eliminate the dependency on a loose JSON file during the `developer` workflow by persisting the execution plan directly within the core `state.json` when the developer persona becomes active.

**Rationale:** This makes the `developer` workflow self-contained and resilient. The state file becomes the single source of truth for the work to be done, immune to accidental file system modifications. It transforms the `execution_plan` from a fragile external dependency into a durable, stateful property of the task itself.

#### **Implementation Plan**

**1. Enhance the `TaskState` Model:**
   *   The `TaskState` must be given a field to hold the plan.

   **File:** `src/alfred/models/state.py`
   **Action:** Add an `execution_plan` field.

   ```python
   class TaskState(BaseModel):
       """Represents the persisted state of a single task."""
       task_id: str
       workflow_step: int = 0
       persona_state: str | None = None
       is_active: bool = False
       # --- NEW ---
       execution_plan: dict | None = None # Holds the active plan for stepwise personas
       # --- END NEW ---
       current_step: int = 0
       completed_steps: list[str] = Field(default_factory=list)
       revision_feedback: str | None = None
   ```

**2. Modify the Orchestrator's Handoff Logic:**
   *   When handing off *to* a `stepwise` persona (like the developer), the orchestrator is now responsible for reading the `execution_plan.json` *once* and embedding it into the `TaskState`.

   **File:** `src/alfred/orchestration/orchestrator.py`
   **Action:** Modify the `_perform_handoff` method.

   ```python
    # In Orchestrator class...
    def _perform_handoff(self, task_id: str, task_state: TaskState, target_persona: str, target_state: str, feedback: str | None = None) -> tuple[str, str | None]:
        """A centralized method to handle all persona handoffs, both forward and backward."""
        try:
            target_step_index = self.workflow_sequence.index(target_persona)
        except ValueError:
            return f"Error: Target persona '{target_persona}' not found in workflow sequence.", None

        # --- START REFACTOR ---
        # Load the target persona's config to check its execution mode
        target_config = self.persona_registry.get(target_persona)
        if not target_config:
            return f"Error: Could not load config for target persona '{target_persona}'.", None

        # Update the task state
        task_state.workflow_step = target_step_index
        task_state.persona_state = target_state
        task_state.revision_feedback = feedback
        task_state.current_step = 0 # Always reset step counter on handoff
        task_state.completed_steps = []

        # If the target persona is stepwise, load its execution plan into the state.
        if target_config.execution_mode == "stepwise":
            plan = artifact_manager.read_execution_plan(task_id)
            if not plan:
                return f"CRITICAL ERROR: Handoff to stepwise persona '{target_persona}' failed. Could not read execution_plan.json for task {task_id}.", None
            task_state.execution_plan = plan
        else:
            # For non-stepwise personas, ensure the plan is cleared from the state.
            task_state.execution_plan = None

        self._save_task_state(task_state)
        # --- END REFACTOR ---

        # Destroy the old runtime and create the new one
        self.active_runtimes.pop(task_id, None)
        next_runtime = self._get_or_create_runtime(task_id)
        if not next_runtime:
            return f"Error: Could not create runtime for target persona '{target_persona}'.", None

        # Pass the feedback into the new persona's first prompt
        next_prompt = next_runtime.get_current_prompt(revision_feedback=feedback)
        message = f"Handoff complete. Task is now with persona '{next_runtime.config.name}' in state '{next_runtime.state}'."
        return message, next_prompt
   ```

**3. Refactor the `process_step_completion` Logic:**
   *   This method will no longer read from the file system. It will read the plan directly from the `TaskState` object.

   **File:** `src/alfred/orchestration/orchestrator.py`
   **Action:** Modify the `process_step_completion` method.

   ```python
    # In Orchestrator class...
    def process_step_completion(self, task_id: str, step_id: str) -> tuple[str, str | None]:
        """
        Processes a step completion for any persona configured for stepwise execution.
        """
        runtime = self._get_or_create_runtime(task_id)
        # ... null checks ...

        if runtime.config.execution_mode != "stepwise":
            return f"Error: Step completion is not valid for the '{runtime.config.name}' persona.", None

        task_state = self._load_state().tasks.get(task_id)
        if not task_state:
            return "Error: Task state not found.", None

        # --- START REFACTOR ---
        # The plan is now read from the state, NOT the file system.
        execution_plan = task_state.execution_plan
        if not execution_plan or "implementation_steps" not in execution_plan:
            return "Error: Execution plan not found in the current task state.", None
        # --- END REFACTOR ---

        # The rest of the method's logic for checking step IDs and updating the state remains the same...
        # ...

        # Replace implementation_steps with steps
        if task_state.current_step >= len(execution_plan["implementation_steps"]):
            return "Error: All steps already completed.", None

        expected_step_id = execution_plan["implementation_steps"][task_state.current_step]["id"]
        if step_id != expected_step_id:
            return f"Error: Incorrect step ID. Expected '{expected_step_id}', got '{step_id}'.", None

        # ... update state and get next prompt ...
