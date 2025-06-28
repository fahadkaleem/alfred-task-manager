### **Task Directive: ALFRED-02 - Persona Loading and Orchestration**

**Objective:** To build the core orchestration engine that can load persona configurations from YAML files, manage the active task state, and dynamically instantiate a persona's state machine. This task activates the `begin_task` workflow.

---

### **1. Create Orchestration and Persona Runtime Components**

These new classes will manage the lifecycle and execution of personas.

**File:** `src/alfred/orchestration/persona_loader.py`
```python
"""
Loads and validates persona configurations from YAML files.
"""
import yaml
from pathlib import Path
from typing import Dict

from src.alfred.config.settings import settings
from src.alfred.models.config import PersonaConfig

class PersonaLoader:
    """A utility to load all persona configurations from the filesystem."""

    @staticmethod
    def load_all() -> Dict[str, PersonaConfig]:
        """
        Scans the personas directory, loads all .yml files, and validates them.

        Returns:
            A dictionary mapping persona names (filenames without extension)
            to their validated PersonaConfig objects.
        """
        personas: Dict[str, PersonaConfig] = {}
        personas_dir = settings.packaged_personas_dir
        if not personas_dir.exists():
            # In a real scenario, we might want to log this error.
            return {}

        for persona_file in personas_dir.glob("*.yml"):
            try:
                with persona_file.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    config = PersonaConfig(**data)
                    persona_name = persona_file.stem
                    personas[persona_name] = config
            except Exception as e:
                # Log or handle invalid persona file configuration
                print(f"Warning: Could not load or validate persona {persona_file.name}: {e}")
        return personas
```

**File:** `src/alfred/orchestration/persona_runtime.py`
```python
"""
Represents the live, stateful instance of a persona for a specific task.
"""
from transitions.extensions import HierarchicalMachine
from jinja2 import Environment, FileSystemLoader

from src.alfred.config.settings import settings
from src.alfred.models.config import PersonaConfig

class PersonaRuntime:
    """Manages the state and execution of a single persona for one task."""

    def __init__(self, task_id: str, config: PersonaConfig):
        self.task_id = task_id
        self.config = config
        self.machine = HierarchicalMachine(
            model=self,
            states=config.hsm.states,
            transitions=config.hsm.transitions,
            initial=config.hsm.initial_state,
            auto_transitions=False,
        )

    def get_current_prompt(self, revision_feedback: str | None = None) -> str:
        """
        Generates the prompt for the current state of the persona's HSM.
        """
        # Note: self.state is the current state string from the HSM
        prompt_key = self.state.replace("_", "") # e.g., git_setup_working -> gitsetupworking
        # A more robust mapping might be needed, but this is a start.
        # Let's assume the prompt key is the state name for now.
        prompt_template_path = self.config.prompts.get(self.state)

        if not prompt_template_path:
            return f"Error: No prompt template found for state '{self.state}' in persona '{self.config.name}'."

        # Setup Jinja2 environment to load templates from the packaged source
        template_loader = FileSystemLoader(searchpath=str(settings.packaged_templates_dir))
        jinja_env = Environment(loader=template_loader)

        template = jinja_env.get_template(prompt_template_path)

        # Prepare context for rendering
        context = {
            "task_id": self.task_id,
            "persona": self.config,
            "revision_feedback": revision_feedback or "No feedback provided.",
        }
        return template.render(context)
```

