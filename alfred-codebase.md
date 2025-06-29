------ src/alfred/__init__.py ------
``````

``````
------ src/alfred/config/__init__.py ------
``````
"""Alfred configuration module."""

from src.alfred.models.alfred_config import AlfredConfig, FeaturesConfig

from .manager import ConfigManager

__all__ = ["ConfigManager", "AlfredConfig", "FeaturesConfig"]

``````
------ src/alfred/config/manager.py ------
``````
"""Configuration manager for Alfred."""

import json
import logging
from pathlib import Path

from src.alfred.models.alfred_config import AlfredConfig

logger = logging.getLogger("alfred.config.manager")


class ConfigManager:
    """Manages Alfred configuration."""

    CONFIG_FILENAME = "config.json"

    def __init__(self, config_dir: Path):
        """Initialize the config manager.

        Args:
            config_dir: Directory containing the config file
        """
        self.config_dir = config_dir
        self.config_path = config_dir / self.CONFIG_FILENAME
        self._config: AlfredConfig | None = None

    def load(self) -> AlfredConfig:
        """Load configuration from disk.

        Returns:
            Loaded configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path) as f:
                data = json.load(f)

            self._config = AlfredConfig(**data)
            logger.info(f"Loaded configuration from {self.config_path}")
            return self._config
        except Exception as e:
            logger.exception(f"Failed to load configuration: {e}")
            raise

    def save(self, config: AlfredConfig) -> None:
        """Save configuration to disk.

        Args:
            config: Configuration to save
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w") as f:
                json.dump(config.model_dump(), f, indent=2)

            self._config = config
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.exception(f"Failed to save configuration: {e}")
            raise

    def get(self) -> AlfredConfig:
        """Get the current configuration.

        Returns:
            Current configuration

        Raises:
            RuntimeError: If configuration not loaded
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded")
        return self._config

    def create_default(self) -> AlfredConfig:
        """Create and save a default configuration.

        Returns:
            Created default configuration
        """
        config = AlfredConfig()
        self.save(config)
        return config

    def update_feature(self, feature_name: str, enabled: bool) -> None:
        """Update a feature flag.

        Args:
            feature_name: Name of the feature
            enabled: Whether to enable the feature

        Raises:
            RuntimeError: If configuration not loaded
            ValueError: If feature doesn't exist
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded")

        if not hasattr(self._config.features, feature_name):
            raise ValueError(f"Unknown feature: {feature_name}")

        setattr(self._config.features, feature_name, enabled)
        self.save(self._config)

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled.

        Args:
            feature_name: Name of the feature

        Returns:
            True if feature is enabled

        Raises:
            RuntimeError: If configuration not loaded
            ValueError: If feature doesn't exist
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded")

        if not hasattr(self._config.features, feature_name):
            raise ValueError(f"Unknown feature: {feature_name}")

        return getattr(self._config.features, feature_name)

``````
------ src/alfred/config/settings.py ------
``````
"""
Configuration settings for Alfred using pydantic_settings
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_prefix="ALFRED_", case_sensitive=False)

    # Debugging flag
    debugging_mode: bool = True

    # Server configuration
    server_name: str = "alfred"
    version: str = "2.0.0"

    # Directory configuration
    alfred_dir_name: str = ".alfred"
    workflow_filename: str = "workflow.yml"

    # Base paths
    project_root: Path = Path.cwd()

    @property
    def alfred_dir(self) -> Path:
        """Get the .alfred directory path in the user's project."""
        return self.project_root / self.alfred_dir_name

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

    @property
    def workspace_dir(self) -> Path:
        """Get the workspace directory path."""
        return self.alfred_dir / "workspace"


# Global settings instance
settings = Settings()

``````
------ src/alfred/core/__init__.py ------
``````
# src/alfred/core/__init__.py
from .workflow import BaseWorkflowTool, PlanTaskTool, PlanTaskState
from .prompter import Prompter, prompter

__all__ = ["BaseWorkflowTool", "PlanTaskTool", "PlanTaskState", "Prompter", "prompter"]
``````
------ src/alfred/core/prompter.py ------
``````
# src/alfred/core/prompter.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Optional
import json

from src.alfred.config.settings import settings
from src.alfred.models.schemas import Task


class Prompter:
    """Generates persona-driven, state-aware prompts for the AI agent."""

    def __init__(self):
        # Reuse existing settings to find the templates directory
        search_paths = []
        
        # Check for user-initialized templates first
        user_templates_path = settings.alfred_dir / "templates"
        if user_templates_path.exists():
            search_paths.append(str(user_templates_path))
        
        # Always include packaged templates as fallback
        search_paths.append(str(settings.packaged_templates_dir))

        self.template_loader = FileSystemLoader(searchpath=search_paths)
        self.jinja_env = Environment(loader=self.template_loader, trim_blocks=True, lstrip_blocks=True)
        
        # Add custom filters
        self.jinja_env.filters['fromjson'] = json.loads

    def generate_prompt(
        self,
        task: Task,
        tool_name: str,
        state,  # Can be Enum or str
        persona_config: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates a prompt by rendering a template with the given context.

        Args:
            task: The full structured Task object.
            tool_name: The name of the active tool (e.g., 'plan_task').
            state: The current state from the tool's SM (Enum or str).
            persona_config: The loaded YAML config for the tool's persona.
            additional_context: Ad-hoc data like review feedback.

        Returns:
            The rendered prompt string.
        """
        # Handle both Enum and string state values
        state_value = state.value if hasattr(state, 'value') else state
        template_path = f"prompts/{tool_name}/{state_value}.md"
        
        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            # Proper error handling is crucial
            error_message = f"CRITICAL ERROR: Prompt template not found at '{template_path}'. Details: {e}"
            print(error_message)  # Or use logger
            return error_message

        # Build the comprehensive context for the template
        render_context = {
            "task": task,
            "tool_name": tool_name,
            "state": state_value,
            "persona": persona_config,
            **(additional_context or {})
        }

        return template.render(render_context)


# Singleton instance to be used across the application
prompter = Prompter()
``````
------ src/alfred/core/workflow.py ------
``````
# src/alfred/core/workflow.py
from transitions.core import Machine
from typing import List, Dict, Any, Type
from enum import Enum
from pydantic import BaseModel

class PlanTaskState(str, Enum):
    """States for the PlanTaskTool's internal State Machine."""
    CONTEXTUALIZE = "contextualize"
    REVIEW_CONTEXT = "review_context"
    STRATEGIZE = "strategize"
    REVIEW_STRATEGY = "review_strategy"
    DESIGN = "design"
    REVIEW_DESIGN = "review_design"
    GENERATE_SLOTS = "generate_slots"
    REVIEW_PLAN = "review_plan"
    VERIFIED = "verified"  # The final, terminal state for the tool.

class BaseWorkflowTool:
    """A base class providing shared State Machine logic for Alfred's tools."""
    def __init__(self, task_id: str, tool_name: str = None, persona_name: str = None):
        self.task_id = task_id
        self.tool_name = tool_name or self.__class__.__name__.lower().replace('tool', '')
        self.persona_name = persona_name
        self.state = None  # Will be set by the Machine instance
        self.machine = None
        # Add a new attribute for artifact mapping
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}

    @property
    def is_terminal(self) -> bool:
        """
        Checks if the current state is a terminal (final) state.
        Override in subclasses to define terminal states.
        """
        return self.state == "verified"

    def _create_review_transitions(self, source_state: Enum, review_state: Enum, success_destination_state: Enum) -> List[Dict[str, Any]]:
        """Factory for creating the standard two-step (AI, Human) review transitions."""
        return [
            # Submit work, transition into the review state for AI self-review
            {'trigger': f'submit_{source_state.value}', 'source': source_state.value, 'dest': review_state.value},
            # AI self-approves, moves to human review
            {'trigger': 'ai_approve', 'source': review_state.value, 'dest': success_destination_state.value},
            # A rejection from AI review goes back to the source state to be reworked
            {'trigger': 'request_revision', 'source': review_state.value, 'dest': source_state.value},
        ]

class PlanTaskTool(BaseWorkflowTool):
    """Encapsulates the state and logic for the `plan_task` command."""
    def __init__(self, task_id: str, persona_name: str = "planning"):
        super().__init__(task_id, tool_name="plan_task", persona_name=persona_name)
        
        # Import the new artifact models
        from src.alfred.models.planning_artifacts import (
            ContextAnalysisArtifact, 
            StrategyArtifact, 
            DesignArtifact, 
            ExecutionPlanArtifact
        )
        
        # Define the artifact validation map for this tool
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SLOTS: ExecutionPlanArtifact,
        }
        
        # Use the PlanTaskState Enum for state definitions - convert to string values
        states = [state.value for state in PlanTaskState]

        transitions = [
            *self._create_review_transitions(PlanTaskState.CONTEXTUALIZE, PlanTaskState.REVIEW_CONTEXT, PlanTaskState.STRATEGIZE),
            *self._create_review_transitions(PlanTaskState.STRATEGIZE, PlanTaskState.REVIEW_STRATEGY, PlanTaskState.DESIGN),
            *self._create_review_transitions(PlanTaskState.DESIGN, PlanTaskState.REVIEW_DESIGN, PlanTaskState.GENERATE_SLOTS),
            *self._create_review_transitions(PlanTaskState.GENERATE_SLOTS, PlanTaskState.REVIEW_PLAN, PlanTaskState.VERIFIED),
        ]
        
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=PlanTaskState.CONTEXTUALIZE.value)
``````
------ src/alfred/lib/artifact_manager.py ------
``````
"""
Manages reading and writing all artifacts and data within the .alfred workspace.
"""

import json
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task

logger = get_logger(__name__)


