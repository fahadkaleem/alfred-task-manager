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
from src.alfred.constants import Paths


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_prefix="ALFRED_", case_sensitive=False)

    # Debugging flag
    debugging_mode: bool = True

    # Server configuration
    server_name: str = "alfred"
    version: str = "2.0.0"

    # Directory configuration
    alfred_dir_name: str = Paths.ALFRED_DIR
    workflow_filename: str = Paths.WORKFLOW_FILE

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
        return Path(__file__).parent.parent / Paths.WORKFLOW_FILE

    @property
    def packaged_personas_dir(self) -> Path:
        """Get the path to the default personas directory inside the package."""
        return Path(__file__).parent.parent / Paths.PERSONAS_DIR

    @property
    def packaged_templates_dir(self) -> Path:
        """Get the path to the default templates directory inside the package."""
        return Path(__file__).parent.parent / Paths.TEMPLATES_DIR

    @property
    def workspace_dir(self) -> Path:
        """Get the workspace directory path."""
        return self.alfred_dir / Paths.WORKSPACE_DIR


# Global settings instance
settings = Settings()

``````
------ src/alfred/constants.py ------
``````
"""
Central constants and configuration values for Alfred.

This module contains all magic strings and hardcoded values used throughout
the codebase, organized by category for easy maintenance and consistency.
"""

from enum import Enum
from typing import Final


# Tool Names
class ToolName:
    """Tool name constants."""

    PLAN_TASK: Final[str] = "plan_task"
    IMPLEMENT_TASK: Final[str] = "implement_task"


# Directory and File Names
class Paths:
    """File system path constants."""

    # Directories
    ALFRED_DIR: Final[str] = ".alfred"
    WORKSPACE_DIR: Final[str] = "workspace"
    PERSONAS_DIR: Final[str] = "personas"
    TEMPLATES_DIR: Final[str] = "templates"
    ARCHIVE_DIR: Final[str] = "archive"
    DEBUG_DIR: Final[str] = "debug"
    TASKS_DIR: Final[str] = "tasks"

    # Files
    SCRATCHPAD_FILE: Final[str] = "scratchpad.md"
    EXECUTION_PLAN_FILE: Final[str] = "execution_plan.json"
    TOOL_STATE_FILE: Final[str] = "tool_state.json"
    WORKFLOW_FILE: Final[str] = "workflow.yml"
    STATE_FILE: Final[str] = "state.json"
    TASK_FILE: Final[str] = "task.json"

    # Extensions
    TMP_EXTENSION: Final[str] = ".tmp"
    MD_EXTENSION: Final[str] = ".md"
    JSON_EXTENSION: Final[str] = ".json"


# Template Paths
class TemplatePaths:
    """Template path patterns."""

    PROMPT_PATTERN: Final[str] = "prompts/{tool_name}/{state}.md"
    ARTIFACT_PATTERN: Final[str] = "artifacts/{template_name}.md"


# Plan Task State Names (as strings for transitions)
class PlanTaskStates:
    """Plan task state string constants."""

    INITIAL: Final[str] = "initial"
    CONTEXTUALIZE: Final[str] = "contextualize"
    REVIEW_CONTEXT: Final[str] = "review_context"
    STRATEGIZE: Final[str] = "strategize"
    REVIEW_STRATEGY: Final[str] = "review_strategy"
    DESIGN: Final[str] = "design"
    REVIEW_DESIGN: Final[str] = "review_design"
    GENERATE_SUBTASKS: Final[str] = "generate_subtasks"
    REVIEW_PLAN: Final[str] = "review_plan"
    VERIFIED: Final[str] = "verified"


# Artifact Keys and Mappings
class ArtifactKeys:
    """Artifact storage key constants."""

    # State to artifact name mapping
    STATE_TO_ARTIFACT_MAP: Final[dict] = {
        PlanTaskStates.CONTEXTUALIZE: "context",
        PlanTaskStates.STRATEGIZE: "strategy",
        PlanTaskStates.DESIGN: "design",
        PlanTaskStates.GENERATE_SUBTASKS: "execution_plan",
    }

    ARTIFACT_SUFFIX: Final[str] = "_artifact"
    ARTIFACT_CONTENT_KEY: Final[str] = "artifact_content"

    @staticmethod
    def get_artifact_key(state: str) -> str:
        """Get the artifact key for a given state."""
        artifact_name = ArtifactKeys.STATE_TO_ARTIFACT_MAP.get(state, state)
        return f"{artifact_name}{ArtifactKeys.ARTIFACT_SUFFIX}"


# State Descriptions for Documentation
class StateDescriptions:
    """Human-readable state descriptions."""

    DESCRIPTIONS: Final[dict] = {
        PlanTaskStates.CONTEXTUALIZE: "Understanding the Requirements and Codebase",
        PlanTaskStates.STRATEGIZE: "Technical Strategy and Approach",
        PlanTaskStates.DESIGN: "Detailed Implementation Design",
        PlanTaskStates.GENERATE_SUBTASKS: "Execution Plan",
    }


# Trigger Names
class Triggers:
    """State machine trigger constants."""

    AI_APPROVE: Final[str] = "ai_approve"
    REQUEST_REVISION: Final[str] = "request_revision"

    @staticmethod
    def submit_trigger(state: str) -> str:
        """Generate submit trigger name for a state."""
        return f"submit_{state}"


# Response Status Values
class ResponseStatus:
    """Tool response status constants."""

    SUCCESS: Final[str] = "success"
    ERROR: Final[str] = "error"
    CHOICES_NEEDED: Final[str] = "choices_needed"


# Task Provider Names
class TaskProviders:
    """Task provider type constants."""

    JIRA: Final[str] = "jira"
    LINEAR: Final[str] = "linear"
    LOCAL: Final[str] = "local"

    ALL_PROVIDERS: Final[list] = [JIRA, LINEAR, LOCAL]


# Subtask ID Format
class SubtaskFormat:
    """Subtask formatting constants."""

    ID_PREFIX: Final[str] = "ST"
    ID_PATTERN: Final[str] = "{prefix}-{number}"

    @staticmethod
    def format_id(number: int) -> str:
        """Format a subtask ID."""
        return SubtaskFormat.ID_PATTERN.format(prefix=SubtaskFormat.ID_PREFIX, number=number)


# Log Messages
class LogMessages:
    """Standardized log message templates."""

    TASK_NOT_FOUND: Final[str] = "Task '{task_id}' not found."
    NO_ACTIVE_TOOL: Final[str] = "No active tool found for task '{task_id}'."
    STATE_TRANSITION: Final[str] = "Task {task_id}: State transitioned via trigger '{trigger}' to '{state}'."
    ARTIFACT_VALIDATED: Final[str] = "Artifact for state '{state}' validated successfully against {model}."
    EXECUTION_PLAN_SAVED: Final[str] = "Successfully saved execution plan to {path}"
    EXECUTION_PLAN_SAVE_FAILED: Final[str] = "Failed to save execution plan JSON: {error}"