**File:** `src/alfred/orchestration/orchestrator.py`
```python
"""
The central orchestrator for Alfred. Manages tasks and persona runtimes.
"""
from typing import Dict
import yaml

from src.alfred.config.settings import settings
from src.alfred.models.state import StateFile, TaskState
from src.alfred.orchestration.persona_loader import PersonaLoader
from src.alfred.orchestration.persona_runtime import PersonaRuntime

class Orchestrator:
    """Singleton class to manage the application's main logic."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Orchestrator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.persona_registry = PersonaLoader.load_all()
        self.active_runtimes: Dict[str, PersonaRuntime] = {}
        self._load_workflow_sequence()
        self._initialized = True

    def _load_workflow_sequence(self):
        """Loads the persona sequence from the packaged workflow.yml."""
        try:
            with settings.packaged_workflow_file.open('r', encoding='utf-8') as f:
                self.workflow_sequence = yaml.safe_load(f).get('sequence', [])
        except FileNotFoundError:
            self.workflow_sequence = []

    def _get_or_create_runtime(self, task_id: str) -> PersonaRuntime | None:
        """Gets a live runtime or creates one based on the task's persisted state."""
        if task_id in self.active_runtimes:
            return self.active_runtimes[task_id]

        # Load from state file if not in memory
        state_file = self._load_state()
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            # This is a new task
            task_state = TaskState(task_id=task_id)
            if not self.workflow_sequence:
                return None # Cannot proceed without a workflow

            initial_persona_name = self.workflow_sequence[0]
            persona_config = self.persona_registry.get(initial_persona_name)
            if not persona_config:
                return None # Persona not found

            task_state.persona_state = persona_config.hsm.initial_state
            self._save_task_state(task_state)

        # Get current persona from workflow
        current_persona_name = self.workflow_sequence[task_state.workflow_step]
        persona_config = self.persona_registry.get(current_persona_name)
        if not persona_config:
            return None

        # Create a new runtime instance
        runtime = PersonaRuntime(task_id=task_id, config=persona_config)
        # Manually set its HSM state to the persisted state
        runtime.state = task_state.persona_state
        self.active_runtimes[task_id] = runtime
        return runtime

    def begin_task(self, task_id: str) -> tuple[str, str | None]:
        """
        Begins or resumes a task, returning an initial prompt.
        Returns: (message, next_prompt)
        """
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return ("Error: Could not create or find a runtime for this task. Check workflow/persona configuration.", None)

        message = f"Resuming task {task_id} with persona '{runtime.config.name}'. Current state: {runtime.state}"
        prompt = runtime.get_current_prompt()
        return (message, prompt)

    def _load_state(self) -> StateFile:
        """Loads the state.json file from the user's project."""
        if not settings.state_file.exists():
            return StateFile()
        return StateFile.model_validate_json(settings.state_file.read_text())

    def _save_task_state(self, task_state: TaskState):
        """Saves a single task's state back to the state file."""
        state_file = self._load_state()
        state_file.tasks[task_state.task_id] = task_state
        with settings.state_file.open("w", encoding="utf-8") as f:
            f.write(state_file.model_dump_json(indent=2))

orchestrator = Orchestrator()
```

### **2. Implement the `begin_task` Tool**

Create a new tool file that uses the `Orchestrator` to start or resume a task.

**File:** `src/alfred/tools/task_tools.py`
```python
"""
Tools for core task management, like starting and stopping tasks.
"""
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator

def begin_task(task_id: str) -> ToolResponse:
    """
    Initializes a new task in the Alfred workflow or resumes an existing task
    from its current state.
    """
    message, next_prompt = orchestrator.begin_task(task_id)

    if next_prompt is None:
        return ToolResponse(status="error", message=message)

    return ToolResponse(
        status="success",
        message=message,
        next_prompt=next_prompt,
    )
```

### **3. Update Server Entrypoint**

Wire up the new `begin_task` tool to the `FastMCP` server.

**File:** `src/alfred/server.py`
```python
"""
MCP Server for Alfred
"""
from fastmcp import FastMCP
from src.alfred.config.settings import settings
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
# New import
from src.alfred.tools.task_tools import begin_task as begin_task_impl

app = FastMCP(settings.server_name)

@app.tool()
async def initialize_project() -> ToolResponse:
    """

    Initializes the project for Alfred. Creates a .alfred directory with default
    configurations for personas and workflows. This must be the first tool
    called in a new project.
    """
    return initialize_project_impl()

# New tool
@app.tool()
async def begin_task(task_id: str) -> ToolResponse:
    """
    Begins or resumes a task with the appropriate persona and state.
    """
    return begin_task_impl(task_id)


if __name__ == "__main__":
    app.run()
```

---

### **4. Required Third-Party Libraries**

Add the following libraries to your project's `pyproject.toml` or `requirements.txt`.

```
pyyaml
transitions
jinja2
```

---

### **5. Validation**

After implementing the changes:
1.  Ensure you have an initialized `.alfred` directory from the previous task.
2.  Run the server: `python -m src.alfred.server`.
3.  Use an MCP client to call `begin_task(task_id='TEST-01')`.
4.  **Expected Output:**
    *   The tool should return a `ToolResponse` with a `status` of `success`.
    *   The `message` should indicate that the task is being resumed with the 'Branch Manager' persona.
    *   The `next_prompt` field should contain the fully rendered content from `src/alfred/templates/prompts/git_setup/work.md`, with persona details injected.
5.  Check the `.alfred/state.json` file. It should now contain an entry for `TEST-01` with `workflow_step: 0` and `persona_state: "working"`.
