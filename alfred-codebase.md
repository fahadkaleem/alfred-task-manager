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

    START_TASK: Final[str] = "start_task"
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
------ src/alfred/core/context_builder.py ------
``````
# src/alfred/core/context_builder.py
"""
Context assembly for template rendering during state transitions.

This module ensures proper context is built for both forward progression
and backward revision flows in the feedback loop.
"""
from typing import Dict, Any, Optional
from src.alfred.constants import ArtifactKeys
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """Builds proper context for template rendering based on state transitions."""
    
    @staticmethod
    def build_feedback_context(tool: Any, state: str, feedback_notes: str) -> Dict[str, Any]:
        """
        Build context when returning to a work state with feedback.
        
        This ensures the rejected artifact is available under the correct key
        for the destination state's template to render properly.
        
        Args:
            tool: The active workflow tool instance
            state: The destination state (work state we're returning to)
            feedback_notes: The feedback from the reviewer
            
        Returns:
            Dictionary with complete context for template rendering
        """
        context = tool.context_store.copy()
        context["feedback_notes"] = feedback_notes
        
        # Get the expected artifact key for this state
        artifact_key = ArtifactKeys.get_artifact_key(state)
        logger.debug(f"Building feedback context for state '{state}', expecting artifact key '{artifact_key}'")
        
        # Ensure artifact is available with expected key
        if artifact_key not in context:
            logger.warning(f"Artifact key '{artifact_key}' not found in context, searching for recent artifact")
            
            # Find the most recent artifact from any state
            artifact_found = False
            for key, value in tool.context_store.items():
                if key.endswith("_artifact") and value is not None:
                    logger.info(f"Found artifact under key '{key}', copying to '{artifact_key}'")
                    context[artifact_key] = value
                    artifact_found = True
                    break
            
            if not artifact_found:
                logger.error(f"No artifact found in context_store for feedback loop")
        else:
            logger.debug(f"Artifact already available under key '{artifact_key}'")
        
        # Log final context keys for debugging
        logger.debug(f"Final context keys: {list(context.keys())}")
        logger.debug(f"Feedback notes (first 100 chars): {feedback_notes[:100]}")
        
        return context
    
    @staticmethod
    def build_review_context(tool: Any, artifact: Any) -> Dict[str, Any]:
        """
        Build context for review states (AI/Human review).
        
        Args:
            tool: The active workflow tool instance
            artifact: The artifact just submitted
            
        Returns:
            Dictionary with context for review template rendering
        """
        context = tool.context_store.copy()
        
        # Review states expect artifact under 'artifact_content' key
        if hasattr(artifact, 'model_dump'):
            context["artifact_content"] = artifact.model_dump()
        else:
            context["artifact_content"] = artifact
            
        logger.debug(f"Built review context with artifact_content")
        
        return context
    
    @staticmethod
    def build_standard_context(tool: Any) -> Dict[str, Any]:
        """
        Build standard context for forward progression.
        
        Args:
            tool: The active workflow tool instance
            
        Returns:
            Copy of the tool's context_store
        """
        return tool.context_store.copy()
``````
------ src/alfred/core/prompter.py ------
``````
# src/alfred/core/prompter.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Optional
import json
from pydantic import BaseModel

from src.alfred.config.settings import settings
from src.alfred.models.schemas import Task
from src.alfred.constants import TemplatePaths
from src.alfred.lib.logger import get_logger
from src.alfred.models.config import PersonaConfig