class ArtifactManager:
    """
    Handles all file system I/O for task artifacts.
    
    Note: This class is responsible for artifact rendering (scratchpad content),
    NOT prompt generation. Prompt generation is handled by the Prompter class.
    """

    def __init__(self):
        self.template_loader = FileSystemLoader(searchpath=str(settings.packaged_templates_dir))
        self.jinja_env = Environment(loader=self.template_loader)

        # Add custom filter for formatting numbered lists
        self.jinja_env.filters["format_numbered_list"] = self._format_numbered_list

    @staticmethod
    def _format_numbered_list(text: str) -> str:
        """Converts inline numbered lists to properly formatted markdown lists."""
        if not text or not isinstance(text, str):
            return text

        text_segments = re.split(r"(\d+[.)]\s*)", text)

        if len(text_segments) <= 1:
            return text

        result = []
        for i in range(len(text_segments)):
            if re.match(r"\d+[.)]\s*", text_segments[i]):
                # This is a number, add newline before it if not at start
                if i > 0:
                    result.append("\n")
                result.append(text_segments[i])
            else:
                result.append(text_segments[i].strip())

        return "".join(result)

    def _get_task_dir(self, task_id: str) -> Path:
        return settings.workspace_dir / task_id

    def _get_archive_dir(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "archive"

    def _get_scratchpad_path(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "scratchpad.md"

    def create_task_workspace(self, task_id: str):
        task_dir = self._get_task_dir(task_id)
        task_dir.mkdir(parents=True, exist_ok=True)
        self._get_archive_dir(task_id).mkdir(exist_ok=True)
        logger.info(f"Created workspace for task {task_id} at {task_dir}")

    def append_to_scratchpad(self, task_id: str, state_name: str = None, artifact: BaseModel = None, persona_config = None, content: str = None):
        """Renders a structured artifact to markdown and appends it to the scratchpad."""
        # Ensure the task workspace exists (in case of resumed tasks)
        task_dir = self._get_task_dir(task_id)
        if not task_dir.exists():
            self.create_task_workspace(task_id)

        scratchpad_path = self._get_scratchpad_path(task_id)
        
        # If we get raw content (string), append it directly for backward compatibility
        if content is not None:
            with scratchpad_path.open("a", encoding="utf-8") as f:
                if scratchpad_path.stat().st_size > 0:
                    f.write("\n\n---\n\n")
                f.write(content)
            logger.info(f"Appended raw content to scratchpad for task {task_id}")
            return

        # New template-based approach
        if artifact is None:
            logger.error("No artifact provided for template rendering")
            return

        # Dynamically determine template name from artifact class name
        # e.g., ContextAnalysisArtifact -> context_analysis.md
        # Handle special case for ExecutionPlanArtifact (List[SLOT])
        if isinstance(artifact, list) and state_name == "generate_slots":
            template_name_snake = "execution_plan"
        else:
            artifact_type_name = artifact.__class__.__name__
            template_name_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', artifact_type_name).lower().replace('_artifact', '')
        
        template_path = f"artifacts/{template_name_snake}.md"

        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            logger.error(f"Could not find artifact template '{template_path}': {e}. Falling back to raw JSON.")
            rendered_content = f"### Submission for State: `{state_name}`\n\n```json\n{artifact.model_dump_json(indent=2)}\n```"
        else:
            context = {
                "task": load_task(task_id),  # Load task for context
                "state_name": state_name,
                "artifact": artifact,
                "persona": persona_config
            }
            rendered_content = template.render(context)

        with scratchpad_path.open("a", encoding="utf-8") as f:
            if scratchpad_path.stat().st_size > 0:
                f.write("\n\n---\n\n")
            f.write(rendered_content)
        logger.info(f"Appended rendered artifact '{template_name_snake}' to scratchpad for task {task_id}")

    def archive_scratchpad(self, task_id: str, persona_name: str, workflow_step: int):
        """Moves the current scratchpad to a versioned file in the archive and creates a new empty scratchpad."""
        scratchpad_path = self._get_scratchpad_path(task_id)
        if not scratchpad_path.exists():
            logger.warning(f"No scratchpad found for task {task_id} to archive.")
            return

        archive_dir = self._get_archive_dir(task_id)
        archive_filename = f"{workflow_step:02d}-{persona_name.replace(' ', '_')}_scratchpad.md"
        archive_path = archive_dir / archive_filename

        scratchpad_path.rename(archive_path)
        scratchpad_path.touch()
        logger.info(f"Archived scratchpad for persona '{persona_name}' to {archive_path}")

    def write_json_artifact(self, task_id: str, filename: str, data: dict):
        """Writes a machine-readable JSON file to the archive."""
        archive_dir = self._get_archive_dir(task_id)
        json_path = archive_dir / filename
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Wrote JSON artifact to {json_path}")

    def read_execution_plan(self, task_id: str) -> dict | None:
        """Reads the machine-readable execution plan from the archive."""
        plan_path = self._get_archive_dir(task_id) / "planning_execution_plan.json"
        if not plan_path.exists():
            return None
        try:
            with plan_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None


artifact_manager = ArtifactManager()

``````
------ src/alfred/lib/logger.py ------
``````
"""
Centralized logging configuration for Alfred.
"""

import logging

from src.alfred.config.settings import settings

# A dictionary to hold task-specific handlers to avoid duplication
_task_handlers = {}


def get_logger(name: str) -> logging.Logger:
    """Gets a logger instance with the specified name."""
    return logging.getLogger(name)


def setup_task_logging(task_id: str) -> None:
    """
    Sets up a specific file handler for a given task ID.
    This function is idempotent.
    """
    if not settings.debugging_mode or task_id in _task_handlers:
        return

    # Create the debug directory for the task
    debug_dir = settings.alfred_dir / "debug" / task_id
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / "alfred.log"

    # Create a file handler with standard log format
    handler = logging.FileHandler(log_file, mode="a")
    # Standard format: [LEVEL] YYYY-MM-DD HH:MM:SS.mmm - module_name - message
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)

    # Set the level for this specific handler, not the root logger
    handler.setLevel(logging.INFO)

    # Add the handler to the root logger to capture logs from all modules
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    # Ensure the root logger level allows INFO messages to pass through
    if root_logger.level > logging.INFO:
        root_logger.setLevel(logging.INFO)

    _task_handlers[task_id] = handler


def cleanup_task_logging(task_id: str) -> None:
    """Removes a task-specific log handler."""
    if task_id in _task_handlers:
        handler = _task_handlers.pop(task_id)
        logging.getLogger().removeHandler(handler)
        handler.close()

``````
------ src/alfred/lib/md_parser.py ------
``````
# src/alfred/lib/md_parser.py
import re
from typing import Dict, List


class MarkdownTaskParser:
    """Parses a task definition from a markdown string."""

    def parse(self, markdown_content: str) -> Dict:
        """Parses the markdown content into a dictionary."""
        data = {}
        
        # Extract the task_id from the first line, e.g., '# TASK: TS-01'
        task_id_match = re.search(r"^#\s*TASK:\s*(\S+)", markdown_content, re.MULTILINE)
        if task_id_match:
            data['task_id'] = task_id_match.group(1).strip()

        # Parse text-based sections
        sections = {
            "title": r"##\s*Title\s*\n(.*?)(?=\n##|$)",
            "priority": r"##\s*Priority\s*\n(.*?)(?=\n##|$)",
            "context": r"##\s*Context\s*\n(.*?)(?=\n##|$)",
            "implementation_details": r"##\s*Implementation Details\s*\n(.*?)(?=\n##|$)",
            "dev_notes": r"##\s*Dev Notes\s*\n(.*?)(?=\n##|$)",
        }

        for key, pattern in sections.items():
            match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()

        # Parse list-based sections
        list_sections = {
            "dependencies": r"##\s*Dependencies\s*\n(.*?)(?=\n##|$)",
            "acceptance_criteria": r"##\s*Acceptance Criteria\s*\n(.*?)(?=\n##|$)",
            "ac_verification_steps": r"##\s*AC Verification\s*\n(.*?)(?=\n##|$)",
        }

        for key, pattern in list_sections.items():
            match = re.search(pattern, markdown_content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if not content:
                    data[key] = []
                    continue
                
                # Parse list items properly - each item starts with '-' 
                list_items = []
                current_item = ""
                
                for line in content.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith('##'):  # Stop at next section
                        break
                    if line.startswith('- '):
                        # Start of new list item
                        if current_item:
                            list_items.append(current_item.strip())
                        current_item = line[2:].strip()  # Remove '- '
                    elif current_item:
                        # Continuation of current item
                        current_item += " " + line
                
                # Add the last item
                if current_item:
                    list_items.append(current_item.strip())
                
                data[key] = list_items
            
        return data
``````
------ src/alfred/lib/task_utils.py ------
``````
# src/alfred/lib/task_utils.py
import json
from pathlib import Path
from typing import Optional
from src.alfred.config.settings import settings, Settings
from src.alfred.models.schemas import Task, TaskStatus
from .md_parser import MarkdownTaskParser


def load_task(task_id: str, root_dir: Optional[Path] = None) -> Task | None:
    """Loads a Task by parsing its .md file and merging with its state.json.
    
    Args:
        task_id: The ID of the task to load
        root_dir: Optional root directory to use instead of default settings
    """
    alfred_dir = root_dir / settings.alfred_dir_name if root_dir else settings.alfred_dir
    task_md_path = alfred_dir / "tasks" / f"{task_id}.md"

    if not task_md_path.exists():
        return None

    # Parse the markdown definition
    parser = MarkdownTaskParser()
    task_data = parser.parse(task_md_path.read_text())
    task_model = Task(**task_data)

    # Load the dynamic state
    state_file = alfred_dir / "workspace" / task_id / "state.json"
    if state_file.exists():
        state_data = json.loads(state_file.read_text())
        # Update the model with the persisted state
        task_model.task_status = TaskStatus(state_data.get("task_status", "new"))
    
    return task_model


def save_task_state(task_id: str, status: TaskStatus, root_dir: Optional[Path] = None):
    """Saves only the dynamic state of a task.
    
    Args:
        task_id: The ID of the task to save state for
        status: The task status to save
        root_dir: Optional root directory to use instead of default settings
    """
    alfred_dir = root_dir / settings.alfred_dir_name if root_dir else settings.alfred_dir
    state_dir = alfred_dir / "workspace" / task_id
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "state.json"
    
    state_data = {"task_status": status.value}
    state_file.write_text(json.dumps(state_data, indent=2))


def update_task_status(task_id: str, new_status: TaskStatus, root_dir: Optional[Path] = None) -> Task:
    """Loads a task, updates its status, and saves the state.
    
    Args:
        task_id: The ID of the task to update
        new_status: The new status for the task
        root_dir: Optional root directory to use instead of default settings
    """
    task = load_task(task_id, root_dir)
    if not task:
        raise FileNotFoundError(f"Task {task_id} not found.")
    task.task_status = new_status
    save_task_state(task_id, new_status, root_dir)
    return task
``````
------ src/alfred/lib/transaction_logger.py ------
``````
"""
Logs MCP tool requests and responses for debugging and analysis.
"""

from datetime import datetime, timezone
import json

from src.alfred.config.settings import settings
from src.alfred.models.schemas import ToolResponse


class TransactionLogger:
    """Logs a single transaction to a task-specific .jsonl file."""

    def log(self, task_id: str, tool_name: str, request_data: dict, response: ToolResponse) -> None:
        """Appends a transaction record to the log."""
        if not settings.debugging_mode:
            return

        if not task_id:
            # Handle transactions that don't have a task_id (like initialize_project)
            task_id = "SYSTEM"

        # Create the debug directory for the task
        debug_dir = settings.alfred_dir / "debug" / task_id
        debug_dir.mkdir(parents=True, exist_ok=True)
        log_file = debug_dir / "transactions.jsonl"

        # Get the response data and format the next_prompt for readability
        response_data = response.model_dump(mode="json")

        # Format next_prompt as an array of lines if it exists and contains newlines
        if response_data.get("next_prompt"):
            next_prompt = response_data["next_prompt"]
            if isinstance(next_prompt, str) and "\n" in next_prompt:
                # Split into lines - keep empty strings for empty lines for better readability
                response_data["next_prompt"] = next_prompt.split("\n")

        log_entry = {
            tool_name: {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "request": request_data,
                "response": response_data,
            }
        }

        try:
            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, indent=4) + "\n")
        except OSError:
            pass


# Singleton instance
transaction_logger = TransactionLogger()

``````
------ src/alfred/models/__init__.py ------
``````

``````
------ src/alfred/models/alfred_config.py ------
``````
"""Configuration models for Alfred."""

from enum import Enum
from pydantic import BaseModel, Field


class TaskProvider(str, Enum):
    """Supported task provider types."""
    JIRA = "jira"
    LINEAR = "linear"
    LOCAL = "local"


class ProviderConfig(BaseModel):
    """Configuration for task providers."""
    task_provider: TaskProvider = Field(default=TaskProvider.LOCAL, description="The task management system to use")
    # Add provider-specific configs here if needed, e.g., jira_project_key


class FeaturesConfig(BaseModel):
    """Feature flags for Alfred."""

    scaffolding_mode: bool = Field(default=False, description="Enable scaffolding mode to generate TODO placeholders before implementation")


class AlfredConfig(BaseModel):
    """Main configuration model for Alfred."""

    version: str = Field(default="2.0.0", description="Configuration version")
    providers: ProviderConfig = Field(default_factory=ProviderConfig, description="Task provider configuration")
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    model_config = {"validate_assignment": True, "extra": "forbid"}

``````
------ src/alfred/models/artifacts.py ------
``````
"""
Pydantic models for structured work artifacts.
"""

from pydantic import BaseModel, Field


class RequirementsArtifact(BaseModel):
    """
    Structured data artifact for the requirements gathering phase.
    """
    
    task_id: str = Field(..., description="The unique identifier of the task")
    task_summary: str = Field(..., description="A brief summary of the task")
    task_description: str = Field(..., description="Detailed description of the task requirements")
    acceptance_criteria: list[str] = Field(..., description="List of criteria that must be met for task completion")
    task_source: str = Field(..., description="The source of the task (jira, linear, local)")
    additional_context: dict = Field(default_factory=dict, description="Any additional context or metadata from the task source")


class GitSetupArtifact(BaseModel):
    """
    Structured data artifact for the git_setup phase.
    """

    branch_name: str = Field(..., description="The name of the git branch created or used.")
    branch_status: str = Field(..., description="The status of the branch, e.g., 'clean'.")
    ready_for_work: bool = Field(..., description="Confirmation that the branch is ready for development.")


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


class FinalizeArtifact(BaseModel):
    """Structured data for the finalize phase artifact."""

    commit_hash: str = Field(..., description="Git commit hash from the final commit")
    pull_request_url: str = Field(..., description="URL of the created pull request")


class StrategyArtifact(BaseModel):
    """Structured artifact for the strategy planning phase."""

    high_level_strategy: str = Field(..., description="Overall approach and strategic decisions for implementation")
    key_components: list[str] = Field(..., description="List of major components or modules to be implemented")
    architectural_decisions: str = Field(..., description="Key architectural choices and rationale")
    risk_analysis: str = Field(..., description="Potential risks and mitigation strategies")


class FileBreakdownItem(BaseModel):
    """Individual file change in the solution design."""

    file_path: str = Field(..., description="Path to the file to be modified/created")
    action: str = Field(..., description="One of: 'create', 'modify', or 'delete'")
    change_summary: str = Field(..., description="Detailed description of what changes will be made")


class SolutionDesignArtifact(BaseModel):
    """Structured artifact for the solution design phase."""

    approved_strategy_summary: str = Field(..., description="Brief summary of the approved strategy")
    detailed_design: str = Field(..., description="Comprehensive technical design based on the strategy")
    file_breakdown: list[FileBreakdownItem] = Field(..., description="List of files to be modified with details")
    dependencies: list[str] = Field(default_factory=list, description="List of external dependencies or libraries needed")


class FileModification(BaseModel):
    """Individual file modification in the execution plan."""

    path: str = Field(..., description="Path to the file")
    action: str = Field(..., description="create|modify|delete")
    description: str = Field(..., description="What changes to make")


class ExecutionPlanArtifact(BaseModel):
    """Structured artifact for the execution plan phase."""

    implementation_steps: list[str] = Field(..., description="Ordered list of implementation steps")
    file_modifications: list[FileModification] = Field(..., description="Files that will be created or modified")
    testing_strategy: str = Field(..., description="Testing approach and validation steps")
    success_criteria: list[str] = Field(..., description="Criteria for determining successful completion")


class ScaffoldingManifest(BaseModel):
    """Structured artifact for the scaffolding phase."""

    files_scaffolded: list[str] = Field(..., description="List of files that were scaffolded with TODO comments")
    todo_items_generated: int = Field(..., description="Total number of TODO items generated")
    execution_steps_processed: list[str] = Field(..., description="List of execution plan steps that were processed")

``````
------ src/alfred/models/config.py ------
``````
"""
Pydantic models for parsing persona and workflow configurations.
"""

from typing import Any

from pydantic import BaseModel, Field


class HSMConfig(BaseModel):
    """Defines the structure for a Hierarchical State Machine in YAML."""

    initial_state: str
    states: list[str | dict[str, Any]]  # Can be simple strings or complex state dicts
    transitions: list[dict[str, Any]]


class ArtifactValidationConfig(BaseModel):
    """Defines which artifact model to use for validation in a given state."""

    state: str
    model_path: str  # e.g., "src.alfred.models.artifacts.GitSetupArtifact"


class PersonaConfig(BaseModel):
    """Represents the validated configuration of a single persona.yml file."""

    name: str
    title: str
    target_status: str
    completion_status: str
    hsm: HSMConfig
    prompts: dict[str, str] = Field(default_factory=dict)
    core_principles: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactValidationConfig] = Field(default_factory=list)
    execution_mode: str = Field(default="sequential")  # sequential or stepwise

``````
------ src/alfred/models/planning_artifacts.py ------
``````
# src/alfred/models/planning_artifacts.py
from pydantic import BaseModel, Field
from typing import List, Dict, Literal
from .schemas import SLOT

class ContextAnalysisArtifact(BaseModel):
    context_summary: str
    affected_files: List[str]
    questions_for_developer: List[str]

class StrategyArtifact(BaseModel):
    high_level_strategy: str
    key_components: List[str]
    new_dependencies: List[str] = Field(default_factory=list)
    risk_analysis: str | None = None

class FileChange(BaseModel):
    file_path: str = Field(description="The full path to the file that will be created or modified.")
    change_summary: str = Field(description="A detailed description of the new content or changes for this file.")
    operation: Literal["create", "modify"] = Field(description="Whether the file will be created or modified.")

class DesignArtifact(BaseModel):
    design_summary: str = Field(description="A high-level summary of the implementation design.")
    file_breakdown: List[FileChange] = Field(description="A file-by-file breakdown of all required changes.")

# The Execution Plan is simply a list of SLOTs
ExecutionPlanArtifact = List[SLOT]
``````
------ src/alfred/models/schemas.py ------
``````
"""
Pydantic models for Alfred tool responses and core workflow data models.
"""

from typing import Any, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """The standardized response object for all Alfred tools."""

    status: str = Field(description="The status of the operation, typically 'success' or 'error'.")
    message: str = Field(description="A clear, human-readable message describing the result.")
    data: dict[str, Any] | None = Field(default=None)
    next_prompt: str | None = Field(default=None)


class TaskStatus(str, Enum):
    """Enumeration for the high-level status of a Task."""
    NEW = "new"
    PLANNING = "planning"
    READY_FOR_DEVELOPMENT = "ready_for_development"
    IN_DEVELOPMENT = "in_development"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    REVISIONS_REQUESTED = "revisions_requested"
    READY_FOR_TESTING = "ready_for_testing"
    IN_TESTING = "in_testing"
    READY_FOR_FINALIZATION = "ready_for_finalization"
    DONE = "done"


class OperationType(str, Enum):
    """Enumeration for the type of file system operation in a SLOT."""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    REVIEW = "review"  # For tasks that only involve reviewing code, not changing it.


class Task(BaseModel):
    """Represents a single, well-defined unit of work (a user story or engineering task)."""
    task_id: str = Field(description="The unique identifier, e.g., 'TS-01'.")
    title: str = Field(description="A short, human-readable title for the task.")
    context: str = Field(description="The background for this task, explaining the 'why'.")
    implementation_details: str = Field(description="A high-level overview of the proposed 'how'.")
    dev_notes: Optional[str] = Field(None, description="Optional notes for the developer.")
    acceptance_criteria: List[str] = Field(default_factory=list)
    ac_verification_steps: List[str] = Field(default_factory=list)
    task_status: TaskStatus = Field(default=TaskStatus.NEW)


class Taskflow(BaseModel):
    """Defines the step-by-step procedure and verification for a SLOT."""
    procedural_steps: List[str] = Field(description="Sequential steps for the AI to execute.")
    verification_steps: List[str] = Field(description="Checks or tests to verify the SLOT is complete.")


class SLOT(BaseModel):
    """The core, self-contained, and atomic unit of technical work."""
    slot_id: str = Field(description="A unique ID for this SLOT, e.g., 'slot_1.1'.")
    title: str = Field(description="A short, human-readable title for the SLOT.")
    spec: str = Field(description="The detailed specification for this change.")
    location: str = Field(description="The primary file path or directory for the work.")
    operation: OperationType = Field(description="The type of file system operation.")
    taskflow: Taskflow = Field(description="The detailed workflow for execution and testing.")

