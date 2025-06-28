### **Task Directive: ALFRED-01 - Project Scaffolding and Initialization**

**Objective:** To create the foundational directory structure, data models, and configuration files for the new Alfred system. This task establishes the skeleton of the application and implements the initial `initialize_project` tool, which sets up a new project workspace.

---

### **1. Create Directory Structure**

Create the following directory tree inside the `src/` folder. This will exist in parallel with `src/epic_task_manager` for now.

```
src/
└── alfred/
    ├── __init__.py
    ├── config/
    │   ├── __init__.py
    │   └── settings.py
    ├── models/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── schemas.py
    │   └── state.py
    ├── orchestration/
    │   └── __init__.py
    ├── personas/
    │   ├── __init__.py
    │   ├── developer.yml
    │   └── git_setup.yml
    ├── templates/
    │   ├── __init__.py
    │   └── prompts/
    │       ├── __init__.py
    │       ├── developer/
    │       │   ├── __init__.py
    │       │   └── placeholder.md
    │       └── git_setup/
    │           ├── __init__.py
    │           └── work.md
    ├── tools/
    │   ├── __init__.py
    │   └── initialize.py
    ├── server.py
    └── workflow.yml
```

**Note:** Create empty `__init__.py` files in all new directories to ensure they are treated as Python packages.

---

### **2. Create Configuration and Data Models**

Create the following files with the specified content. These files define the core data structures of the application.

**File:** `src/alfred/config/settings.py`
```python
"""
Configuration settings for Alfred using pydantic_settings
"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_prefix="ALFRED_", case_sensitive=False)

    # Server configuration
    server_name: str = "alfred"
    version: str = "2.0.0"

    # Directory configuration
    alfred_dir_name: str = ".alfred"
    state_filename: str = "state.json"
    workflow_filename: str = "workflow.yml"

    # Base paths
    project_root: Path = Path.cwd()

    @property
    def alfred_dir(self) -> Path:
        """Get the .alfred directory path in the user's project."""
        return self.project_root / self.alfred_dir_name

    @property
    def state_file(self) -> Path:
        """Get the state file path."""
        return self.alfred_dir / self.state_filename

    @property
    def workflow_file(self) -> Path:
        """Get the project's workflow.yml file path."""
        return self.alfred_dir / self.workflow_filename

    @property
    def packaged_workflow_file(self) -> Path:
        """Get the path to the default workflow file inside the package."""
        return Path(__file__).parent.parent / "workflow.yml"

    @property
    def packaged_personas_dir(self) -> Path:
        """Get the path to the default personas directory inside the package."""
        return Path(__file__).parent.parent / "personas"

    @property
    def packaged_templates_dir(self) -> Path:
        """Get the path to the default templates directory inside the package."""
        return Path(__file__).parent.parent / "templates"

# Global settings instance
settings = Settings()
```

**File:** `src/alfred/models/schemas.py`
```python
"""
Pydantic models for Alfred tool responses.
"""
from typing import Any
from pydantic import BaseModel, Field

class ToolResponse(BaseModel):
    """The standardized response object for all Alfred tools."""
    status: str = Field(description="The status of the operation, typically 'success' or 'error'.")
    message: str = Field(description="A clear, human-readable message describing the result.")
    data: dict[str, Any] | None = Field(default=None)
    next_prompt: str | None = Field(default=None)
```

**File:** `src/alfred/models/state.py`
```python
"""
Pydantic models for Alfred's state management.
"""
from pydantic import BaseModel, Field

class TaskState(BaseModel):
    """Represents the persisted state of a single task."""
    task_id: str
    workflow_step: int = 0
    persona_state: str | None = None
    is_active: bool = False

class StateFile(BaseModel):
    """Represents the root state.json file."""
    tasks: dict[str, TaskState] = Field(default_factory=dict)
```

**File:** `src/alfred/models/config.py`
```python
"""
Pydantic models for parsing persona and workflow configurations.
"""
from pydantic import BaseModel, Field
from typing import Any

class HSMConfig(BaseModel):
    """Defines the structure for a Hierarchical State Machine in YAML."""
    initial_state: str
    states: list[dict[str, Any]]
    transitions: list[dict[str, Any]]

class PersonaConfig(BaseModel):
    """Represents the validated configuration of a single persona.yml file."""
    name: str
    title: str
    target_status: str
    completion_status: str
    hsm: HSMConfig
    prompts: dict[str, str] = Field(default_factory=dict)
    core_principles: list[str] = Field(default_factory=list)
```

---