logger = get_logger(__name__)


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
        self.jinja_env.filters["tojson"] = self._pydantic_safe_tojson
    
    def _pydantic_safe_tojson(self, obj, indent=2):
        """Custom JSON filter that handles Pydantic models"""
        if isinstance(obj, BaseModel):
            return json.dumps(obj.model_dump(), indent=indent)
        return json.dumps(obj, indent=indent)

    def generate_prompt(
        self,
        task: Task,
        tool_name: str,
        state,  # Can be Enum or str
        persona_config: PersonaConfig,  # CHANGE THIS: No longer a Dict, it's the Pydantic object
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a prompt by rendering a template with the given context.

        Args:
            task: The full structured Task object.
            tool_name: The name of the active tool (e.g., 'plan_task').
            state: The current state from the tool's SM (Enum or str).
            persona_config: The PersonaConfig Pydantic object for the tool's persona.
            additional_context: Ad-hoc data like review feedback.

        Returns:
            The rendered prompt string.
        """
        # Handle both Enum and string state values
        state_value = state.value if hasattr(state, "value") else state
        template_path = TemplatePaths.PROMPT_PATTERN.format(tool_name=tool_name, state=state_value)
        
        logger.info(f"[PROMPTER] Generating prompt for tool='{tool_name}', state='{state_value}'")
        logger.info(f"[PROMPTER] Additional context keys: {list(additional_context.keys()) if additional_context else 'None'}")

        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            # Proper error handling is crucial
            error_message = f"CRITICAL ERROR: Prompt template not found at '{template_path}'. Details: {e}"
            logger.error(error_message)
            return error_message

        # Build the comprehensive context for the template
        render_context = {
            "task": task,
            "tool_name": tool_name,
            "state": state_value,
            "persona": persona_config,  # Pass the object directly
            "additional_context": additional_context or {},
        }
        
        # AL-11: Simplified logic, as we now always have the Pydantic object
        ai_config = persona_config.ai
        
        # Get state-specific analysis patterns
        analysis_patterns = ai_config.analysis_patterns.get(state_value, [])
        validation_criteria = ai_config.validation_criteria.get(state_value, [])
        
        # Inject AI directives into context
        render_context["ai_directives"] = {
            "style": ai_config.style,
            "analysis_patterns": analysis_patterns,
            "validation_criteria": validation_criteria,
        }
        
        logger.info(f"[PROMPTER] AL-11: Injecting AI directives for state '{state_value}'")
        logger.info(f"[PROMPTER] AL-11: Analysis patterns count: {len(analysis_patterns)}")
        logger.info(f"[PROMPTER] AL-11: Validation criteria count: {len(validation_criteria)}")
        
        # Log important context details for debugging
        if additional_context and "feedback_notes" in additional_context:
            logger.info(f"[PROMPTER DEBUG] Feedback notes present (first 100 chars): {additional_context['feedback_notes'][:100]}")
        if additional_context:
            artifact_keys = [k for k in additional_context.keys() if k.endswith("_artifact")]
            if artifact_keys:
                logger.info(f"[PROMPTER DEBUG] Artifact keys in context: {artifact_keys}")
        
        # Log what's being passed to template
        logger.info(f"[PROMPTER DEBUG] Rendering template with additional_context keys: {list(additional_context.keys()) if additional_context else 'None'}")
        
        rendered = template.render(render_context)
        
        # Check if feedback section was rendered
        if additional_context and "feedback_notes" in additional_context:
            if "Building on Your Previous Analysis" in rendered:
                logger.info("[PROMPTER DEBUG] Feedback section successfully rendered in template")
            else:
                logger.warning("[PROMPTER DEBUG] Feedback section NOT rendered despite feedback_notes present!")
        
        return rendered


# Singleton instance to be used across the application
prompter = Prompter()

``````
------ src/alfred/core/workflow.py ------
``````
# src/alfred/core/workflow.py
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from transitions.core import Machine

from src.alfred.constants import ToolName, Triggers
from src.alfred.models.planning_artifacts import (
    BranchCreationArtifact,
    ContextAnalysisArtifact,
    DesignArtifact,
    ExecutionPlanArtifact,
    GitStatusArtifact,
    StrategyArtifact,
)


class ReviewState(str, Enum):
    AWAITING_AI_REVIEW = "awaiting_ai_review"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"


class PlanTaskState(str, Enum):
    CONTEXTUALIZE = "contextualize"
    STRATEGIZE = "strategize"
    DESIGN = "design"
    GENERATE_SUBTASKS = "generate_subtasks"
    VERIFIED = "verified"


class StartTaskState(str, Enum):
    """A leaner, more logical state model for StartTaskTool."""
    AWAITING_GIT_STATUS = "awaiting_git_status"
    AWAITING_BRANCH_CREATION = "awaiting_branch_creation"
    VERIFIED = "verified"


class BaseWorkflowTool:
    def __init__(self, task_id: str, tool_name: str, persona_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.persona_name = persona_name
        self.state: Optional[str] = None
        self.machine: Optional[Machine] = None
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}
        self.context_store: Dict[str, Any] = {}

    @property
    def is_terminal(self) -> bool:
        return self.state == "verified"

    def _create_review_transitions(self, source_state: str, success_destination_state: str) -> List[Dict[str, Any]]:
        return [
            {"trigger": Triggers.submit_trigger(source_state), "source": source_state, "dest": ReviewState.AWAITING_AI_REVIEW.value},
            {"trigger": "ai_approve", "source": ReviewState.AWAITING_AI_REVIEW.value, "dest": ReviewState.AWAITING_HUMAN_REVIEW.value},
            {"trigger": "request_revision", "source": ReviewState.AWAITING_AI_REVIEW.value, "dest": source_state},
            {"trigger": "human_approve", "source": ReviewState.AWAITING_HUMAN_REVIEW.value, "dest": success_destination_state},
            {"trigger": "request_revision", "source": ReviewState.AWAITING_HUMAN_REVIEW.value, "dest": source_state},
        ]


class PlanTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str, persona_name: str = "planning"):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK, persona_name=persona_name)
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }
        states = [state.value for state in PlanTaskState] + [state.value for state in ReviewState]
        transitions = [
            *self._create_review_transitions(PlanTaskState.CONTEXTUALIZE.value, PlanTaskState.STRATEGIZE.value),
            *self._create_review_transitions(PlanTaskState.STRATEGIZE.value, PlanTaskState.DESIGN.value),
            *self._create_review_transitions(PlanTaskState.DESIGN.value, PlanTaskState.GENERATE_SUBTASKS.value),
            *self._create_review_transitions(PlanTaskState.GENERATE_SUBTASKS.value, PlanTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=PlanTaskState.CONTEXTUALIZE.value)


class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""
    def __init__(self, task_id: str, persona_name: str = "onboarding"):
        super().__init__(task_id, tool_name=ToolName.START_TASK, persona_name=persona_name)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }
        states = [state.value for state in StartTaskState] + [state.value for state in ReviewState]
        transitions = [
            # 1. User submits Git Status. After review, success moves to AWAITING_BRANCH_CREATION.
            *self._create_review_transitions(StartTaskState.AWAITING_GIT_STATUS.value, StartTaskState.AWAITING_BRANCH_CREATION.value),
            # 2. User submits Branch Creation result. After review, success moves to VERIFIED (terminal).
            *self._create_review_transitions(StartTaskState.AWAITING_BRANCH_CREATION.value, StartTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=StartTaskState.AWAITING_GIT_STATUS.value)
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
            # Handle both Pydantic models and plain dicts
            if hasattr(artifact, 'model_dump_json'):
                artifact_json = artifact.model_dump_json(indent=2)
            else:
                artifact_json = json.dumps(artifact, indent=2)
            rendered_content = f"## {state_desc}\n\n**Task:** {task_id}\n\n```json\n{artifact_json}\n```"
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
from pathlib import Path
from typing import Optional

from src.alfred.models.schemas import Task
from src.alfred.state.manager import state_manager

from .md_parser import MarkdownTaskParser
from src.alfred.config.settings import settings


def load_task(task_id: str, root_dir: Optional[Path] = None) -> Task | None:
    """
    Loads a Task by parsing its .md file and merging with its unified state.

    Args:
        task_id: The ID of the task to load
        root_dir: Optional root directory to use instead of default settings
    """
    alfred_dir = (
        root_dir / settings.alfred_dir_name if root_dir else settings.alfred_dir
    )
    task_md_path = alfred_dir / "tasks" / f"{task_id}.md"

    if not task_md_path.exists():
        return None

    parser = MarkdownTaskParser()
    task_data = parser.parse(task_md_path.read_text())
    task_model = Task(**task_data)

    # Load the dynamic state from the unified state file
    unified_state = state_manager.load_or_create_task_state(task_id)
    task_model.task_status = unified_state.task_status

    return task_model
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
    autonomous_mode: bool = Field(default=False, description="Enable autonomous mode to bypass human review steps.")


class AlfredConfig(BaseModel):
    """Main configuration model for Alfred."""

    version: str = Field(default="2.0.0", description="Configuration version")
    providers: ProviderConfig = Field(default_factory=ProviderConfig, description="Task provider configuration")
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)

    model_config = {"validate_assignment": True, "extra": "forbid"}

``````
------ src/alfred/models/config.py ------
``````
# src/alfred/models/config.py
"""
Pydantic models for parsing persona configurations, including the
new dual-mode (Human/AI) interaction structure.
"""
from typing import Dict, List

from pydantic import BaseModel, Field


class HumanInteraction(BaseModel):
    """Configuration for human-facing communication."""

    greeting: str = Field(description="The persona's introductory greeting.")
    communication_style: str = Field(
        description="A description of the persona's conversational style and tone with humans."
    )


class AIInteraction(BaseModel):
    """Configuration for AI agent directives."""

    style: str = Field(
        default="precise, technical, directive",
        description="The persona's communication style when issuing instructions to the AI agent.",
    )
    analysis_patterns: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="A dictionary mapping a tool's state to a list of specific analysis commands or patterns for the AI.",
    )
    validation_criteria: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="A dictionary mapping a tool's state to a list of specific validation criteria for AI self-review.",
    )


class PersonaConfig(BaseModel):
    """
    Represents the validated configuration of a single persona.yml file,
    supporting dual-mode communication.
    """

    name: str = Field(description="The persona's first name, e.g., 'Alex'.")
    title: str = Field(description="The persona's job title, e.g., 'Solution Architect'.")
    thinking_methodology: List[str] = Field(
        default_factory=list,
        description="A list of core principles that guide the persona's reasoning.",
    )
    human: HumanInteraction
    ai: AIInteraction
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


class GitStatusArtifact(BaseModel):
    is_clean: bool
    current_branch: str
    uncommitted_files: List[str]


class BranchCreationArtifact(BaseModel):
    branch_name: str
    success: bool
    details: str

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
# src/alfred/models/state.py
"""
Pydantic models for Alfred's state management.
This module defines the single source of truth for task state.
"""
from datetime import datetime
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

from src.alfred.models.schemas import TaskStatus


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
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UnifiedTaskState(BaseModel):
    """
    The single, unified state object for a task.
    This is the schema for the new `task_state.json` file.
    """

    task_id: str
    task_status: TaskStatus = Field(default=TaskStatus.NEW)
    active_tool_state: Optional[WorkflowState] = Field(default=None)
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
------ src/alfred/personas/onboarding.yml ------
``````
name: Alfred
title: Personal Butler & Project Lead
thinking_methodology:
- Methodical and thorough in approach
- Safety-first mindset
- Clear communication of requirements
human:
  greeting: Good day. I am Alfred, at your service. Before we proceed with the task, we must ensure our workspace is in perfect
    order. Let's begin.
  communication_style: Polite, professional, and precise. I guide the user through necessary setup procedures with patience
    and clarity, ensuring nothing is overlooked.
ai:
  style: directive, procedural, safe
  analysis_patterns:
    initialized:
    - Execute systematic Git repository analysis.
    - 'Command 1: `git status --porcelain` (to check for uncommitted changes).'
    - 'Command 2: `git rev-parse --abbrev-ref HEAD` (to get the current branch name).'
    branch_created:
    - Execute Git branch creation.
    - 'Command: `git checkout -b feature/{{ task.task_id }}` (or `git checkout` if branch exists).'
    git_status_checked:
    - Analyze git status results for proper workflow continuation.
    - Determine if a new branch creation is appropriate based on current branch and changes.
    awaiting_ai_review:
    - Review submitted artifact for technical accuracy.
    - Verify all required fields are present and properly formatted.
    - Check that Git operations align with best practices.
    awaiting_human_review:
    - Present artifact clearly for human validation.
    - Ensure human understands the implications of the proposed action.
    completed:
    - Confirm all workspace setup steps have been executed.
    - Summarize the current state and readiness for task work.
    - Provide clear next steps for the user.
  validation_criteria:
    initialized:
    - Has git status been checked successfully?
    - Is the repository in a valid state for task work?
    - Are all required tools and permissions available?
    git_status_checked:
    - Is `is_clean` field present and a boolean?
    - Is `current_branch` field present and a non-empty string?
    branch_created:
    - Is `success` field present and a boolean?
    - Is `details` field present and a non-empty string?
    awaiting_ai_review:
    - Are all artifact fields technically valid?
    - Does the artifact represent a successful operation?
    awaiting_human_review:
    - Is the artifact presentation clear and understandable?
    - Are the next steps clearly communicated?
    completed:
    - Have all setup steps been completed successfully?
    - Is the workspace ready for task implementation?
    - Has the user been properly informed of the next steps?

``````
------ src/alfred/personas/planning.yml ------
``````
name: Alex
title: Solution Architect
thinking_methodology:
- Always start with the business goal and work backwards to the technical solution.
- Favor simplicity and clarity over unnecessary complexity.
- Ensure every part of the plan is testable and verifiable.
human:
  greeting: Hey there! I'm Alex. I'll be your solution architect for this task. My job is to help you create a rock-solid
    technical plan before we write any code. Let's get the ball rolling.
  communication_style: Professional yet approachable. I explain complex technical concepts in simple terms. I am proactive
    in identifying risks and dependencies. I focus on the 'why' behind the architecture, not just the 'what'.
ai:
  style: analytical, structured, exhaustive
  analysis_patterns:
    contextualize:
    - Perform deep codebase analysis starting from the project root.
    - Identify all files and code blocks relevant to the provided Task Context.
    - Compare the task goal with code analysis to identify ambiguities.
    strategize:
    - Analyze architectural approaches with trade-off analysis.
    - Map out state management, data flow, and integration points.
    - Generate multiple strategy options with pros/cons.
    design:
    - Generate detailed interface specifications for all components.
    - Create exhaustive mapping of function signatures and parameters.
    - Document all error states and edge cases.
    generate_subtasks:
    - Map subtasks to specific files and line ranges.
    - Include verification criteria for each subtask.
    - Order subtasks by dependency graph.
    review_context:
    - Validate context analysis completeness.
    - Ensure all ambiguities are properly identified.
    review_strategy:
    - Verify strategy aligns with business goals.
    - Check for technical feasibility and risks.
    review_design:
    - Validate design completeness and consistency.
    - Ensure all components are properly specified.
    review_plan:
    - Verify subtasks cover all requirements.
    - Check dependency ordering and completeness.
    awaiting_ai_review:
    - Perform comprehensive artifact validation.
    - Check technical accuracy and completeness.
    - Verify alignment with task requirements.
    awaiting_human_review:
    - Present complex technical details clearly.
    - Highlight key decisions for human validation.
    - Ensure business alignment is evident.
    verified:
    - Confirm all planning phases have been completed successfully.
    - Validate the execution plan is ready for implementation.
    - Summarize key decisions and next steps.
  validation_criteria:
    contextualize:
    - Is `context_summary` a comprehensive summary of existing code and proposed integration?
    - Is `affected_files` a non-empty list of relevant file paths?
    - Are `questions_for_developer` specific, actionable, and designed to resolve ambiguity?
    strategize:
    - Is `goal_summary` clear and specific about the task objective?
    - Is `technical_approach` detailed with justifications?
    - Are `risks` realistic and mitigation strategies provided?
    design:
    - Are `components` fully specified with clear responsibilities?
    - Is `data_flow` complete with all state transitions?
    - Are `integration_points` mapped to existing code?
    generate_subtasks:
    - Does each subtask have clear acceptance criteria?
    - Are subtasks atomic and independently verifiable?
    - Is the dependency order technically correct?
    review_context:
    - Is the context analysis thorough and accurate?
    - Are identified ambiguities genuine concerns?
    review_strategy:
    - Is the strategy technically sound?
    - Are risks properly identified and mitigated?
    review_design:
    - Is the design implementable as specified?
    - Are all edge cases considered?
    review_plan:
    - Is the execution plan complete?
    - Can each subtask be independently verified?
    awaiting_ai_review:
    - Does the artifact meet all technical requirements?
    - Is the artifact internally consistent?
    awaiting_human_review:
    - Is the technical content accessible to the human reviewer?
    - Are business implications clearly stated?
    verified:
    - Has the complete planning process been executed successfully?
    - Is the execution plan comprehensive and ready for implementation?
    - Are all artifacts properly validated and approved?

``````
------ src/alfred/server.py ------
``````
# src/alfred/server.py
"""
MCP Server for Alfred
This version preserves the original comprehensive docstrings while maintaining
the clean V2 Alfred architecture.
"""
import inspect

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl
from src.alfred.tools.progress import mark_subtask_complete_impl
from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.tools.start_task import start_task_impl
from src.alfred.tools.submit_work import submit_work_impl

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
    transaction_logger.log(
        task_id=None, tool_name=tool_name, request_data=request_data, response=response
    )
    return response


@app.tool()
async def start_task(task_id: str) -> ToolResponse:
    """
    Initializes the workspace for a specific task, making it ready for planning.

    This is the first command to run for any given task. It sets up the necessary
    directory structure and state files. If the task is new, its status will be
    set to 'planning'. If the task already exists, it simply ensures the workspace
    is ready for the next command.

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01").

    Returns:
        ToolResponse: Contains success/error status and a prompt guiding the user to call 'plan_task'.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = start_task_impl(task_id)
    transaction_logger.log(
        task_id=task_id,
        tool_name=tool_name,
        request_data=request_data,
        response=response,
    )
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
    transaction_logger.log(
        task_id=task_id,
        tool_name=tool_name,
        request_data=request_data,
        response=response,
    )
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
    transaction_logger.log(
        task_id=task_id,
        tool_name=tool_name,
        request_data=request_data,
        response=response,
    )
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
    request_data = {
        "task_id": task_id,
        "is_approved": is_approved,
        "feedback_notes": feedback_notes,
    }
    response = provide_review_impl(task_id, is_approved, feedback_notes)
    transaction_logger.log(
        task_id=task_id,
        tool_name=tool_name,
        request_data=request_data,
        response=response,
    )
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
    transaction_logger.log(
        task_id=task_id,
        tool_name=tool_name,
        request_data=request_data,
        response=response,
    )
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
# src/alfred/state/manager.py
"""
Unified state management for Alfred.
Provides atomic state persistence for the UnifiedTaskState object.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from src.alfred.config.settings import settings
from src.alfred.constants import Paths
from src.alfred.lib.logger import get_logger
from src.alfred.models.schemas import TaskStatus
from src.alfred.models.state import UnifiedTaskState, WorkflowState

logger = get_logger(__name__)


class StateManager:
    """Manages the persistent state for a single task via task_state.json."""

    def _get_task_state_file(self, task_id: str) -> Path:
        """Gets the path to the unified state file for a task."""
        return settings.workspace_dir / task_id / "task_state.json"

    def load_or_create_task_state(self, task_id: str) -> UnifiedTaskState:
        """Loads a task's unified state from disk, or creates it if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)
        if not state_file.exists():
            logger.info(f"No state file found for task {task_id}. Creating new state.")
            new_state = UnifiedTaskState(task_id=task_id)
            self.save_task_state(new_state)
            return new_state

        try:
            state_json = state_file.read_text()
            state_data = UnifiedTaskState.model_validate_json(state_json)
            tool_name = (
                state_data.active_tool_state.tool_name
                if state_data.active_tool_state
                else "None"
            )
            logger.info(
                f"Loaded state for task {task_id}. Status: {state_data.task_status.value}, Active Tool: {tool_name}."
            )
            return state_data
        except Exception as e:
            logger.error(
                f"Failed to load or validate state for task {task_id}, creating new state. Error: {e}"
            )
            new_state = UnifiedTaskState(task_id=task_id)
            self.save_task_state(new_state)
            return new_state

    def save_task_state(self, state: UnifiedTaskState) -> None:
        """Atomically saves the entire unified state for a task."""
        state.updated_at = datetime.utcnow().isoformat()
        state_file = self._get_task_state_file(state.task_id)
        state_file.parent.mkdir(parents=True, exist_ok=True)

        temp_file = state_file.with_suffix(Paths.JSON_EXTENSION + Paths.TMP_EXTENSION)
        try:
            temp_file.write_text(state.model_dump_json(indent=2))
            temp_file.replace(state_file)
            logger.info(f"Successfully saved state for task {state.task_id}.")
        except Exception as e:
            logger.error(f"Failed to save state for task {state.task_id}: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> UnifiedTaskState:
        """Loads, updates the task_status, and saves the state."""
        state = self.load_or_create_task_state(task_id)
        state.task_status = new_status
        self.save_task_state(state)
        logger.info(f"Updated task {task_id} status to {new_status.value}")
        return state

    def update_tool_state(
        self, task_id: str, tool: "BaseWorkflowTool"
    ) -> UnifiedTaskState:
        """Loads, updates the tool state portion, and saves."""
        state = self.load_or_create_task_state(task_id)

        serializable_context = {}
        if tool.context_store:
            for key, value in tool.context_store.items():
                if isinstance(value, BaseModel):
                    serializable_context[key] = value.model_dump()
                else:
                    serializable_context[key] = value

        tool_state_data = WorkflowState(
            task_id=task_id,
            tool_name=tool.tool_name,
            current_state=str(tool.state),
            context_store=serializable_context,
            persona_name=tool.persona_name,
            updated_at=datetime.utcnow().isoformat(),
        )
        state.active_tool_state = tool_state_data
        self.save_task_state(state)
        return state

    def clear_tool_state(self, task_id: str) -> UnifiedTaskState:
        """Loads, clears the active tool state, and saves."""
        state = self.load_or_create_task_state(task_id)
        if state.active_tool_state:
            logger.info(f"Clearing active tool state for task {task_id}.")
            state.active_tool_state = None
            self.save_task_state(state)
        return state


# Singleton instance
state_manager = StateManager()
``````
------ src/alfred/state/recovery.py ------
``````
# src/alfred/state/recovery.py
"""
Tool recovery functionality for Alfred workflow tools.
Handles reconstruction of workflow tools from persisted state.
"""
from typing import Dict, Optional, Type

from src.alfred.core.workflow import BaseWorkflowTool, PlanTaskTool, StartTaskTool
from src.alfred.lib.logger import get_logger
from src.alfred.state.manager import state_manager
from src.alfred.constants import ToolName

logger = get_logger(__name__)


class ToolRecovery:
    """Handles recovery of workflow tools from persisted state."""

    TOOL_REGISTRY: Dict[str, Type[BaseWorkflowTool]] = {
        ToolName.START_TASK: StartTaskTool,
        ToolName.PLAN_TASK: PlanTaskTool,
    }

    @classmethod
    def recover_tool(cls, task_id: str) -> Optional[BaseWorkflowTool]:
        """Attempt to recover a tool from the unified persisted state."""
        task_state = state_manager.load_or_create_task_state(task_id)
        persisted_tool_state = task_state.active_tool_state

        if not persisted_tool_state:
            logger.debug(f"No active tool state found for task {task_id} to recover.")
            return None

        tool_name = persisted_tool_state.tool_name
        tool_class = cls.TOOL_REGISTRY.get(tool_name)
        if not tool_class:
            logger.error(f"Unknown tool type: {tool_name}. Cannot recover.")
            return None

        try:
            tool = tool_class(task_id=task_id)
            tool.state = persisted_tool_state.current_state
            tool.context_store = persisted_tool_state.context_store
            tool.persona_name = persisted_tool_state.persona_name

            logger.info(
                f"Successfully recovered {tool_name} for task {task_id} in state {tool.state}"
            )
            return tool
        except Exception as e:
            logger.error(
                f"Failed to recover tool for task {task_id}: {e}", exc_info=True
            )
            return None

    @classmethod
    def register_tool(cls, tool_name: str, tool_class: Type[BaseWorkflowTool]) -> None:
        """Register a new tool type for recovery."""
        cls.TOOL_REGISTRY[tool_name] = tool_class
        logger.debug(f"Registered tool type: {tool_name}")

    @classmethod
    def can_recover(cls, task_id: str) -> bool:
        """Check if a task has a recoverable tool state."""
        task_state = state_manager.load_or_create_task_state(task_id)
        persisted_tool_state = task_state.active_tool_state
        if not persisted_tool_state:
            return False

        tool_name = persisted_tool_state.tool_name
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
------ src/alfred/templates/prompts/generic/awaiting_ai_review.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have just submitted the artifact for the `{{ additional_context.last_state | replace("_", " ") | title }}` step. I must now perform a critical self-review to ensure the artifact meets all quality standards before it proceeds to human review.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content }}
```

---
### **Directive: AI Self-Review**

Critically evaluate the artifact above against the original goal of the step.

**Review Checklist:**
1.  **Completeness:** Does the artifact contain all required fields and information?
2.  **Clarity:** Is the information clear, specific, and unambiguous?
3.  **Correctness:** Does the artifact accurately reflect the work that was required?
4.  **Adherence to Standards:** Does the artifact follow all specified formatting and structural rules?

---
### **Required Action**

Call `alfred.provide_review`.
-   If the artifact is perfect, set `is_approved=True`.
-   If the artifact has any flaws, set `is_approved=False` and provide detailed `feedback_notes` explaining the necessary corrections.
``````
------ src/alfred/templates/prompts/generic/awaiting_human_review.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

My self-review is complete. The artifact for the `{{ additional_context.last_state | replace("_", " ") | title }}` step is now ready for your final approval.

**Artifact for Your Review:**
```json
{{ additional_context.artifact_content }}
```

---
### **Directive: Await Human Approval**

Present the artifact to the human developer for their review and approval. They will provide a simple "yes/no" or "approve/reject" decision.

-   If they approve, call `alfred.provide_review` with `is_approved=True`.
-   If they request changes, call `alfred.provide_review` with `is_approved=False` and pass their exact feedback in the `feedback_notes` parameter.
``````
------ src/alfred/templates/prompts/plan_task/awaiting_ai_review.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have just submitted my artifact for review. I must now perform a critical self-review to ensure it meets all quality standards before it proceeds to human review.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: AI Self-Review**

Critically evaluate the ContextAnalysisArtifact above against the original goal of understanding the codebase and identifying ambiguities.

**Review Checklist:**
1. **Context Summary Completeness:** Does the summary accurately capture the existing codebase relevant to the task?
2. **Affected Files Coverage:** Are all relevant files identified? Are any missing or unnecessary?
3. **Question Quality:** Are the questions specific, actionable, and focused on genuine ambiguities?
4. **Accuracy:** Is all technical information correct based on the codebase analysis?

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

Call `alfred.provide_review`.
- If the artifact meets all quality standards, set `is_approved=True`.
- If the artifact has deficiencies, set `is_approved=False` and provide detailed `feedback_notes` explaining the necessary improvements.
``````
------ src/alfred/templates/prompts/plan_task/awaiting_human_review.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

My self-review is complete and approved. The artifact is now ready for your final human review and approval.

**Artifact for Your Review:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: Await Human Approval**

Present the ContextAnalysisArtifact to the human developer for their review and approval. They will provide feedback on whether the codebase analysis and ambiguity questions are satisfactory.

**What to look for in the human's response:**
- Simple approval signals like "yes", "approve", "looks good", "LGTM"
- Specific feedback requesting changes to the context summary, affected files, or questions
- Additional requirements or clarifications they want to add

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

Based on the human developer's response:
- If they approve, call `alfred.provide_review` with `is_approved=True`
- If they request changes, call `alfred.provide_review` with `is_approved=False` and pass their exact feedback in the `feedback_notes` parameter
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
**Communication Style:** {% if persona.human %}{{ persona.human.communication_style }}{% else %}{{ persona.communication_style }}{% endif %}

You MUST embody this persona. **Do not use repetitive, canned phrases.** Your first message to the user should be a unique greeting based on the persona's `greeting` and `style`. For example: `{% if persona.human %}{{ persona.human.greeting }}{% else %}{{ persona.greeting }}{% endif %}` (Use creative greetings each time). Adapt your language to feel like a genuine, collaborative partner.
---

**Task Context:**
- **Goal:** {{ task.context }}
- **Implementation Overview:** {{ task.implementation_details }}
- **Acceptance Criteria:**
{% for criterion in task.acceptance_criteria %}
  - {{ criterion }}
{% endfor %}

{% if additional_context.feedback_notes %}
---
### **Building on Your Previous Analysis**

Your earlier ContextAnalysisArtifact has been reviewed and needs some refinements. Here's what you submitted:

```json
{{ additional_context.context_artifact | tojson(indent=2) if additional_context.context_artifact else "No artifact data available" }}
```

The reviewer provided this feedback to help strengthen your analysis:

> {{ additional_context.feedback_notes }}

Please refine your ContextAnalysisArtifact by incorporating these suggestions. Focus on addressing the specific areas highlighted while maintaining the quality of your existing work.

{% endif %}
---
### **Directive: Codebase Analysis & Ambiguity Detection**

Your mission is to become the expert on this task. You must:
1.  **Analyze the existing codebase.** Start from the project root. Identify all files and code blocks relevant to the provided Task Context.
2.  **Identify Ambiguities.** Compare the task goal with your code analysis. Create a list of precise questions for the human developer to resolve any uncertainties or missing requirements.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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

{% if additional_context.feedback_notes %}
---
### **Iterating on Your Design**

Your DesignArtifact has been carefully reviewed, and there are some valuable suggestions to make it even stronger. Here's your current design:

```json
{{ additional_context.design_artifact | tojson(indent=2) if additional_context.design_artifact else "No artifact data available" }}
```

The review highlighted these areas for enhancement:

> {{ additional_context.feedback_notes }}

Please refine your DesignArtifact by incorporating these insights. Think about how these suggestions can improve the clarity, completeness, and implementability of your design while preserving the strong elements you've already developed.

{% endif %}
---
### **Directive: Create Detailed Design**

Based on the approved strategy, create a comprehensive, file-by-file breakdown of all necessary changes. For each file that needs to be created or modified, provide a clear summary of the required changes.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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

{% if additional_context.feedback_notes %}
---
### **Refining Your Execution Plan**

Your ExecutionPlan has been reviewed with a focus on precision and implementability. Here's your current subtask breakdown:

```json
{{ additional_context.execution_plan_artifact | tojson(indent=2) if additional_context.execution_plan_artifact else "No artifact data available" }}
```

The review identified opportunities to enhance your plan:

> {{ additional_context.feedback_notes }}

Please revise your ExecutionPlan by incorporating these insights. Focus on making your subtasks even more precise, atomic, and actionable while maintaining the solid structure you've established. Remember, each subtask should be executable in complete isolation.

{% endif %}
---
### **Your Mission**

Transform the approved design into subtasks that are:
1. **Atomic** - One indivisible action each
2. **Independent** - Executable in complete isolation
3. **Precise** - No room for interpretation
4. **Verifiable** - Clear pass/fail conditions
5. **Complete** - When all done, the feature works perfectly

Remember: You are writing instructions for agents who know nothing about the project except what you tell them. Every detail matters.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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
**Communication Style:** {% if persona.human %}{{ persona.human.communication_style }}{% else %}{{ persona.communication_style }}{% endif %}

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

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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
### **Refining Your Technical Strategy**
{% if additional_context.feedback_notes %}
Your previous StrategyArtifact has been reviewed and the team has provided valuable insights to strengthen your approach. Here's your earlier strategy:

```json
{{ additional_context.strategy_artifact | tojson(indent=2) if additional_context.strategy_artifact else "No artifact data available" }}
```

The reviewer shared these insights to help you refine the strategy:

> {{ additional_context.feedback_notes }}

Please enhance your StrategyArtifact by incorporating this feedback. Consider how these suggestions can improve the overall technical approach while building on the solid foundation you've already established.
{% else %}
No specific clarifications were provided. Proceed based on the original task context and approved requirements.
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

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

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
------ src/alfred/templates/prompts/start_task/awaiting_ai_review.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have just submitted my artifact for review. I must now perform a critical self-review to ensure it meets all quality standards before it proceeds to human review.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: AI Self-Review**

Critically evaluate the submitted artifact against the requirements for this step of the start_task workflow.

**Review Checklist:**
1. **Data Accuracy:** Is all information in the artifact accurate and complete?
2. **Required Fields:** Are all required fields present and properly formatted?
3. **Git Status Assessment:** For GitStatusArtifact, does the assessment align with proper Git workflow practices?
4. **Branch Strategy:** For BranchCreationArtifact, was the branch creation successful and properly named?

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

Call `alfred.provide_review`.
- If the artifact meets all quality standards, set `is_approved=True`.
- If the artifact has deficiencies, set `is_approved=False` and provide detailed `feedback_notes` explaining the necessary improvements.
``````
------ src/alfred/templates/prompts/start_task/awaiting_branch_creation.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.start_task`
# TASK: {{ task.task_id }}
# STATE: branch_created