``````
------ src/alfred/models/state.py ------
``````
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
    execution_plan: dict | None = None  # Holds the active plan for stepwise personas
    current_step: int = 0
    completed_steps: list[str] = Field(default_factory=list)
    revision_feedback: str | None = None


class StateFile(BaseModel):
    """Represents the root state.json file."""

    tasks: dict[str, TaskState] = Field(default_factory=dict)

``````
------ src/alfred/orchestration/__init__.py ------
``````

``````
------ src/alfred/orchestration/orchestrator.py ------
``````
"""
The central orchestrator for Alfred. Manages tasks and persona runtimes.
"""

import yaml
from typing import Dict

from src.alfred.config import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import cleanup_task_logging, get_logger, setup_task_logging
from src.alfred.models.config import PersonaConfig
from src.alfred.models.state import StateFile, TaskState
from src.alfred.orchestration.persona_loader import PersonaLoader
from src.alfred.orchestration.persona_runtime import PersonaRuntime
from src.alfred.core.workflow import BaseWorkflowTool

logger = get_logger(__name__)


class Orchestrator:
    """Singleton class to manage the application's main logic."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._validate_configuration()
        self.persona_registry = PersonaLoader.load_all()
        self.active_runtimes: dict[str, PersonaRuntime] = {}
        self.active_tools: Dict[str, BaseWorkflowTool] = {}
        self.config_manager = ConfigManager(settings.alfred_dir)
        self._load_workflow_sequence()
        self._initialized = True

    def _validate_configuration(self):
        """
        Validates the Alfred configuration during startup.
        
        This method:
        1. Parses workflow.yml to get the persona sequence
        2. Ensures corresponding persona .yml files exist in the personas/ directory
        3. Validates that PersonaLoader can parse each required YAML file against PersonaConfig
        
        Raises:
            SystemExit: If any persona is missing or misconfigured
        """
        try:
            # Parse workflow.yml
            if not settings.packaged_workflow_file.exists():
                logger.critical(f"workflow.yml not found at: {settings.packaged_workflow_file}")
                raise SystemExit("CRITICAL ERROR: workflow.yml file is missing. Alfred cannot start.")
            
            with settings.packaged_workflow_file.open("r", encoding="utf-8") as f:
                workflow_data = yaml.safe_load(f)
            
            if not workflow_data or "sequence" not in workflow_data:
                logger.critical("workflow.yml is missing required 'sequence' field")
                raise SystemExit("CRITICAL ERROR: workflow.yml is malformed - missing 'sequence' field. Alfred cannot start.")
            
            sequence = workflow_data["sequence"]
            if not isinstance(sequence, list) or not sequence:
                logger.critical("workflow.yml 'sequence' field must be a non-empty list")
                raise SystemExit("CRITICAL ERROR: workflow.yml 'sequence' field must be a non-empty list. Alfred cannot start.")
            
            # Validate personas directory exists
            if not settings.packaged_personas_dir.exists():
                logger.critical(f"Personas directory not found at: {settings.packaged_personas_dir}")
                raise SystemExit(f"CRITICAL ERROR: Personas directory missing at {settings.packaged_personas_dir}. Alfred cannot start.")
            
            # Check each persona in the sequence
            missing_personas = []
            invalid_personas = []
            
            for persona_name in sequence:
                persona_file = settings.packaged_personas_dir / f"{persona_name}.yml"
                
                # Check if persona file exists
                if not persona_file.exists():
                    missing_personas.append(persona_name)
                    continue
                
                # Validate persona file can be parsed
                try:
                    with persona_file.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    
                    if not data:
                        invalid_personas.append(f"{persona_name} (empty file)")
                        continue
                    
                    # Validate against PersonaConfig model
                    PersonaConfig(**data)
                    logger.debug(f"Successfully validated persona: {persona_name}")
                    
                except yaml.YAMLError as e:
                    invalid_personas.append(f"{persona_name} (YAML parsing error: {e})")
                except Exception as e:
                    invalid_personas.append(f"{persona_name} (validation error: {e})")
            
            # Report all validation errors
            if missing_personas or invalid_personas:
                error_msg = "CRITICAL ERROR: Alfred configuration validation failed:\n"
                
                if missing_personas:
                    error_msg += f"Missing persona files: {', '.join(missing_personas)}\n"
                    error_msg += f"Expected location: {settings.packaged_personas_dir}/\n"
                
                if invalid_personas:
                    error_msg += f"Invalid persona configurations: {', '.join(invalid_personas)}\n"
                
                error_msg += "Alfred cannot start until all personas are properly configured."
                logger.critical(error_msg)
                raise SystemExit(error_msg)
            
            logger.info(f"Configuration validation successful. Validated {len(sequence)} personas: {', '.join(sequence)}")
            
        except SystemExit:
            raise
        except Exception as e:
            logger.critical(f"Unexpected error during configuration validation: {e}")
            raise SystemExit(f"CRITICAL ERROR: Configuration validation failed with unexpected error: {e}")

    def _load_workflow_sequence(self):
        """Loads the persona sequence from workflow.yml and applies configuration."""
        try:
            with settings.packaged_workflow_file.open("r", encoding="utf-8") as f:
                base_sequence = yaml.safe_load(f).get("sequence", [])
        except FileNotFoundError:
            base_sequence = []

        try:
            config = self.config_manager.load()
        except FileNotFoundError:
            self.workflow_sequence = base_sequence
            return

        self.workflow_sequence = base_sequence.copy()

        if config.features.scaffolding_mode and "scaffolder" not in self.workflow_sequence:
            try:
                planning_idx = self.workflow_sequence.index("planning")
                self.workflow_sequence.insert(planning_idx + 1, "scaffolder")
                logger.info("Scaffolding mode enabled - inserted scaffolder persona into workflow")
            except ValueError:
                logger.warning("Could not find 'planning' persona in workflow sequence")

    def _get_or_create_runtime(self, task_id: str) -> PersonaRuntime | None:
        """Gets a live runtime or creates one based on the task's persisted state."""
        if task_id in self.active_runtimes:
            return self.active_runtimes[task_id]

        state_file = self._load_state(task_id)
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            task_state = TaskState(task_id=task_id)
            artifact_manager.create_task_workspace(task_id)
            if not self.workflow_sequence:
                return None
            initial_persona_name = self.workflow_sequence[0]
            persona_config = self.persona_registry.get(initial_persona_name)
            if not persona_config:
                return None
            task_state.persona_state = persona_config.hsm.initial_state
            self._save_task_state(task_state)

        current_persona_name = self.workflow_sequence[task_state.workflow_step]
        persona_config = self.persona_registry.get(current_persona_name)
        if not persona_config:
            return None

        runtime = PersonaRuntime(task_id=task_id, config=persona_config)
        runtime.state = task_state.persona_state
        self.active_runtimes[task_id] = runtime
        return runtime

    def _load_state(self, task_id: str | None = None) -> StateFile:
        """Loads the state from a per-task state.json file or returns default state."""
        if task_id:
            task_state_file = settings.workspace_dir / task_id / "state.json"
            if task_state_file.exists():
                try:
                    task_state = TaskState.model_validate_json(task_state_file.read_text())
                    return StateFile(tasks={task_id: task_state})
                except Exception as e:
                    logger.error(f"Failed to load state for task {task_id}: {e}")
        
        # Return empty state file for new tasks or when no task_id provided
        return StateFile()

    def _save_task_state(self, task_state: TaskState):
        """Saves a single task's state to its dedicated state.json file."""
        task_dir = settings.workspace_dir / task_state.task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        task_state_file = task_dir / "state.json"
        with task_state_file.open("w", encoding="utf-8") as f:
            f.write(task_state.model_dump_json(indent=2))
        
        logger.debug(f"Saved state for task {task_state.task_id} to {task_state_file}")

    def begin_task(self, task_id: str) -> tuple[str, str | None]:
        """Begins or resumes a task, returning an initial prompt."""
        setup_task_logging(task_id)
        logger.info(f"Orchestrator beginning/resuming task {task_id}.")
        
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            logger.error(f"Failed to get or create runtime for task {task_id}.")
            return ("Error: Could not create or find a runtime for this task. Check workflow/persona configuration.", None)

        additional_context = self._build_task_context(runtime, task_id)
        message = f"Resuming task {task_id} with persona '{runtime.config.name}'. Current state: {runtime.state}"
        prompt = runtime.get_current_prompt(additional_context=additional_context if additional_context else None)
        return (message, prompt)

    def _build_task_context(self, runtime, task_id: str) -> dict:
        """Builds additional context for task execution."""
        additional_context = {}
        
        self._add_provider_context(runtime, additional_context)
        self._add_stepwise_context(runtime, task_id, additional_context)
        
        return additional_context

    def _add_provider_context(self, runtime, additional_context: dict) -> None:
        """Adds provider information for requirements persona."""
        if runtime.config.name == "Intake Analyst":
            try:
                config = self.config_manager.load()
                additional_context["task_provider"] = config.providers.task_provider.value
            except:
                additional_context["task_provider"] = "local"

    def _add_stepwise_context(self, runtime, task_id: str, additional_context: dict) -> None:
        """Adds stepwise execution context for stepwise personas."""
        if runtime.config.execution_mode == "stepwise" and runtime.state.endswith("_working"):
            task_state = self._load_state(task_id).tasks.get(task_id)
            if task_state and task_state.execution_plan:
                steps = task_state.execution_plan.get("implementation_steps", [])
                if task_state.current_step < len(steps):
                    step = steps[task_state.current_step]
                    additional_context.update({
                        "step_id": f"step_{task_state.current_step + 1}",
                        "step_instruction": str(step),
                        "step_number": task_state.current_step + 1,
                        "total_steps": len(steps),
                    })

    def submit_work_for_task(self, task_id: str, artifact_data: dict) -> tuple[str, str | None]:
        """Routes a work submission, validating and persisting the artifact."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        validated_artifact = runtime.validate_artifact(artifact_data)
        if not validated_artifact:
            return f"Artifact validation failed for state '{runtime.state}'.", None

        artifact_manager.append_to_scratchpad(
            task_id=task_id,
            state_name=runtime.state,
            artifact=validated_artifact,
            persona_config=runtime.config
        )
        runtime.submitted_artifact_data = artifact_data

        success, message = runtime.trigger_submission()
        if not success:
            return (message, None)

        task_state = self._load_state(task_id).tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)

        return (message, runtime.get_current_prompt())

    def _perform_handoff(self, task_id: str, task_state: TaskState, target_persona: str, target_state: str, feedback: str | None = None) -> tuple[str, str | None]:
        """Centralized method to handle all persona handoffs."""
        try:
            target_step_index = self.workflow_sequence.index(target_persona)
        except ValueError:
            return f"Error: Target persona '{target_persona}' not found in workflow.", None

        target_config = self.persona_registry.get(target_persona)
        if not target_config:
            return f"Error: Could not load config for target persona '{target_persona}'.", None

        task_state.workflow_step = target_step_index
        task_state.persona_state = target_state
        task_state.revision_feedback = feedback
        task_state.current_step = 0
        task_state.completed_steps = []

        if target_config.execution_mode == "stepwise":
            plan = artifact_manager.read_execution_plan(task_id)
            if not plan:
                return f"CRITICAL ERROR: Handoff to stepwise persona '{target_persona}' failed. Could not read execution_plan.json.", None
            task_state.execution_plan = plan
        else:
            task_state.execution_plan = None

        self._save_task_state(task_state)
        self.active_runtimes.pop(task_id, None)
        next_runtime = self._get_or_create_runtime(task_id)
        if not next_runtime:
            return f"Error: Could not create runtime for '{target_persona}'.", None

        next_prompt = next_runtime.get_current_prompt(revision_feedback=feedback)
        message = f"Handoff complete. Task is now with '{next_runtime.config.name}' in state '{next_runtime.state}'."
        return message, next_prompt

    def process_review(self, task_id: str, is_approved: bool, feedback: str) -> tuple[str, str | None]:
        """Routes a review, handling internal transitions and backward handoffs."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None
        task_state = self._load_state(task_id).tasks.get(task_id)
        if not task_state:
            return "Error: Task state not found.", None

        success, result = runtime.process_review(is_approved)
        if not success:
            return result, None

        if isinstance(result, dict) and "handoff_to" in result:
            return self._perform_handoff(task_id, task_state, result["handoff_to"], result["target_state"], feedback=feedback)

        task_state.persona_state = runtime.state
        task_state.revision_feedback = feedback if not is_approved else None
        self._save_task_state(task_state)
        return result, runtime.get_current_prompt(revision_feedback=task_state.revision_feedback)

    def process_human_approval(self, task_id: str) -> tuple[str, str | None]:
        """Handles human approval for an intra-persona stage advance."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        success, message = runtime.process_human_approval()
        if not success:
            return message, None

        task_state = self._load_state(task_id).tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)
        return message, runtime.get_current_prompt()

    def process_handoff(self, task_id: str) -> tuple[str, str | None]:
        """Processes final approval and hands off to the next persona."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        # If we are in a devreview state, first trigger the final human_approve.
        if runtime.state.endswith("devreview"):
            success, message = runtime.process_human_approval()
            if not success:
                return f"Handoff failed: could not process final approval. Error: {message}", None

        if not runtime.state.endswith("verified"):
            return f"Error: Handoff requires persona to be in a verified state. Current state: '{runtime.state}'.", None

        task_state = self._load_state(task_id).tasks.get(task_id)
        if not task_state:
            return "Error: Cannot find task state to update.", None

        artifact_manager.archive_scratchpad(task_id, runtime.config.name, task_state.workflow_step)

        if runtime.config.name == "Alex" and runtime.submitted_artifact_data:
            artifact_manager.write_json_artifact(task_id, "planning_execution_plan.json", runtime.submitted_artifact_data)

        next_step_index = task_state.workflow_step + 1
        if next_step_index >= len(self.workflow_sequence):
            cleanup_task_logging(task_id)
            return "Workflow complete!", "Task is fully complete."

        target_persona = self.workflow_sequence[next_step_index]
        target_config = self.persona_registry.get(target_persona)
        if not target_config:
            return f"Error: Next persona '{target_persona}' not found.", None

        return self._perform_handoff(task_id, task_state, target_persona, target_config.hsm.initial_state)

    def process_step_completion(self, task_id: str, step_id: str) -> tuple[str, str | None]:
        """Processes a step completion for any stepwise persona."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None
        if runtime.config.execution_mode != "stepwise":
            return f"Error: Step completion is not valid for the '{runtime.config.name}' persona.", None

        task_state = self._load_state(task_id).tasks.get(task_id)
        if not task_state:
            return "Error: Task state not found.", None

        execution_plan = task_state.execution_plan
        if not execution_plan or "implementation_steps" not in execution_plan:
            return "Error: Execution plan not found in the current task state.", None

        steps = execution_plan.get("implementation_steps", [])
        if task_state.current_step >= len(steps):
            return "Error: All steps already completed.", None

        expected_step_id = f"step_{task_state.current_step + 1}"
        if step_id != expected_step_id:
            return f"Error: Incorrect step ID. Expected '{expected_step_id}', got '{step_id}'.", None

        return self._update_step_state_and_get_next(task_id, task_state, execution_plan, step_id)

    def _update_step_state_and_get_next(self, task_id: str, task_state, execution_plan: dict, step_id: str) -> tuple[str, str | None]:
        """Updates step state and gets the next prompt via the runtime."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Could not get runtime.", None

        self._complete_current_step(task_state, step_id)
        steps = execution_plan.get("implementation_steps", [])
        
        if task_state.current_step >= len(steps):
            return self._handle_all_steps_complete(runtime, task_state)
        else:
            return self._get_next_step_prompt(runtime, task_state, steps, step_id)

    def _complete_current_step(self, task_state, step_id: str) -> None:
        """Marks the current step as complete and updates state."""
        task_state.completed_steps.append(step_id)
        task_state.current_step += 1
        self._save_task_state(task_state)

    def _handle_all_steps_complete(self, runtime, task_state) -> tuple[str, str | None]:
        """Handles completion of all steps and transitions to submission state."""
        try:
            runtime.step_complete()
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)
            message = "All steps complete. Ready for final manifest submission."
            next_prompt = runtime.get_current_prompt()
        except Exception:
            runtime.state = f"{runtime.state.split('_')[0]}_submission"
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)
            message = "All steps complete. Ready for final manifest submission."
            next_prompt = runtime.get_current_prompt()
        return message, next_prompt

    def _get_next_step_prompt(self, runtime, task_state, steps: list, completed_step_id: str) -> tuple[str, str | None]:
        """Gets the prompt for the next step in execution."""
        step = steps[task_state.current_step]
        step_context = {
            "step_id": f"step_{task_state.current_step + 1}",
            "step_instruction": str(step),
            "step_number": task_state.current_step + 1,
            "total_steps": len(steps),
        }
        message = f"Step '{completed_step_id}' complete."
        next_prompt = runtime.get_current_prompt(additional_context=step_context)
        return message, next_prompt


