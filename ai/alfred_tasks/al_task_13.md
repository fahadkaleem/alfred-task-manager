
### **Task Directive: ALFRED-13 - Decouple Orchestrator from Persona Implementation**

**Objective:** To remove the hardcoded logic in the `Orchestrator` that is specific to the "developer" persona. The Orchestrator should not know about "James"; it should only know about persona capabilities declared in the configuration.

**Rationale:** The current implementation (`if runtime.config.name == "James"`) is a brittle, hardcoded link. If the persona's name is changed in the YAML, the checkpoint logic breaks. This violates the principle of configuration-driven behavior. The persona's execution mode must be a declared property.

**Implementation Plan:**

**1. Update the `PersonaConfig` Model:**
   *   Add a new field to define the execution mode.

   **File:** `src/alfred/models/config.py`
   **Action:** Add an `execution_mode` field to the `PersonaConfig` model.

   ```python
   class PersonaConfig(BaseModel):
       """Represents the validated configuration of a single persona.yml file."""
       name: str
       title: str
       target_status: str
       completion_status: str
       execution_mode: str = "batch" # "batch" or "stepwise"
       hsm: HSMConfig
       # ... rest of the model
   ```

**2. Update the `developer.yml` Configuration:**
   *   Explicitly declare that the developer persona uses the stepwise execution model.

   **File:** `src/alfred/personas/developer.yml`
   **Action:** Add the `execution_mode` key.

   ```yaml
   name: "James"
   title: "Full Stack Developer"
   target_status: "ready_for_dev"
   completion_status: "ready_for_qa"
   execution_mode: "stepwise" # <-- ADD THIS LINE

   hsm:
     # ... rest of the file
   ```

**3. Refactor the `Orchestrator` Logic:**
   *   Replace the hardcoded name check with a check for the `execution_mode` configuration property.

   **File:** `src/alfred/orchestration/orchestrator.py`
   **Action:** Modify the `process_step_completion` method.

   ```python
    def process_step_completion(self, task_id: str, step_id: str) -> tuple[str, str | None]:
        """
        Processes a step completion for any persona configured for stepwise execution.
        """
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        # --- START REFACTOR ---
        # Replace the brittle name check with a robust configuration check.
        if runtime.config.execution_mode != "stepwise":
            return f"Error: Step completion is not valid for the '{runtime.config.name}' persona, which is not in 'stepwise' mode.", None
        # --- END REFACTOR ---

        task_state = self._load_state().tasks.get(task_id)
        # ... rest of the method remains the same ...
   ```