# Error Messages
class ErrorMessages:
    """Standardized error message templates."""

    INVALID_STATE: Final[str] = "Invalid state: {state}"
    VALIDATION_FAILED: Final[str] = "Artifact validation failed for state '{state}'"
    FILE_NOT_FOUND: Final[str] = "File not found: {path}"
    PERMISSION_DENIED: Final[str] = "Permission denied: {path}"
    INVALID_TASK_FORMAT: Final[str] = "Invalid task format: {reason}"

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
from src.alfred.constants import TemplatePaths


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
        self.jinja_env.filters["fromjson"] = json.loads

    def generate_prompt(
        self,
        task: Task,
        tool_name: str,
        state,  # Can be Enum or str
        persona_config: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None,
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
        state_value = state.value if hasattr(state, "value") else state
        template_path = TemplatePaths.PROMPT_PATTERN.format(tool_name=tool_name, state=state_value)

        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            # Proper error handling is crucial
            error_message = f"CRITICAL ERROR: Prompt template not found at '{template_path}'. Details: {e}"
            print(error_message)  # Or use logger
            return error_message

        # Build the comprehensive context for the template
        render_context = {"task": task, "tool_name": tool_name, "state": state_value, "persona": persona_config, "additional_context": additional_context or {}}

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
from src.alfred.constants import ToolName, Triggers


class PlanTaskState(str, Enum):
    """States for the PlanTaskTool's internal State Machine."""

    CONTEXTUALIZE = "contextualize"
    REVIEW_CONTEXT = "review_context"
    STRATEGIZE = "strategize"
    REVIEW_STRATEGY = "review_strategy"
    DESIGN = "design"
    REVIEW_DESIGN = "review_design"
    GENERATE_SUBTASKS = "generate_subtasks"
    REVIEW_PLAN = "review_plan"
    VERIFIED = "verified"  # The final, terminal state for the tool.


class BaseWorkflowTool:
    """A base class providing shared State Machine logic for Alfred's tools."""

    def __init__(self, task_id: str, tool_name: str = None, persona_name: str = None):
        self.task_id = task_id
        self.tool_name = tool_name or self.__class__.__name__.lower().replace("tool", "")
        self.persona_name = persona_name
        self.state = None  # Will be set by the Machine instance
        self.machine = None
        # Add a new attribute for artifact mapping
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}
        # Context store for persisting artifacts between state transitions
        self.context_store: Dict[str, Any] = {}

    @property
    def is_terminal(self) -> bool:
        """
        Checks if the current state is a terminal (final) state.
        Override in subclasses to define terminal states.
        """
        return self.state == "verified"

    @classmethod
    def get_state_from_string(cls, state_string: str) -> str:
        """
        Convert a string state back to the appropriate enum value.

        This is used during tool recovery to restore the state from
        persisted string values.

        Args:
            state_string: The state as a string

        Returns:
            The state string (for now, states are already strings)
        """
        # For now, our states are already strings due to the Enum.value usage
        # This method provides a hook for future enum handling if needed
        return state_string

    def _create_review_transitions(self, source_state: Enum, review_state: Enum, success_destination_state: Enum) -> List[Dict[str, Any]]:
        """Factory for creating the standard two-step (AI, Human) review transitions."""
        return [
            # Submit work, transition into the review state for AI self-review
            {"trigger": Triggers.submit_trigger(source_state.value), "source": source_state.value, "dest": review_state.value},
            # AI self-approves, moves to human review
            {"trigger": Triggers.AI_APPROVE, "source": review_state.value, "dest": success_destination_state.value},
            # A rejection from AI review goes back to the source state to be reworked
            {"trigger": Triggers.REQUEST_REVISION, "source": review_state.value, "dest": source_state.value},
        ]