orchestrator = Orchestrator()

``````
------ src/alfred/orchestration/persona_loader.py ------
``````
"""
Loads and validates persona configurations from YAML files.
"""

from pydantic import ValidationError
import yaml

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.models.config import PersonaConfig

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
                logger.exception(f"Failed to parse YAML for persona '{persona_name}': {e}")
            except ValidationError as e:
                logger.exception(f"Validation failed for persona '{persona_name}': {e}")
            except Exception as e:
                logger.exception(f"An unexpected error occurred loading persona '{persona_name}': {e}")

        return personas


def load_persona(persona_name: str) -> dict[str, any]:
    """Loads and parses a persona YAML file.
    
    Args:
        persona_name: Name of the persona file (without .yml extension)
        
    Returns:
        Dict containing the parsed persona configuration
        
    Raises:
        FileNotFoundError: If the persona file doesn't exist
    """
    persona_file = settings.alfred_dir / "personas" / f"{persona_name}.yml"
    if not persona_file.exists():
        # Fallback to packaged personas
        persona_file = settings.packaged_personas_dir / f"{persona_name}.yml"
        if not persona_file.exists():
            raise FileNotFoundError(f"Persona config '{persona_name}.yml' not found.")
    
    with open(persona_file, 'r') as f:
        return yaml.safe_load(f)

``````
------ src/alfred/orchestration/persona_runtime.py ------
``````
"""
Represents the live, stateful instance of a persona for a specific task.
"""

import importlib
import json

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from transitions.extensions import HierarchicalMachine

from src.alfred.config.settings import settings
from src.alfred.models.config import PersonaConfig


class PersonaRuntime:
    """Manages the state and execution of a single persona for one task."""

    def __init__(self, task_id: str, config: PersonaConfig):
        self.task_id = task_id
        self.config = config
        
        # Ensure transitions have source as list
        transitions = []
        for t in config.hsm.transitions:
            transition = t.copy()
            if isinstance(transition.get("source"), str):
                transition["source"] = [transition["source"]]
            transitions.append(transition)
        
        self.machine = HierarchicalMachine(
            model=self,
            states=config.hsm.states,
            transitions=transitions,
            initial=config.hsm.initial_state,
            auto_transitions=False,
        )
        self.submitted_artifact_data: dict | None = None

    def get_current_prompt(self, revision_feedback: str | None = None, additional_context: dict | None = None) -> str:
        """
        Generates the prompt for the current state of the persona's HSM,
        now with support for additional, ad-hoc context.
        """
        prompt_template_path = self.config.prompts.get(self.state)
        
        # Special handling for requirements persona to select provider-specific prompt
        if self.config.name == "Intake Analyst" and additional_context and "task_provider" in additional_context:
            provider = additional_context["task_provider"]
            provider_specific_key = f"{self.state}_{provider}"
            if provider_specific_key in self.config.prompts:
                prompt_template_path = self.config.prompts.get(provider_specific_key)

        if not prompt_template_path:
            return f"Error: No prompt template found for state '{self.state}' in persona '{self.config.name}'."

        # Setup Jinja2 environment to load templates from the packaged source
        template_loader = FileSystemLoader(searchpath=str(settings.packaged_templates_dir))
        jinja_env = Environment(loader=template_loader)

        template = jinja_env.get_template(prompt_template_path)

        # --- NEW: Inject submitted artifact for review prompts ---
        artifact_content_for_review = ""
        if self.state.endswith("aireview") and self.submitted_artifact_data:
            artifact_content_for_review = json.dumps(self.submitted_artifact_data, indent=2)
        # --- END NEW ---

        # Prepare base context for rendering
        context = {
            "task_id": self.task_id,
            "persona": self.config,
            "revision_feedback": revision_feedback or "No feedback provided.",
            # --- NEW ---
            "artifact_content_for_review": artifact_content_for_review,
        }

        # --- NEW: Merge additional context from the orchestrator ---
        if additional_context:
            context.update(additional_context)
        # --- END NEW ---

        return template.render(context)

    def validate_artifact(self, artifact_data: dict) -> BaseModel | None:
        """Validates artifact data against the configured Pydantic model for the current state."""
        validator_config = next((a for a in self.config.artifacts if a.state == self.state), None)
        if not validator_config:
            # If no validator is defined for this state, return the raw data as a simple namespace
            from types import SimpleNamespace
            return SimpleNamespace(**artifact_data)
        try:
            module_path, class_name = validator_config.model_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            validator_class = getattr(module, class_name)
            return validator_class(**artifact_data)
        except Exception as e:
            from src.alfred.lib.logger import get_logger

            logger = get_logger(__name__)
            logger.exception(f"Artifact validation failed for state '{self.state}': {e}")
            return None

    def trigger_submission(self) -> tuple[bool, str]:
        """Triggers the appropriate submission transition on the HSM."""
        try:
            trigger = "submit_manifest" if self.state.endswith("_submission") else "submit"
            trigger_method = getattr(self, trigger, None)
            if not trigger_method:
                return False, f"No trigger '{trigger}' found for state '{self.state}'."

            trigger_method()
            return True, f"Work submitted. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not trigger submission from state '{self.state}': {e}"

    def process_review(self, is_approved: bool) -> tuple[bool, str | dict]:
        """
        Processes a review. Returns a signal if a handoff is required.
        """
        # Determine the correct trigger based on state and approval
        if self.state.endswith("devreview") and is_approved:
            trigger_name = "human_approve"
        else:
            trigger_name = "ai_approve" if is_approved else "request_revision"
            
        transition_config = None
        
        for t in self.config.hsm.transitions:
            if t["trigger"] == trigger_name:
                source = t["source"]
                if isinstance(source, str) and source == self.state:
                    transition_config = t
                    break
                elif isinstance(source, list) and self.state in source:
                    transition_config = t
                    break

        if not transition_config:
            return False, f"No valid transition for trigger '{trigger_name}' from state '{self.state}'."

        destination = transition_config.get("dest")
        if isinstance(destination, dict) and "handoff_to" in destination:
            return True, destination  # Signal for cross-persona handoff

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

``````
------ src/alfred/personas/__init__.py ------
``````

``````
------ src/alfred/personas/developer.yml ------
``````
name: "James"
title: "Full Stack Developer"
target_status: "ready_for_dev"
completion_status: "ready_for_qa"
execution_mode: "stepwise"

hsm:
  initial_state: "coding_working"
  states:
    - "coding_working"
    - "coding_submission"
    - "coding_aireview"
    - "coding_devreview"
    - "coding_verified"

  transitions:
    - trigger: "step_complete"
      source: "coding_working"
      dest: "coding_submission"
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
      dest: "coding_working"

prompts:
  coding_working: "prompts/developer/coding_step.md"
  coding_submission: "prompts/developer/coding_submission.md"
  coding_aireview: "prompts/developer/ai_review.md"
  coding_devreview: "prompts/developer/dev_review.md"
  coding_verified: "prompts/verified.md"

artifacts:
  - state: "coding_submission"
    model_path: "src.alfred.models.artifacts.CodingManifest"

``````
------ src/alfred/personas/devops.yml ------
``````
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
  verified: "prompts/verified.md"

artifacts:
  - state: "working"
    model_path: "src.alfred.models.artifacts.FinalizeArtifact"

``````
------ src/alfred/personas/git_setup.yml ------
``````
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

artifacts:
  - state: "working"
    model_path: "src.alfred.models.artifacts.GitSetupArtifact"

``````
------ src/alfred/personas/planning.yml ------
``````
name: "Alex"
title: "Solution Architect"
target_status: "ready_for_planning"
completion_status: "ready_for_setup"
execution_mode: "batch"

# --- NEW FIELDS ---
greeting: "Hey there! I'm Alex. I'll be your solution architect for this task. My job is to help you create a rock-solid technical plan before we write any code. Let's get the ball rolling."

communication_style: "Professional yet approachable. I explain complex technical concepts in simple terms. I am proactive in identifying risks and dependencies. I focus on the 'why' behind the architecture, not just the 'what'."

thinking_methodology:
  - "Always start with the business goal and work backwards to the technical solution."
  - "Favor simplicity and clarity over unnecessary complexity."
  - "Ensure every part of the plan is testable and verifiable."

hsm:
  initial_state: "strategy_working"
  states:
    - "strategy_working"
    - "strategy_aireview"
    - "strategy_devreview"
    - "solution_design_working"
    - "solution_design_aireview"
    - "solution_design_devreview"
    - "execution_plan_working"
    - "execution_plan_aireview"
    - "execution_plan_devreview"
    - "planning_verified"

  transitions:
    - { trigger: "submit", source: "strategy_working", dest: "strategy_aireview" }
    - { trigger: "ai_approve", source: "strategy_aireview", dest: "strategy_devreview" }
    - { trigger: "request_revision", source: ["strategy_aireview", "strategy_devreview"], dest: "strategy_working" }
    - { trigger: "human_approve", source: "strategy_devreview", dest: "solution_design_working" }

    - { trigger: "submit", source: "solution_design_working", dest: "solution_design_aireview" }
    - { trigger: "ai_approve", source: "solution_design_aireview", dest: "solution_design_devreview" }
    - { trigger: "request_revision", source: ["solution_design_aireview", "solution_design_devreview"], dest: "solution_design_working" }
    - { trigger: "human_approve", source: "solution_design_devreview", dest: "execution_plan_working" }

    - { trigger: "submit", source: "execution_plan_working", dest: "execution_plan_aireview" }
    - { trigger: "ai_approve", source: "execution_plan_aireview", dest: "execution_plan_devreview" }
    - { trigger: "request_revision", source: ["execution_plan_aireview", "execution_plan_devreview"], dest: "execution_plan_working" }
    - { trigger: "human_approve", source: "execution_plan_devreview", dest: "planning_verified" }

prompts:
  strategy_working: "prompts/planning/strategy_work.md"
  strategy_aireview: "prompts/planning/strategy_ai_review.md"
  strategy_devreview: "prompts/planning/strategy_dev_review.md"
  solution_design_working: "prompts/planning/solution_design_work.md"
  solution_design_aireview: "prompts/planning/solution_design_ai_review.md"
  solution_design_devreview: "prompts/planning/solution_design_dev_review.md"
  execution_plan_working: "prompts/planning/execution_plan_work.md"
  execution_plan_aireview: "prompts/planning/execution_plan_ai_review.md"
  execution_plan_devreview: "prompts/planning/execution_plan_dev_review.md"
  execution_plan_verified: "prompts/verified.md"

artifacts:
  - state: "strategy_working"
    model_path: "src.alfred.models.artifacts.StrategyArtifact"
  - state: "solution_design_working"
    model_path: "src.alfred.models.artifacts.SolutionDesignArtifact"
  - state: "execution_plan_working"
    model_path: "src.alfred.models.artifacts.ExecutionPlanArtifact"

``````
------ src/alfred/personas/qa.yml ------
``````
name: "Valerie"
title: "QA Engineer"
target_status: "ready_for_qa"
completion_status: "ready_for_devops"

hsm:
  initial_state: "testing_working"
  states:
    - "testing_working"
    - "testing_aireview"
    - "testing_devreview"
    - "testing_verified"

  transitions:
    - trigger: "submit"
      source: "testing_working"
      dest: "testing_aireview"
    - trigger: "ai_approve"
      source: "testing_aireview"
      dest: "testing_devreview"
    - trigger: "request_revision"
      source: "testing_aireview"
      dest:
        handoff_to: "developer"
        target_state: "coding_working"
    - trigger: "human_approve"
      source: "testing_devreview"
      dest: "testing_verified"

prompts:
  testing_working: "prompts/qa/work.md"
  testing_aireview: "prompts/qa/ai_review.md"
  testing_devreview: "prompts/qa/dev_review.md"
  testing_verified: "prompts/verified.md"

core_principles:
  - "My purpose is to be the quality gate for the project."
  - "I will execute tests precisely as instructed and report results without bias."
  - "A failing test is a non-negotiable blocker."

artifacts:
  - state: "testing_working"
    model_path: "src.alfred.models.artifacts.TestingArtifact"

``````
------ src/alfred/personas/requirements.yml ------
``````
name: "Intake Analyst"
title: "Requirements Specialist"

# This persona is always the first, targeting new or unstated tasks.
target_status: "new"
completion_status: "ready_for_planning"

hsm:
  initial_state: "working"
  states:
    - "working"
    - "verified" # This persona is simple: it fetches data and is done.
  transitions:
    # A single submission marks this as complete. No complex review needed.
    - { trigger: "submit", source: "working", dest: "verified" }

prompts:
  # The key is that the orchestrator will dynamically select the correct prompt
  # based on the provider configured in config.json.
  working_local: "prompts/requirements/local_work.md"
  working_jira: "prompts/requirements/jira_work.md"
  working_linear: "prompts/requirements/linear_work.md"
  verified: "prompts/verified.md"

artifacts:
  - state: "working"
    model_path: "src.alfred.models.artifacts.RequirementsArtifact"
``````
------ src/alfred/personas/scaffolder.yml ------
``````
name: "Scaffy"
title: "Code Scaffolder"
target_status: "ready_for_scaffolding"
completion_status: "ready_for_dev"
execution_mode: "stepwise"

hsm:
  initial_state: "scaffolding_working"
  states:
    - "scaffolding_working"
    - "scaffolding_submission"
    - "scaffolding_aireview"
    - "scaffolding_devreview"
    - "scaffolding_verified"
  transitions:
    - { trigger: "step_complete", source: "scaffolding_working", dest: "scaffolding_submission" }
    - { trigger: "submit_manifest", source: "scaffolding_submission", dest: "scaffolding_aireview" }
    - { trigger: "ai_approve", source: "scaffolding_aireview", dest: "scaffolding_devreview" }
    - { trigger: "human_approve", source: "scaffolding_devreview", dest: "scaffolding_verified" }
    - { trigger: "request_revision", source: ["scaffolding_aireview", "scaffolding_devreview"], dest: "scaffolding_working" }

