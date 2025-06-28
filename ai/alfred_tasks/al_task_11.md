### **Task Directive: ALFRED-11 - Harden the Persona Loader**

**Objective:** To eliminate silent failures in the `PersonaLoader` by implementing specific, informative error handling. The current `except Exception: pass` is an unacceptable vulnerability.

**Rationale:** If a user defines a custom persona in a `.yml` file with a syntax error or a schema violation, the system currently fails silently. The persona simply won't be available, and the user will have no idea why. This is a critical failure of user experience and debuggability. The system must fail loudly and informatively.

**Implementation Plan:**

**File:** `src/alfred/orchestration/persona_loader.py`
**Action:** Replace the `load_all` method with the following hardened implementation.

```python
"""
Loads and validates persona configurations from YAML files.
"""
import yaml
from pydantic import ValidationError

from src.alfred.config.settings import settings
from src.alfred.models.config import PersonaConfig
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)

class PersonaLoader:
    """A utility to load all persona configurations from the filesystem."""

    @staticmethod
    def load_all() -> dict[str, PersonaConfig]:
        """
        Scans the personas directory, loads all .yml files, and validates them.
        """
        personas: dict[str, PersonaConfig] = {}
        personas_dir = settings.packaged_personas_dir

        if not personas_dir.exists():
            logger.error(f"Personas directory not found at: {personas_dir}")
            return {}

        for persona_file in personas_dir.glob("*.yml"):
            persona_name = persona_file.stem
            try:
                with persona_file.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if not data:
                        logger.warning(f"Persona file '{persona_file.name}' is empty. Skipping.")
                        continue
                    config = PersonaConfig(**data)
                    personas[persona_name] = config
            except yaml.YAMLError as e:
                logger.error(f"Failed to parse YAML for persona '{persona_name}': {e}")
            except ValidationError as e:
                logger.error(f"Validation failed for persona '{persona_name}': {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred loading persona '{persona_name}': {e}")

        return personas

```

---

### **Task Directive: ALFRED-12 - Decouple Orchestrator from Persona Implementation**

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

---

### **Conclusion and Path Forward**

Once `ALFRED-10`, `ALFRED-11`, and `ALFRED-12` are complete, the v1 migration is concluded. The Alfred system will be functionally equivalent to ETM, architecturally superior, and hardened against the most obvious points of failure.

At that point, we will execute the final cutover:
1.  Delete the `src/epic_task_manager` directory.
2.  Update `pyproject.toml` to point all entry points to the `alfred` modules.
3.  Begin work on the next phase of features for Alfred, such as the "Intelligence Layer" and UI integration, built upon this now-stable foundation.

Execute these hardening directives.

</architectural_analysis>