### **3. Create Default Workflow and Persona Configurations**

These files define the default behavior of Alfred. They will be copied into the user's project during initialization.

**File:** `src/alfred/workflow.yml`
```yaml
# The default sequence of personas for a task workflow.
sequence:
  - git_setup
  - developer
```

**File:** `src/alfred/personas/git_setup.yml`
```yaml
name: "Branch Manager"
title: "Git Setup Specialist"
target_status: "ready_for_setup"
completion_status: "ready_for_dev"

hsm:
  initial_state: "working"
  states:
    - name: "working"
    - name: "verified"
  transitions:
    - trigger: "submit"
      source: "working"
      dest: "verified"

prompts:
  work: "prompts/git_setup/work.md"

core_principles:
  - "My sole focus is ensuring the Git repository is in a clean, correct state."
  - "The branch name convention `feature/{task_id}` is non-negotiable."
```

**File:** `src/alfred/personas/developer.yml`
```yaml
# Placeholder for the developer persona
name: "James"
title: "Full Stack Developer"
target_status: "ready_for_dev"
completion_status: "ready_for_qa"

hsm:
  initial_state: "working"
  states:
    - name: "working"
    - name: "verified"
  transitions:
    - trigger: "submit"
      source: "working"
      dest: "verified"

prompts:
  work: "prompts/developer/placeholder.md"

core_principles:
  - "I am a developer. I write clean, efficient code."
```

**File:** `src/alfred/templates/prompts/git_setup/work.md`
```markdown
# Role: {{ persona.name }} ({{ persona.title }})

Your task is to prepare the git branch for task `{task_id}`.

**Core Principles:**
{% for principle in persona.core_principles %}
- {{ principle }}
{% endfor %}

Please check the repository status and create the feature branch `feature/{task_id}`. When complete, submit your work.
```

**File:** `src/alfred/templates/prompts/developer/placeholder.md`
```markdown
Placeholder for developer prompt.
```

---

### **4. Implement the `initialize` Tool**

This is the first functional component. It sets up the user's project directory.

**File:** `src/alfred/tools/initialize.py`
```python
"""
Initialization tool for Alfred.
"""
import shutil
import json

from src.alfred.config.settings import settings
from src.alfred.models.schemas import ToolResponse
from src.alfred.models.state import StateFile

def initialize_project() -> ToolResponse:
    """
    Initializes the project workspace by creating the .alfred directory and
    copying default configuration and template files. This tool is idempotent.
    """
    alfred_dir = settings.alfred_dir
    if alfred_dir.exists():
        return ToolResponse(
            status="success",
            message=f"Project already initialized at '{alfred_dir}'. No changes were made."
        )

    try:
        # Create base directory
        alfred_dir.mkdir(parents=True, exist_ok=True)

        # Create empty state file
        initial_state = StateFile()
        with settings.state_file.open("w", encoding="utf-8") as f:
            f.write(initial_state.model_dump_json(indent=2))

        # Copy default workflow file
        shutil.copyfile(settings.packaged_workflow_file, settings.workflow_file)

        # Copy default persona and template directories
        shutil.copytree(settings.packaged_personas_dir, alfred_dir / "personas")
        shutil.copytree(settings.packaged_templates_dir, alfred_dir / "templates")

        return ToolResponse(
            status="success",
            message=f"Successfully initialized Alfred project in '{alfred_dir}'."
        )
    except (OSError, shutil.Error) as e:
        return ToolResponse(
            status="error",
            message=f"Failed to initialize project due to a file system error: {e}"
        )

```

---

### **5. Create the Server Entrypoint**

This file wires up the `initialize_project` tool to the MCP server.

**File:** `src/alfred/server.py`
```python
"""
MCP Server for Alfred
"""
from fastmcp import FastMCP
from src.alfred.config.settings import settings
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl

app = FastMCP(settings.server_name)

@app.tool()
async def initialize_project() -> ToolResponse:
    """
    Initializes the project for Alfred. Creates a .alfred directory with default
    configurations for personas and workflows. This must be the first tool
    called in a new project.
    """
    return initialize_project_impl()

if __name__ == "__main__":
    app.run()
```

---

### **6. Validation**

After creating all files:
1.  Run the server: `python -m src.alfred.server`.
2.  In a separate terminal, use an MCP client to call the `initialize_project` tool.
3.  Verify that a `.alfred` directory is created in your project root.
4.  Verify that `.alfred` contains `state.json`, `workflow.yml`, a `personas` directory, and a `templates` directory with the content you created above.