class PlanTaskTool(BaseWorkflowTool):
    """Encapsulates the state and logic for the `plan_task` command."""

    def __init__(self, task_id: str, persona_name: str = "planning"):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK, persona_name=persona_name)

        # Import the new artifact models
        from src.alfred.models.planning_artifacts import ContextAnalysisArtifact, StrategyArtifact, DesignArtifact, ExecutionPlanArtifact

        # Define the artifact validation map for this tool
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }

        # Use the PlanTaskState Enum for state definitions - convert to string values
        states = [state.value for state in PlanTaskState]

        transitions = [
            *self._create_review_transitions(PlanTaskState.CONTEXTUALIZE, PlanTaskState.REVIEW_CONTEXT, PlanTaskState.STRATEGIZE),
            *self._create_review_transitions(PlanTaskState.STRATEGIZE, PlanTaskState.REVIEW_STRATEGY, PlanTaskState.DESIGN),
            *self._create_review_transitions(PlanTaskState.DESIGN, PlanTaskState.REVIEW_DESIGN, PlanTaskState.GENERATE_SUBTASKS),
            *self._create_review_transitions(PlanTaskState.GENERATE_SUBTASKS, PlanTaskState.REVIEW_PLAN, PlanTaskState.VERIFIED),
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
from src.alfred.constants import Paths, StateDescriptions

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
        return self._get_task_dir(task_id) / Paths.ARCHIVE_DIR

    def _get_scratchpad_path(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / Paths.SCRATCHPAD_FILE

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
        artifact_type_name = artifact.__class__.__name__
        template_name_snake = re.sub(r'(?<!^)(?=[A-Z])', '_', artifact_type_name).lower().replace('_artifact', '')
        
        template_path = f"artifacts/{template_name_snake}.md"

        # Use centralized state descriptions
        state_descriptions = StateDescriptions.DESCRIPTIONS

        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            logger.error(f"Could not find artifact template '{template_path}': {e}. Falling back to raw JSON.")
            # Use professional heading even in fallback
            state_desc = state_descriptions.get(state_name, "Artifact Submission")
            rendered_content = f"## {state_desc}\n\n**Task:** {task_id}\n\n```json\n{artifact.model_dump_json(indent=2)}\n```"
        else:
            
            context = {
                "task": load_task(task_id),  # Load task for context
                "state_name": state_name,  # Keep for technical reference if needed
                "state_description": state_descriptions.get(state_name, state_name),
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
# src/alfred/models/config.py
"""
Pydantic models for parsing persona configurations.
This has been simplified to only contain conversational and identity fields.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class PersonaConfig(BaseModel):
    """
    Represents the validated configuration of a single persona.yml file.
    Its sole purpose is to define the "character" and "voice" of the AI for a given tool.
    """
    name: str = Field(description="The persona's first name, e.g., 'Alex'.")
    title: str = Field(description="The persona's job title, e.g., 'Solution Architect'.")
    
    greeting: Optional[str] = Field(None, description="An example greeting the persona can use to introduce itself.")
    communication_style: Optional[str] = Field(None, description="A description of the persona's conversational style and tone.")
    
    thinking_methodology: List[str] = Field(default_factory=list, description="A list of core principles that guide the persona's reasoning.")
    personality_traits: List[str] = Field(default_factory=list, description="A list of traits that define the persona's character.")
``````
------ src/alfred/models/planning_artifacts.py ------
``````
# src/alfred/models/planning_artifacts.py
from pydantic import BaseModel, Field
from typing import List, Dict, Literal
from .schemas import Subtask


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
    operation: Literal["CREATE", "MODIFY"] = Field(description="Whether the file will be created or modified.")


class DesignArtifact(BaseModel):
    design_summary: str = Field(description="A high-level summary of the implementation design.")
    file_breakdown: List[FileChange] = Field(description="A file-by-file breakdown of all required changes.")


# The Execution Plan is a collection of Subtasks
class ExecutionPlanArtifact(BaseModel):
    subtasks: List[Subtask] = Field(description="The ordered list of Subtasks that form the execution plan")

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
    """Enumeration for the type of file system operation in a Subtask."""

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    REVIEW = "REVIEW"  # For tasks that only involve reviewing code, not changing it.


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


class Subtask(BaseModel):
    """The core, self-contained unit of work, based on the LOST framework."""

    subtask_id: str = Field(description="A unique ID for this Subtask, e.g., 'ST-1'.")
    title: str = Field(description="A short, human-readable title for the Subtask.")
    summary: Optional[str] = Field(None, description="Optional summary when title isn't sufficient to explain the changes.")

    # L: Location
    location: str = Field(description="The primary file path or directory for the work.")

    # O: Operation
    operation: OperationType = Field(description="The type of file system operation.")

    # S: Specification
    specification: List[str] = Field(description="An ordered list of procedural steps for the AI to execute.")

    # T: Test
    test: List[str] = Field(description="A list of concrete verification steps or unit tests to confirm success.")

    model_config = {"use_enum_values": True}

``````
------ src/alfred/models/state.py ------
``````
"""
Pydantic models for Alfred's state management.
"""

from datetime import datetime
from typing import Dict, Any, List
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


class WorkflowState(BaseModel):
    """
    Represents the complete state of a workflow tool.

    This model captures all necessary information to reconstruct
    a workflow tool after a crash or restart.
    """

    task_id: str
    tool_name: str
    current_state: str  # String representation of the state enum
    context_store: Dict[str, Any] = Field(default_factory=dict)
    persona_name: str
    artifact_map_states: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

``````
------ src/alfred/orchestration/__init__.py ------
``````

``````
------ src/alfred/orchestration/orchestrator.py ------
``````
# src/alfred/orchestration/orchestrator.py
"""
A simplified, central session manager for Alfred's active workflow tools.
"""
from typing import Dict
from src.alfred.config import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)

class Orchestrator:
    """
    Singleton class to manage active tool sessions.
    This class holds a dictionary of active tool instances, keyed by task_id.
    It no longer manages workflows or personas directly.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.active_tools: Dict[str, BaseWorkflowTool] = {}
        self.config_manager = ConfigManager(settings.alfred_dir)
        self._initialized = True
        logger.info("Orchestrator initialized as a simple tool session manager.")

# Global singleton instance
orchestrator = Orchestrator()
``````
------ src/alfred/orchestration/persona_loader.py ------
``````
# src/alfred/orchestration/persona_loader.py
"""
A simple utility to load a single persona configuration from a YAML file.
"""
import yaml
from pydantic import ValidationError
from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.models.config import PersonaConfig # Uses the new, simplified model

logger = get_logger(__name__)

def load_persona(persona_name: str) -> PersonaConfig:
    """
    Loads and validates a single persona YAML file.

    Args:
        persona_name: Name of the persona file (without .yml extension).

    Returns:
        A validated PersonaConfig object.

    Raises:
        FileNotFoundError: If the persona file doesn't exist.
        ValueError: If the persona file is invalid.
    """
    # First, check for a user-customized persona
    user_persona_file = settings.alfred_dir / "personas" / f"{persona_name}.yml"
    
    # Fallback to the packaged persona if user one doesn't exist
    persona_file = user_persona_file if user_persona_file.exists() else settings.packaged_personas_dir / f"{persona_name}.yml"

    if not persona_file.exists():
        raise FileNotFoundError(f"Persona config '{persona_name}.yml' not found in user or package directories.")

    try:
        with persona_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                raise ValueError(f"Persona file '{persona_file.name}' is empty.")
            
            config = PersonaConfig(**data)
            return config
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML for persona '{persona_name}': {e}")
        raise ValueError(f"Invalid YAML in '{persona_name}.yml'.") from e
    except ValidationError as e:
        logger.error(f"Validation failed for persona '{persona_name}': {e}")
        raise ValueError(f"Invalid structure in '{persona_name}.yml'.") from e
``````
------ src/alfred/personas/__init__.py ------
``````

``````
------ src/alfred/personas/planning.yml ------
``````
# src/alfred/personas/planning.yml
name: "Alex"
title: "Solution Architect"

greeting: "Hey there! I'm Alex. I'll be your solution architect for this task. My job is to help you create a rock-solid technical plan before we write any code. Let's get the ball rolling."

communication_style: "Professional yet approachable. I explain complex technical concepts in simple terms. I am proactive in identifying risks and dependencies. I focus on the 'why' behind the architecture, not just the 'what'."

thinking_methodology:
  - "Always start with the business goal and work backwards to the technical solution."
  - "Favor simplicity and clarity over unnecessary complexity."
  - "Ensure every part of the plan is testable and verifiable."
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
from src.alfred.tools.progress import mark_subtask_complete_impl

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
    into a concrete, machine-executable 'Execution Plan' composed of Subtasks.
    A Subtask (based on LOST framework) is an atomic unit of work.

    This tool manages a multi-step, interactive planning process:
    1. **Contextualize**: Deep analysis of the task requirements and codebase context
    2. **Strategize**: High-level technical approach and architecture decisions
    3. **Design**: Detailed technical design and component specifications
    4. **Generate Subtasks**: Break down into atomic, executable work units

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


@app.tool()
async def mark_subtask_complete(task_id: str, subtask_id: str) -> ToolResponse:
    """
    Marks a specific subtask as complete during the implementation phase.

    This tool is used to track progress while implementing the execution plan generated
    by the planning phase. It helps monitor which subtasks have been completed and
    calculates overall progress.

    The tool validates that:
    - An active workflow tool exists for the task
    - The subtask_id corresponds to a valid subtask in the execution plan
    - The state is properly persisted after marking completion

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")
        subtask_id (str): The subtask identifier to mark as complete (e.g., "subtask-1")

    Returns:
        ToolResponse: Success/error status with progress information including:
            - Current progress percentage
            - Number of completed vs total subtasks
            - List of remaining subtasks

    Example:
        mark_subtask_complete("TS-01", "subtask-1")
        # Returns progress update showing 1/5 subtasks complete (20%)
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "subtask_id": subtask_id}
    response = mark_subtask_complete_impl(task_id, subtask_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


if __name__ == "__main__":
    app.run()

``````
------ src/alfred/state/__init__.py ------
``````
"""
State management module for Alfred workflow tools.

This module provides persistence and recovery capabilities for workflow tools,
ensuring that task progress survives crashes and restarts.
"""

from src.alfred.state.manager import StateManager, state_manager
from src.alfred.state.recovery import ToolRecovery

__all__ = ["StateManager", "state_manager", "ToolRecovery"]

``````
------ src/alfred/state/manager.py ------
``````
"""
State management for Alfred workflow tools.

Provides atomic state persistence and recovery capabilities.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.constants import Paths

logger = get_logger(__name__)


class StateManager:
    """
    Manages persistent state for workflow tools.

    This class provides:
    - Atomic state persistence with temp file + rename
    - State recovery from disk
    - Cleanup of completed tool states
    """

    def __init__(self):
        """Initialize the state manager with the workspace directory."""
        self.state_dir = settings.alfred_dir / "workspace"

    def get_task_state_file(self, task_id: str) -> Path:
        """
        Get the state file path for a task.

        Args:
            task_id: The task identifier

        Returns:
            Path to the tool state file
        """
        return self.state_dir / task_id / Paths.TOOL_STATE_FILE

    def save_tool_state(self, task_id: str, tool: Any) -> None:
        """
        Atomically save tool state to disk.

        This method ensures state is persisted safely using a temp file
        and atomic rename operation.

        Args:
            task_id: The task identifier
            tool: The workflow tool instance to persist
        """
        logger.info(f"[STATE_MANAGER] save_tool_state called for task {task_id}")
        logger.info(f"[STATE_MANAGER] Tool info - name: {tool.tool_name}, state: {tool.state}, context_keys: {list(tool.context_store.keys())}")

        from src.alfred.models.state import WorkflowState

        # Create the state data
        # Convert any Pydantic models in context_store to dicts
        serializable_context = {}
        for key, value in tool.context_store.items():
            if hasattr(value, "model_dump"):
                # It's a Pydantic model, convert to dict
                serializable_context[key] = value.model_dump()
            else:
                serializable_context[key] = value

        state_data = WorkflowState(
            task_id=task_id,
            tool_name=tool.tool_name,
            current_state=str(tool.state),  # Convert enum to string
            context_store=serializable_context,
            persona_name=tool.persona_name,
            artifact_map_states=[str(state) for state in tool.artifact_map.keys()],
            updated_at=datetime.utcnow().isoformat(),
        )

        # Ensure directory exists
        state_file = self.get_task_state_file(task_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[STATE_MANAGER] Writing state to {state_file}")

        # Atomic write with temp file
        temp_file = state_file.with_suffix(".tmp")
        try:
            temp_file.write_text(state_data.model_dump_json(indent=2))
            temp_file.replace(state_file)
            logger.info(f"[STATE_MANAGER] Successfully saved tool state for task {task_id} in state {tool.state}")
        except Exception as e:
            logger.error(f"[STATE_MANAGER] Failed to save tool state for task {task_id}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def load_tool_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Load persisted tool state from disk.

        Args:
            task_id: The task identifier

        Returns:
            WorkflowState dict if found, None otherwise
        """
        state_file = self.get_task_state_file(task_id)
        if not state_file.exists():
            logger.debug(f"No persisted state found for task {task_id}")
            return None

        try:
            from src.alfred.models.state import WorkflowState

            state_json = state_file.read_text()
            state_data = WorkflowState.model_validate_json(state_json)
            logger.info(f"Loaded tool state for task {task_id}: {state_data.tool_name} in state {state_data.current_state}")
            return state_data.model_dump()
        except Exception as e:
            logger.error(f"Failed to load tool state for task {task_id}: {e}")
            return None

    def clear_tool_state(self, task_id: str) -> None:
        """
        Remove tool state when a workflow completes.

        Args:
            task_id: The task identifier
        """
        state_file = self.get_task_state_file(task_id)
        if state_file.exists():
            try:
                state_file.unlink()
                logger.debug(f"Cleared tool state for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to clear tool state for task {task_id}: {e}")

    def has_persisted_state(self, task_id: str) -> bool:
        """
        Check if a task has persisted state.

        Args:
            task_id: The task identifier

        Returns:
            True if state file exists, False otherwise
        """
        return self.get_task_state_file(task_id).exists()


# Singleton instance
state_manager = StateManager()

``````
------ src/alfred/state/recovery.py ------
``````
"""
Tool recovery functionality for Alfred workflow tools.

Handles reconstruction of workflow tools from persisted state after crashes or restarts.
"""

from typing import Optional, Dict, Type

from src.alfred.core.workflow import BaseWorkflowTool, PlanTaskTool
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger
from src.alfred.constants import ToolName

logger = get_logger(__name__)


class ToolRecovery:
    """
    Handles recovery of workflow tools from persisted state.

    This class provides the ability to reconstruct workflow tools
    from their persisted state after a crash or restart.
    """

    # Registry of tool types for reconstruction
    TOOL_REGISTRY: Dict[str, Type[BaseWorkflowTool]] = {
        ToolName.PLAN_TASK: PlanTaskTool,
        # Future tools will be added here as they are implemented
        # ToolName.IMPLEMENT_TASK: ImplementTaskTool,
        # "review_code": ReviewCodeTool,
    }

    @classmethod
    def recover_tool(cls, task_id: str) -> Optional[BaseWorkflowTool]:
        """
        Attempt to recover a tool from persisted state.

        This method:
        1. Loads the persisted state from disk
        2. Identifies the correct tool class
        3. Reconstructs the tool with its saved state

        Args:
            task_id: The task identifier

        Returns:
            Reconstructed tool instance if successful, None otherwise
        """
        # Load persisted state
        persisted_state = state_manager.load_tool_state(task_id)
        if not persisted_state:
            logger.debug(f"No persisted state found for task {task_id}")
            return None

        # Find the tool class
        tool_name = persisted_state.get("tool_name")
        tool_class = cls.TOOL_REGISTRY.get(tool_name)
        if not tool_class:
            logger.error(f"Unknown tool type: {tool_name}. Cannot recover.")
            return None

        try:
            # Reconstruct the tool
            tool = tool_class(task_id=task_id)

            # Restore the state
            # Convert string state back to enum if necessary
            current_state = persisted_state.get("current_state")
            if hasattr(tool_class, "get_state_from_string"):
                tool.state = tool_class.get_state_from_string(current_state)
            else:
                # Fallback: try to set directly
                tool.state = current_state

            # Restore context store
            tool.context_store = persisted_state.get("context_store", {})

            # Restore persona name
            tool.persona_name = persisted_state.get("persona_name", tool.persona_name)

            logger.info(f"Successfully recovered {tool_name} for task {task_id} in state {current_state}")
            return tool

        except Exception as e:
            logger.error(f"Failed to recover tool for task {task_id}: {e}")
            return None

    @classmethod
    def register_tool(cls, tool_name: str, tool_class: Type[BaseWorkflowTool]) -> None:
        """
        Register a new tool type for recovery.

        Args:
            tool_name: The name identifier for the tool
            tool_class: The tool class that can be instantiated
        """
        cls.TOOL_REGISTRY[tool_name] = tool_class
        logger.debug(f"Registered tool type: {tool_name}")

    @classmethod
    def can_recover(cls, task_id: str) -> bool:
        """
        Check if a task has recoverable state.

        Args:
            task_id: The task identifier

        Returns:
            True if the task can be recovered, False otherwise
        """
        if not state_manager.has_persisted_state(task_id):
            return False

        state = state_manager.load_tool_state(task_id)
        if not state:
            return False

        tool_name = state.get("tool_name")
        return tool_name in cls.TOOL_REGISTRY

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
## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Analysis Summary
{{ artifact.context_summary }}

### Affected Components
{% for file in artifact.affected_files -%}
- `{{ file }}`
{% endfor %}

### Clarification Requirements
{% for question in artifact.questions_for_developer -%}
- {{ question }}
{% endfor %}
``````
------ src/alfred/templates/artifacts/design.md ------
``````
## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Design Summary
{{ artifact.design_summary }}

### File-Level Implementation
{%- for file_change in artifact.file_breakdown %}
#### {{ file_change.file_path }} ({{ file_change.operation | upper }})
{{ file_change.change_summary }}
{% endfor %}
``````
------ src/alfred/templates/artifacts/execution_plan.md ------
``````
## Execution Plan

**Task:** {{ task.task_id }} - {{ task.title }}

Total Subtasks: **{{ artifact.subtasks | length }}**

{% for subtask in artifact.subtasks %}
### {{ subtask.subtask_id }}: {{ subtask.title }}
{% if subtask.summary -%}
**Summary**: {{ subtask.summary }}
{% endif -%}
**{{ subtask.operation }}** `{{ subtask.location }}`

Specification:
{%- for step in subtask.specification %}
- {{ step }}
{%- endfor %}

Test:
{%- for step in subtask.test %}
- {{ step }}
{%- endfor %}

{% endfor %}
``````
------ src/alfred/templates/artifacts/strategy.md ------
``````
## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Strategy Overview
{{ artifact.high_level_strategy }}

### Key Components
{%- for component in artifact.key_components %}
- {{ component }}
{%- endfor %}
{%- if artifact.new_dependencies %}

### New Dependencies
{%- for dependency in artifact.new_dependencies %}
- {{ dependency }}
{%- endfor %}
{%- endif %}
{%- if artifact.risk_analysis %}

### Risk Analysis
{{ artifact.risk_analysis }}
{%- endif %}
``````
------ src/alfred/templates/prompts/__init__.py ------
``````

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

You MUST embody this persona. **Do not use repetitive, canned phrases.** Your first message to the user should be a unique greeting based on the persona's `greeting` and `style`. For example: `{{ persona.greeting }}` (Use creative greetings each time). Adapt your language to feel like a genuine, collaborative partner.
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
------ src/alfred/templates/prompts/plan_task/generate_subtasks.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: generate_subtasks

You are transforming an approved design into a precision-engineered execution plan. Each subtask you create must be so precise, complete, and independent that any developer or AI agent could execute it in complete isolation without questions or ambiguity.

## CRITICAL MINDSET: The Isolation Principle

Imagine each subtask will be executed by a different agent who:
- Has NEVER seen the other subtasks
- Has NO access to project context beyond what you provide
- Cannot ask questions or seek clarification
- Must produce code that integrates perfectly with others' work

This forces you to be surgically precise about every detail.

## The Deep LOST Philosophy

LOST is not just a format - it's a methodology for eliminating ambiguity through systematic precision:

### **L - Location (The Context Anchor)**
The Location does more than specify a file path. It:
- **Activates Language Context**: `src/models/user.py` tells the agent "Python, likely SQLAlchemy/Django"
- **Implies Conventions**: `src/components/UserAvatar.tsx` signals "React, TypeScript, component patterns"
- **Defines Boundaries**: Precise paths prevent accidental modifications to wrong files
- **Creates Namespace**: Helps avoid naming conflicts between parallel implementations

### **O - Operation (The Precision Verb)**
Operations are not generic actions but specific engineering patterns:

**Foundation Operations** (Create structure):
- `CREATE` - Generate new file/class/module from scratch
- `DEFINE` - Establish interfaces, types, schemas (contracts for others)
- `ESTABLISH` - Set up configuration, constants, shared resources

**Implementation Operations** (Add logic):
- `IMPLEMENT` - Fill in a method/function body (structure exists)
- `INTEGRATE` - Connect components (both endpoints exist)
- `EXTEND` - Add capabilities to existing code
- `COMPOSE` - Build from smaller parts

**Modification Operations** (Change existing):
- `MODIFY` - Alter existing code behavior
- `REFACTOR` - Restructure without changing behavior
- `OPTIMIZE` - Improve performance characteristics
- `ENHANCE` - Add features to existing functionality

**Structural Operations** (Architecture changes):
- `EXTRACT` - Pull out into separate module/function
- `INJECT` - Add dependency injection
- `WRAP` - Add middleware/decorator layer
- `EXPOSE` - Make internal functionality public

### **S - Specification (The Contract)**
This is where precision becomes surgical. A specification must include:

**1. Exact Signatures** (No ambiguity):
```
"Define method authenticate(email: str, password: str) -> Union[User, None]"
NOT "Add authentication method"
```

**2. Precise Types** (Every parameter, return value):
```
"Accept config: Dict[str, Union[str, int, bool]] with keys: 'timeout' (int), 'retry' (bool)"
NOT "Accept configuration object"
```

**3. Explicit Contracts** (What it promises):
```
"Returns User object with populated 'id', 'email', 'role' fields on success, None on failure"
NOT "Returns user data"
```

**4. Clear Dependencies** (What it needs):
```
"Imports: from src.models.user import User; from src.utils.crypto import hash_password"
NOT "Uses user model and crypto utilities"
```

**5. Exact Integration Points** (How it connects):
```
"Registers route POST /api/auth/login with AuthRouter instance from src/routes/auth.py"
NOT "Adds login endpoint"
```

### **T - Test (The Proof)**
Tests must be executable commands or verifiable conditions:

**1. Concrete Execution**:
```
"Run: python -m pytest tests/test_auth.py::test_authenticate_valid -xvs"
NOT "Test authentication works"
```

**2. Specific Validation**:
```
"Verify: curl -X POST http://localhost:8000/api/auth/login -d '{"email":"test@example.com","password":"123"}' returns 401"
NOT "Check login endpoint"
```

**3. Integration Verification**:
```
"Confirm: from src.auth.handler import authenticate; result = authenticate('test@example.com', 'password'); assert result is None"
NOT "Verify function works"
```

## Handling Shared Dependencies Without Conflicts

Since subtasks execute independently, shared resources must be carefully managed:

### **1. Interface Definition Strategy**
First subtask DEFINES the interface, others IMPLEMENT/USE it:
```
Subtask-1: DEFINE UserInterface in src/types/user.ts
Subtask-2: IMPLEMENT User class matching UserInterface
Subtask-3: CREATE UserService using UserInterface
```

### **2. Configuration Constants**
One subtask ESTABLISHES shared constants, others IMPORT:
```
Subtask-1: ESTABLISH auth constants in src/config/auth.config.ts
Subtask-2: IMPLEMENT login using AUTH_CONFIG from src/config/auth.config.ts
```

### **3. Database Schema Coordination**
Define schema/migrations first, then build on them:
```
Subtask-1: CREATE migration 001_create_users_table.sql
Subtask-2: IMPLEMENT UserModel based on users table schema
```

### **4. API Contract Definition**
Define contracts before implementation:
```
Subtask-1: DEFINE OpenAPI spec in docs/api/auth.yaml
Subtask-2: IMPLEMENT endpoints matching OpenAPI spec
```

## The Subtask Creation Process

For each element in the design, follow this rigorous process:

### **Step 1: Identify Atomic Units**
Break down until you can't break down further:
- ❌ "Create authentication system" 
- ❌ "Create login endpoint with validation"
- ✅ "Define IAuthService interface"
- ✅ "Implement password hashing function"
- ✅ "Create POST /login route handler"

### **Step 2: Determine Dependencies**
Map what each atomic unit needs:
- What types/interfaces must exist?
- What configuration is required?
- What external services are called?
- What data structures are used?

### **Step 3: Order by Dependency**
Subtasks that DEFINE come before those that USE:
1. Define interfaces/types
2. Create shared utilities
3. Implement core logic
4. Add API layers
5. Create UI components

### **Step 4: Write Surgical Specifications**
For each subtask, specify:
- **Exact imports** with full paths
- **Precise signatures** with all types
- **Specific return values** with structure
- **Explicit error cases** with types
- **Clear side effects** if any

### **Step 5: Create Executable Tests**
Each test must be runnable in isolation:
- Use specific test commands
- Include test data inline
- Specify expected outputs
- Provide validation steps

## CRITICAL FORMATTING REQUIREMENTS

1. **Subtask IDs**: Use format `ST-1`, `ST-2`, etc. (NOT `subtask-1`)
2. **Summary Field**: Only include if the title doesn't fully explain the changes
3. **Compact Format**: Combine operation and location on one line
4. **Progress Reporting**: The **final step** in every specification **MUST** be:
   ```
   Call alfred.mark_subtask_complete with task_id='{{ task.task_id }}' and subtask_id='ST-X'
   ```

## Comprehensive Examples: Precision in Practice

### ❌ BAD Example - Vague and Interdependent:
```json
{
  "subtask_id": "subtask-1",
  "title": "Create user authentication",
  "location": "src/auth/",
  "operation": "CREATE",
  "specification": [
    "Create authentication system",
    "Add login and registration",
    "Handle tokens and sessions",
    "Call alfred.mark_subtask_complete with task_id='TS-01' and subtask_id='subtask-1' to report completion."
  ],
  "test": [
    "Test that users can log in",
    "Verify authentication works"
  ]
}
```
**Problems**: Wrong ID format, vague location, multiple operations hidden, no precise contracts, untestable

### ✅ GOOD Example - Define Interface First:
```json
{
  "subtask_id": "ST-1",
  "title": "Define IAuthService interface with method signatures",
  "location": "src/interfaces/auth.interface.ts",
  "operation": "CREATE",
  "specification": [
    "Create new file src/interfaces/auth.interface.ts",
    "Define TypeScript interface IAuthService with the following methods:",
    "- authenticate(email: string, password: string): Promise<AuthResult>",
    "- validateToken(token: string): Promise<TokenValidation>",
    "- refreshToken(refreshToken: string): Promise<AuthTokens>",
    "Define type AuthResult = { success: boolean; user?: User; tokens?: AuthTokens; error?: string }",
    "Define type AuthTokens = { accessToken: string; refreshToken: string; expiresIn: number }",
    "Define type TokenValidation = { valid: boolean; userId?: string; exp?: number }",
    "Export all interfaces and types",
    "Add JSDoc comments for each method describing parameters and return values",
    "Call alfred.mark_subtask_complete with task_id='{{ task.task_id }}' and subtask_id='ST-1' to report completion."
  ],
  "test": [
    "File src/interfaces/auth.interface.ts exists",
    "Run: npx tsc src/interfaces/auth.interface.ts --noEmit (should compile without errors)",
    "Verify interface has all three methods with correct signatures",
    "Run: grep -E '(authenticate|validateToken|refreshToken)' src/interfaces/auth.interface.ts | wc -l (should output: 3)"
  ]
}
```

### ✅ GOOD Example - Implement with Precision:
```json
{
  "subtask_id": "ST-2", 
  "title": "Implement password hashing utility using bcrypt",
  "location": "src/utils/crypto.ts",
  "operation": "CREATE",
  "specification": [
    "Create new file src/utils/crypto.ts",
    "Add imports: import * as bcrypt from 'bcrypt'",
    "Define constant SALT_ROUNDS = 10",
    "Implement async function hashPassword(plainPassword: string): Promise<string>",
    "- Validate plainPassword is non-empty string, throw Error('Password cannot be empty') if not",
    "- Use bcrypt.hash(plainPassword, SALT_ROUNDS) to generate hash",
    "- Return the hashed password string",
    "Implement async function verifyPassword(plainPassword: string, hashedPassword: string): Promise<boolean>",
    "- Validate both parameters are non-empty strings",
    "- Use bcrypt.compare(plainPassword, hashedPassword)",
    "- Return boolean result",
    "Export both functions as named exports",
    "Call alfred.mark_subtask_complete with task_id='{{ task.task_id }}' and subtask_id='ST-2' to report completion."
  ],
  "test": [
    "File src/utils/crypto.ts exists",
    "Run: npm install --save bcrypt @types/bcrypt (ensure dependencies are installed)",
    "Run: npx ts-node -e \"import { hashPassword, verifyPassword } from './src/utils/crypto'; (async () => { const hash = await hashPassword('test123'); console.log(hash.length > 20 ? 'PASS' : 'FAIL'); })()\"",
    "Run: npx ts-node -e \"import { hashPassword, verifyPassword } from './src/utils/crypto'; (async () => { const hash = await hashPassword('test123'); const valid = await verifyPassword('test123', hash); console.log(valid ? 'PASS' : 'FAIL'); })()\"",
    "Verify error handling: npx ts-node -e \"import { hashPassword } from './src/utils/crypto'; hashPassword('').catch(e => console.log(e.message))\" (should output: 'Password cannot be empty')"
  ]
}
```

### ✅ GOOD Example - Integration with Dependencies:
```json
{
  "subtask_id": "ST-3",
  "title": "Create POST /api/auth/login endpoint handler",
  "summary": "Add login endpoint that validates credentials and returns JWT tokens on success",
  "location": "src/routes/auth.routes.ts", 
  "operation": "MODIFY",
  "specification": [
    "Locate the existing Express router instance in src/routes/auth.routes.ts",
    "Add imports at the top of the file:",
    "- import { IAuthService } from '../interfaces/auth.interface'",
    "- import { authService } from '../services/auth.service'",
    "- import { validateLoginRequest } from '../validators/auth.validator'",
    "Add new POST route handler: router.post('/login', async (req, res, next) => { ... })",
    "Inside the handler, implement the following logic:",
    "1. Extract { email, password } from req.body",
    "2. Call validateLoginRequest(email, password) - if validation fails, return res.status(400).json({ error: validation.error })",
    "3. Call const result = await authService.authenticate(email, password)",
    "4. If result.success is false, return res.status(401).json({ error: result.error || 'Invalid credentials' })",
    "5. If result.success is true, return res.status(200).json({ user: result.user, tokens: result.tokens })",
    "6. Wrap entire handler body in try-catch, on error call next(error)",
    "Call alfred.mark_subtask_complete with task_id='{{ task.task_id }}' and subtask_id='ST-3' to report completion."
  ],
  "test": [
    "Verify route exists: grep -E \"router\\.post\\(['\\\"]?\\/login\" src/routes/auth.routes.ts",
    "Run integration test: npm test -- tests/integration/auth.test.ts -t 'POST /api/auth/login'",
    "Test valid login: curl -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"password123\"}' (should return 200)",
    "Test invalid login: curl -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\",\"password\":\"wrong\"}' (should return 401)",
    "Test validation: curl -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"invalid-email\"}' (should return 400)"
  ]
}
```

## Common Anti-Patterns to Avoid

### ❌ **The Kitchen Sink**
Trying to do too much in one subtask:
- "Create user service with all CRUD operations"
- "Implement complete authentication flow"

### ❌ **The Mind Reader**
Assuming context not provided:
- "Update the validation logic" (which validation? where?)
- "Fix the bug in authentication" (what bug? what's broken?)

### ❌ **The Handwave**
Being vague about specifications:
- "Handle errors appropriately"
- "Add proper validation"
- "Implement according to best practices"

### ❌ **The Dependency Nightmare**
Creating circular or unclear dependencies:
- Subtask A needs output from Subtask B
- Subtask B needs output from Subtask A

## Patterns for Success

### ✅ **The Contract-First Pattern**
1. Define all interfaces/types first
2. Create shared configurations
3. Implement concrete classes
4. Add integration layers
5. Build UI on top

### ✅ **The Test-Driven Pattern**
Each subtask's test is a contract:
- Test can be written before implementation
- Test is specific and executable
- Test validates the contract, not implementation

### ✅ **The Isolation Pattern**
Each subtask includes:
- All necessary imports (with paths)
- All required types (inline or imported)
- All configuration values (explicit)
- All error messages (exact text)

**Approved Design:**
```json
{{ additional_context.design_artifact | tojson(indent=2) }}
```

---
### **Your Mission**

Transform the approved design into subtasks that are:
1. **Atomic** - One indivisible action each
2. **Independent** - Executable in complete isolation
3. **Precise** - No room for interpretation
4. **Verifiable** - Clear pass/fail conditions
5. **Complete** - When all done, the feature works perfectly

Remember: You are writing instructions for agents who know nothing about the project except what you tell them. Every detail matters.

---
### **Required Action**

Call `alfred.submit_work` with an artifact containing your ExecutionPlan:

```json
{
  "subtasks": [
    {
      "subtask_id": "ST-1",
      "title": "Precise description of atomic work",
      "summary": "Optional extended description if title isn't sufficient",
      "location": "exact/path/to/file.ext",
      "operation": "PRECISE_VERB",
      "specification": [
        "Exact step 1 with all details",
        "Exact step 2 with types and signatures",
        "...",
        "Call alfred.mark_subtask_complete with task_id='{{ task.task_id }}' and subtask_id='ST-1' to report completion."
      ],
      "test": [
        "Executable verification command 1",
        "Specific validation step 2",
        "Edge case verification 3"
      ]
    }
  ]
}
```

Generate subtasks now, with surgical precision.

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
{% set artifact = additional_context.artifact_content | fromjson %}
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

Review the generated `list[Subtask]` against the original `Task` context.

**Review Checklist:**
1. **Coverage:** Is every `acceptance_criterion` from the original task fully addressed by the combination of all Subtasks?
2. **Completeness:** Is the plan comprehensive? Are there any missing steps or logical gaps between Subtasks?
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
        return ToolResponse(status="success", message=f"Project already initialized at '{alfred_dir}'. No changes were made.")

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
        config = AlfredConfig(providers=ProviderConfig(task_provider=TaskProvider(provider_choice)))
        config_manager.save(config)

        # Setup provider-specific resources
        _setup_provider_resources(provider_choice, alfred_dir)

        return ToolResponse(status="success", message=f"Successfully initialized Alfred project in '{alfred_dir}' with {provider_choice} provider.")

    except (OSError, shutil.Error) as e:
        return ToolResponse(status="error", message=f"Failed to initialize project due to a file system error: {e}")


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
import json
from typing import Optional
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.core.workflow import PlanTaskTool, PlanTaskState
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import setup_task_logging, get_logger
from src.alfred.state.recovery import ToolRecovery
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


def _get_previous_state(current_state: str) -> Optional[str]:
    """Helper to get the previous state for a review state"""
    state_map = {"review_context": "contextualize", "review_strategy": "strategize", "review_design": "design", "review_plan": "generate_subtasks"}
    return state_map.get(current_state)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """
    Implementation logic for the plan_task tool.

    This implementation includes recovery capability - if the tool
    crashes mid-workflow, it can be recovered from persisted state.
    """
    # Setup logging for this task
    setup_task_logging(task_id)

    # Check if tool already exists in memory
    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
    else:
        # Try to recover from disk
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            # No existing tool - create new one
            task = load_task(task_id)
            if not task:
                return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

            # Check preconditions for new planning
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' task or resume a 'planning' task.")

            # Create new tool instance
            tool_instance = PlanTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance

            # Update task status to planning
            if task.task_status == TaskStatus.NEW:
                update_task_status(task_id, TaskStatus.PLANNING)

            # Save initial state
            state_manager.save_tool_state(task_id, tool_instance)
            logger.info(f"Created new planning tool for task {task_id}")

    # Load persona config
    try:
        persona_config = load_persona(tool_instance.persona_name or "planning")
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    # Reload task to get latest state
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # Generate appropriate prompt for current state
    logger.info(f"[PLAN_TASK] Generating prompt for state: {tool_instance.state}")
    logger.info(f"[PLAN_TASK] Context store keys: {list(tool_instance.context_store.keys())}")

    # Prepare context for prompt generation
    prompt_context = tool_instance.context_store.copy()

    # For review states, ensure artifact_content is available
    if "review" in tool_instance.state and "artifact_content" not in prompt_context:
        # Try to reconstruct artifact_content from the previous state's artifact
        prev_state = _get_previous_state(tool_instance.state)
        if prev_state:
            # Map state names to cleaner artifact names (same as in submit_work)
            artifact_name_map = {"contextualize": "context", "strategize": "strategy", "design": "design", "generate_subtasks": "execution_plan"}

            # Try both naming conventions for backward compatibility
            artifact_name = artifact_name_map.get(prev_state, prev_state)
            artifact_key = f"{artifact_name}_artifact"
            old_artifact_key = f"{prev_state}_artifact"

            # Check both keys
            if artifact_key in prompt_context:
                artifact_data = prompt_context[artifact_key]
            elif old_artifact_key in prompt_context:
                artifact_data = prompt_context[old_artifact_key]
            else:
                artifact_data = None

            if artifact_data:
                # Handle both dict and Pydantic model
                if hasattr(artifact_data, "model_dump"):
                    artifact_dict = artifact_data.model_dump()
                else:
                    artifact_dict = artifact_data
                prompt_context["artifact_content"] = json.dumps(artifact_dict, indent=2)
                logger.info(f"[PLAN_TASK] Reconstructed artifact_content from artifact")

    prompt = prompter.generate_prompt(task=task, tool_name=tool_instance.tool_name, state=tool_instance.state, persona_config=persona_config, additional_context=prompt_context)

    # Determine appropriate message based on whether we're resuming
    if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value:
        message = f"Planning initiated for task '{task_id}'."
    else:
        message = f"Resumed planning for task '{task_id}' from state '{tool_instance.state}'."

    return ToolResponse(status="success", message=message, next_prompt=prompt)

``````
------ src/alfred/tools/progress.py ------
``````
# src/alfred/tools/progress.py
"""
Progress tracking tools for Alfred workflow system.

Provides functionality to track subtask completion during implementation phase.
"""

from typing import Set

from src.alfred.lib.logger import get_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.core.workflow import BaseWorkflowTool

logger = get_logger(__name__)


def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """
    Marks a specific subtask as complete during the implementation phase.

    This function:
    1. Verifies an active tool exists for the task
    2. Checks if the subtask_id is valid for the current execution plan
    3. Tracks completed subtasks in the tool's context_store
    4. Persists the updated state

    Args:
        task_id: The unique identifier for the task
        subtask_id: The subtask identifier to mark as complete (e.g., "subtask-1")

    Returns:
        ToolResponse: Success/error status with appropriate message
    """
    # Check if there's an active tool for this task
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'. Cannot mark subtask complete.")

    active_tool = orchestrator.active_tools[task_id]

    # Get the execution plan from context store if available
    execution_plan = active_tool.context_store.get("execution_plan_artifact")
    if not execution_plan:
        # Try alternative key names
        execution_plan = active_tool.context_store.get("generate_subtasks_artifact")

    if not execution_plan:
        return ToolResponse(status="error", message="No execution plan found in the active tool's context. Cannot validate subtask.")

    # Validate the subtask_id exists in the execution plan
    valid_subtask_ids = {subtask.subtask_id for subtask in execution_plan.subtasks}
    if subtask_id not in valid_subtask_ids:
        return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'. Valid subtask IDs are: {', '.join(sorted(valid_subtask_ids))}")

    # Initialize completed_subtasks set if it doesn't exist
    if "completed_subtasks" not in active_tool.context_store:
        active_tool.context_store["completed_subtasks"] = set()

    # Ensure completed_subtasks is a set (handle deserialization from JSON)
    completed_subtasks = active_tool.context_store["completed_subtasks"]
    if isinstance(completed_subtasks, list):
        completed_subtasks = set(completed_subtasks)
        active_tool.context_store["completed_subtasks"] = completed_subtasks

    # Check if already marked complete
    if subtask_id in completed_subtasks:
        return ToolResponse(status="success", message=f"Subtask '{subtask_id}' was already marked as complete.")

    # Mark the subtask as complete
    completed_subtasks.add(subtask_id)

    # Calculate progress
    total_subtasks = len(valid_subtask_ids)
    completed_count = len(completed_subtasks)
    progress_percentage = (completed_count / total_subtasks) * 100

    # Save the updated state
    try:
        state_manager.save_tool_state(task_id, active_tool)
        logger.info(f"Task {task_id}: Marked subtask '{subtask_id}' as complete. Progress: {completed_count}/{total_subtasks} ({progress_percentage:.1f}%)")

        # Build progress summary
        remaining_subtasks = valid_subtask_ids - completed_subtasks
        progress_message = f"Successfully marked subtask '{subtask_id}' as complete.\n\nProgress: {completed_count}/{total_subtasks} subtasks completed ({progress_percentage:.1f}%)\n"

        if remaining_subtasks:
            progress_message += f"Remaining subtasks: {', '.join(sorted(remaining_subtasks))}"
        else:
            progress_message += "All subtasks completed! 🎉"

        return ToolResponse(
            status="success",
            message=progress_message,
            data={
                "completed_count": completed_count,
                "total_count": total_subtasks,
                "progress_percentage": progress_percentage,
                "completed_subtasks": sorted(list(completed_subtasks)),
                "remaining_subtasks": sorted(list(remaining_subtasks)),
            },
        )

    except Exception as e:
        logger.error(f"Failed to save progress for task {task_id}: {e}")
        # Remove the subtask from completed set since save failed
        completed_subtasks.discard(subtask_id)

        return ToolResponse(status="error", message=f"Failed to save progress: {str(e)}")

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
from src.alfred.state.manager import state_manager
from src.alfred.constants import ToolName, Paths, PlanTaskStates, ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Processes review feedback, advancing the active tool's State Machine.
    Handles both mid-workflow reviews and final tool completion.

    IMPORTANT: This implementation uses atomic state transitions to prevent
    state corruption if prompt generation fails.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id))

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.TASK_NOT_FOUND.format(task_id=task_id))

    # Determine the trigger
    trigger = Triggers.AI_APPROVE if is_approved else Triggers.REQUEST_REVISION
    if not hasattr(active_tool, trigger):
        return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot trigger '{trigger}' from state '{active_tool.state}'.")

    # Save current state for potential rollback
    original_state = active_tool.state
    original_context = active_tool.context_store.copy()

    try:
        # PHASE 1: Prepare everything that could fail
        # Calculate what the next state will be
        next_transitions = active_tool.machine.get_transitions(source=active_tool.state, trigger=trigger)
        if not next_transitions:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger}' from state '{active_tool.state}'.")

        next_state = next_transitions[0].dest

        # Check if the next state will be terminal
        will_be_terminal = next_state == PlanTaskStates.VERIFIED

        if will_be_terminal:
            # Prepare completion logic
            final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
            handoff_message = (
                f"Planning for task {task_id} is complete and verified. The task is now '{final_task_status.value}'.\n\nTo begin implementation, run `alfred.implement_task(task_id='{task_id}')`."
            )
            next_prompt = handoff_message
        else:
            # Prepare mid-workflow logic
            try:
                persona_config = load_persona(active_tool.persona_name)
            except FileNotFoundError as e:
                return ToolResponse(status=ResponseStatus.ERROR, message=str(e))

            # Always provide feedback_notes in additional_context
            additional_context = {}
            # Convert any Pydantic models to dicts
            for key, value in active_tool.context_store.items():
                if hasattr(value, "model_dump"):
                    additional_context[key] = value.model_dump()
                else:
                    additional_context[key] = value
            additional_context["feedback_notes"] = feedback_notes or ""

            # Generate prompt for the NEXT state (most likely to fail)
            next_prompt = prompter.generate_prompt(
                task=task,
                tool_name=active_tool.tool_name,
                state=next_state,  # Use the calculated next state
                persona_config=persona_config,
                additional_context=additional_context,
            )

        # PHASE 2: Commit - only if everything succeeded
        # Now do the actual state transition
        getattr(active_tool, trigger)()
        logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))

        # Persist the new state immediately
        state_manager.save_tool_state(task_id, active_tool)

        # Save execution plan JSON if we just approved the plan
        if (
            active_tool.tool_name == ToolName.PLAN_TASK
            and original_state == PlanTaskStates.REVIEW_PLAN
            and is_approved
            and ArtifactKeys.get_artifact_key(PlanTaskStates.GENERATE_SUBTASKS) in active_tool.context_store
        ):
            try:
                import json
                from pathlib import Path
                from src.alfred.config.settings import settings

                logger.info(f"Attempting to save execution plan for task {task_id}")
                logger.info(f"Context store keys: {list(active_tool.context_store.keys())}")

                # Create workspace directory if it doesn't exist
                workspace_dir = settings.alfred_dir / Paths.WORKSPACE_DIR / task_id
                workspace_dir.mkdir(parents=True, exist_ok=True)

                # Save execution plan as JSON
                execution_plan_path = workspace_dir / Paths.EXECUTION_PLAN_FILE
                artifact_key = ArtifactKeys.get_artifact_key(PlanTaskStates.GENERATE_SUBTASKS)
                execution_plan = active_tool.context_store[artifact_key]

                # Convert Pydantic model to dict
                plan_dict = execution_plan.model_dump() if hasattr(execution_plan, "model_dump") else execution_plan

                with open(execution_plan_path, "w") as f:
                    json.dump(plan_dict, f, indent=2)

                logger.info(LogMessages.EXECUTION_PLAN_SAVED.format(path=execution_plan_path))
            except Exception as e:
                logger.error(LogMessages.EXECUTION_PLAN_SAVE_FAILED.format(error=e), exc_info=True)
                # Don't fail the review if we can't save the JSON

        # Handle terminal state cleanup
        if active_tool.is_terminal:
            update_task_status(task_id, final_task_status)
            state_manager.clear_tool_state(task_id)  # Clean up persisted state
            del orchestrator.active_tools[task_id]
            cleanup_task_logging(task_id)
            logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")

            return ToolResponse(status=ResponseStatus.SUCCESS, message=f"Tool '{active_tool.tool_name}' completed successfully.", next_prompt=next_prompt)
        else:
            message = "Review approved. Proceeding to next step." if is_approved else "Revision requested."
            return ToolResponse(status=ResponseStatus.SUCCESS, message=message, next_prompt=next_prompt)

    except Exception as e:
        # Rollback on any failure
        logger.error(f"State transition failed for task {task_id}: {e}")
        active_tool.state = original_state
        active_tool.context_store = original_context

        # Save the rolled-back state
        try:
            state_manager.save_tool_state(task_id, active_tool)
        except:
            pass  # Don't fail the error response if state save fails

        return ToolResponse(status=ResponseStatus.ERROR, message=f"Failed to process review: {str(e)}")

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
from src.alfred.state.manager import state_manager
from src.alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """
    Implements the logic for submitting a work artifact to the active tool.

    IMPORTANT: This implementation uses atomic state transitions to prevent
    state corruption if any operation fails.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.TASK_NOT_FOUND.format(task_id=task_id))

    # Save current state for potential rollback
    original_state = active_tool.state
    original_context = active_tool.context_store.copy()

    try:
        # PHASE 1: Prepare - validate and prepare everything that could fail

        # Artifact Validation
        current_state = active_tool.state
        artifact_model = active_tool.artifact_map.get(current_state)

        if artifact_model:
            # Normalize operation values to uppercase for consistency
            if artifact_model.__name__ == "ExecutionPlanArtifact" and "subtasks" in artifact:
                # Normalize Subtask operation values
                for subtask in artifact["subtasks"]:
                    if "operation" in subtask and isinstance(subtask["operation"], str):
                        subtask["operation"] = subtask["operation"].upper()
            elif artifact_model.__name__ == "DesignArtifact" and "file_breakdown" in artifact:
                # Normalize FileChange operation values
                for file_change in artifact["file_breakdown"]:
                    if "operation" in file_change and isinstance(file_change["operation"], str):
                        file_change["operation"] = file_change["operation"].upper()

            try:
                # Validate the submitted dictionary against the Pydantic model
                validated_artifact = artifact_model.model_validate(artifact)
                logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state.value if hasattr(current_state, "value") else current_state, model=artifact_model.__name__))
            except ValidationError as e:
                error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state.value if hasattr(current_state, 'value') else current_state)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
                return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
        else:
            validated_artifact = artifact  # No validator for this state, proceed

        # Load persona config (used for both persistence and prompt generation)
        try:
            persona_config = load_persona(active_tool.persona_name)
        except FileNotFoundError as e:
            return ToolResponse(status=ResponseStatus.ERROR, message=str(e))

        # Calculate next state
        current_state_val = active_tool.state.value if hasattr(active_tool.state, "value") else active_tool.state
        trigger = Triggers.submit_trigger(current_state_val)

        if not hasattr(active_tool, trigger):
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")

        # Get the next state
        next_transitions = active_tool.machine.get_transitions(source=active_tool.state, trigger=trigger)
        if not next_transitions:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger}' from state '{active_tool.state}'.")
        next_state = next_transitions[0].dest

        # Prepare additional context for prompt generation
        temp_context = active_tool.context_store.copy()

        # Use the centralized artifact key generation
        artifact_key = ArtifactKeys.get_artifact_key(current_state_val)

        temp_context[artifact_key] = validated_artifact
        temp_context[ArtifactKeys.ARTIFACT_CONTENT_KEY] = json.dumps(artifact, indent=2)

        # Generate prompt for the NEXT state (most likely to fail)
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=next_state,  # Use calculated next state
            persona_config=persona_config,
            additional_context=temp_context,
        )

        # PHASE 2: Commit - only if everything succeeded

        # Store validated artifact in the tool's context using the same clean name
        active_tool.context_store[artifact_key] = validated_artifact
        # Convert Pydantic model to dict for JSON serialization
        artifact_dict = validated_artifact.model_dump() if hasattr(validated_artifact, "model_dump") else validated_artifact
        active_tool.context_store[ArtifactKeys.ARTIFACT_CONTENT_KEY] = json.dumps(artifact_dict, indent=2)
        logger.info(f"Stored artifact in context_store with key '{artifact_key}' and {ArtifactKeys.ARTIFACT_CONTENT_KEY}.")

        # Persist artifact to scratchpad
        artifact_manager.append_to_scratchpad(task_id=task_id, state_name=current_state_val, artifact=validated_artifact, persona_config=persona_config)

        # Trigger the state transition
        getattr(active_tool, trigger)()
        logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))

        # Persist the new state immediately
        state_manager.save_tool_state(task_id, active_tool)

        return ToolResponse(status=ResponseStatus.SUCCESS, message="Work submitted. Awaiting review.", next_prompt=next_prompt)

    except Exception as e:
        # Rollback on any failure
        logger.error(f"Work submission failed for task {task_id}: {e}")
        active_tool.state = original_state
        active_tool.context_store = original_context

        # Save the rolled-back state
        try:
            state_manager.save_tool_state(task_id, active_tool)
        except:
            pass  # Don't fail the error response if state save fails

        return ToolResponse(status=ResponseStatus.ERROR, message=f"Failed to submit work: {str(e)}")

``````