Excellent. The human operator has approved the action.

---
### **Directive: Create and Verify Branch**

Please execute the proposed git command to create and switch to the new feature branch:
`git checkout -b feature/{{ task.task_id }}`

If the branch already exists, use `git checkout feature/{{ task.task_id }}` instead.

After executing the command, please report the outcome.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `BranchCreationArtifact`.

**Required Artifact Structure:**
```json
{
  "branch_name": "string - The name of the new branch, 'feature/{{ task.task_id }}'.",
  "success": "boolean - True if the command executed without errors.",
  "details": "string - The output from the git command."
}
```
``````
------ src/alfred/templates/prompts/start_task/awaiting_git_status.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.start_task`
# TASK: {{ task.task_id }}
# STATE: awaiting_git_status

Welcome. I am {{ persona.name }}, your {{ persona.title }}.

{{ persona.context }}

---
### **System Checkpoint: Environment Assessment**

Before we begin work on task **{{ task.task_id }}**, we must establish a clean working environment.

Please execute:
```bash
git status
```

Report the current repository state for validation.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

You MUST now call `alfred.submit_work` with a `GitStatusArtifact`.

**Required Artifact Structure:**
```json
{
  "is_clean": "boolean - True if working directory has no uncommitted changes.",
  "current_branch": "string - The name of the current git branch.",
  "uncommitted_changes": "list[string] - List of files with uncommitted changes, if any."
}
```
``````
------ src/alfred/templates/prompts/start_task/awaiting_human_review.md ------
``````
# ROLE: {{ persona.name }}, {{ persona.title }}
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

The AI has reviewed my submission and found it satisfactory. Now I require human approval to proceed with the next step.

**Current Artifact:**
```json
{{ additional_context.artifact_content | fromjson if additional_context.artifact_content else {} }}
```

---
### **Directive: Human Review**

Please review my submission above and confirm whether you approve proceeding to the next step.

The AI has already validated the technical accuracy. Your approval confirms that the proposed action aligns with your intentions and project requirements.

{% if ai_directives %}
---
### **AI Agent Instructions**

**Analysis Style:** {{ ai_directives.style }}

**Required Analysis Steps:**
{% for pattern in ai_directives.analysis_patterns %}
- {{ pattern }}
{% endfor %}

**Self-Validation Checklist:**
{% for criterion in ai_directives.validation_criteria %}
- {{ criterion }}
{% endfor %}
{% endif %}

---
### **Required Action**

Call `alfred.provide_review`.
- If you approve proceeding to the next step, set `is_approved=True`.
- If you need changes or have concerns, set `is_approved=False` and provide `feedback_notes` with your specific requirements.
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

from src.alfred.core.prompter import prompter
from src.alfred.core.workflow import PlanTaskState, PlanTaskTool
from src.alfred.lib.logger import get_logger, setup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery

logger = get_logger(__name__)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool with unified state."""
    setup_task_logging(task_id)

    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(
            f"Found active tool for task {task_id} in state {tool_instance.state}"
        )
    else:
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(
                f"Recovered tool from disk for task {task_id} in state {tool_instance.state}"
            )
        else:
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' task or resume a 'planning' task.",
                )

            tool_instance = PlanTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance

            if task.task_status == TaskStatus.NEW:
                state_manager.update_task_status(task_id, TaskStatus.PLANNING)

            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new planning tool for task {task_id}")

    try:
        persona_config = load_persona(tool_instance.persona_name or "planning")
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        persona_config=persona_config,
        additional_context=prompt_context,
    )

    message = (
        f"Planning initiated for task '{task_id}'."
        if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value
        else f"Resumed planning for task '{task_id}' from state '{tool_instance.state}'."
    )

    return ToolResponse(status="success", message=message, next_prompt=prompt)
``````
------ src/alfred/tools/progress.py ------
``````
# src/alfred/tools/progress.py
"""
Progress tracking tools for Alfred workflow system.
"""
from src.alfred.lib.logger import get_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """Marks a specific subtask as complete during the implementation phase."""
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    execution_plan_artifact = active_tool.context_store.get("execution_plan_artifact")
    if not execution_plan_artifact:
        return ToolResponse(status="error", message="No execution plan found in context.")

    # Note: Pydantic models in context are stored as dicts after deserialization
    execution_plan = execution_plan_artifact.get("subtasks", [])
    valid_subtask_ids = {subtask["subtask_id"] for subtask in execution_plan}
    if subtask_id not in valid_subtask_ids:
        return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'.")

    completed_subtasks = set(active_tool.context_store.get("completed_subtasks", []))
    if subtask_id in completed_subtasks:
        return ToolResponse(status="success", message=f"Subtask '{subtask_id}' already marked complete.")

    completed_subtasks.add(subtask_id)
    active_tool.context_store["completed_subtasks"] = list(completed_subtasks)

    # --- THIS IS THE FIX ---
    # Use the correct, unified state manager method.
    state_manager.update_tool_state(task_id, active_tool)
    # --- END FIX ---

    completed_count = len(completed_subtasks)
    total_subtasks = len(valid_subtask_ids)
    progress = (completed_count / total_subtasks) * 100 if total_subtasks > 0 else 0
    message = f"Acknowledged: Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_subtasks} ({progress:.0f}%)."
    logger.info(message)

    return ToolResponse(
        status="success",
        message=message,
        data={
            "completed_count": completed_count,
            "total_count": total_subtasks,
            "progress_percentage": progress,
        },
    )
``````
------ src/alfred/tools/provide_review.py ------
``````
# src/alfred/tools/provide_review.py
from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.constants import ToolName
from src.alfred.core.prompter import prompter
from src.alfred.core.workflow import ReviewState
from src.alfred.core.context_builder import ContextBuilder
from src.alfred.lib.logger import cleanup_task_logging, get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)

# Force server reload marker - AL-09 implementation active

def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Processes review feedback, advancing the active tool's State Machine."""
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info(f"Processing review for task {task_id} in state '{current_state}', approved={is_approved}")
    
    if not is_approved:
        logger.info(f"Review rejected, transitioning back from '{current_state}'")
        active_tool.request_revision()
        message = "Revision requested. Returning to previous step."
        logger.info(f"After revision, new state is '{active_tool.state}'")
    else:
        if current_state == ReviewState.AWAITING_AI_REVIEW.value:
            active_tool.ai_approve()
            config_manager = ConfigManager(settings.alfred_dir)
            config = config_manager.load()
            if config.features.autonomous_mode:
                logger.info(f"Autonomous mode enabled. Bypassing human review for task {task_id}.")
                active_tool.human_approve()
                message = "AI review approved. Autonomous mode bypassed human review."
            else:
                message = "AI review approved. Awaiting human review."
        elif current_state == ReviewState.AWAITING_HUMAN_REVIEW.value:
            active_tool.human_approve()
            message = "Human review approved. Proceeding to next step."
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{active_tool.state}'.")

    state_manager.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        # --- ADD THIS LOGIC ---
        if active_tool.tool_name == ToolName.START_TASK:
            final_task_status = TaskStatus.PLANNING
            handoff_message = f"Setup for task {task_id} is complete. The task is now '{final_task_status.value}'. Call 'plan_task' to begin planning."
        # --- END ADDED LOGIC ---
        elif active_tool.tool_name == ToolName.PLAN_TASK:
            final_task_status = TaskStatus.READY_FOR_DEVELOPMENT
            handoff_message = f"Planning for task {task_id} is complete. The task is now '{final_task_status.value}'. To begin implementation, use the 'implement_task' tool."
        else:
            final_task_status = TaskStatus.DONE # Default fallback
            handoff_message = f"Tool '{active_tool.tool_name}' for task {task_id} completed."

        state_manager.update_task_status(task_id, final_task_status)
        state_manager.clear_tool_state(task_id)
        del orchestrator.active_tools[task_id]
        cleanup_task_logging(task_id)
        logger.info(f"Tool '{active_tool.tool_name}' for task {task_id} completed. Task status updated to '{final_task_status.value}'.")
        
        return ToolResponse(status="success", message=message, next_prompt=handoff_message)
    else:
        persona_config = load_persona(active_tool.persona_name)
        
        # CRITICAL: Force visible logging to verify code execution
        logger.warning(f"[AL-09 VERIFICATION] Building context for state '{active_tool.state}', is_approved={is_approved}")
        
        # Build proper context based on transition type
        if not is_approved:
            # Rejection: returning to work state, need feedback context
            logger.info(f"[FEEDBACK LOOP] Building feedback context for rejection flow")
            logger.info(f"[FEEDBACK LOOP] State: '{active_tool.state}', Feedback: {feedback_notes[:100]}")
            additional_context = ContextBuilder.build_feedback_context(
                active_tool,
                active_tool.state,  # Current state after revision
                feedback_notes
            )
            logger.info(f"[FEEDBACK LOOP] Context keys after building: {list(additional_context.keys())}")
            logger.info(f"[FEEDBACK LOOP] Has feedback_notes: {'feedback_notes' in additional_context}")
            logger.info(f"[FEEDBACK LOOP] Has context_artifact: {'context_artifact' in additional_context}")
        else:
            # Approval: moving forward, standard context
            logger.info(f"[FEEDBACK LOOP] Building standard context for approval flow")
            additional_context = ContextBuilder.build_standard_context(active_tool)
            
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=active_tool.state,
            persona_config=persona_config,
            additional_context=additional_context,
        )
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)
``````
------ src/alfred/tools/start_task.py ------
``````
# src/alfred/tools/start_task.py
"""
The start_task tool, re-architected as a stateful workflow tool.
"""
from src.alfred.core.prompter import prompter
from src.alfred.core.workflow import StartTaskTool
from src.alfred.lib.logger import get_logger, setup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery

logger = get_logger(__name__)


def start_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the interactive start_task tool."""
    setup_task_logging(task_id)

    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
    else:
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task_id}' has status '{task.task_status.value}'. Setup can only start on a 'new' task.",
                )

            tool_instance = StartTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new start_task tool for task {task_id}")

    try:
        persona_config = load_persona(tool_instance.persona_name)
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        persona_config=persona_config,
    )

    message = f"Starting setup for task '{task_id}'. Current step: {tool_instance.state}."

    return ToolResponse(status="success", message=message, next_prompt=prompt)
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
    """Implements the logic for submitting a work artifact to the active tool."""
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.TASK_NOT_FOUND.format(task_id=task_id))

    current_state_enum = active_tool.state
    current_state_val = active_tool.state.value if hasattr(active_tool.state, "value") else active_tool.state
    artifact_model = active_tool.artifact_map.get(current_state_enum)

    if artifact_model:
        try:
            validated_artifact = artifact_model.model_validate(artifact)
            logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state_val, model=artifact_model.__name__))
        except ValidationError as e:
            error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state_val)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
            return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
    else:
        validated_artifact = artifact

    try:
        persona_config = load_persona(active_tool.persona_name)
    except FileNotFoundError as e:
        return ToolResponse(status=ResponseStatus.ERROR, message=str(e))

    trigger = Triggers.submit_trigger(current_state_val)
    if not hasattr(active_tool, trigger):
        return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")

    next_transitions = active_tool.machine.get_transitions(source=active_tool.state, trigger=trigger)
    if not next_transitions:
        return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger}' from state '{active_tool.state}'.")
    next_state = next_transitions[0].dest

    temp_context = active_tool.context_store.copy()
    artifact_key = ArtifactKeys.get_artifact_key(current_state_val)
    temp_context[artifact_key] = validated_artifact
    temp_context[ArtifactKeys.ARTIFACT_CONTENT_KEY] = json.dumps(artifact, indent=2)

    next_prompt = prompter.generate_prompt(
        task=task,
        tool_name=active_tool.tool_name,
        state=next_state,
        persona_config=persona_config,
        additional_context=temp_context,
    )

    active_tool.context_store[artifact_key] = validated_artifact
    artifact_manager.append_to_scratchpad(task_id=task_id, state_name=current_state_val, artifact=validated_artifact, persona_config=persona_config)
    
    getattr(active_tool, trigger)()
    logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))

    state_manager.update_tool_state(task_id, active_tool)

    return ToolResponse(status=ResponseStatus.SUCCESS, message="Work submitted. Awaiting review.", next_prompt=next_prompt)
``````
------ src/alfred/workflow.yml ------
``````
# Default Alfred workflow configuration
# This file defines the workflow structure and persona mappings

tools:
  start_task:
    persona: onboarding
    states:
      - initialized
      - git_status_checked
      - branch_created
      - awaiting_ai_review
      - awaiting_human_review
      - completed
      
  plan_task:
    persona: planning
    states:
      - contextualize
      - review_context
      - strategize
      - review_strategy
      - design
      - review_design
      - generate_subtasks
      - review_plan
      - awaiting_ai_review
      - awaiting_human_review
      - verified
      
  implement_task:
    persona: implementation
    states:
      - initialized
      - in_progress
      - awaiting_ai_review
      - awaiting_human_review
      - completed
``````