prompts:
  scaffolding_working: "prompts/scaffolder/work_step.md"
  scaffolding_submission: "prompts/scaffolder/submission.md"
  scaffolding_aireview: "prompts/scaffolder/ai_review.md"
  scaffolding_devreview: "prompts/scaffolder/dev_review.md"
  scaffolding_verified: "prompts/verified.md"

artifacts:
  - state: "scaffolding_submission"
    model_path: "src.alfred.models.artifacts.ScaffoldingManifest"

core_principles:
  - "My sole purpose is to transcribe the execution plan into TODO comments in the codebase."
  - "I do not write implementation code. I only prepare the way for the developer."
  - "I will process one step of the plan at a time."

``````
------ src/alfred/server.py ------
``````
"""
MCP Server for Alfred
"""

import inspect

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl

# New generic state-advancing tool implementations
from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.tools.provide_review import provide_review_impl

app = FastMCP(settings.server_name)


@app.tool()
async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initializes the project workspace for Alfred by creating the .alfred directory with default configurations for personas and workflows.

    - **Primary Function**: Sets up a new project for use with the Alfred workflow system.
    - **Key Features**:
      - Interactive provider selection when no provider is specified.
      - Creates the necessary `.alfred` directory structure.
      - Deploys default `workflow.yml` and persona configuration files.
      - Copies default prompt templates for user customization.
      - Configures the selected task provider (Jira, Linear, or Local).
    - **Use this tool when**: You are starting a brand new project and need to set up the Alfred environment.
    - **Crucial Guardrails**:
      - This tool MUST be the very first tool called in a new project. Other tools will fail until initialization is complete.
      - Do NOT use this tool if the project is already initialized (it will return success but make no changes).

    ## Parameters
    - **provider** `[string]` (optional): The task source provider to configure. Valid values: "jira", "linear", or "local". 
      If not provided, the tool will return available choices for interactive selection.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"provider": provider} if provider else {}
    response = initialize_project_impl(provider)
    transaction_logger.log(task_id=None, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def plan_task(task_id: str) -> ToolResponse:
    """
    Initiates the detailed technical planning for a specific task.

    This is the primary tool for transforming a high-level task or user story
    into a concrete, machine-executable 'Execution Plan' composed of SLOTs.
    A SLOT (Specification, Location, Operation, Task) is an atomic unit of work.

    This tool manages a multi-step, interactive planning process:
    1. **Contextualize**: Deep analysis of the task requirements and codebase context
    2. **Strategize**: High-level technical approach and architecture decisions  
    3. **Design**: Detailed technical design and component specifications
    4. **Generate SLOTs**: Break down into atomic, executable work units

    Each step includes AI self-review followed by human approval gates to ensure quality.
    The final output is a validated execution plan ready for implementation.

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")

    Returns:
        ToolResponse: Contains success/error status and the next prompt to guide planning

    Preconditions:
        - Task must exist and be in 'new' or 'planning' status
        - Project must be initialized with Alfred

    Postconditions:
        - Task status updated to 'planning'
        - Planning tool instance registered and active
        - First planning prompt returned for contextualization phase
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    
    response = await plan_task_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step of a workflow tool.

    This is the generic state-advancing tool that handles work submission for any active workflow tool.
    It automatically determines the correct state transition based on the current state and advances 
    the tool's state machine accordingly.

    Args:
        task_id (str): The unique identifier for the task
        artifact (dict): A dictionary containing the structured work data

    Returns:
        ToolResponse: Contains success/error status and the next prompt
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "artifact": artifact}
    response = submit_work_impl(task_id, artifact)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def provide_review(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Provides feedback on a work artifact during a review step.

    This is the generic state-advancing tool that handles review feedback for any active workflow tool.
    It automatically determines the correct state transition based on the approval status and advances
    the tool's state machine accordingly.

    Args:
        task_id (str): The unique identifier for the task
        is_approved (bool): True to approve, False to request revisions
        feedback_notes (str): Specific feedback for revision (required if is_approved=False)

    Returns:
        ToolResponse: Contains success/error status and the next prompt
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "is_approved": is_approved, "feedback_notes": feedback_notes}
    response = provide_review_impl(task_id, is_approved, feedback_notes)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response




if __name__ == "__main__":
    app.run()
``````
------ src/alfred/templates/__init__.py ------
``````

``````
------ src/alfred/templates/artifacts/Alex.md ------
``````
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: reviewed
---

{# This template conditionally renders the correct artifact based on the model type #}
{%- if artifact.high_level_strategy is defined %}
{# This is a StrategyArtifact #}
# Strategy: {{ task_id }}

## 1. High-Level Strategy
{{ artifact.high_level_strategy }}

## 2. Key Components
{%- for component in artifact.key_components %}
- {{ component }}
{%- endfor %}

## 3. Architectural Decisions
{{ artifact.architectural_decisions }}

## 4. Risk Analysis
{{ artifact.risk_analysis }}
{%- elif artifact.detailed_design is defined %}
{# This is a SolutionDesignArtifact #}
# Solution Design: {{ task_id }}

## 1. Approved Strategy Summary
{{ artifact.approved_strategy_summary }}

## 2. Detailed Design
{{ artifact.detailed_design }}

## 3. File Breakdown
| File Path | Action | Change Summary |
|-----------|--------|----------------|
{%- for item in artifact.file_breakdown %}
| `{{ item.file_path }}` | {{ item.action }} | {{ item.change_summary }} |
{%- endfor %}

## 4. Dependencies
{%- if artifact.dependencies %}
{%- for dependency in artifact.dependencies %}
- {{ dependency }}
{%- endfor %}
{%- else %}
None
{%- endif %}
{%- elif artifact.implementation_steps is defined %}
{# This is an ExecutionPlanArtifact #}
# Execution Plan: {{ task_id }}

## 1. Implementation Steps
{%- for step in artifact.implementation_steps %}
{{ loop.index }}. {{ step }}
{%- endfor %}

## 2. File Modifications
| File Path | Action | Description |
|-----------|--------|-------------|
{%- for mod in artifact.file_modifications %}
| `{{ mod.path }}` | {{ mod.action }} | {{ mod.description }} |
{%- endfor %}

## 3. Testing Strategy
{{ artifact.testing_strategy }}

## 4. Success Criteria
{%- for criterion in artifact.success_criteria %}
- {{ criterion }}
{%- endfor %}
{%- endif %}

---
*Phase completed by {{ persona.name }} ({{ persona.title }})*
``````
------ src/alfred/templates/artifacts/Branch_Manager.md ------
``````
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Git Setup Complete: {{ task_id }}

## Branch Information

- **Branch Name:** `{{ artifact.branch_name }}`
- **Branch Status:** {{ artifact.branch_status }}
- **Ready for Work:** {{ artifact.ready_for_work }}

## Summary

The git environment has been successfully prepared for development work on the specified feature branch.
``````
------ src/alfred/templates/artifacts/Commander.md ------
``````
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

The Alfred workflow for this task is now complete.
``````
------ src/alfred/templates/artifacts/James.md ------
``````
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Implementation Manifest: {{ task_id }}

## 1. Implementation Summary
{{ artifact.implementation_summary }}

## 2. Execution Steps Completed
{% for step in artifact.execution_steps_completed %}
- `{{ step }}`
{% endfor %}

## 3. Testing Notes
{{ artifact.testing_notes }}
``````
------ src/alfred/templates/artifacts/Scaffy.md ------
``````
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Scaffolding Complete: {{ task_id }}

## Scaffolding Summary

- **Files Scaffolded**: {{ artifact.files_scaffolded | length }}
- **TODO Items Generated**: {{ artifact.todo_items_generated }}
- **Execution Steps Processed**: {{ artifact.execution_steps_processed | length }}

## Files Modified
The following files received TODO comments:
{% for file in artifact.files_scaffolded %}
- `{{ file }}`
{% endfor %}
``````
------ src/alfred/templates/artifacts/Valerie.md ------
``````
---
task_id: {{ task_id }}
persona: {{ persona.name }}
status: verified
---

# Test Results: {{ task_id }}

## Test Execution Summary

**Command:** `{{ artifact.test_results.command_run }}`
**Exit Code:** {{ artifact.test_results.exit_code }}

## Test Output

```
{{ artifact.test_results.full_output }}
```
``````
------ src/alfred/templates/artifacts/context_analysis.md ------
``````
### Context Analysis for `{{ task.task_id }}`
*State: `contextualize`*

**Analysis Summary:**
{{ artifact.context_summary }}

**Identified Affected Files:**
{% for file in artifact.affected_files -%}
- `{{ file }}`
{% endfor %}
**Questions for Developer:**
{% for question in artifact.questions_for_developer -%}
- {{ question }}
{% endfor %}
``````
------ src/alfred/templates/artifacts/design.md ------
``````
### Design for `{{ task.task_id }}`
*State: `design`*

**Design Summary:**
{{ artifact.design_summary }}

**File Breakdown:**
{% for file_change in artifact.file_breakdown -%}
**{{ file_change.file_path }}** ({{ file_change.operation }})
{{ file_change.change_summary }}

{% endfor %}
``````
------ src/alfred/templates/artifacts/execution_plan.md ------
``````
### Execution Plan for `{{ task.task_id }}`
*State: `generate_slots`*

**Implementation Plan:**

{% for slot in artifact %}
#### Slot {{ slot.slot_id }}: {{ slot.title }}

**Specification:**
{{ slot.spec }}

**Acceptance Criteria:**
{% for criteria in slot.acceptance_criteria -%}
- {{ criteria }}
{% endfor %}

**Task Flow:** {{ slot.taskflow.value }}
{% if slot.dependencies %}
**Dependencies:** {{ slot.dependencies|join(", ") }}
{% endif %}

{% endfor %}
``````
------ src/alfred/templates/artifacts/strategy.md ------
``````
### Strategy for `{{ task.task_id }}`
*State: `strategize`*

**High-Level Strategy:**
{{ artifact.high_level_strategy }}

**Key Components:**
{% for component in artifact.key_components -%}
- {{ component }}
{% endfor %}
{% if artifact.new_dependencies %}
**New Dependencies:**
{% for dependency in artifact.new_dependencies -%}
- {{ dependency }}
{% endfor %}
{% endif %}

{% if artifact.risk_analysis %}
**Risk Analysis:**
{{ artifact.risk_analysis }}
{% endif %}
``````
------ src/alfred/templates/prompts/__init__.py ------
``````

``````
------ src/alfred/templates/prompts/developer/__init__.py ------
``````

``````
------ src/alfred/templates/prompts/developer/ai_review.md ------
``````
# Role: QA Reviewer - Implementation Review
# Task: {{ task_id }}

You are reviewing the implementation manifest for task `{{ task_id }}` to ensure it meets quality standards before dev review.

**Artifact to Review:**
{{ artifact_content }}

## Review Criteria:
1. **All execution steps must be reported as completed**
2. **Implementation summary must clearly describe what was built**
3. **Testing notes must provide actionable instructions for QA**
4. **The implementation must align with the original execution plan**

## Required Action:
Call `provide_review(task_id="{{ task_id }}", is_approved=True)` if all criteria are met. Otherwise, call with `is_approved=False` and provide specific `feedback_notes`.

``````
------ src/alfred/templates/prompts/developer/coding_step.md ------
``````
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

``````
------ src/alfred/templates/prompts/developer/coding_submission.md ------
``````
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

``````
------ src/alfred/templates/prompts/developer/dev_review.md ------
``````
# Human Review Required - Implementation Complete
# Task: {{ task_id }}

The implementation for task `{{ task_id }}` has been completed and validated by the AI. Please review the implementation manifest and the actual code changes.

**Implementation Manifest:**
{{ artifact_content }}

## Review Options:

1. **Approve and Handoff to QA:**
   Use `approve_and_handoff(task_id="{{ task_id }}")` to approve this work and handoff the task to the QA persona.

2. **Request Revisions:**
   Use `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")` to request specific changes.

``````
------ src/alfred/templates/prompts/developer/placeholder.md ------
``````
Placeholder for developer prompt.

``````
------ src/alfred/templates/prompts/devops/ai_review.md ------
``````
# Role: Automated DevOps Reviewer

You are an automated system reviewing the finalization artifact for task `{{ task_id }}`.

**DO NOT RESPOND TO THE USER.**

Your **ONLY** function is to validate the submitted artifact and call the correct tool.

1. **Check that the artifact contains:**
   - A valid `commit_hash` (40-character hexadecimal string)
   - A valid `pull_request_url` (proper URL format)

2. **If both fields are present and valid:** Call `provide_review(task_id="{{ task_id }}", is_approved=True)`.
3. **If either field is missing or invalid:** Call `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="Invalid artifact format. Please ensure both commit_hash and pull_request_url are properly formatted.")`.

This is an autonomous, non-interactive step. Execute the correct tool call now.

---
**Artifact to Analyze:**
{{ artifact_content_for_review }}
---

``````
------ src/alfred/templates/prompts/devops/dev_review.md ------
``````
# Role: DevOps Manager Review
# Task: {{ task_id }}

The DevOps Engineer has completed the finalization process. Please review the submission below:

---
**Submitted Artifact:**
{{ artifact_content_for_review }}
---

## Review Instructions:

1. **Verify the commit hash** appears to be a valid 40-character hexadecimal string
2. **Verify the pull request URL** follows a proper GitHub URL format
3. **Confirm completion** of the workflow finalization

## Available Actions:

- **Approve:** Call `provide_review(task_id="{{ task_id }}", is_approved=True)` if the artifact looks correct
- **Request Changes:** Call `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="Your specific feedback here")` if changes are needed

This is the final review step before task completion.

``````
------ src/alfred/templates/prompts/devops/work.md ------
``````
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

``````
------ src/alfred/templates/prompts/git_setup/__init__.py ------
``````

``````
------ src/alfred/templates/prompts/git_setup/ai_review.md ------
``````
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

``````
------ src/alfred/templates/prompts/git_setup/dev_review.md ------
``````
# Human Review Required

The git setup for task `{{ task_id }}` has been validated by the AI. Please review the artifact and the repository state.

## Next Step:
Use the `approve_and_handoff(task_id="{{ task_id }}")` tool to approve this work and handoff the task to the next persona (Developer).

Or, use `provide_review` to request revisions.

``````
------ src/alfred/templates/prompts/git_setup/verified.md ------
``````
# Git Setup Complete! 🎉

Great work! The git environment has been successfully prepared for task **{{ task_id }}**.

## What was accomplished:
- Created/switched to the feature branch
- Verified the branch is clean and ready for development
- Confirmed all git setup requirements are met

## Next Steps:
The git setup phase is now complete. The task is ready to move to the next phase in the workflow.

---
**Task ID:** {{ task_id }}
**Persona:** {{ persona.name }}
**Status:** Verified ✓

``````
------ src/alfred/templates/prompts/git_setup/work.md ------
``````
# Role: {{ persona.name }} ({{ persona.title }})

Your task is to prepare the git branch for task `{task_id}`.

**Core Principles:**
{% for principle in persona.core_principles %}
- {{ principle }}
{% endfor %}

Please check the repository status and create the feature branch `feature/{task_id}`. When complete, submit your work.

``````
------ src/alfred/templates/prompts/plan_task/contextualize.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: contextualize

I am beginning the planning process for '{{ task.title }}'.

---
### **Persona Guidelines**

**Your Persona:** {{ persona.name }}, {{ persona.title }}.
**Communication Style:** {{ persona.communication_style }}

You MUST embody this persona. **Do not use repetitive, canned phrases.** Your first message to the user should be a unique greeting based on the persona's `greeting` and `style`. For example: `{{ persona.greeting }}`. Adapt your language to feel like a genuine, collaborative partner.
---

**Task Context:**
- **Goal:** {{ task.context }}
- **Implementation Overview:** {{ task.implementation_details }}
- **Acceptance Criteria:**
{% for criterion in task.acceptance_criteria %}
  - {{ criterion }}
{% endfor %}

---
### **Directive: Codebase Analysis & Ambiguity Detection**

Your mission is to become the expert on this task. You must:
1.  **Analyze the existing codebase.** Start from the project root. Identify all files and code blocks relevant to the provided Task Context.
2.  **Identify Ambiguities.** Compare the task goal with your code analysis. Create a list of precise questions for the human developer to resolve any uncertainties or missing requirements.

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `ContextAnalysisArtifact`.

**Required Artifact Structure:**
```json
{
  "context_summary": "string - A summary of your understanding of the existing code and how the new feature will integrate.",
  "affected_files": ["string - A list of files you have identified as relevant."],
  "questions_for_developer": ["string - Your list of precise questions for the human developer."]
}
```
``````
------ src/alfred/templates/prompts/plan_task/design.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: design

The technical strategy has been approved. Now, you must translate this strategy into a detailed, file-level implementation design.

**Approved Strategy:**
```json
{{ additional_context.strategy_artifact | tojson(indent=2) }}
```

---
### **Directive: Create Detailed Design**

Based on the approved strategy, create a comprehensive, file-by-file breakdown of all necessary changes. For each file that needs to be created or modified, provide a clear summary of the required changes.

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `DesignArtifact`.

**Required Artifact Structure:**
```json
{
  "design_summary": "string",
  "file_breakdown": [
    {
      "file_path": "string",
      "change_summary": "string",
      "operation": "create | modify"
    }
  ]
}
```
``````
------ src/alfred/templates/prompts/plan_task/generate_slots.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: generate_slots

The detailed implementation design has been approved. Your final task is to convert this design into a machine-executable `ExecutionPlan` composed of `SLOT`s.

**Approved Design:**
```json
{{ additional_context.design_artifact | tojson(indent=2) }}
```

---
### **Directive: Generate SLOTs**

Mechanically translate each item in the `file_breakdown` into one or more `SLOT` objects.

For each `SLOT`, you must define:
- `slot_id`: A unique, sequential ID (e.g., "slot-1", "slot-2").
- `title`: A concise title.
- `spec`: A detailed specification, derived from the `change_summary`.
- `location`: The `file_path`.
- `operation`: The `operation`.
- `taskflow`: A detailed `procedural_steps` and `verification_steps` (unit tests) for this specific SLOT.

**CRITICAL: Use `delegation` for complex SLOTs.** If a SLOT's `spec` involves complex logic, security considerations, or significant architectural work, you MUST add a `delegation` field to it. The `delegation` spec should instruct a specialist sub-agent on how to approach the task.

---
### **Required Action**

You MUST now call `alfred.submit_work` with the final `ExecutionPlanArtifact` (the list of `SLOT`s).

**Required Artifact Structure:** `List[SLOT]`
``````
------ src/alfred/templates/prompts/plan_task/review_context.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_context

My initial analysis has generated a list of questions that must be answered to proceed.

---
### **Persona Guidelines**

**Your Persona:** {{ persona.name }}, {{ persona.title }}.
**Communication Style:** {{ persona.communication_style }}

You are now in a **Clarification Loop**. Your goal is to get complete answers for all your questions from the human developer.
---
### **Directive: Manage Clarification Dialogue**

1.  **Maintain a checklist** of the questions below in your context.
2.  **Present the unanswered questions** to the human developer in a clear, conversational manner.
3.  **Receive their response.** They may not answer all questions at once.
4.  **Check your list.** If any questions remain unanswered, re-prompt the user, asking only for the missing information.
5.  **Repeat until all questions are answered.**

**My Questions Checklist:**
{% set artifact = artifact_content | fromjson %}
{% for question in artifact.questions_for_developer %}
- [ ] {{ question }}
{% endfor %}

---
### **Required Action**

**ONLY when all questions have been answered**, you MUST call `alfred.provide_review`.

- Set `is_approved=True`.
- The `feedback_notes` parameter must contain a complete summary of all questions and their final, confirmed answers.
``````
------ src/alfred/templates/prompts/plan_task/review_design.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_design

The detailed design has been drafted. I will now perform a self-review to ensure it fully implements the approved strategy.

---
### **Directive: AI Self-Review**

Critically evaluate the design against the original strategy.

**Review Checklist:**
1. **Strategy Coverage:** Does the `file_breakdown` fully and accurately implement every `key_component` mentioned in the strategy?
2. **Clarity:** Is the `change_summary` for each file clear, specific, and actionable?
3. **Correctness:** Are the file paths and proposed operations logical and correct?

---
### **Required Action**

If the design is sound, call `alfred.provide_review` with `is_approved=True` and a brief confirmation in `feedback_notes`.

If the design is flawed or incomplete, call `alfred.provide_review` with `is_approved=False` and detailed `feedback_notes` on the necessary corrections.
``````
------ src/alfred/templates/prompts/plan_task/review_plan.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_plan

The complete `ExecutionPlan` has been generated. I will now perform a final holistic review before presenting it for human sign-off.

---
### **Directive: Final Plan Review**

Review the generated `list[SLOT]` against the original `Task` context.

**Review Checklist:**
1. **Coverage:** Is every `acceptance_criterion` from the original task fully addressed by the combination of all SLOTs?
2. **Completeness:** Is the plan comprehensive? Are there any missing steps or logical gaps between SLOTs?
3. **Traceability:** Does the plan clearly and logically derive from the approved `strategy` and `design`?
4. **Delegation:** Have complex tasks been appropriately marked with a `delegation` spec?

---
### **Required Action**

If the `ExecutionPlan` is complete and correct, call `alfred.provide_review` with `is_approved=True` to send it for final human approval.

If the plan is flawed, call `provide_review` with `is_approved=False` and detailed `feedback_notes` explaining the required changes.
``````
------ src/alfred/templates/prompts/plan_task/review_strategy.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_strategy

The initial technical strategy has been drafted. I will now perform a self-review to ensure its quality and alignment with the project goals before presenting it for human approval.

---
### **Directive: AI Self-Review**

Critically evaluate the strategy you just created.

**Review Checklist:**
1.  **Goal Alignment:** Does the strategy directly address all acceptance criteria for '{{ task.title }}'?
2.  **Feasibility:** Is the strategy technically sound and achievable within a reasonable scope?
3.  **Completeness:** Are all key components and potential dependencies identified?
4.  **Simplicity:** Is this the simplest viable approach, or is there a less complex alternative?

---
### **Required Action**

If the strategy passes your self-review, call `alfred.provide_review` with `is_approved=True`. The `feedback_notes` should contain a brief summary of your review (e.g., "Strategy is sound and covers all ACs.").

If the strategy is flawed, call `alfred.provide_review` with `is_approved=False` and provide detailed `feedback_notes` on what needs to be corrected. You will then be prompted to create a new strategy.
``````
------ src/alfred/templates/prompts/plan_task/strategize.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: strategize

Context is verified. The human developer has provided all necessary clarifications. We will now create the high-level technical strategy for '{{ task.title }}'. This strategy will serve as the guiding principle for the detailed design.

---
### **Clarifications from Developer**
{% if additional_context.feedback_notes %}
The following clarifications were provided and MUST be incorporated into your strategy:
```
{{ additional_context.feedback_notes }}
```
{% else %}
No specific clarifications were provided. Proceed based on the original task context.
{% endif %}

---
### **Thinking Methodology**
{% for principle in persona.thinking_methodology %}
- {{ principle }}
{% endfor %}

---
### **Directive: Develop Technical Strategy**

Based on the full task context, develop a concise technical strategy.

- **Strategy:** Define the overall technical approach (e.g., "Create a new microservice," "Refactor the existing `UserService`," "Add a new middleware layer").
- **Components:** List the major new or modified components, classes, or modules.
- **Dependencies (Optional):** List any new third-party libraries that will be required.
- **Risks (Optional):** Note any potential risks or important architectural trade-offs.

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `StrategyArtifact`.

**Required Artifact Structure:**
```json
{
  "high_level_strategy": "string",
  "key_components": ["string"],
  "new_dependencies": ["string", "Optional"],
  "risk_analysis": "string", "Optional"
}
```
``````
------ src/alfred/templates/prompts/plan_task/verified.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: verified

# TODO: Implement full prompt.
``````
------ src/alfred/templates/prompts/planning/execution_plan_ai_review.md ------
``````
# AI Review: Execution Plan Phase - Task {{ task_id }}

You are reviewing your execution plan as {{ persona.title }} {{ persona.name }}.

## Your Submitted Plan
```json
{{ artifact_content_for_review }}
```

## Review Criteria

Evaluate your execution plan against:

1. **Design Coverage**: Does the plan implement all aspects of the approved design?
2. **Step Clarity**: Is each implementation step clear and actionable?
3. **Dependency Order**: Are steps arranged in the correct order?
4. **File Accuracy**: Do file modifications match the solution design?
5. **Testing Completeness**: Is the testing strategy comprehensive?
6. **Success Criteria**: Are the criteria measurable and complete?

## Self-Review Questions
- Can a developer follow these steps without ambiguity?
- Have I included all necessary implementation details?
- Will executing these steps result in a working implementation?
- Are there any missing steps or dependencies?
- Is the testing strategy sufficient to validate the implementation?

## Action Required
Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If the plan is complete and ready for human review
- **REQUEST REVISION** (is_approved=false): If improvements are needed (provide specific feedback)

This is your final check before the plan is handed to the developer persona.

``````
------ src/alfred/templates/prompts/planning/execution_plan_dev_review.md ------
``````
# Human Review Required: Execution Plan Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the execution plan and it's ready for your review.

## Current Execution Plan Artifact
The AI has created a step-by-step implementation plan based on the approved solution design.

## Review Guidance
Please review the execution plan focusing on:
- Complete coverage of the solution design
- Clarity and actionability of each step
- Correct dependency ordering
- Adequacy of testing strategy
- Achievability of success criteria

## Available Actions
- To **approve and complete planning**, call: `approve_and_handoff(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

**Note**: This plan will be executed step-by-step by the developer. Ensure it's clear and complete before approval.

``````
------ src/alfred/templates/prompts/planning/execution_plan_work.md ------
``````
# Role: {{ persona.title }} (Execution Plan Generation Phase)

You are {{ persona.name }}, in the **final stage** of planning for task `{{ task_id }}`. Your sole objective is to mechanically translate an approved Solution Design into a series of precise, machine-executable **Execution Steps**.

The output of this phase will be the exact script that the next AI agent will use to write the code.

The solution design has been completed and approved. You must now create the step-by-step execution plan.

{% if revision_feedback and revision_feedback != "No feedback provided." %}
---
**Previous Revision Feedback:** {{ revision_feedback }}
---
{% endif %}

## Instructions:

1. Extract the `approved_design_summary` and any execution order notes from the Solution Design phase.
2. Analyze the `file_breakdown` from the Solution Design. For each item, generate specific implementation steps.
3. Create a comprehensive list of execution steps that can be followed sequentially.

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "implementation_steps": [
    "string - Step 1: Specific action with clear outcome",
    "string - Step 2: Next action building on step 1",
    "..."
  ],
  "file_modifications": [
    {
      "path": "string - Path to the file",
      "action": "string - create|modify|delete",
      "description": "string - What changes to make"
    }
  ],
  "testing_strategy": "string - How to test the implementation",
  "success_criteria": ["string - Measurable criteria for completion"]
}
```

**Example:**
```json
{
  "implementation_steps": [
    "Step 1: Add the StrategyArtifact model to src/epic_task_manager/models/artifacts.py with fields for metadata, high_level_strategy, key_components, architectural_decisions, and risk_analysis",
    "Step 2: Add the SolutionDesignArtifact model with fields for approved_strategy_summary, detailed_design, file_breakdown, and dependencies",
    "Step 3: Update the planning state machine in src/epic_task_manager/state/machine.py to include the new sub-states",
    "Step 4: Create prompt templates for each planning sub-phase in the templates directory"
  ],
  "file_modifications": [
    {
      "path": "src/epic_task_manager/models/artifacts.py",
      "action": "modify",
      "description": "Add three new Pydantic models for planning artifacts"
    },
    {
      "path": "src/epic_task_manager/state/machine.py",
      "action": "modify",
      "description": "Update planning state transitions and add new sub-states"
    }
  ],
  "testing_strategy": "Run pytest to ensure all models are valid, state transitions work correctly, and prompts render without errors",
  "success_criteria": [
    "All new Pydantic models can be instantiated without errors",
    "State machine transitions correctly through all planning sub-phases",
    "Prompt templates render with appropriate context",
    "All existing tests continue to pass"
  ]
}
```

**CRITICAL NOTES:**
- Each step must be atomic and verifiable
- Steps should be in dependency order
- Include enough detail for implementation
- This is a mechanical translation of the approved design
- The `developer` persona will execute these steps verbatim

Construct the complete execution plan artifact and call the `submit_work` tool with the result.

``````
------ src/alfred/templates/prompts/planning/solution_design_ai_review.md ------
``````
# AI Review: Solution Design Phase - Task {{ task_id }}

You are reviewing your solution design as {{ persona.title }} {{ persona.name }}.

## Your Submitted Design
```json
{{ artifact_content_for_review }}
```

## Review Criteria

Evaluate your solution design against:

1. **Strategy Alignment**: Does the design fully implement the approved strategy?
2. **Completeness**: Are all components from the strategy addressed?
3. **File Coverage**: Have all necessary files been identified?
4. **Technical Accuracy**: Are the proposed changes technically correct?
5. **Implementation Order**: Can the changes be implemented in the order specified?
6. **Design Clarity**: Is each file change clearly described?

## Self-Review Questions
- Have I translated every aspect of the strategy into concrete file changes?
- Are there any missing files or components?
- Will developers understand exactly what to implement?
- Are the dependencies complete and accurate?
- Is this the most efficient design to achieve the strategy?

## Action Required
Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If the design is complete and ready for human review
- **REQUEST REVISION** (is_approved=false): If improvements are needed (provide specific feedback)

Focus on ensuring the design is implementable and complete.

``````
------ src/alfred/templates/prompts/planning/solution_design_dev_review.md ------
``````
# Human Review Required: Solution Design Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the solution design phase and it's ready for your review.

## Current Design Artifact
The AI has created a detailed technical design based on the approved strategy.

## Review Guidance
Please review the solution design focusing on:
- Complete implementation of the approved strategy
- Technical correctness of proposed changes
- Completeness of file breakdown
- Feasibility of implementation
- Clarity of change descriptions

## Available Actions
- To **approve this stage** and proceed to Execution Planning, call: `approve_and_advance_stage(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

**Note**: This design will directly guide the implementation. Ensure it's complete and accurate before approval.

``````
------ src/alfred/templates/prompts/planning/solution_design_work.md ------
``````
# Role: {{ persona.title }} (Solution Design Phase)

You are {{ persona.name }}, translating the approved strategy into a comprehensive file-by-file implementation plan for task `{{ task_id }}`.

**Your objective is to create a detailed technical design that implements the approved strategy.**

The strategy phase has been completed and approved. You must now design the detailed solution.

{% if revision_feedback and revision_feedback != "No feedback provided." %}
---
**Revision Feedback:** {{ revision_feedback }}
---
{% endif %}

## Instructions:

1. Review the approved strategy carefully.
2. Create a detailed technical design that implements the strategy.
3. Break down the implementation into specific file changes.
4. Ensure every component mentioned in the strategy is addressed.
5. If revision feedback is provided, address it specifically.

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "approved_strategy_summary": "string - Brief summary of the approved strategy",
  "detailed_design": "string - Comprehensive technical design based on the strategy",
  "file_breakdown": [
    {
      "file_path": "string - Path to the file to be modified/created",
      "action": "string - One of: 'create', 'modify', or 'delete'",
      "change_summary": "string - Detailed description of what changes will be made"
    }
  ],
  "dependencies": ["string - List of external dependencies or libraries needed"]
}
```

**Example:**
```json
{
  "approved_strategy_summary": "Implementing a three-stage planning workflow with Strategy, Solution Design, and Execution Plan Generation phases, each with their own review cycles.",
  "detailed_design": "The implementation will extend the existing HSM by: 1. Adding new planning sub-states to replace the simple planning state. 2. Creating new Pydantic models for each stage's artifacts. 3. Enhancing the Prompter to handle context propagation between stages. 4. Creating phase-specific prompt templates.",
  "file_breakdown": [
    {
      "file_path": "src/epic_task_manager/state/machine.py",
      "action": "modify",
      "change_summary": "Replace planning phase children with new sub-stages: strategy, strategydevreview, solutiondesign, solutiondesigndevreview, executionplan, executionplandevreview, verified. Update transitions to support the new workflow."
    },
    {
      "file_path": "src/epic_task_manager/models/artifacts.py",
      "action": "modify",
      "change_summary": "Add three new Pydantic models: StrategyArtifact, SolutionDesignArtifact, and ExecutionPlanArtifact with appropriate fields for each stage."
    },
    {
      "file_path": "src/epic_task_manager/templates/prompts/planning_strategy_work.md",
      "action": "create",
      "change_summary": "Create prompt template for strategy phase work, instructing AI to generate high-level strategic plan."
    }
  ],
  "dependencies": []
}
```

**CRITICAL NOTES:**
- Your design must fully implement the approved strategy
- Include ALL files that need to be changed
- Be specific about what changes will be made to each file
- Consider the order of implementation (some changes may depend on others)
- Ensure the design is complete and leaves no gaps

Construct the complete solution design artifact and call the `submit_work` tool with the result.

``````
------ src/alfred/templates/prompts/planning/strategy_ai_review.md ------
``````
# AI Review: Strategy Phase - Task {{ task_id }}

You are reviewing your own strategy artifact as {{ persona.title }} {{ persona.name }}.

## Your Submitted Strategy
```json
{{ artifact_content_for_review }}
```

## Review Criteria

Please critically evaluate your strategy against these criteria:

1. **Completeness**: Does the strategy address all aspects of the task requirements?
2. **Technical Soundness**: Is the proposed approach architecturally sound and feasible?
3. **Risk Coverage**: Have all major risks been identified with appropriate mitigations?
4. **Component Design**: Are the key components well-defined and properly scoped?
5. **Architectural Clarity**: Are the architectural decisions clear and well-justified?

## Self-Review Questions
- Is the high-level strategy clear and actionable?
- Are there any missing components or considerations?
- Do the architectural decisions follow best practices?
- Is the risk analysis comprehensive?
- Will this strategy lead to a maintainable and scalable solution?

## Action Required
Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If the strategy is comprehensive and ready for human review
- **REQUEST REVISION** (is_approved=false): If significant improvements are needed (provide specific feedback)

Be critical but fair in your assessment. The goal is to ensure high quality before human review.

``````
------ src/alfred/templates/prompts/planning/strategy_dev_review.md ------
``````
# Human Review Required: Strategy Phase - Task {{ task_id }}

{{ persona.name }} ({{ persona.title }}) has completed the strategy phase and it's ready for your review.

## Current Strategy Artifact
The AI has developed a high-level strategic plan for implementing this task.

## Review Guidance
Please review the strategy focusing on:
- Alignment with business requirements
- Technical feasibility of the proposed approach
- Completeness of the component breakdown
- Adequacy of risk analysis and mitigations
- Overall architectural soundness

## Available Actions
- To **approve this stage** and proceed to Solution Design, call: `approve_and_advance_stage(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

**Note**: This is a critical gate. The strategy sets the foundation for all subsequent work. Ensure it's correct before approving.

``````
------ src/alfred/templates/prompts/planning/strategy_work.md ------
``````
# Role: {{ persona.title }} (Strategy Phase)

You are {{ persona.name }}, developing the high-level strategic plan for task `{{ task_id }}`.

**Your objective is to create a strategic architectural vision that will guide the detailed implementation.**

{% if revision_feedback and revision_feedback != "No feedback provided." %}
---
**Revision Feedback:** {{ revision_feedback }}
---
{% endif %}

## Instructions:

1. Analyze the task requirements thoroughly.
2. Develop a high-level strategic approach for implementation.
3. Focus on architectural decisions, component design, and risk mitigation.
4. If revision feedback is provided, address it specifically.

## Required Work Artifact Structure:

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "high_level_strategy": "string - Overall approach and strategic decisions for implementation",
  "key_components": ["string - List of major components or modules to be implemented"],
  "architectural_decisions": "string - Key architectural choices and rationale",
  "risk_analysis": "string - Potential risks and mitigation strategies"
}
```

**Example:**
```json
{
  "high_level_strategy": "Implement a modular three-stage planning workflow using the existing hierarchical state machine. Each stage will have its own work/review cycle, with human approval gates between stages to ensure quality and alignment.",
  "key_components": [
    "Strategy Phase - High-level architectural planning",
    "Solution Design Phase - Detailed file-by-file breakdown",
    "Execution Plan Phase - Machine-executable task list",
    "Enhanced Prompter - Context-aware prompt generation",
    "Artifact Models - Structured data models for each stage"
  ],
  "architectural_decisions": "1. Leverage existing HSM infrastructure: Extend the current state machine rather than creating a new one. 2. Use composition pattern: Each planning sub-stage will compose into the overall planning phase. 3. Context propagation: Each stage will receive the approved artifact from the previous stage as context.",
  "risk_analysis": "Risks: 1. State explosion - Mitigated by reusing existing review patterns. 2. Context size - Mitigated by only passing approved artifacts forward. 3. Complexity - Mitigated by clear separation of concerns between stages."
}
```

**CRITICAL NOTES:**
- Focus on HIGH-LEVEL strategy, not implementation details
- Consider architectural patterns, design principles, and best practices
- Think about maintainability, extensibility, and testability
- Address all aspects of the requirements but at a strategic level
- Your strategy will guide the detailed design in the next phase

Construct the complete strategy artifact and call the `submit_work` tool with the result.

``````
------ src/alfred/templates/prompts/qa/ai_review.md ------
``````
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

``````
------ src/alfred/templates/prompts/qa/dev_review.md ------
``````
# Role: QA Engineer
# Task: {{ task_id }}

The automated tests have passed. The implementation appears to be working correctly.

## Test Results Summary
The submitted test results have been reviewed and verified.

## Developer Review
Please review the test execution results and ensure:
1. All critical paths have been tested
2. Edge cases have been considered
3. The implementation meets the acceptance criteria

## Required Action
To approve and hand off this task to the next stage, call:
```
approve_and_handoff(task_id="{{ task_id }}")
```

To request revisions, call:
```
provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="Your specific feedback here")
```

``````
------ src/alfred/templates/prompts/qa/work.md ------
``````
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

``````
------ src/alfred/templates/prompts/requirements/__init__.py ------
``````
# Requirements persona prompts
``````
------ src/alfred/templates/prompts/requirements/jira_work.md ------
``````
# Requirements Gathering from Jira

You are the **Intake Analyst** - your role is to fetch and extract task requirements from Jira using the Atlassian MCP tools.

## Your Mission

Connect to Jira via MCP and retrieve all relevant information about the specified task.

## Steps to Complete

1. **Validate Task Access**
   - Use the `mcp__atlassian__getJiraIssue` tool to fetch the issue details
   - Verify you have access to the issue

2. **Extract Core Information**
   - Task summary
   - Detailed description
   - Issue type
   - Status
   - Priority
   - Assignee

3. **Extract Acceptance Criteria**
   - Look for acceptance criteria in the description
   - Check for specific AC fields
   - Parse any checklist items

4. **Gather Additional Context**
   - Labels
   - Components
   - Fix Version
   - Related issues
   - Attachments (note their presence)

## Required MCP Tool Usage

```
mcp__atlassian__getJiraIssue(
    cloudId="<from config>",
    issueIdOrKey="{task_id}",
    expand="description"
)
```

## Artifact to Submit

Submit a `RequirementsArtifact` with:
- `task_id`: The Jira issue key
- `task_summary`: The issue summary
- `task_description`: The full description
- `acceptance_criteria`: Parsed acceptance criteria list
- `task_source`: "jira"
- `additional_context`: Dictionary containing:
  - `issue_type`: The Jira issue type
  - `status`: Current status
  - `priority`: Issue priority
  - `labels`: List of labels
  - `components`: List of components
  - Any other relevant Jira fields

## Error Handling

If the MCP connection fails or the issue is not accessible:
1. Provide a clear error message
2. Suggest checking MCP server status
3. Verify the issue key is correct
``````
------ src/alfred/templates/prompts/requirements/linear_work.md ------
``````
# Requirements Gathering from Linear

You are the **Intake Analyst** - your role is to fetch and extract task requirements from Linear using the Linear MCP tools.

## Your Mission

Connect to Linear via MCP and retrieve all relevant information about the specified task.

## Steps to Complete

1. **Validate Task Access**
   - Use the `mcp__linear__get_issue` tool to fetch the issue details
   - Verify you have access to the issue

2. **Extract Core Information**
   - Issue title
   - Detailed description
   - State/Status
   - Priority
   - Assignee
   - Team

3. **Extract Acceptance Criteria**
   - Parse the description for acceptance criteria
   - Look for checklist items
   - Extract any definition of done

4. **Gather Additional Context**
   - Labels
   - Project association
   - Cycle/Sprint
   - Estimate
   - Related issues
   - Attachments

## Required MCP Tool Usage

```
mcp__linear__get_issue(
    id="{task_id}"
)
```

## Artifact to Submit

Submit a `RequirementsArtifact` with:
- `task_id`: The Linear issue ID
- `task_summary`: The issue title
- `task_description`: The full description (converted from markdown)
- `acceptance_criteria`: Parsed acceptance criteria list
- `task_source`: "linear"
- `additional_context`: Dictionary containing:
  - `state`: Current state/status
  - `priority`: Issue priority (0-4)
  - `team`: Team name
  - `project`: Project name if applicable
  - `labels`: List of label names
  - `estimate`: Point estimate if set
  - Any other relevant Linear fields

## Error Handling

If the MCP connection fails or the issue is not accessible:
1. Provide a clear error message
2. Suggest checking Linear MCP server status
3. Verify the issue ID is correct
4. Check if the user has access to the workspace
``````
------ src/alfred/templates/prompts/requirements/local_work.md ------
``````
# Requirements Gathering from Local Task

You are the **Intake Analyst** - your role is to locate and extract task requirements from a local markdown file.

## Your Mission

Find and parse the task file from the `.alfred/tasks/` directory and extract all relevant information.

## Steps to Complete

1. **Locate the Task File**
   - Look in `.alfred/tasks/` for a file named `{task_id}.md`
   - If the file doesn't exist, provide a clear error message

2. **Parse the Task Information**
   - Extract the task summary
   - Extract the detailed description
   - Extract acceptance criteria
   - Note any additional context or requirements

3. **Structure the Output**
   - Format the extracted information into the RequirementsArtifact structure

## Expected File Format

The task file should follow this format:
```markdown
# TASK-ID

## Summary
Brief summary of the task

## Description
Detailed description of what needs to be done

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

## Artifact to Submit

Submit a `RequirementsArtifact` with:
- `task_id`: The task ID from the filename
- `task_summary`: The summary section content
- `task_description`: The description section content
- `acceptance_criteria`: List of criteria from the acceptance criteria section
- `task_source`: "local"
- `additional_context`: Any other relevant information found in the file

## Error Handling

If the task file is not found or is malformed, provide a clear error message explaining what went wrong and what the user should do.
``````
------ src/alfred/templates/prompts/scaffolder/ai_review.md ------
``````
# AI Review: Scaffolding Phase - Task {{ task_id }}

You are reviewing your own scaffolding work as Code Scaffolder Scaffy.

## Your Submitted ScaffoldingManifest
```json
{{ artifact | tojson(indent=2) }}
```

## Review Criteria

Please critically evaluate your scaffolding work against these criteria:

1. **TODO Comment Quality**: Are the TODO comments clear, actionable, and properly formatted?
2. **Execution Plan Coverage**: Have all execution plan steps been properly processed?
3. **File Identification**: Are all necessary files correctly identified and scaffolded?
4. **No Implementation Code**: Verify that only TODO comments were added, no actual code implementation
5. **Format Compliance**: Do TODO comments follow the specified format with step IDs and descriptions?
6. **Completeness**: Is the ScaffoldingManifest accurate and complete?

## Self-Review Questions

- Are the TODO comments clear enough for a developer to understand what needs to be implemented?
- Did I correctly identify all files mentioned in the execution plan steps?
- Are my TODO counts accurate?
- Did I maintain the separation between scaffolding and implementation?
- Do the TODO comments provide sufficient context and guidance?

## Validation Checklist

For each scaffolded file, verify:
- [ ] TODO comments use the correct format: `// TODO: [ALFRED-20/step_id] description`
- [ ] Comments include helpful implementation notes and context
- [ ] No actual implementation code was written
- [ ] File paths are accurate and complete
- [ ] Step references are correct

## Artifact Validation

Check the ScaffoldingManifest for:
- [ ] `files_scaffolded` contains all modified files
- [ ] `todo_items_generated` count is accurate
- [ ] `execution_steps_processed` includes all handled steps
- [ ] All fields are properly filled

## Action Required

Use the `provide_review` tool to either:
- **APPROVE** (is_approved=true): If scaffolding meets all quality standards
- **REQUEST REVISION** (is_approved=false): If improvements are needed (provide specific feedback)

Focus on ensuring the scaffolding will provide clear guidance for the developer while maintaining separation from implementation.

``````
------ src/alfred/templates/prompts/scaffolder/dev_review.md ------
``````
# Human Review Required: Scaffolding Phase - Task {{ task_id }}

Scaffy (Code Scaffolder) has completed the scaffolding phase and it's ready for your review.

## Current ScaffoldingManifest Artifact
The AI has processed the execution plan and inserted TODO comments throughout the codebase to guide implementation.

## Review Guidance

Please review the scaffolding work focusing on:

### 1. TODO Comment Quality
- Are the TODO comments clear and actionable?
- Do they provide sufficient context for implementation?
- Are they properly formatted with step IDs and descriptions?

### 2. Coverage and Completeness
- Have all files mentioned in the execution plan been scaffolded?
- Are all execution plan steps properly represented?
- Is the scaffolding comprehensive enough to guide development?

### 3. Separation of Concerns
- Verify that only TODO comments were added (no implementation code)
- Ensure scaffolding maintains clear boundaries with actual development
- Check that the scaffolding provides guidance without being prescriptive

### 4. Developer Readiness
- Will the TODO comments help a developer understand what to implement?
- Are the comments organized logically within each file?
- Is there sufficient detail to proceed with confidence?

## What to Look For

**Good Scaffolding:**
- Clear, actionable TODO items with specific guidance
- Proper organization within files
- Helpful implementation notes and context
- Complete coverage of execution plan requirements

**Issues to Flag:**
- Vague or unclear TODO comments
- Missing scaffolding for required files
- Implementation code mixed with scaffolding
- Insufficient detail for development

## Available Actions

- To **approve this phase** and proceed to Development, call: `approve_and_handoff(task_id="{{ task_id }}")`
- To **request revisions**, call: `provide_review(task_id="{{ task_id }}", is_approved=False, feedback_notes="...")`

## Review Files

You may want to examine the scaffolded files directly to verify:
- TODO comment format and clarity
- Implementation guidance quality
- Complete coverage of planned changes

**Note**: This is the final gate before development begins. Ensure the scaffolding provides clear direction for implementation.

``````
------ src/alfred/templates/prompts/scaffolder/submission.md ------
``````
# Role: Code Scaffolder - Work Submission

You are Scaffy, completing the scaffolding phase for task `{{ task_id }}`.

## Work Summary

You have finished processing all execution plan steps and inserting TODO comments throughout the codebase. Now you must review your work and submit the final ScaffoldingManifest artifact.

{% if revision_feedback and revision_feedback != "No feedback provided." %}
---
**Previous Revision Feedback:** {{ revision_feedback }}
---
{% endif %}

## Required Work Artifact Structure

You MUST submit a work artifact containing these EXACT fields as a JSON object:

```json
{
  "files_scaffolded": ["string - List of files that received TODO comments"],
  "todo_items_generated": "integer - Total count of TODO items created",
  "execution_steps_processed": ["string - List of execution plan steps that were processed"]
}
```

**Example:**
```json
{
  "files_scaffolded": [
    "src/alfred/models/alfred_config.py",
    "src/alfred/orchestration/orchestrator.py",
    "src/alfred/models/artifacts.py"
  ],
  "todo_items_generated": 15,
  "execution_steps_processed": [
    "step_1",
    "step_2",
    "step_3"
  ]
}
```

## Submission Instructions

1. **Review all scaffolded files** - Ensure TODO comments are properly formatted and complete
2. **Count TODO items accurately** - Verify the total number of TODO comments added
3. **List all processed steps** - Include every execution plan step that was handled
4. **Submit the manifest** - Call the submit_work tool with your ScaffoldingManifest

## Quality Checklist

Before submission, verify:
- [ ] All target files identified in execution plan have appropriate TODO comments
- [ ] TODO comments follow the specified format with step IDs and descriptions
- [ ] No implementation code was written (only TODO scaffolding)
- [ ] All execution plan steps were processed
- [ ] Files list is complete and accurate
- [ ] TODO count is correct

Construct the complete ScaffoldingManifest artifact and call the `submit_work` tool with the result.

``````
------ src/alfred/templates/prompts/scaffolder/work_step.md ------
``````
# Role: Code Scaffolder
# Task: {{ task_id }} | Step {{ step_number }} of {{ total_steps }}

You are Scaffy, the Code Scaffolder. Your sole purpose is to transcribe execution plan steps into structured TODO comments in the codebase.

---
### **Step ID: `{{ step_id }}`**
---

### **Execution Plan Step:**
```
{{ step_instruction }}
```
---

## Your Mission

1. **Read the execution plan step carefully** - Understand what needs to be implemented
2. **Identify target files** - Determine which files need TODO comments based on the step
3. **Insert structured TODO comments** - Add clear, actionable TODO items that guide the developer
4. **DO NOT implement code** - Only create scaffolding, never write actual implementation

## TODO Comment Format

Use this exact format for TODO comments:

```
// TODO: [ALFRED-20/{{ step_id }}] {{ brief_description }}
// Description: {{ detailed_description }}
// Files involved: {{ list_of_files }}
// Implementation notes: {{ helpful_guidance }}
```

## Required Action

After inserting TODO comments in the appropriate files:

1. **Document your work** - Note which files were scaffolded
2. **Count TODO items** - Track how many TODO comments were added
3. **Call mark_step_complete** - Use the exact step_id: `{{ step_id }}`

**Tool Call:**
`mcp_alfred_mark_step_complete(task_id="{{ task_id }}", step_id="{{ step_id }}")`

## Core Principles

- Focus on clarity and actionability
- Provide context and guidance for the developer
- Never write implementation code
- Only create structured scaffolding

``````
------ src/alfred/templates/prompts/verified.md ------
``````
# Task Complete: {{ persona.name }}

Task `{{ task_id }}` has been successfully completed by {{ persona.title }} ({{ persona.name }}).

The work has been verified and is ready for the next phase of the workflow.

**Status:** {{ persona.completion_status }}

This is an informational prompt. No further action is required from this persona.
``````
------ src/alfred/tools/__init__.py ------
``````

``````
------ src/alfred/tools/initialize.py ------
``````
"""
Initialization tool for Alfred.
"""

import shutil
from pathlib import Path

from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.models.alfred_config import AlfredConfig, ProviderConfig, TaskProvider
from src.alfred.models.schemas import ToolResponse


def initialize_project(provider: str | None = None, test_dir: Path | None = None) -> ToolResponse:
    """
    Initializes the project workspace by creating the .alfred directory with
    provider-specific configuration.
    
    Args:
        provider: Provider choice ('jira', 'linear', or 'local'). If None, returns available choices.
        test_dir: Optional test directory for testing purposes. If provided, will use this instead of settings.alfred_dir.
        
    Returns:
        ToolResponse: Standardized response object.
    """
    alfred_dir = test_dir if test_dir is not None else settings.alfred_dir
    
    # Check if already initialized
    if alfred_dir.exists() and (alfred_dir / "workflow.yml").exists():
        return ToolResponse(
            status="success", 
            message=f"Project already initialized at '{alfred_dir}'. No changes were made."
        )
    
    # Return choices if no provider specified
    if provider is None:
        return _get_provider_choices_response()
    
    try:
        # Validate provider choice
        provider_choice = _validate_provider_choice(provider)
        
        # Create base directory
        alfred_dir.mkdir(parents=True, exist_ok=True)

        # Copy default workflow file
        workflow_file = alfred_dir / settings.workflow_filename
        shutil.copyfile(settings.packaged_workflow_file, workflow_file)

        # Copy default persona and template directories
        shutil.copytree(settings.packaged_personas_dir, alfred_dir / "personas")
        shutil.copytree(settings.packaged_templates_dir, alfred_dir / "templates")
        
        # Create workspace directory
        workspace_dir = alfred_dir / "workspace"
        workspace_dir.mkdir(exist_ok=True)

        # Create configuration with selected provider
        config_manager = ConfigManager(alfred_dir)
        config = AlfredConfig(
            providers=ProviderConfig(task_provider=TaskProvider(provider_choice))
        )
        config_manager.save(config)
        
        # Setup provider-specific resources
        _setup_provider_resources(provider_choice, alfred_dir)

        return ToolResponse(
            status="success", 
            message=f"Successfully initialized Alfred project in '{alfred_dir}' with {provider_choice} provider."
        )
        
    except (OSError, shutil.Error) as e:
        return ToolResponse(
            status="error", 
            message=f"Failed to initialize project due to a file system error: {e}"
        )


def _get_provider_choices_response() -> ToolResponse:
    """Return provider choices for client to prompt user."""
    choices_data = {
        "choices": [
            {
                "value": "jira",
                "label": "Jira (requires Atlassian MCP server)",
                "description": "Connect to Jira for task management via MCP",
            },
            {
                "value": "linear",
                "label": "Linear (requires Linear MCP server)",
                "description": "Connect to Linear for task management via MCP",
            },
            {
                "value": "local",
                "label": "Local markdown files",
                "description": "Use local .md files for task definitions",
            },
        ],
        "prompt": "How will you be sourcing your tasks?",
    }
    return ToolResponse(
        status="choices_needed",
        message="Please select a task source provider.",
        data=choices_data,
    )


def _validate_provider_choice(provider: str) -> str:
    """Validate and normalize provider choice."""
    provider_choice = provider.lower()
    if provider_choice not in ["jira", "linear", "local"]:
        raise ValueError(f"Invalid provider '{provider}'. Must be 'jira', 'linear', or 'local'.")
    return provider_choice


def _setup_provider_resources(provider: str, alfred_dir: Path) -> None:
    """Setup provider-specific resources."""
    if provider == "local":
        # Create tasks inbox for local provider
        tasks_dir = alfred_dir / "tasks"
        tasks_dir.mkdir(exist_ok=True)
        
        readme_path = tasks_dir / "README.md"
        readme_content = """# Local Task Files

This directory is your task inbox for Alfred.

## Creating Tasks

Create markdown files in this directory with the following format:

```markdown
# TASK-ID

## Summary
Brief summary of the task

## Description
Detailed description of what needs to be done

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

When you run `begin_task("TASK-ID")`, Alfred will read the corresponding file and start the workflow.
"""
        readme_path.write_text(readme_content, encoding="utf-8")
``````
------ src/alfred/tools/plan_task.py ------
``````
# src/alfred/tools/plan_task.py
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.core.workflow import PlanTaskTool, PlanTaskState
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import setup_task_logging


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool."""
    # --- ADD LOGGING INITIATION ---
    setup_task_logging(task_id)
    
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # Precondition Check
    if task.task_status != TaskStatus.NEW:
        return ToolResponse(
            status="error",
            message=f"Task '{task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' task."
        )

    tool_instance = PlanTaskTool(task_id=task_id)
    orchestrator.active_tools[task_id] = tool_instance
    
    try:
        # The persona for plan_task is 'planning'
        persona_config = load_persona("planning") 
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    initial_prompt = prompter.generate_prompt(
        task=task,
        tool_name="plan_task",
        state=PlanTaskState.CONTEXTUALIZE,
        persona_config=persona_config
    )

    update_task_status(task_id, TaskStatus.PLANNING)

    return ToolResponse(
        status="success",
        message=f"Planning initiated for task '{task_id}'.",
        next_prompt=initial_prompt
    )
``````
------ src/alfred/tools/progress_tools.py ------
``````
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

``````
------ src/alfred/tools/provide_review.py ------
``````
# src/alfred/tools/provide_review.py
import json
from src.alfred.models.schemas import ToolResponse, Task, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.lib.logger import get_logger, cleanup_task_logging

logger = get_logger(__name__)

def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Processes review feedback, advancing the active tool's State Machine.
    Handles both mid-workflow reviews and final tool completion.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # Determine the trigger and advance the state machine
    trigger = "ai_approve" if is_approved else "request_revision"
    if not hasattr(active_tool, trigger):
        return ToolResponse(status="error", message=f"Invalid action: cannot trigger '{trigger}' from state '{active_tool.state}'.")
    
    getattr(active_tool, trigger)()
    logger.info(f"Task {task_id}: State transitioned via trigger '{trigger}' to '{active_tool.state}'.")

    # Check if the new state is the tool's terminal state
    if active_tool.is_terminal:
        # --- TOOL COMPLETION LOGIC ---
        # This logic must be extensible for different tools in the future.
        # For now, we hardcode the outcome for plan_task.
        final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
        handoff_message = (
            f"Planning for task {task_id} is complete and verified. "
            f"The task is now '{final_task_status.value}'.\n\n"
            f"To begin implementation, run `alfred.implement_task(task_id='{task_id}')`."
        )
        
        update_task_status(task_id, final_task_status)
        del orchestrator.active_tools[task_id]
        
        # --- ADD LOGGING CLEANUP ---
        cleanup_task_logging(task_id)
        
        logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")

        return ToolResponse(
            status="success",
            message=f"Tool '{active_tool.tool_name}' completed successfully.",
            next_prompt=handoff_message
        )
    else:
        # --- MID-WORKFLOW REVIEW LOGIC ---
        try:
            persona_config = load_persona(active_tool.persona_name)
        except FileNotFoundError as e:
            return ToolResponse(status="error", message=str(e))
        
        additional_context = {"feedback_notes": feedback_notes} if not is_approved and feedback_notes else {}
        
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=active_tool.state,
            persona_config=persona_config,
            additional_context=additional_context
        )
        
        message = "Review approved. Proceeding to next step." if is_approved else "Revision requested."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)
``````
------ src/alfred/tools/review_tools.py ------
``````
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


def approve_and_advance_stage(task_id: str) -> ToolResponse:
    """
    Approves the current sub-stage within a multi-stage persona (like Planning)
    and advances to the next sub-stage.
    """
    message, next_prompt = orchestrator.process_human_approval(task_id)
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

``````
------ src/alfred/tools/submit_work.py ------
``````
# src/alfred/tools/submit_work.py
import json

from pydantic import ValidationError
from src.alfred.core.prompter import prompter
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona

logger = get_logger(__name__)

def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """
    Implements the logic for submitting a work artifact to the active tool.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'. Cannot submit work.")
    
    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # --- NEW: Artifact Validation ---
    current_state = active_tool.state
    artifact_model = active_tool.artifact_map.get(current_state)

    if artifact_model:
        try:
            # Validate the submitted dictionary against the Pydantic model
            validated_artifact = artifact_model.model_validate(artifact)
            logger.info(f"Artifact for state '{current_state.value if hasattr(current_state, 'value') else current_state}' validated successfully against {artifact_model.__name__}.")
        except ValidationError as e:
            error_msg = f"Artifact validation failed for state '{current_state.value if hasattr(current_state, 'value') else current_state}'. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
            return ToolResponse(status="error", message=error_msg)
    else:
        validated_artifact = artifact  # No validator for this state, proceed

    # --- Load persona config (used for both persistence and prompt generation) ---
    try:
        persona_config = load_persona(active_tool.persona_name)
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))
        
    # --- Artifact Persistence ---
    # The tool no longer renders anything. It just passes the validated
    # artifact model to the manager.
    current_state_val = active_tool.state.value if hasattr(active_tool.state, 'value') else active_tool.state
    artifact_manager.append_to_scratchpad(
        task_id=task_id,
        state_name=current_state_val,
        artifact=validated_artifact,
        persona_config=persona_config
    )
    
    # --- State Transition ---
    trigger = f"submit_{current_state_val}"
    
    if not hasattr(active_tool, trigger):
        return ToolResponse(status="error", message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")
    
    # Trigger the state transition (e.g., tool.submit_contextualize())
    getattr(active_tool, trigger)()
    logger.info(f"Task {task_id}: State transitioned via trigger '{trigger}' to '{active_tool.state}'.")
    
    # --- Generate Next Prompt for the new review state ---
        
    next_prompt = prompter.generate_prompt(
        task=task,
        tool_name=active_tool.tool_name,
        state=active_tool.state,
        persona_config=persona_config,
        # Pass the submitted artifact into the context for the AI review prompt
        additional_context={"artifact_content": json.dumps(artifact, indent=2)}
    )

    return ToolResponse(status="success", message="Work submitted. Awaiting review.", next_prompt=next_prompt)

``````
------ src/alfred/tools/task_tools.py ------
``````
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


def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a completed work artifact for the current phase of a task.
    """
    message, next_prompt = orchestrator.submit_work_for_task(task_id, artifact)

    if next_prompt is None:
        return ToolResponse(status="error", message=message)

    return ToolResponse(
        status="success",
        message=message,
        next_prompt=next_prompt,
    )

``````
------ src/alfred/workflow.yml ------
``````
# The default sequence of personas for a task workflow.
sequence:
  - requirements
  - planning
  - git_setup
  - developer
  - qa
  - devops

``````
