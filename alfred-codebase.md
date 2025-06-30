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

    CREATE_SPEC: Final[str] = "create_spec"
    CREATE_TASKS: Final[str] = "create_tasks"
    START_TASK: Final[str] = "start_task"
    PLAN_TASK: Final[str] = "plan_task"
    IMPLEMENT_TASK: Final[str] = "implement_task"
    REVIEW_TASK: Final[str] = "review_task"
    TEST_TASK: Final[str] = "test_task"
    FINALIZE_TASK: Final[str] = "finalize_task"
    WORK_ON: Final[str] = "work_on"
    APPROVE_AND_ADVANCE: Final[str] = "approve_and_advance"


# Directory and File Names
class Paths:
    """File system path constants."""

    # Directories
    ALFRED_DIR: Final[str] = ".alfred"
    WORKSPACE_DIR: Final[str] = "workspace"
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
        # PlanTask states
        PlanTaskStates.CONTEXTUALIZE: "context",
        PlanTaskStates.STRATEGIZE: "strategy",
        PlanTaskStates.DESIGN: "design",
        PlanTaskStates.GENERATE_SUBTASKS: "execution_plan",
        # Other tool states
        "drafting_spec": "drafting_spec",
        "drafting_tasks": "drafting_tasks",
        "implementing": "implementing",
        "reviewing": "reviewing",
        "testing": "testing",
        "finalizing": "finalizing",
    }

    @staticmethod
    def get_base_state_name(state: str) -> str:
        """Extract base state name from a potentially suffixed state.

        Example: 'strategize_awaiting_ai_review' -> 'strategize'
        """
        if state.endswith("_awaiting_ai_review") or state.endswith("_awaiting_human_review"):
            # Remove the review suffix
            parts = state.rsplit("_awaiting_", 1)
            return parts[0]
        return state

    ARTIFACT_SUFFIX: Final[str] = "_artifact"
    ARTIFACT_CONTENT_KEY: Final[str] = "artifact_content"

    @staticmethod
    def get_artifact_key(state: str) -> str:
        """Get the artifact key for a given state."""
        base_state = ArtifactKeys.get_base_state_name(state)
        artifact_name = ArtifactKeys.STATE_TO_ARTIFACT_MAP.get(base_state, base_state)
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
    HUMAN_APPROVE: Final[str] = "human_approve"
    SUBMIT_WORK: Final[str] = "submit_work"

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
        if hasattr(artifact, "model_dump"):
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

logger = get_logger(__name__)


class Prompter:
    """Generates state-aware prompts for the AI agent."""

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
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a prompt by rendering a template with the given context.

        Args:
            task: The full structured Task object.
            tool_name: The name of the active tool (e.g., 'plan_task').
            state: The current state from the tool's SM (Enum or str).
            additional_context: Ad-hoc data like review feedback.

        Returns:
            The rendered prompt string.
        """
        # Handle both Enum and string state values
        state_value = state.value if hasattr(state, "value") else state

        # Map dynamic review states to generic templates
        template_state = state_value
        if state_value.endswith("_awaiting_ai_review"):
            template_state = "awaiting_ai_review"
        elif state_value.endswith("_awaiting_human_review"):
            template_state = "awaiting_human_review"

        template_path = TemplatePaths.PROMPT_PATTERN.format(tool_name=tool_name, state=template_state)

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
            "additional_context": additional_context or {},
        }

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
    FinalizeArtifact,
    GitStatusArtifact,
    ImplementationManifestArtifact,
    PRDInputArtifact,
    ReviewArtifact,
    StrategyArtifact,
    TaskCreationArtifact,
    TestResultArtifact,
)
from src.alfred.models.engineering_spec import EngineeringSpec


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


class ImplementTaskState(str, Enum):
    DISPATCHING = "dispatching"
    IMPLEMENTING = "implementing"
    VERIFIED = "verified"


class ReviewTaskState(str, Enum):
    DISPATCHING = "dispatching"
    REVIEWING = "reviewing"
    VERIFIED = "verified"


class TestTaskState(str, Enum):
    DISPATCHING = "dispatching"
    TESTING = "testing"
    VERIFIED = "verified"


class FinalizeTaskState(str, Enum):
    DISPATCHING = "dispatching"
    FINALIZING = "finalizing"
    VERIFIED = "verified"


class CreateSpecState(str, Enum):
    DISPATCHING = "dispatching"
    DRAFTING_SPEC = "drafting_spec"
    VERIFIED = "verified"


class CreateTasksState(str, Enum):
    DISPATCHING = "dispatching"
    DRAFTING_TASKS = "drafting_tasks"
    VERIFIED = "verified"


class BaseWorkflowTool:
    def __init__(self, task_id: str, tool_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.state: Optional[str] = None
        self.machine: Optional[Machine] = None
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}
        self.context_store: Dict[str, Any] = {}

    @property
    def is_terminal(self) -> bool:
        return self.state == "verified"

    def _create_review_transitions(self, source_state: str, success_destination_state: str, revision_destination_state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generates a unique, state-specific review cycle.
        Example: For source_state 'strategize', it creates 'strategize_awaiting_ai_review'.
        """
        if revision_destination_state is None:
            revision_destination_state = source_state

        # Dynamic state name generation
        ai_review_state = f"{source_state}_awaiting_ai_review"
        human_review_state = f"{source_state}_awaiting_human_review"

        return [
            # Trigger to enter the review cycle for this specific state
            {
                "trigger": Triggers.submit_trigger(source_state),
                "source": source_state,
                "dest": ai_review_state,
            },
            # AI approves its own work
            {
                "trigger": Triggers.AI_APPROVE,
                "source": ai_review_state,
                "dest": human_review_state,
            },
            # AI requests revision (goes back to the start of this state's work)
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": ai_review_state,
                "dest": revision_destination_state,
            },
            # Human approves the work, advancing to the next major state
            {
                "trigger": Triggers.HUMAN_APPROVE,
                "source": human_review_state,
                "dest": success_destination_state,
            },
            # Human requests revision
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": human_review_state,
                "dest": revision_destination_state,
            },
        ]

    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        return [f"{state}_awaiting_ai_review", f"{state}_awaiting_human_review"]

    def get_final_work_state(self) -> str:
        """Get the final work state that produces the main artifact.

        This method should be overridden by subclasses to return the state
        that produces the primary artifact for the tool.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_final_work_state()")


class PlanTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)
        self.artifact_map = {
            PlanTaskState.CONTEXTUALIZE: ContextAnalysisArtifact,
            PlanTaskState.STRATEGIZE: StrategyArtifact,
            PlanTaskState.DESIGN: DesignArtifact,
            PlanTaskState.GENERATE_SUBTASKS: ExecutionPlanArtifact,
        }

        # Define the base states
        base_states = [state.value for state in PlanTaskState]

        # Dynamically generate the unique review states for each step
        review_states = []
        for state in [PlanTaskState.CONTEXTUALIZE, PlanTaskState.STRATEGIZE, PlanTaskState.DESIGN, PlanTaskState.GENERATE_SUBTASKS]:
            review_states.extend(self.get_review_states_for_state(state.value))

        all_states = base_states + review_states

        # Define the transitions using the new helper
        transitions = [
            *self._create_review_transitions(source_state=PlanTaskState.CONTEXTUALIZE.value, success_destination_state=PlanTaskState.STRATEGIZE.value),
            *self._create_review_transitions(source_state=PlanTaskState.STRATEGIZE.value, success_destination_state=PlanTaskState.DESIGN.value),
            *self._create_review_transitions(source_state=PlanTaskState.DESIGN.value, success_destination_state=PlanTaskState.GENERATE_SUBTASKS.value),
            *self._create_review_transitions(source_state=PlanTaskState.GENERATE_SUBTASKS.value, success_destination_state=PlanTaskState.VERIFIED.value),
        ]

        self.machine = Machine(model=self, states=all_states, transitions=transitions, initial=PlanTaskState.CONTEXTUALIZE.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return PlanTaskState.GENERATE_SUBTASKS.value


class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""

    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.START_TASK)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }

        # Define base states
        base_states = [state.value for state in StartTaskState]

        # Generate review states
        review_states = []
        review_states.extend(self.get_review_states_for_state(StartTaskState.AWAITING_GIT_STATUS.value))
        review_states.extend(self.get_review_states_for_state(StartTaskState.AWAITING_BRANCH_CREATION.value))

        all_states = base_states + review_states

        transitions = [
            # 1. User submits Git Status. After review, success moves to AWAITING_BRANCH_CREATION.
            *self._create_review_transitions(StartTaskState.AWAITING_GIT_STATUS.value, StartTaskState.AWAITING_BRANCH_CREATION.value),
            # 2. User submits Branch Creation result. After review, success moves to VERIFIED (terminal).
            *self._create_review_transitions(StartTaskState.AWAITING_BRANCH_CREATION.value, StartTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=all_states, transitions=transitions, initial=StartTaskState.AWAITING_GIT_STATUS.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return StartTaskState.AWAITING_BRANCH_CREATION.value


class ImplementTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.IMPLEMENT_TASK)
        self.artifact_map = {
            # The ONLY artifact submitted is from the IMPLEMENTING state.
            ImplementTaskState.IMPLEMENTING: ImplementationManifestArtifact,
        }

        source_state = ImplementTaskState.IMPLEMENTING.value

        # Dynamically generate the state names
        states = [
            ImplementTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            ImplementTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": ImplementTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=ImplementTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=ImplementTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return ImplementTaskState.IMPLEMENTING.value


class ReviewTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.REVIEW_TASK)
        self.artifact_map = {
            # Only the reviewing state produces an artifact
            ReviewTaskState.REVIEWING: ReviewArtifact,
        }

        source_state = ReviewTaskState.REVIEWING.value

        states = [
            ReviewTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            ReviewTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": ReviewTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=ReviewTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=ReviewTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return ReviewTaskState.REVIEWING.value


class TestTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.TEST_TASK)
        self.artifact_map = {
            # Only the testing state produces an artifact
            TestTaskState.TESTING: TestResultArtifact,
        }

        source_state = TestTaskState.TESTING.value

        states = [
            TestTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            TestTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": TestTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=TestTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=TestTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return TestTaskState.TESTING.value


class FinalizeTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.FINALIZE_TASK)
        self.artifact_map = {
            # Only the finalizing state produces an artifact
            FinalizeTaskState.FINALIZING: FinalizeArtifact,
        }

        source_state = FinalizeTaskState.FINALIZING.value

        states = [
            FinalizeTaskState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            FinalizeTaskState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": FinalizeTaskState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=FinalizeTaskState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=FinalizeTaskState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return FinalizeTaskState.FINALIZING.value


class CreateSpecTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_SPEC)
        self.artifact_map = {
            CreateSpecState.DRAFTING_SPEC: EngineeringSpec,  # Only one artifact
        }

        source_state = CreateSpecState.DRAFTING_SPEC.value

        states = [
            CreateSpecState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            CreateSpecState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": CreateSpecState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=CreateSpecState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=CreateSpecState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return CreateSpecState.DRAFTING_SPEC.value


class CreateTasksTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_TASKS)
        self.artifact_map = {
            CreateTasksState.DRAFTING_TASKS: TaskCreationArtifact,  # Only one artifact
        }

        source_state = CreateTasksState.DRAFTING_TASKS.value

        states = [
            CreateTasksState.DISPATCHING.value,
            source_state,
            f"{source_state}_awaiting_ai_review",
            f"{source_state}_awaiting_human_review",
            CreateTasksState.VERIFIED.value,
        ]

        transitions = [
            {"trigger": "dispatch", "source": CreateTasksState.DISPATCHING.value, "dest": source_state},
            *self._create_review_transitions(source_state=source_state, success_destination_state=CreateTasksState.VERIFIED.value),
        ]
        self.machine = Machine(model=self, states=states, transitions=transitions, initial=CreateTasksState.DISPATCHING.value, auto_transitions=False)

    def get_final_work_state(self) -> str:
        return CreateTasksState.DRAFTING_TASKS.value

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

    def append_to_scratchpad(self, task_id: str, state_name: str = None, artifact: BaseModel = None, content: str = None):
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
                "artifact": artifact
            }
            rendered_content = template.render(context)

        with scratchpad_path.open("a", encoding="utf-8") as f:
            if scratchpad_path.stat().st_size > 0:
                f.write("\n\n---\n\n")
            f.write(rendered_content)
        logger.info(f"Appended rendered artifact '{template_name_snake}' to scratchpad for task {task_id}")

    def archive_scratchpad(self, task_id: str, tool_name: str, workflow_step: int):
        """Moves the current scratchpad to a versioned file in the archive and creates a new empty scratchpad."""
        scratchpad_path = self._get_scratchpad_path(task_id)
        if not scratchpad_path.exists():
            logger.warning(f"No scratchpad found for task {task_id} to archive.")
            return

        archive_dir = self._get_archive_dir(task_id)
        # Clean filename without _scratchpad suffix
        archive_filename = f"{workflow_step:02d}-{tool_name.replace('_', '-')}.md"
        archive_path = archive_dir / archive_filename

        scratchpad_path.rename(archive_path)
        scratchpad_path.touch()
        logger.info(f"Archived scratchpad for tool '{tool_name}' to {archive_path}")

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
    
    def archive_final_artifact(self, task_id: str, tool_name: str, artifact_data: dict):
        """Saves the final, certified artifact to a permanent location in the archive."""
        logger.info(f"ARCHIVING final artifact from tool '{tool_name}' for task '{task_id}'.")
        
        # Special handling for plan_task - save execution plan as JSON
        if tool_name == "plan_task" and isinstance(artifact_data, dict):
            # If it's the ExecutionPlanArtifact, save it as planning_execution_plan.json
            if "subtasks" in artifact_data:
                self.write_json_artifact(task_id, "planning_execution_plan.json", artifact_data)
            else:
                # For other artifacts, use a generic name
                filename = f"{tool_name}_final_artifact.json"
                self.write_json_artifact(task_id, filename, artifact_data)
        elif hasattr(artifact_data, 'model_dump'):
            # Handle Pydantic models
            filename = f"{tool_name}_final_artifact.json"
            self.write_json_artifact(task_id, filename, artifact_data.model_dump())
        else:
            # Generic handling
            filename = f"{tool_name}_final_artifact.json"
            self.write_json_artifact(task_id, filename, artifact_data)


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
from typing import Dict, List, Tuple, Optional


class MarkdownTaskParser:
    """Parses a task definition from a markdown string."""
    
    def validate_format(self, markdown_content: str) -> Tuple[bool, Optional[str]]:
        """Validates the markdown format and returns (is_valid, error_message)."""
        if not markdown_content.strip():
            return False, "Task file is empty"
            
        lines = markdown_content.split('\n')
        if not lines:
            return False, "Task file is empty"
            
        # Check first line format
        first_line = lines[0].strip()
        if not re.match(r"^#\s*TASK:\s*\S+", first_line):
            return False, f"First line must be '# TASK: <task_id>', found: '{first_line}'"
            
        # Check for required sections
        required_sections = ['Title', 'Context', 'Implementation Details', 'Acceptance Criteria']
        found_sections = []
        for line in lines:
            if line.strip().startswith('##'):
                section = line.strip().replace('##', '').strip()
                found_sections.append(section)
                
        missing_sections = []
        for required in required_sections:
            if not any(required.lower() in found.lower() for found in found_sections):
                missing_sections.append(f"## {required}")
                
        if missing_sections:
            return False, f"Missing required sections: {', '.join(missing_sections)}"
            
        return True, None

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
from src.alfred.lib.logger import get_logger
from src.alfred.config.settings import settings

logger = get_logger(__name__)


def load_task(task_id: str, root_dir: Optional[Path] = None) -> Task | None:
    """
    Loads a Task using the configured task provider.

    This function now uses the task provider factory to ensure consistent
    task loading across the application, regardless of the underlying
    data source (local files, Jira, Linear, etc.).

    Args:
        task_id: The ID of the task to load
        root_dir: Optional root directory (preserved for backward compatibility,
                 but may be ignored by non-local providers)
                 
    Returns:
        Task object if found, None otherwise
    """
    try:
        # Use the task provider factory to get the configured provider
        from src.alfred.task_providers.factory import get_provider
        
        provider = get_provider()
        
        # Note: The root_dir parameter is preserved for backward compatibility
        # but is only relevant for local providers. Other providers (Jira, Linear)
        # will ignore this parameter.
        if root_dir:
            logger.warning(
                f"root_dir parameter provided to load_task, but may be ignored by "
                f"non-local task providers. Consider removing this parameter."
            )
        
        return provider.get_task(task_id)
        
    except Exception as e:
        logger.error(f"Failed to load task {task_id}: {e}")
        return None


def does_task_exist_locally(task_id: str) -> bool:
    """
    Check if a task exists in the local cache.
    
    Args:
        task_id: The task identifier
        
    Returns:
        True if the task file exists locally, False otherwise
    """
    task_file = settings.alfred_dir / "tasks" / f"{task_id}.md"
    return task_file.exists()


def write_task_to_markdown(task: Task) -> None:
    """
    Write a Task object to markdown format in the local cache.
    
    Args:
        task: The Task object to write
    """
    tasks_dir = settings.alfred_dir / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    
    # Build markdown content
    content_parts = [f"# TASK: {task.task_id}"]
    
    if task.title:
        content_parts.append(f"\n## Title\n{task.title}")
    
    if hasattr(task, 'priority') and task.priority:
        content_parts.append(f"\n## Priority\n{task.priority}")
    
    if hasattr(task, 'summary') and task.summary:
        content_parts.append(f"\n## Summary\n{task.summary}")
    
    if hasattr(task, 'description') and task.description:
        content_parts.append(f"\n## Description\n{task.description}")
        
    if hasattr(task, 'context') and task.context:
        content_parts.append(f"\n## Context\n{task.context}")
    
    if task.acceptance_criteria:
        content_parts.append("\n## Acceptance Criteria")
        for criterion in task.acceptance_criteria:
            content_parts.append(f"- {criterion}")
    
    if hasattr(task, 'implementation_details') and task.implementation_details:
        content_parts.append(f"\n## Implementation Details\n{task.implementation_details}")
    
    if hasattr(task, 'dev_notes') and task.dev_notes:
        content_parts.append(f"\n## Dev Notes\n{task.dev_notes}")
    
    # Write to file
    task_file = tasks_dir / f"{task.task_id}.md"
    task_file.write_text("\n".join(content_parts), encoding="utf-8")
    
    logger.info(f"Wrote task {task.task_id} to {task_file}")


def get_local_task_path(task_id: str) -> Path:
    """
    Get the path to a local task file.
    
    Args:
        task_id: The task identifier
        
    Returns:
        Path to the task markdown file
    """
    return settings.alfred_dir / "tasks" / f"{task_id}.md"
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
Pydantic models for parsing workflow configurations.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """
    Represents the validated configuration of a workflow.
    """

    # Add any workflow-specific configuration here if needed
    pass

``````
------ src/alfred/models/engineering_spec.py ------
``````
# src/alfred/models/engineering_spec.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ReviewerStatus(BaseModel):
    reviewer: str
    status: str
    notes: Optional[str] = None


class SuccessMetrics(BaseModel):
    product_perspective: str
    engineering_perspective: str


class Requirement(BaseModel):
    story: str  # "As a user, I want to..."


class ApiDetails(BaseModel):
    name_and_method: str
    description: str


class DataStorageField(BaseModel):
    field_name: str
    is_required: bool
    data_type: str
    description: str
    example: str


class ABTestTreatment(BaseModel):
    treatment_name: str
    description: str


class ABTest(BaseModel):
    trial_name: str
    control: str
    treatments: List[ABTestTreatment]


class EngineeringSpec(BaseModel):
    project_name: str
    overview: str
    review_status: List[ReviewerStatus] = Field(default_factory=list)
    definition_of_success: SuccessMetrics
    glossary: Optional[Dict[str, str]] = Field(default_factory=dict)

    functional_requirements: List[Requirement] = Field(default_factory=list)
    non_functional_requirements: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    # Design Section
    major_design_considerations: str
    architecture_diagrams: Optional[str] = None  # Text description, link to diagram
    api_changes: List[ApiDetails] = Field(default_factory=list)
    api_usage_estimates: Optional[str] = None
    event_flows: Optional[str] = None
    frontend_updates: Optional[str] = None
    data_storage: List[DataStorageField] = Field(default_factory=list)
    auth_details: Optional[str] = None
    resiliency_plan: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    dependents: List[str] = Field(default_factory=list)

    # Observability Section
    failure_scenarios: str
    logging_plan: str
    metrics_plan: str
    monitoring_plan: str

    # Testing Section
    testing_approach: str
    new_technologies_considered: Optional[str] = None

    # Rollout Section
    rollout_plan: str
    release_milestones: str
    ab_testing: List[ABTest] = Field(default_factory=list)

    alternatives_considered: Optional[str] = None
    misc_considerations: Optional[str] = None

``````
------ src/alfred/models/planning_artifacts.py ------
``````
# src/alfred/models/planning_artifacts.py
from pydantic import BaseModel, Field
from typing import List, Dict, Literal
from .schemas import Subtask, Task


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


class ImplementationManifestArtifact(BaseModel):
    summary: str
    completed_subtasks: List[str]
    testing_notes: str


class ReviewArtifact(BaseModel):
    summary: str
    approved: bool
    feedback: List[str]


class TestResultArtifact(BaseModel):
    command: str
    exit_code: int
    output: str


class FinalizeArtifact(BaseModel):
    commit_hash: str
    pr_url: str


# Pre-planning Phase Artifacts
class PRDInputArtifact(BaseModel):
    prd_content: str = Field(description="The raw text or content of the Product Requirements Document.")


class TaskCreationArtifact(BaseModel):
    tasks: List[Task] = Field(description="A list of all generated Task objects.")

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
    CREATING_SPEC = "creating_spec"
    SPEC_COMPLETED = "spec_completed"
    CREATING_TASKS = "creating_tasks"
    TASKS_CREATED = "tasks_created"
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
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskState(BaseModel):
    """
    The single state object for a task.
    This is the schema for the `task_state.json` file.
    """

    task_id: str
    task_status: TaskStatus = Field(default=TaskStatus.NEW)
    active_tool_state: Optional[WorkflowState] = Field(default=None)
    completed_tool_outputs: Dict[str, Any] = Field(default_factory=dict)
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
------ src/alfred/server.py ------
``````
# src/alfred/server.py
"""
MCP Server for Alfred
This version preserves the original comprehensive docstrings while maintaining
the clean V2 Alfred architecture.
"""

import functools
import inspect
from typing import Callable

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.approve_and_advance import approve_and_advance_impl
from src.alfred.tools.create_spec import create_spec_impl
from src.alfred.tools.create_tasks import create_tasks_impl
from src.alfred.tools.finalize_task import finalize_task_impl
from src.alfred.tools.get_next_task import get_next_task_impl
from src.alfred.tools.implement_task import implement_task_impl
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl
from src.alfred.tools.progress import mark_subtask_complete_impl
from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.tools.review_task import review_task_impl
from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.tools.test_task import test_task_impl
from src.alfred.tools.work_on import work_on_impl

app = FastMCP(settings.server_name)


def log_tool_transaction(impl_func: Callable) -> Callable:
    """Decorator factory that creates a logging wrapper for tool functions.

    This decorator expects the implementation function to be passed as an argument.
    It handles both sync and async implementation functions.
    """

    def decorator(tool_func: Callable) -> Callable:
        @functools.wraps(tool_func)
        async def wrapper(*args, **kwargs) -> ToolResponse:
            tool_name = tool_func.__name__

            # Extract task_id from kwargs if present
            task_id = kwargs.get("task_id", None)

            # Build request data from kwargs
            request_data = {k: v for k, v in kwargs.items() if v is not None}

            # Call the implementation function (handle both async and sync)
            if inspect.iscoroutinefunction(impl_func):
                response = await impl_func(**kwargs)
            else:
                response = impl_func(**kwargs)

            # Log the transaction
            transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)

            return response

        return wrapper

    return decorator


@app.tool()
@log_tool_transaction(initialize_project_impl)
async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initializes the project workspace for Alfred by creating the .alfred directory with default configurations for workflows.

    - **Primary Function**: Sets up a new project for use with the Alfred workflow system.
    - **Key Features**:
      - Interactive provider selection when no provider is specified.
      - Creates the necessary `.alfred` directory structure.
      - Deploys default `workflow.yml` configuration file.
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
    return initialize_project_impl(provider)


@app.tool()
@log_tool_transaction(get_next_task_impl)
async def get_next_task() -> ToolResponse:
    """
    Intelligently determines and recommends the next task to work on.

    This tool analyzes all available tasks and their current states to provide
    an intelligent recommendation for what to work on next. It prioritizes based on:

    - Tasks already in progress (to avoid context switching)
    - Tasks ready for immediate action
    - Task dependencies and blockers
    - Task age and priority

    The recommendation includes reasoning for why this task was chosen and
    alternatives if you prefer to work on something else.

    Returns:
        ToolResponse: Contains the recommended task with:
        - task_id: The recommended task identifier
        - title: Task title for context
        - status: Current task status
        - reasoning: Why this task was recommended
        - alternatives: Other tasks you could work on
        - next_prompt: Suggested command to start working

    Example:
        get_next_task() -> Recommends "AL-42" with reasoning and alternatives
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(work_on_impl)
async def work_on_task(task_id: str) -> ToolResponse:
    """
    Primary entry point for working on any task - the Smart Dispatch model.

    This tool intelligently routes users to the appropriate specialized tool
    based on the current task status. It examines the task state and provides
    clear guidance on which tool to use next.

    Task Status Routing:
    - NEW: Routes to plan_task for creating execution plan
    - PLANNING: Routes to plan_task to continue planning
    - READY_FOR_DEVELOPMENT: Routes to implement_task to start implementation
    - IN_PROGRESS: Routes to implement_task to continue implementation
    - COMPLETED: Informs user the task is complete

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")

    Returns:
        ToolResponse: Contains routing guidance to the appropriate specialized tool

    Example:
        work_on_task("TS-01") -> Guides to plan_task if task is new
        work_on_task("TS-02") -> Guides to implement_task if planning is complete
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(create_spec_impl)
async def create_spec(task_id: str, prd_content: str) -> ToolResponse:
    """
    Creates a technical specification from a Product Requirements Document (PRD).

    This is the first tool in the "idea-to-code" pipeline. It transforms a PRD
    into a structured Technical Specification that serves as the foundation for
    engineering planning and implementation.

    The tool guides through creating a comprehensive spec including:
    - Background and business context
    - Technical goals and non-goals
    - Proposed architecture
    - System boundaries and APIs
    - Data model changes
    - Security considerations
    - Open questions

    Args:
        task_id (str): The unique identifier for the epic/feature (e.g., "EPIC-01")
        prd_content (str): The raw PRD content to analyze and transform

    Returns:
        ToolResponse: Contains the first prompt to guide spec creation

    Example:
        create_spec("EPIC-01", "Build a notification system...") -> Guides spec creation
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(create_tasks_impl)
async def create_tasks(task_id: str) -> ToolResponse:
    """
    Creates a list of actionable tasks from a Technical Specification.

    This is the second tool in the "idea-to-code" pipeline. It takes a completed
    Technical Specification and breaks it down into individual Task objects that
    can be tracked, assigned, and implemented independently.

    The tool guides through creating tasks that are:
    - Atomic and focused
    - Properly ordered with dependencies
    - Sized appropriately (1-3 days of work)
    - Complete with acceptance criteria

    Args:
        task_id (str): The unique identifier for the epic/feature with a completed spec

    Returns:
        ToolResponse: Contains the first prompt to guide task breakdown

    Preconditions:
        - Technical specification must be completed (via create_spec)
        - Task status must be "spec_completed"

    Example:
        create_tasks("EPIC-01") -> Guides creation of task list from spec
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(plan_task_impl)
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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(submit_work_impl)
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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(provide_review_impl)
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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(mark_subtask_complete_impl)
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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(implement_task_impl)
async def implement_task(task_id: str) -> ToolResponse:
    """
    Executes the implementation phase for a task that has completed planning.

    This tool is used after the planning phase is complete and the task status
    is READY_FOR_DEVELOPMENT. It guides the implementation of the execution plan
    created during the planning phase.

    Prerequisites:
    - Task must have status READY_FOR_DEVELOPMENT
    - Execution plan must exist from completed planning phase

    The tool manages:
    - Loading the execution plan from the planning phase
    - Tracking progress on individual subtasks
    - Maintaining implementation state across sessions

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")

    Returns:
        ToolResponse: Contains success/error status and implementation guidance

    Example:
        implement_task("TS-01") -> Starts implementation of planned task
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(review_task_impl)
async def review_task(task_id: str) -> ToolResponse:
    """
    Initiates the code review phase for a task that has completed implementation.

    This tool manages the review process where the implementation is checked
    against requirements, best practices, and quality standards.

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status and review guidance
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(test_task_impl)
async def test_task(task_id: str) -> ToolResponse:
    """
    Initiates the testing phase for a task that has passed code review.

    This tool manages the test execution process including unit tests,
    integration tests, and verification of the implementation.

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status and test results
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(finalize_task_impl)
async def finalize_task(task_id: str) -> ToolResponse:
    """
    Completes the task by creating a commit and pull request.

    This tool manages the finalization process including:
    - Creating a git commit with changes
    - Creating a pull request
    - Updating task status to completed

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status with PR details
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(approve_and_advance_impl)
async def approve_and_advance(task_id: str) -> ToolResponse:
    """
    Approves the current phase and advances to the next phase in the workflow.

    This is a convenience tool that automatically approves the current review
    step and advances the workflow to the next phase.

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status and next phase guidance
    """
    pass  # Implementation handled by decorator


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
State management for Alfred.
Provides atomic state persistence for the TaskState object.
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
from src.alfred.models.state import TaskState, WorkflowState

logger = get_logger(__name__)


class StateManager:
    """Manages the persistent state for a single task via task_state.json."""

    def _get_task_state_file(self, task_id: str) -> Path:
        """Gets the path to the unified state file for a task."""
        return settings.workspace_dir / task_id / "task_state.json"

    def load_or_create(self, task_id: str) -> TaskState:
        """Loads a task's unified state from disk, or creates it if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)
        if not state_file.exists():
            logger.info(f"No state file found for task {task_id}. Creating new state.")
            new_state = TaskState(task_id=task_id)
            self.save_task_state(new_state)
            return new_state

        try:
            state_json = state_file.read_text()
            state_data = TaskState.model_validate_json(state_json)
            tool_name = state_data.active_tool_state.tool_name if state_data.active_tool_state else "None"
            logger.info(f"Loaded state for task {task_id}. Status: {state_data.task_status.value}, Active Tool: {tool_name}.")
            return state_data
        except Exception as e:
            logger.error(f"Failed to load or validate state for task {task_id}, creating new state. Error: {e}")
            new_state = TaskState(task_id=task_id)
            self.save_task_state(new_state)
            return new_state

    def save_task_state(self, state: TaskState) -> None:
        """Atomically saves the entire unified state for a task."""
        from src.alfred.lib.artifact_manager import artifact_manager

        state.updated_at = datetime.utcnow().isoformat()
        state_file = self._get_task_state_file(state.task_id)

        # Ensure the complete workspace structure is created (including archive dir)
        if not state_file.parent.exists():
            artifact_manager.create_task_workspace(state.task_id)

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

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> TaskState:
        """Loads, updates the task_status, and saves the state."""
        state = self.load_or_create(task_id)
        state.task_status = new_status
        self.save_task_state(state)
        logger.info(f"Updated task {task_id} status to {new_status.value}")
        return state

    def update_tool_state(self, task_id: str, tool: "BaseWorkflowTool") -> TaskState:
        """Loads, updates the tool state portion, and saves."""
        state = self.load_or_create(task_id)

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
            updated_at=datetime.utcnow().isoformat(),
        )
        state.active_tool_state = tool_state_data
        self.save_task_state(state)
        return state

    def clear_tool_state(self, task_id: str) -> TaskState:
        """Loads, clears the active tool state, and saves."""
        state = self.load_or_create(task_id)
        if state.active_tool_state:
            logger.info(f"Clearing active tool state for task {task_id}.")
            state.active_tool_state = None
            self.save_task_state(state)
        return state

    def load_or_create_task_state(self, task_id: str) -> TaskState:
        return self.load_or_create(task_id)

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        archive_path = settings.workspace_dir / task_id / Paths.ARCHIVE_DIR
        archive_path.mkdir(parents=True, exist_ok=True)
        return archive_path

    def register_tool(self, task_id: str, tool: "BaseWorkflowTool") -> None:
        """Register a tool with the orchestrator and update state."""
        from src.alfred.orchestration.orchestrator import orchestrator

        orchestrator.active_tools[task_id] = tool
        self.update_tool_state(task_id, tool)
        logger.info(f"Registered {tool.tool_name} tool for task {task_id}")


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

from src.alfred.core.workflow import (
    BaseWorkflowTool,
    CreateSpecTool,
    CreateTasksTool,
    PlanTaskTool,
    StartTaskTool,
    ImplementTaskTool,
    ReviewTaskTool,
    TestTaskTool,
    FinalizeTaskTool,
)
from src.alfred.lib.logger import get_logger
from src.alfred.state.manager import state_manager
from src.alfred.constants import ToolName

logger = get_logger(__name__)


class ToolRecovery:
    """Handles recovery of workflow tools from persisted state."""

    TOOL_REGISTRY: Dict[str, Type[BaseWorkflowTool]] = {
        ToolName.CREATE_SPEC: CreateSpecTool,
        ToolName.CREATE_TASKS: CreateTasksTool,
        ToolName.START_TASK: StartTaskTool,
        ToolName.PLAN_TASK: PlanTaskTool,
        ToolName.IMPLEMENT_TASK: ImplementTaskTool,
        ToolName.REVIEW_TASK: ReviewTaskTool,
        ToolName.TEST_TASK: TestTaskTool,
        ToolName.FINALIZE_TASK: FinalizeTaskTool,
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

            logger.info(f"Successfully recovered {tool_name} for task {task_id} in state {tool.state}")
            return tool
        except Exception as e:
            logger.error(f"Failed to recover tool for task {task_id}: {e}", exc_info=True)
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


def recover_tool_from_state(task_id: str, tool_name: str) -> BaseWorkflowTool:
    """
    Helper function to recover or create a tool for the given task and tool name.
    This is used by the individual tool implementations.
    """
    from src.alfred.orchestration.orchestrator import orchestrator

    # Check if tool is already active
    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
        return tool_instance

    # Try to recover from persisted state
    tool_instance = ToolRecovery.recover_tool(task_id)
    if tool_instance:
        orchestrator.active_tools[task_id] = tool_instance
        logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        return tool_instance

    # Create new tool
    tool_class = ToolRecovery.TOOL_REGISTRY.get(tool_name)
    if not tool_class:
        raise ValueError(f"Unknown tool type: {tool_name}")

    tool_instance = tool_class(task_id=task_id)
    orchestrator.active_tools[task_id] = tool_instance

    # Persist the initial state
    state_manager.update_tool_state(task_id, tool_instance)
    logger.info(f"Created new {tool_name} tool for task {task_id}")

    return tool_instance

``````
------ src/alfred/task_providers/__init__.py ------
``````
"""Task provider implementations for Alfred."""

``````
------ src/alfred/task_providers/base.py ------
``````
"""Base task provider interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.alfred.models.schemas import Task, ToolResponse


class BaseTaskProvider(ABC):
    """Abstract base class for all task providers.

    This defines the contract that all task providers must implement,
    ensuring a consistent interface regardless of the underlying data source.
    """

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        """Fetches the details for a single task.

        Args:
            task_id: The unique identifier for the task

        Returns:
            Task object if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all_tasks(self) -> List[Task]:
        """Fetches all available tasks from the source.

        Returns:
            List of all tasks from the provider
        """
        pass

    @abstractmethod
    def get_next_task(self) -> ToolResponse:
        """Intelligently determines and returns the next recommended task.

        Returns:
            ToolResponse containing the recommended task and reasoning
        """
        pass

    @abstractmethod
    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Updates the status of a task.

        Args:
            task_id: The unique identifier for the task
            new_status: The new status to set

        Returns:
            True if update was successful, False otherwise
        """
        pass

``````
------ src/alfred/task_providers/factory.py ------
``````
"""Task provider factory for instantiating the correct provider based on configuration."""

from src.alfred.models.alfred_config import TaskProvider as ProviderType
from src.alfred.lib.logger import get_logger
from .base import BaseTaskProvider
from .local_provider import LocalTaskProvider
from .jira_provider import JiraTaskProvider

logger = get_logger(__name__)


def get_provider() -> BaseTaskProvider:
    """Factory function to instantiate the configured task provider.

    This function reads the current Alfred configuration and returns
    the appropriate task provider instance based on the configured
    provider type.

    Returns:
        BaseTaskProvider: An instance of the configured task provider

    Raises:
        NotImplementedError: If the configured provider is not yet implemented
    """
    # Import here to avoid circular dependency
    from src.alfred.orchestration.orchestrator import orchestrator

    try:
        # Load the current configuration
        config = orchestrator.config_manager.load()
        provider_type = config.providers.task_provider

        logger.info(f"Instantiating task provider: {provider_type}")

        # Return the appropriate provider based on configuration
        if provider_type == ProviderType.LOCAL:
            return LocalTaskProvider()
        elif provider_type == ProviderType.JIRA:
            return JiraTaskProvider()
        elif provider_type == ProviderType.LINEAR:
            raise NotImplementedError(f"Linear task provider is not yet implemented. Please use 'local' provider for now.")
        else:
            raise NotImplementedError(f"Unknown task provider type: '{provider_type}'. Supported providers: local, jira (coming soon), linear (coming soon)")

    except Exception as e:
        logger.error(f"Failed to instantiate task provider: {e}")
        # Fall back to local provider as default
        logger.warning("Falling back to local task provider")
        return LocalTaskProvider()

``````
------ src/alfred/task_providers/jira_provider.py ------
``````
"""Jira task provider implementation (placeholder for AL-65 testing)."""

from typing import List, Optional
from datetime import datetime

from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.lib.logger import get_logger
from .base import BaseTaskProvider

logger = get_logger(__name__)


class JiraTaskProvider(BaseTaskProvider):
    """Task provider that fetches tasks from Jira via MCP.

    This is a placeholder implementation for AL-65 testing.
    In production, this will make actual API calls via MCP tools.
    """

    def __init__(self):
        """Initialize the Jira task provider."""
        logger.info("Initializing JiraTaskProvider (placeholder implementation)")

    def get_task(self, task_id: str) -> Optional[Task]:
        """Fetches a task from Jira.

        This is a placeholder that returns hardcoded data for testing.
        In production, this will call MCP Atlassian tools.

        Args:
            task_id: The Jira issue key (e.g., "TS-01")

        Returns:
            Task object if found, None otherwise
        """
        # Placeholder implementation - return hardcoded task for testing
        if task_id == "TS-01":
            logger.info(f"Returning placeholder Jira task for {task_id}")
            return Task(
                task_id="TS-01",
                title="Implement user authentication",
                description="""As a user, I want to be able to log in to the application
so that I can access my personalized content and features.

This involves implementing a secure authentication system with the following components:
- Login form with email/password
- Password hashing and validation
- Session management
- Remember me functionality
- Password reset flow""",
                acceptance_criteria=[
                    "Users can log in with email and password",
                    "Passwords are securely hashed using bcrypt",
                    "Sessions persist across browser restarts when 'Remember me' is checked",
                    "Users can reset their password via email",
                    "Failed login attempts are rate-limited",
                ],
                task_status=TaskStatus.NEW,
            )

        logger.warning(f"Task {task_id} not found in Jira (placeholder)")
        return None

    def get_all_tasks(self) -> List[Task]:
        """Fetches all tasks from Jira.

        This is a placeholder that returns an empty list.
        In production, this will use JQL queries via MCP.

        Returns:
            List of tasks (empty in placeholder)
        """
        logger.info("get_all_tasks called on JiraTaskProvider (not implemented)")
        return []

    def get_next_task(self) -> ToolResponse:
        """Get next task recommendation.

        For Jira provider, this would analyze the project board.
        Currently returns a placeholder response.

        Returns:
            ToolResponse indicating this feature is not yet implemented
        """
        return ToolResponse(status="error", message="get_next_task is not yet implemented for Jira provider. Please specify a task ID directly.")

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Updates task status in Jira.

        This is a placeholder that logs the update.
        In production, this will transition the Jira issue.

        Args:
            task_id: The Jira issue key
            new_status: The new status

        Returns:
            True (placeholder always succeeds)
        """
        logger.info(f"Would update Jira task {task_id} to status {new_status} (placeholder)")
        return True

``````
------ src/alfred/task_providers/local_provider.py ------
``````
"""Local file system task provider implementation."""

import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.lib.md_parser import MarkdownTaskParser
from src.alfred.lib.logger import get_logger
from src.alfred.config.settings import settings
from src.alfred.state.manager import state_manager
from .base import BaseTaskProvider

logger = get_logger(__name__)


class LocalTaskProvider(BaseTaskProvider):
    """Task provider that reads tasks from local markdown files.

    This provider implements the BaseTaskProvider interface for local
    file system based task management, reading from .alfred/tasks/*.md files.
    """

    def __init__(self):
        """Initialize the local task provider."""
        self.tasks_dir = settings.alfred_dir / "tasks"
        self.parser = MarkdownTaskParser()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Fetches the details for a single task from markdown file.

        Args:
            task_id: The unique identifier for the task

        Returns:
            Task object if found, None otherwise
        """
        task_md_path = self.tasks_dir / f"{task_id}.md"

        if not task_md_path.exists():
            logger.warning(f"Task file not found: {task_md_path}")
            return None

        try:
            # Read and validate the markdown file
            content = task_md_path.read_text()
            
            # Validate format first
            is_valid, error_msg = self.parser.validate_format(content)
            if not is_valid:
                logger.error(f"Task file {task_md_path} has invalid format: {error_msg}")
                logger.error(f"Please refer to .alfred/tasks/README.md for the correct task file format.")
                logger.error(f"See .alfred/tasks/SAMPLE-FORMAT.md for a working example.")
                return None
            
            # Parse the markdown file
            task_data = self.parser.parse(content)
            
            # Validate required fields and provide helpful error if missing
            if not task_data.get('task_id'):
                logger.error(f"Task file {task_md_path} is missing task_id. Expected format: '# TASK: {task_id}'")
                logger.error(f"Current format in file: {content.split('\\n')[0] if content else 'Empty file'}")
                return None
                
            task_model = Task(**task_data)

            # Load and merge the dynamic state
            task_state = state_manager.load_or_create(task_id)
            task_model.task_status = task_state.task_status

            return task_model
        except ValueError as e:
            logger.error(f"Task file {task_md_path} has invalid format: {e}")
            logger.error(f"Please refer to .alfred/tasks/README.md for the correct task file format.")
            logger.error(f"See .alfred/tasks/SAMPLE-FORMAT.md for a working example.")
            return None
        except Exception as e:
            logger.error(f"Failed to load task {task_id} from {task_md_path}: {e}")
            return None

    def get_all_tasks(self) -> List[Task]:
        """Fetches all available tasks from the tasks directory.

        Returns:
            List of all tasks found in the .alfred/tasks directory
        """
        tasks = []

        if not self.tasks_dir.exists():
            logger.warning(f"Tasks directory does not exist: {self.tasks_dir}")
            return tasks

        for task_file in self.tasks_dir.glob("*.md"):
            task_id = task_file.stem
            task = self.get_task(task_id)
            if task:
                tasks.append(task)

        return tasks

    def get_next_task(self) -> ToolResponse:
        """Intelligently determines and returns the next recommended task.

        This implementation uses the AL-61 ranking algorithm to prioritize tasks.

        Returns:
            ToolResponse containing the recommended task and reasoning
        """
        try:
            all_tasks = self.get_all_tasks()

            if not all_tasks:
                return ToolResponse(status="success", message="No tasks found in the system. Please create tasks first.", data={"tasks_found": 0})

            # Filter out completed tasks
            active_tasks = [t for t in all_tasks if t.task_status != TaskStatus.DONE]

            if not active_tasks:
                return ToolResponse(status="success", message="All tasks are completed! Great work!", data={"tasks_found": len(all_tasks), "active_tasks": 0})

            # Rank tasks using our prioritization algorithm
            ranked_tasks = self._rank_tasks(active_tasks)

            # Get the top task
            recommended_task = ranked_tasks[0]

            # Generate reasoning for the recommendation
            reasoning = self._generate_recommendation_reasoning(recommended_task, ranked_tasks)

            return ToolResponse(
                status="success",
                message=f"Recommended task: {recommended_task.task_id} - {recommended_task.title}",
                data={
                    "task_id": recommended_task.task_id,
                    "title": recommended_task.title,
                    "status": recommended_task.task_status.value,
                    "reasoning": reasoning,
                    "total_active_tasks": len(active_tasks),
                    "alternatives": [
                        {"task_id": t.task_id, "title": t.title, "status": t.task_status.value}
                        for t in ranked_tasks[1:4]  # Show top 3 alternatives
                    ],
                },
                next_prompt=f"Task {recommended_task.task_id} is ready. Use 'work_on {recommended_task.task_id}' to begin.",
            )
        except Exception as e:
            logger.error(f"Failed to get next task: {e}")
            return ToolResponse(status="error", message=f"Failed to determine next task: {str(e)}")

    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Updates the status of a task.

        Args:
            task_id: The unique identifier for the task
            new_status: The new status to set

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Convert string to TaskStatus enum
            status_enum = TaskStatus(new_status)

            # Update via state manager
            state_manager.update_task_status(task_id, status_enum)

            return True
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status to {new_status}: {e}")
            return False

    def _rank_tasks(self, tasks: List[Task]) -> List[Task]:
        """Rank tasks based on the AL-61 prioritization algorithm.

        Priority factors:
        1. In-progress tasks (highest priority)
        2. Tasks ready for action
        3. Priority level (if available)
        4. Task age (older tasks get slight boost)
        """

        def calculate_score(task: Task) -> tuple:
            # Score is a tuple for stable sorting (higher is better)

            # First priority: In-progress tasks
            in_progress_score = (
                1 if task.task_status in [TaskStatus.IN_DEVELOPMENT, TaskStatus.IN_REVIEW, TaskStatus.IN_TESTING, TaskStatus.PLANNING, TaskStatus.CREATING_SPEC, TaskStatus.CREATING_TASKS] else 0
            )

            # Second priority: Ready for action
            ready_score = (
                1
                if task.task_status
                in [TaskStatus.NEW, TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.READY_FOR_REVIEW, TaskStatus.READY_FOR_TESTING, TaskStatus.READY_FOR_FINALIZATION, TaskStatus.REVISIONS_REQUESTED]
                else 0
            )

            # Third priority: Task ID numeric value (lower ID = older task = higher priority)
            # Extract numeric part from task ID (e.g., "AL-42" -> 42)
            try:
                task_number = int(task.task_id.split("-")[-1])
                # Invert so lower numbers get higher scores
                age_score = 1000 - task_number
            except:
                age_score = 0

            return (in_progress_score, ready_score, age_score)

        # Sort tasks by score (descending)
        return sorted(tasks, key=calculate_score, reverse=True)

    def _generate_recommendation_reasoning(self, task: Task, all_ranked: List[Task]) -> str:
        """Generate human-readable reasoning for why this task was recommended."""
        reasons = []

        # Check if it's in progress
        if task.task_status in [TaskStatus.IN_DEVELOPMENT, TaskStatus.IN_REVIEW, TaskStatus.IN_TESTING, TaskStatus.PLANNING]:
            reasons.append(f"Task is already in progress ({task.task_status.value})")

        # Check if it's ready for action
        elif task.task_status in [TaskStatus.NEW, TaskStatus.READY_FOR_DEVELOPMENT]:
            reasons.append(f"Task is ready to start ({task.task_status.value})")

        # Check if it needs attention
        elif task.task_status == TaskStatus.REVISIONS_REQUESTED:
            reasons.append("Task has requested revisions that need to be addressed")

        # Add context about alternatives
        if len(all_ranked) > 1:
            reasons.append(f"Selected from {len(all_ranked)} active tasks based on priority")

        return ". ".join(reasons) + "."

``````
------ src/alfred/templates/__init__.py ------
``````

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
------ src/alfred/templates/artifacts/engineering_spec.md ------
``````
# Engineering Specification: {{ artifact.project_name }}

## Overview
{{ artifact.overview }}

## Definition of Success

### Product Perspective
{{ artifact.definition_of_success.product_perspective }}

### Engineering Perspective
{{ artifact.definition_of_success.engineering_perspective }}

## Functional Requirements
{% for req in artifact.functional_requirements %}
- {{ req.story }}
{% endfor %}

## Non-Functional Requirements
{% for req in artifact.non_functional_requirements %}
- {{ req }}
{% endfor %}

## Assumptions
{% for assumption in artifact.assumptions %}
- {{ assumption }}
{% endfor %}

## Major Design Considerations
{{ artifact.major_design_considerations }}

## Architecture
{{ artifact.architecture_diagrams }}

## API Changes
{% for api in artifact.api_changes %}
- {{ api }}
{% endfor %}

## Data Storage
{% for storage in artifact.data_storage %}
- {{ storage }}
{% endfor %}

## Dependencies
{% for dep in artifact.dependencies %}
- {{ dep }}
{% endfor %}

## Testing Approach
{{ artifact.testing_approach }}

## Rollout Plan
{{ artifact.rollout_plan }}

## Alternatives Considered
{{ artifact.alternatives_considered }}
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
------ src/alfred/templates/artifacts/implementation_manifest.md ------
``````
# Implementation Manifest

## Summary
{{ artifact.summary }}

## Completed Subtasks
{% for subtask_id in artifact.completed_subtasks %}
- {{ subtask_id }}
{% endfor %}

## Testing Notes
{{ artifact.testing_notes }}
``````
------ src/alfred/templates/artifacts/review.md ------
``````
## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Review Summary
{{ artifact.summary }}

### Approval Status
**{{ "Approved" if artifact.approved else "Revisions Requested" }}**

### Feedback
{% if artifact.feedback %}
{% for item in artifact.feedback %}
- {{ item }}
{% endfor %}
{% else %}
- N/A
{% endif %}
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
------ src/alfred/templates/artifacts/task_creation.md ------
``````
# Task Breakdown

## Tasks Created

{% for task in artifact.tasks %}
### {{ task.task_id }}: {{ task.title }}

**Context:**  
{{ task.context }}

**Implementation Details:**  
{{ task.implementation_details }}

**Acceptance Criteria:**
{% for ac in task.acceptance_criteria %}
- {{ ac }}
{% endfor %}

**Verification Steps:**
{% for step in task.ac_verification_steps %}
- {{ step }}
{% endfor %}

---

{% endfor %}
``````
------ src/alfred/templates/artifacts/test_result.md ------
``````
## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Test Execution Summary
**Command:** `{{ artifact.command }}`
**Exit Code:** {{ artifact.exit_code }} ({{ "Success" if artifact.exit_code == 0 else "Failure" }})

### Full Output
```
{{ artifact.output }}
```
``````
------ src/alfred/templates/engineering_spec_template.md ------
``````
***For any sections that do not apply, DO NOT delete them but rather explain WHY they are not relevant.***   

# \[Project Name\] \- Engineering Spec



# Review Status

**\[Optional:** *Move to the bottom of the document once approved by everyone*\]


# Overview

\[*Provide a 1-2 paragraph overview of the project and the problem we are trying to solve. If there is a product brief, rely on that for most of the justification. If there is not a product brief, include justification for the project here. Additionally, the definition of success and the product perspective needs to be approved by Product before the spec is filled out.*\] 

| Product Reviewer | Status | Notes |
| :---- | :---- | :---- |
| Person | Unviewed |  |

## Definition of Success

\[*Provide context on what success looks like for this project.*\] 

### Product Perspective

\[*Describe how the above definition will be measured / quantified from a product perspective.*\] 

### Engineering Perspective

\[*Describe how the above definition will be measured / quantified from an engineering perspective.*\] 

## Glossary / Acronyms

\[*Include any terms and acronyms that should be defined for reference.*\] 

## Requirements

### Functional Requirements

*\[Provide all functional requirements as agile stories “As a user I want to X in order to doY”\]*

### Non-Functional requirements

*\[Provide all non functional requirements such as scalability, tps, etc\]*

## Assumptions

*\[Provide any assumptions about the domain\]*

# Design

## Major Design Considerations

\[*This is the main section where major details will be documented. This may be a list of functionality, behaviors, interactions, etc. Call out major concepts and any considerations or details that a reviewer would not otherwise expect to see in a project like this. List steps in the process and main components.*\]

## Architecture Diagrams

\[*Add architectural diagrams, sequence diagrams, or any other drawings that help give a high-level overview of the new system or the components that are changing. For each diagram, provide a 1-2 sentence description of what the diagram shows.*\]

## API

\[*Identify new APIs or APIs whose behavior will be updated.*\]

| API | Description |
| :---- | :---- |
| **\[*ApiName*\] \[Method\] \[Path\]** | \[*Description of API, request/response structure, status codes*\] |

### Usage Estimates

\[What is the call pattern for each API? What is the *expected volume (RPM/RPS) that could inform the need for any load tests.*\]

## Events

\[*Identify new event flows or events that will be updated at a high-level (e.g. new infrastructure or sequence diagrams)*\]

## Front End Updates

\[*If your feature or project includes front end changes add mocks for how the user experience is being changed. Be sure to include before and after which clearly articulates how our customers will use this. For Metro, this likely refers to either the Agent Customer Admin tool, or Metro UI.* \]

## Data Storage

\[*Where is data stored? List any new databases or tables, and provide information on stored values in the table. Include indexes and constraints. Describe any special considerations about how the data will be read and written, including frequency, expected volume, whether data can be deleted, backup, and expiration. Can the data be manually inspected for debugging or investigative purposes? Are there any provisions for updating incorrect data?*\]

| Field | isRequired | Data Type | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| \[***FieldName***\] | \[*Yes|No*\] | \[*Dependent on technology*\] | \[*Description of data meaning.*\] | \[*Example value*\] |

## Auth

\[*Can this be accessed internally or externally? Are there limitations on who can access it? How will that be enforced?*\]

## Resiliency

\[*Describe how the product will react to diverse conditions. Ensure that we have designed for failure and can succeed in as many cases as possible. Consider using queues and/or notifications to eliminate failures and the impact of disruptions. Outline plans for failover, rollback, and retries.*\] 

## Dependencies

\[*List dependencies, either existing components or new required components that are outside the scope of this design. What use cases on each dependency are you using ? Action item : Verify these use cases work as expected.  For service dependencies, by sure to specify tasks for setting up network access (via Kong gateway or similar), requesting required access keys or scope permissions, etc\]*

## Dependents

\[*List components that will be dependent on the new features. These may be existing dependents that will be impacted by the changes, or future dependents that will be added after this project is complete. These are also called upstream dependencies*\]

# Observability

## Failure Scenarios

\[*List out different failure scenarios and how we plan to handle them, whether it’s propagating errors to downstream dependencies, or handling the error to provide an alternate successful path. List each dependency and how the product will attempt to be successful despite the dependency’s outage. If the product itself breaks, how can we still attempt to provide success to our users (through manual means or dependents’ reactions.* \]

## Logging

\[*What info, warn, and error logs will be collected? What information will we need to investigate errors or interesting scenarios? Does any data need to be sent to DataLake?*\]

## Metrics

\[*What events deserve metrics to help us understand usage or health? What thresholds will be set for those metrics? What dashboards or reports will allow viewing of the metrics?*\]

## Monitoring

\[*What provisions are in place for ensuring the features are behaving as expected? How will the team know if the features are not working properly? Describe any new or existing Panoptes Monitors, Zon tests. Splunk / Umbra Dashboard metrics to track (latency, requests, dependencies to monitor). Include access and error logging to be monitored*\]

# Testing

\[*Describe our approach to testing the features. Consider test automation (unit tests, integration tests, user acceptance tests), post deployment tests (pre-prod and/or prod), exploratory testing, static analysis tool, security analysis tool, and code coverage. Be explicit about test priority. Define the quality criteria the features must meet. Are there any designs that need to be considered to enable the testability of the features? What services will need to be mocked and what mocked data is required during development?\]* 

## Integration Tests

## Internal (Manual) Tests

## Performance/Load Tests

## End to End Test

## New technologies considered

*\[List new technologies considered, if you haven’t considered them please take a minute to explore how new technologies could help\]*

# Rollout Plan

\[*How will this feature be rolled out? Will it be turned on in stages? Do any components need to be rolled out in order? Are there any dependencies that need to be in place before this feature? How will we validate the release(s) or decide to rollback? 
## Pre Launch Checklist

## Launch Checklist

## Post Launch Checklist

## A/B Testing

\[*What existing A/B trials will impact this feature? Are any new A/B trials planned for experimentation or rollout? List the trials, treatments, and what they mean.*\]

| Trial | Treatment | Description |
| :---- | :---- | :---- |
| **\[*TrialName*\]** | CONTROL | \[*Expected behavior*\] |
|  | \[*TreatmentName*\] | \[*Expected behavior*\] |

# Release Milestones

\[*List the milestones that will be met during development of this project. Break the project down into as many milestones as feasible, including MVP (minimum viable product), to ensure that we are delivering incrementally. Include the approximate size of each milestone. Include future milestones that are not yet planned for delivery. You can use table to display a visual of the ticket dependenciesnbreakdown as well.*\] 

# Alternatives Considered

\[*List the alternatives that were considered when designing the implementation details for this project. What options did we rule out and why? Describing the alternatives will allow others to understand how we arrived at this design and not repeat evaluations of the same alternatives again. This section may also include original designs that needed to be pivoted away from during implementation. Please include a link to the Spike document so reviewers can look into the high-level alternatives considered if needed*\]

# Misc Considerations
N/A
``````
------ src/alfred/templates/prompts/__init__.py ------
``````

``````
------ src/alfred/templates/prompts/create_spec/awaiting_ai_review.md ------
``````
# AI Review: Engineering Specification

## Task ID: {{ task.task_id }}

Please review the engineering specification for completeness and quality.

## Specification to Review

{{ additional_context.drafting_spec_artifact | tojson(indent=2) }}

## Review Guidelines

Evaluate the specification for:
1. Completeness of all required fields
2. Clarity and specificity
3. Technical soundness
4. Alignment with PRD requirements

Call `provide_review` with your assessment.
``````
------ src/alfred/templates/prompts/create_spec/awaiting_human_review.md ------
``````
# Human Review: Engineering Specification

## Task ID: {{ task.task_id }}

Please review the engineering specification that has been created.

## Specification

{{ additional_context.drafting_spec_artifact | tojson(indent=2) }}

## Your Options

1. **Approve**: Call `provide_review` with `is_approved=true`
2. **Request Changes**: Call `provide_review` with `is_approved=false` and specific feedback

The specification should be complete, technically sound, and ready for task breakdown.
``````
------ src/alfred/templates/prompts/create_spec/drafting_spec.md ------
``````
# Review Your Engineering Specification

You previously created an engineering specification. Please review it carefully and consider if any improvements are needed.

## Task ID: {{ task.task_id }}

## Your Engineering Specification

{{ additional_context.artifact_content }}

## Review Checklist

Consider the following:

1. **Completeness**: Are all required fields populated with meaningful content?
2. **Requirements Coverage**: Does the spec fully address all aspects of the PRD?
3. **Technical Accuracy**: Are the technical choices appropriate and well-justified?
4. **Success Metrics**: Are both product and engineering success criteria clearly defined?
5. **API Design**: Are all API changes clearly documented with methods and descriptions?
6. **Data Model**: Is the data storage design complete with all fields specified?
7. **Observability**: Are failure scenarios, logging, metrics, and monitoring adequately planned?
8. **Testing Strategy**: Is the testing approach comprehensive?
9. **Rollout Plan**: Is there a safe, staged rollout strategy?
10. **Dependencies**: Are all dependencies and dependents identified?

## Quality Standards

- Each section should provide actionable information
- No placeholder or vague content
- All lists should have concrete items, not generic statements
- Technical decisions should be justified
- Edge cases and failure modes should be considered

## Next Steps

If you're satisfied with the specification:
- Call `provide_review` with `is_approved=true`

If you want to make improvements:
- Call `provide_review` with `is_approved=false` and provide specific feedback
- You'll have the opportunity to revise the specification
``````
------ src/alfred/templates/prompts/create_spec/drafting_spec_initial.md ------
``````
# Engineering Specification Creation

You are about to transform a Product Requirements Document (PRD) into a comprehensive Engineering Specification.

## Task ID: {{ additional_context.task_id }}

## Product Requirements Document

```
{{ additional_context.prd_content }}
```

## Your Objective

Analyze the PRD above and create a structured Engineering Specification that will serve as the foundation for implementation. Your specification should be detailed enough for engineers to understand the scope, approach, and technical requirements.

## Required Specification Structure

Create an EngineeringSpec with the following fields:

### Basic Information
- **project_name**: Clear, descriptive name for the project
- **overview**: High-level summary of what this project accomplishes
- **review_status**: Leave empty initially (will be filled during reviews)

### Success Metrics
- **definition_of_success**: Object containing:
  - `product_perspective`: How success is measured from product/user standpoint
  - `engineering_perspective`: Technical success criteria

### Requirements
- **functional_requirements**: List of Requirement objects, each with a `story` field (e.g., "As a user, I want to...")
- **non_functional_requirements**: List of strings for performance, scalability, security requirements
- **assumptions**: List of assumptions being made
- **glossary**: Dictionary of technical terms and their definitions

### Design Section
- **major_design_considerations**: Key architectural decisions and trade-offs
- **architecture_diagrams**: Text description or links to diagrams
- **api_changes**: List of ApiDetails objects, each with:
  - `name_and_method`: e.g., "GET /api/users"
  - `description`: What the API does
- **api_usage_estimates**: Expected load and usage patterns
- **event_flows**: Description of event-driven workflows if applicable
- **frontend_updates**: UI/UX changes required
- **data_storage**: List of DataStorageField objects, each with:
  - `field_name`: Name of the field
  - `is_required`: Boolean
  - `data_type`: Type of data
  - `description`: What the field stores
  - `example`: Example value
- **auth_details**: Authentication/authorization requirements
- **resiliency_plan**: How the system handles failures
- **dependencies**: External services or libraries this depends on
- **dependents**: Services that will depend on this

### Observability
- **failure_scenarios**: What could go wrong and how to detect it
- **logging_plan**: What to log and when
- **metrics_plan**: Key metrics to track
- **monitoring_plan**: Alerts and dashboards needed

### Testing & Rollout
- **testing_approach**: Unit, integration, E2E testing strategy
- **rollout_plan**: How to deploy safely
- **release_milestones**: Key milestones and timeline
- **ab_testing**: List of A/B tests if applicable

### Additional Considerations
- **new_technologies_considered**: Any new tech being introduced
- **alternatives_considered**: Other approaches that were evaluated
- **misc_considerations**: Any other important notes

## Guidelines

- Be comprehensive but concise
- Focus on clarity and completeness
- Consider operational aspects from day one
- Think about failure modes and recovery
- Ensure all fields are thoughtfully populated

Call `submit_work` with your completed EngineeringSpec.
``````
------ src/alfred/templates/prompts/create_tasks/awaiting_ai_review.md ------
``````
# AI Review: Task Breakdown

## Task ID: {{ task.task_id }}

Please review the task breakdown for completeness and quality.

## Tasks to Review

{{ additional_context.drafting_tasks_artifact | tojson(indent=2) }}

## Review Guidelines

Evaluate the task breakdown for:
1. Complete coverage of the technical specification
2. Logical ordering and dependencies
3. Appropriate task granularity (1-3 days of work)
4. Clear acceptance criteria
5. Technical feasibility

Call `provide_review` with your assessment.
``````
------ src/alfred/templates/prompts/create_tasks/awaiting_human_review.md ------
``````
# Human Review: Task Breakdown

## Task ID: {{ task.task_id }}

Please review the task breakdown that has been created.

## Tasks

{{ additional_context.drafting_tasks_artifact | tojson(indent=2) }}

## Your Options

1. **Approve**: Call `provide_review` with `is_approved=true`
2. **Request Changes**: Call `provide_review` with `is_approved=false` and specific feedback

The task breakdown should comprehensively cover the technical specification.
``````
------ src/alfred/templates/prompts/create_tasks/drafting_tasks.md ------
``````
# Review Your Task Breakdown

You previously created a task breakdown from the technical specification. Please review it carefully.

## Task ID: {{ task.task_id }}

## Your Task List

{{ additional_context.artifact_content }}

## Review Checklist

Consider the following:

1. **Completeness**: Do the tasks cover all aspects of the technical specification?
2. **Dependencies**: Are task dependencies correctly identified and ordered?
3. **Granularity**: Are tasks appropriately sized (1-3 days of work)?
4. **Clarity**: Is each task clear and actionable?
5. **Technical Accuracy**: Are the technical details correct?
6. **Missing Tasks**: Are there any gaps? Consider:
   - Error handling tasks
   - Testing tasks
   - Documentation tasks
   - Migration tasks
   - Monitoring/logging tasks

## Validation Questions

- Can these tasks be executed in the specified order?
- Are acceptance criteria measurable and clear?
- Would a developer understand exactly what to do for each task?
- Are effort estimates reasonable?

## Next Steps

If you're satisfied with the task breakdown:
- Call `provide_review` with `is_approved=true`

If you want to make improvements:
- Call `provide_review` with `is_approved=false` and provide specific feedback
- You'll have the opportunity to revise the task list
``````
------ src/alfred/templates/prompts/create_tasks/drafting_tasks_initial.md ------
``````
# Task Breakdown from Engineering Specification

You are about to break down an Engineering Specification into individual, actionable tasks.

## Task ID: {{ additional_context.task_id }}

## Engineering Specification Summary

**Project**: {{ additional_context.technical_spec.project_name }}

**Overview**: {{ additional_context.technical_spec.overview }}

### Functional Requirements
{% for req in additional_context.technical_spec.functional_requirements %}
- {{ req.story }}
{% endfor %}

### API Changes
{% for api in additional_context.technical_spec.api_changes %}
- {{ api.name_and_method }}: {{ api.description }}
{% endfor %}

### Data Storage Requirements
{% for field in additional_context.technical_spec.data_storage %}
- {{ field.field_name }} ({{ field.data_type }}{% if field.is_required %}, required{% endif %}): {{ field.description }}
{% endfor %}

### Major Design Considerations
{{ additional_context.technical_spec.major_design_considerations }}

### Dependencies
{% for dep in additional_context.technical_spec.dependencies %}
- {{ dep }}
{% endfor %}

## Your Objective

Analyze the technical specification above and create a comprehensive list of Task objects that cover the entire implementation. Each task should be:

1. **Atomic**: A single, focused piece of work
2. **Actionable**: Clear about what needs to be done
3. **Measurable**: Has clear completion criteria
4. **Ordered**: Consider dependencies between tasks

## Task Structure

Each Task object should have:
- **id**: A unique identifier (e.g., "TASK-001", "TASK-002")
- **title**: Clear, concise title describing the work
- **description**: Detailed description of what needs to be done
- **acceptance_criteria**: List of criteria that must be met for completion
- **dependencies**: List of task IDs this task depends on (if any)
- **estimated_effort**: Rough estimate (e.g., "Small", "Medium", "Large")
- **technical_notes**: Any technical details or considerations

## Guidelines for Task Creation

1. **Coverage**: Ensure all aspects of the technical spec are covered
2. **Granularity**: Tasks should be completable in 1-3 days of work
3. **Dependencies**: Order tasks logically based on dependencies
4. **Categories**: Consider grouping by:
   - Data model/schema changes
   - API endpoints
   - Business logic
   - UI components
   - Testing
   - Documentation
   - DevOps/Infrastructure

5. **Don't Forget**:
   - Database migrations
   - API documentation
   - Unit and integration tests
   - Error handling
   - Logging and monitoring
   - Security implementation
   - Performance optimizations

## Example Task

```json
{
  "id": "TASK-001",
  "title": "Create User Authentication Schema",
  "description": "Design and implement the database schema for user authentication including users table, sessions table, and required indexes",
  "acceptance_criteria": [
    "Users table created with email, password_hash, created_at fields",
    "Sessions table created with user_id, token, expires_at fields",
    "Appropriate indexes added for performance",
    "Migration script created and tested"
  ],
  "dependencies": [],
  "estimated_effort": "Small",
  "technical_notes": "Use bcrypt for password hashing, consider UUID for session tokens"
}
```

Call `submit_work` with a TaskCreationArtifact containing your list of Task objects.
``````
------ src/alfred/templates/prompts/finalize_task/dispatching.md ------
``````
# TASK: {{ task.task_id }}
# STATE: dispatching

All phases are complete. Please finalize the task.

**Test Results:**
Exit Code: {{ task.completed_tool_outputs.test_task.exit_code }}
Output: {{ task.completed_tool_outputs.test_task.output }}

If tests passed, please:
1. Create a git commit with the changes
2. Create a pull request if appropriate

Once finalization is complete, call `alfred.submit_work` with a `FinalizeArtifact` containing:
- commit_hash: The git commit hash (or "N/A" if not applicable)
- pr_url: The PR URL (or "N/A" if not applicable)
``````
------ src/alfred/templates/prompts/finalize_task/finalizing.md ------
``````
# Finalization Phase

You are now finalizing task {{ task.task_id }}.

## Finalization Steps

Create a commit and pull request for the completed work.

## Required Information

Create a `FinalizeArtifact` with:
- **commit_message**: Clear, descriptive commit message
- **pr_title**: Pull request title
- **pr_description**: Detailed pull request description

Call `submit_work` with your finalization details.
``````
------ src/alfred/templates/prompts/generic/awaiting_ai_review.md ------
``````
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
------ src/alfred/templates/prompts/implement_task/awaiting_ai_review.md ------
``````
# AI Review Required

## Task: {{ task.task_id }}

Your implementation manifest has been submitted and is now ready for AI review.

### Submitted Implementation Manifest

{% if artifact_content %}
{{ artifact_content | tojson(indent=2) }}
{% elif additional_context.artifact_content %}
{{ additional_context.artifact_content | tojson(indent=2) }}
{% else %}
Error: No artifact content found
{% endif %}

### Review Process

The AI will now review your implementation for:
- Completeness of subtask completion
- Quality of implementation summary
- Adequacy of testing notes

Please wait for the AI review to complete.
``````
------ src/alfred/templates/prompts/implement_task/awaiting_human_review.md ------
``````
# Human Review Required

## Task: {{ task.task_id }}

Your implementation has passed AI review and now requires human approval.

### Implementation Summary

{% if additional_context.implementing_artifact %}
{{ additional_context.implementing_artifact.summary }}

### Completed Subtasks
{% for subtask_id in additional_context.implementing_artifact.completed_subtasks %}
- {{ subtask_id }}
{% endfor %}

### Testing Notes
{{ additional_context.implementing_artifact.testing_notes }}
{% else %}
Implementation artifact not found in context.
{% endif %}

### Next Steps

Please wait for human review and approval to proceed to the next phase.
``````
------ src/alfred/templates/prompts/implement_task/dispatching.md ------
``````
# TASK: {{ task.task_id }}
# STATE: dispatching

The Execution Plan is ready. Please execute all subtasks from the plan.

**Execution Plan:**
{{ task.completed_tool_outputs.plan_task.execution_plan | tojson(indent=2) }}

Once all subtasks are complete, call `alfred.submit_work` with an `ImplementationManifestArtifact` containing:
- summary: Brief summary of what was implemented
- completed_subtasks: List of completed subtask IDs
- testing_notes: Any notes for the testing phase
``````
------ src/alfred/templates/prompts/implement_task/implementing.md ------
``````
# Implementation Phase

You are now in the implementation phase for task {{ task.task_id }}.

## Your Execution Plan

{% if additional_context.execution_plan %}
{{ additional_context.execution_plan | tojson(indent=2) }}
{% else %}
No execution plan found. Please check the planning phase outputs.
{% endif %}

## Your Mission

Implement the subtasks from the execution plan. As you complete each subtask, call `mark_subtask_complete` to track progress.

When all subtasks are complete, submit an `ImplementationManifestArtifact` with:
- **summary**: Brief summary of what was implemented
- **completed_subtasks**: List of completed subtask IDs
- **testing_notes**: Any notes about testing or validation

Call `submit_work` with your final implementation manifest.
``````
------ src/alfred/templates/prompts/plan_task/awaiting_ai_review.md ------
``````
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
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: contextualize

I am beginning the planning process for '{{ task.title }}'.

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
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: review_context

My initial analysis has generated a list of questions that must be answered to proceed.

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
# TOOL: `alfred.plan_task`
# TASK: {{ task.task_id }}
# STATE: verified

# TODO: Implement full prompt.
``````
------ src/alfred/templates/prompts/review_task/awaiting_ai_review.md ------
``````
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have submitted the review artifact. I must now perform a self-review to ensure the feedback is clear, actionable, and fair.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | tojson(indent=2) }}
```

---
### **Directive: AI Self-Review**

**Review Checklist:**
1. **Clarity:** Is the `summary` clear? Is the `feedback` specific and easy to understand?
2. **Actionability:** If `approved` is false, does the feedback give the developer a clear path to fixing the issues?
3. **Tone:** Is the feedback constructive and professional?

---
### **Required Action**
Call `alfred.provide_review` with `is_approved=True` if the review artifact is high quality.
``````
------ src/alfred/templates/prompts/review_task/awaiting_human_review.md ------
``````
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

The review artifact has passed AI review and is now ready for your final approval.

**Review Summary:**
{{ additional_context.review_artifact.summary }}

**Approval Status:** {{ "Approved" if additional_context.review_artifact.approved else "Changes Requested" }}

**Feedback:**
{% for item in additional_context.review_artifact.feedback %}
- {{ item }}
{% endfor %}

---
### **Required Action**

Based on your assessment:
- If you agree with the review, call `alfred.provide_review` with `is_approved=True`
- If you want to modify the review, call `alfred.provide_review` with `is_approved=False` and provide feedback
``````
------ src/alfred/templates/prompts/review_task/dispatching.md ------
``````
# TASK: {{ task.task_id }}
# STATE: dispatching

Please review the implementation that was just completed.

**Implementation Summary:**
{{ task.completed_tool_outputs.implement_task.summary }}

**Completed Subtasks:**
{{ task.completed_tool_outputs.implement_task.completed_subtasks | tojson(indent=2) }}

Review the code changes for:
- Correctness and completeness
- Code quality and standards
- Security considerations
- Performance implications

Once your review is complete, call `alfred.submit_work` with a `ReviewArtifact` containing:
- summary: Review summary
- approved: true/false
- feedback: List of feedback items
``````
------ src/alfred/templates/prompts/review_task/reviewing.md ------
``````
# Code Review Phase

You are now reviewing the implementation for task {{ task.task_id }}.

## Implementation Details

Review the changes made during the implementation phase. Look for:
- Code quality and style
- Potential bugs or issues
- Performance concerns
- Security considerations
- Best practices

## Your Review

Create a `ReviewArtifact` with:
- **review_summary**: Overall assessment of the implementation
- **issues_found**: List of any issues discovered
- **suggestions**: List of improvement suggestions

Call `submit_work` with your review findings.
``````
------ src/alfred/templates/prompts/start_task/awaiting_ai_review.md ------
``````
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
# TOOL: `alfred.start_task`
# TASK: {{ task.task_id }}
# STATE: awaiting_git_status

Welcome. Let's begin setting up the workspace for this task.

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
------ src/alfred/templates/prompts/test_task/awaiting_ai_review.md ------
``````
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_ai_review

I have submitted the test results. I must now perform an automated analysis of the results to determine the pass/fail status.

**My Submitted Artifact:**
```json
{{ additional_context.artifact_content | tojson(indent=2) }}
```

---
### **Directive: Automated Test Result Analysis**

**Analysis Rule:**
- Examine the `exit_code` field in the artifact.
- If `exit_code` is `0`, the test run is considered a **PASS**.
- If `exit_code` is anything other than `0`, the test run is a **FAIL**.

---
### **Required Action**
Call `alfred.provide_review`.
- Set `is_approved=True` if `exit_code` is `0`.
- Set `is_approved=False` if `exit_code` is not `0`. Provide `feedback_notes` stating "Tests failed with exit code [exit_code]. See output for details."
``````
------ src/alfred/templates/prompts/test_task/awaiting_human_review.md ------
``````
# TOOL: `alfred.provide_review`
# TASK: {{ task.task_id }}
# STATE: awaiting_human_review

The test results have been analyzed and are ready for your review.

**Test Command:** `{{ additional_context.test_artifact.command }}`

**Exit Code:** {{ additional_context.test_artifact.exit_code }} ({{ "PASS" if additional_context.test_artifact.exit_code == 0 else "FAIL" }})

**Test Output:**
```
{{ additional_context.test_artifact.output }}
```

---
### **Required Action**

Based on the test results:
- If tests are satisfactory, call `alfred.provide_review` with `is_approved=True`
- If tests need to be re-run or modified, call `alfred.provide_review` with `is_approved=False` and provide feedback
``````
------ src/alfred/templates/prompts/test_task/dispatching.md ------
``````
# TASK: {{ task.task_id }}
# STATE: dispatching

Please run the test suite to verify the implementation.

**Testing Notes from Implementation:**
{{ task.completed_tool_outputs.implement_task.testing_notes }}

Run the appropriate test command (e.g., `uv run python -m pytest tests/ -v`) and report the results.

Once testing is complete, call `alfred.submit_work` with a `TestResultArtifact` containing:
- command: The test command that was run
- exit_code: The exit code (0 for success)
- output: The test output
``````
------ src/alfred/templates/prompts/test_task/testing.md ------
``````
# Testing Phase

You are now in the testing phase for task {{ task.task_id }}.

## Test Objectives

Run tests to validate the implementation. This includes:
- Unit tests
- Integration tests
- Any manual validation required

## Test Results

Create a `TestResultArtifact` with:
- **test_summary**: Overall test results summary
- **tests_run**: List of test names/identifiers that were executed
- **test_results**: List of test result objects with:
  - `name`: Test name
  - `status`: "passed" or "failed"
  - `message`: Optional failure message

Call `submit_work` with your test results.
``````
------ src/alfred/templates/prompts/verified.md ------
``````
# Task Complete

Task `{{ task_id }}` has been successfully completed.

The work has been verified and is ready for the next phase of the workflow.

This is an informational prompt. No further action is required.
``````
------ src/alfred/tools/__init__.py ------
``````

``````
------ src/alfred/tools/approve_and_advance.py ------
``````
from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.constants import ToolName
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)

STATUS_TRANSITION_MAP = {
    TaskStatus.CREATING_SPEC: TaskStatus.SPEC_COMPLETED,
    TaskStatus.CREATING_TASKS: TaskStatus.TASKS_CREATED,
    TaskStatus.PLANNING: TaskStatus.READY_FOR_DEVELOPMENT,
    TaskStatus.IN_DEVELOPMENT: TaskStatus.READY_FOR_REVIEW,
    TaskStatus.IN_REVIEW: TaskStatus.READY_FOR_TESTING,
    TaskStatus.IN_TESTING: TaskStatus.READY_FOR_FINALIZATION,
    TaskStatus.READY_FOR_FINALIZATION: TaskStatus.DONE,
}

ARTIFACT_PRODUCER_MAP = {
    TaskStatus.CREATING_SPEC: ToolName.CREATE_SPEC,
    TaskStatus.CREATING_TASKS: ToolName.CREATE_TASKS,
    TaskStatus.PLANNING: ToolName.PLAN_TASK,
    TaskStatus.IN_DEVELOPMENT: ToolName.IMPLEMENT_TASK,
    TaskStatus.IN_REVIEW: ToolName.REVIEW_TASK,
    TaskStatus.IN_TESTING: ToolName.TEST_TASK,
    TaskStatus.READY_FOR_FINALIZATION: ToolName.FINALIZE_TASK,
}


def approve_and_advance_impl(task_id: str) -> ToolResponse:
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status

    if current_status not in STATUS_TRANSITION_MAP:
        return ToolResponse(status="error", message=f"Cannot advance task '{task_id}'. Its status is '{current_status.value}', which is not a completed phase.")

    producer_tool_name = ARTIFACT_PRODUCER_MAP.get(current_status)
    if producer_tool_name:
        # Determine workflow step number based on status
        workflow_step_map = {
            TaskStatus.CREATING_SPEC: 1,
            TaskStatus.CREATING_TASKS: 2,
            TaskStatus.PLANNING: 3,
            TaskStatus.IN_DEVELOPMENT: 4,
            TaskStatus.IN_REVIEW: 5,
            TaskStatus.IN_TESTING: 6,
            TaskStatus.READY_FOR_FINALIZATION: 7,
        }
        workflow_step = workflow_step_map.get(current_status, 0)

        # Archive the scratchpad BEFORE transitioning
        artifact_manager.archive_scratchpad(task_id, producer_tool_name, workflow_step)
        logger.info(f"Archived scratchpad for tool '{producer_tool_name}' at workflow step {workflow_step}")

        final_artifact = task_state.completed_tool_outputs.get(producer_tool_name)
        if final_artifact:
            artifact_manager.archive_final_artifact(task_id, producer_tool_name, final_artifact)
            logger.info(f"Archived final artifact for phase '{current_status.value}'.")
        else:
            logger.warning(f"No final artifact found for tool '{producer_tool_name}' to archive.")

    next_status = STATUS_TRANSITION_MAP[current_status]
    state_manager.update_task_status(task_id, next_status)

    message = f"Phase '{current_status.value}' approved. Task '{task_id}' is now in status '{next_status.value}'."
    logger.info(message)

    if next_status == TaskStatus.DONE:
        message += "\n\nThe task is fully complete."
        return ToolResponse(status="success", message=message)

    return ToolResponse(status="success", message=message, next_prompt=f"To proceed, call `alfred.work_on(task_id='{task_id}')` to get the next action.")

``````
------ src/alfred/tools/create_spec.py ------
``````
# src/alfred/tools/create_spec.py
from src.alfred.models.schemas import ToolResponse
from src.alfred.constants import ToolName
from src.alfred.core.workflow import CreateSpecTool
from src.alfred.models.planning_artifacts import PRDInputArtifact
from src.alfred.models.engineering_spec import EngineeringSpec
from src.alfred.state.manager import state_manager


async def create_spec_impl(task_id: str, prd_content: str) -> ToolResponse:
    """
    Initializes the workflow for creating a technical specification from a PRD.

    This is the first tool in the "idea-to-code" pipeline. It takes a Product
    Requirements Document (PRD) and guides the transformation into a structured
    Technical Specification that can be used for engineering planning.

    Args:
        task_id: The unique identifier for the epic/feature (e.g., "EPIC-01")
        prd_content: The raw PRD content to analyze

    Returns:
        ToolResponse containing the first prompt to guide spec creation
    """
    # Load or create task state
    task_state = state_manager.load_or_create_task_state(task_id)

    # Update status to creating_spec
    from src.alfred.models.schemas import TaskStatus

    state_manager.update_task_status(task_id, TaskStatus.CREATING_SPEC)

    # Initialize the create_spec tool
    tool = CreateSpecTool(task_id)

    # Store the PRD content in context
    prd_artifact = PRDInputArtifact(prd_content=prd_content)
    tool.context_store["prd_input"] = prd_artifact

    # Register the tool
    state_manager.register_tool(task_id, tool)

    # Dispatch immediately to drafting state
    tool.dispatch()
    state_manager.update_tool_state(task_id, tool)

    # Load the drafting prompt
    from src.alfred.core.prompter import prompter
    from src.alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the spec creation phase
        from src.alfred.models.schemas import Task

        task = Task(
            task_id=task_id,
            title=f"Create specification for {task_id}",
            context="Creating engineering specification from PRD",
            implementation_details="Transform PRD into engineering specification",
            task_status=TaskStatus.CREATING_SPEC,
        )

    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool.tool_name,
        state=tool.state,
        additional_context={
            "task_id": task_id,
            "prd_content": prd_content,
        },
    )

    return ToolResponse(status="success", message=f"Starting specification creation for task '{task_id}'.", next_prompt=prompt)

``````
------ src/alfred/tools/create_tasks.py ------
``````
# src/alfred/tools/create_tasks.py
from src.alfred.models.schemas import ToolResponse
from src.alfred.constants import ToolName
from src.alfred.core.workflow import CreateTasksTool
from src.alfred.models.engineering_spec import EngineeringSpec
from src.alfred.lib.logger import get_logger
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


async def create_tasks_impl(task_id: str) -> ToolResponse:
    """
    Initializes the workflow for creating tasks from a technical specification.

    This is the second tool in the "idea-to-code" pipeline. It takes a completed
    Technical Specification and breaks it down into actionable Task objects that
    can be individually planned and implemented.

    Args:
        task_id: The unique identifier for the epic/feature that has a completed spec

    Returns:
        ToolResponse containing the first prompt to guide task creation
    """
    # Load the task state
    task_state = state_manager.load_or_create_task_state(task_id)

    from src.alfred.models.schemas import TaskStatus

    # Check if we have a completed technical spec
    if task_state.task_status != TaskStatus.SPEC_COMPLETED:
        return ToolResponse(status="error", message=f"Task {task_id} does not have a completed technical specification. Current status: {task_state.task_status.value}")

    # Load the engineering spec from archive
    archive_path = state_manager.get_archive_path(task_id)
    spec_file = archive_path / "engineering_spec.json"

    if not spec_file.exists():
        return ToolResponse(status="error", message=f"Technical specification not found for task {task_id}. Please complete create_spec first.")

    try:
        import json

        with open(spec_file, "r") as f:
            spec_data = json.load(f)
        tech_spec = EngineeringSpec(**spec_data)
    except Exception as e:
        logger.error(f"Failed to load technical spec for {task_id}: {e}")
        return ToolResponse(status="error", message=f"Failed to load technical specification: {str(e)}")

    # Update status
    state_manager.update_task_status(task_id, TaskStatus.CREATING_TASKS)

    # Initialize the create_tasks tool
    tool = CreateTasksTool(task_id)

    # Store the technical spec in context
    tool.context_store["technical_spec"] = tech_spec

    # Register the tool
    state_manager.register_tool(task_id, tool)

    # Dispatch immediately to drafting state
    tool.dispatch()
    state_manager.update_tool_state(task_id, tool)

    # Load the drafting prompt with the technical spec
    from src.alfred.core.prompter import prompter
    from src.alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the task creation phase
        from src.alfred.models.schemas import Task

        task = Task(
            task_id=task_id,
            title=f"Create tasks for {task_id}",
            context="Breaking down engineering specification into tasks",
            implementation_details="Transform engineering spec into actionable tasks",
            task_status=TaskStatus.CREATING_TASKS,
        )

    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool.tool_name,
        state=tool.state,
        additional_context={
            "task_id": task_id,
            "technical_spec": tech_spec.model_dump(),
        },
    )

    return ToolResponse(status="success", message=f"Starting task breakdown for '{task_id}'.", next_prompt=prompt)

``````
------ src/alfred/tools/finalize_task.py ------
``````
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import FinalizeTaskTool
from src.alfred.core.prompter import prompter
from src.alfred.constants import ToolName

logger = get_logger(__name__)


async def finalize_task_impl(task_id: str) -> ToolResponse:
    """
    Finalize task entry point - handles the completion phase
    """
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
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status != TaskStatus.READY_FOR_FINALIZATION:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Finalization can only start on a 'ready_for_finalization' task.")

            tool_instance = FinalizeTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_task_status(task_id, TaskStatus.READY_FOR_FINALIZATION)

            # Dispatch immediately to finalizing state
            tool_instance.dispatch()
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new finalize tool for task {task_id}")

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Finalization phase initiated for task '{task_id}'."
    return ToolResponse(status="success", message=message, next_prompt=prompt)

``````
------ src/alfred/tools/get_next_task.py ------
``````
"""Get next task implementation using the task provider factory."""

from src.alfred.models.schemas import ToolResponse
from src.alfred.task_providers.factory import get_provider
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


async def get_next_task_impl() -> ToolResponse:
    """Gets the next recommended task using the configured provider.

    This tool intelligently determines which task should be worked on next
    based on task status, priority, and other factors. It uses the configured
    task provider (local, jira, linear) to fetch and rank tasks.

    Returns:
        ToolResponse containing:
        - The recommended task ID and details
        - Reasoning for the recommendation
        - Alternative tasks that could be worked on
        - A prompt suggesting how to proceed
    """
    try:
        # Get the configured task provider
        provider = get_provider()

        # Delegate to the provider's implementation
        return provider.get_next_task()

    except NotImplementedError as e:
        # Handle providers that aren't implemented yet
        logger.error(f"Provider not implemented: {e}")
        return ToolResponse(status="error", message=str(e))
    except Exception as e:
        # Handle any other errors
        logger.error(f"Failed to get next task: {e}")
        return ToolResponse(status="error", message=f"Failed to get next task: {str(e)}")

``````
------ src/alfred/tools/implement_task.py ------
``````
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import ImplementTaskTool
from src.alfred.core.prompter import prompter
from src.alfred.constants import ToolName

logger = get_logger(__name__)


async def implement_task_impl(task_id: str) -> ToolResponse:
    """
    Implementation task entry point - handles the development phase
    """
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
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status != TaskStatus.READY_FOR_DEVELOPMENT:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Implementation can only start on a 'ready_for_development' task.")

            tool_instance = ImplementTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_task_status(task_id, TaskStatus.IN_DEVELOPMENT)

            # Dispatch immediately to implementing state
            tool_instance.dispatch()
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new implementation tool for task {task_id}")

    # Load execution plan from previous phase
    task_state = state_manager.load_or_create(task_id)
    logger.info(f"Completed tool outputs: {list(task_state.completed_tool_outputs.keys())}")
    plan_task_outputs = task_state.completed_tool_outputs.get(ToolName.PLAN_TASK, {})
    logger.info(f"Plan task outputs type: {type(plan_task_outputs)}")

    # The execution plan IS the plan_task output (it's the ExecutionPlanArtifact)
    if plan_task_outputs and isinstance(plan_task_outputs, dict) and "subtasks" in plan_task_outputs:
        # Store with the key that mark_subtask_complete expects
        tool_instance.context_store["execution_plan_artifact"] = plan_task_outputs
        logger.info(f"Loaded execution plan with {len(plan_task_outputs.get('subtasks', []))} subtasks")
    else:
        logger.warning("No execution plan found from plan_task phase")

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Implementation initiated for task '{task_id}'."
    return ToolResponse(status="success", message=message, next_prompt=prompt)

``````
------ src/alfred/tools/initialize.py ------
``````
"""
Initialization tool for Alfred.

This module provides the interactive initialize_project tool that sets up the
.alfred directory with provider-specific configuration.
"""

import logging
from pathlib import Path
import shutil

from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.constants import ResponseStatus
from src.alfred.models.alfred_config import TaskProvider
from src.alfred.models.schemas import ToolResponse

logger = logging.getLogger(__name__)


def initialize_project(provider: str | None = None, test_dir: Path | None = None) -> ToolResponse:
    """Initialize Alfred with provider selection.

    Args:
        provider: Provider choice ('jira', 'linear', or 'local'). If None, returns available choices.
        test_dir: Optional test directory for testing purposes. If provided, will use this instead of settings.alfred_dir.

    Returns:
        ToolResponse: Standardized response object.
    """
    alfred_dir = test_dir if test_dir is not None else settings.alfred_dir

    # Check if already initialized
    if _is_already_initialized(alfred_dir):
        return _create_already_initialized_response(alfred_dir)

    # Return choices if no provider specified
    if provider is None:
        return _get_provider_choices_response()

    try:
        # Validate and perform initialization
        provider_choice = _validate_provider_choice(provider)
        return _perform_initialization(provider_choice, alfred_dir)

    except KeyboardInterrupt:
        return ToolResponse(status=ResponseStatus.ERROR, message="Initialization cancelled by user.")
    except (OSError, shutil.Error, ValueError) as e:
        return ToolResponse(
            status=ResponseStatus.ERROR,
            message=f"Failed to initialize project. Error: {e}",
        )


def _is_already_initialized(alfred_dir: Path) -> bool:
    """Check if project is already initialized."""
    return alfred_dir.exists() and (alfred_dir / "workflow.yml").exists()


def _create_already_initialized_response(alfred_dir: Path) -> ToolResponse:
    """Create response for already initialized project."""
    return ToolResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Project already initialized at '{alfred_dir}'. No changes were made.",
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
        msg = f"Invalid provider '{provider}'. Must be 'jira', 'linear', or 'local'."
        raise ValueError(msg)
    return provider_choice


def _perform_initialization(provider_choice: str, alfred_dir: Path) -> ToolResponse:
    """Perform the actual initialization setup."""
    # Create directories
    _create_project_directories(alfred_dir)

    # Copy default workflow file
    _copy_workflow_file(alfred_dir)

    # Copy default templates to user workspace
    _copy_default_templates(alfred_dir)

    # Setup provider-specific configuration
    result = _setup_provider_configuration(provider_choice, alfred_dir)
    if result["status"] == ResponseStatus.ERROR:
        return ToolResponse(status=ResponseStatus.ERROR, message=result["message"])

    return ToolResponse(
        status=ResponseStatus.SUCCESS,
        message=f"Successfully initialized Alfred project in '{alfred_dir}' with {provider_choice} provider.",
    )


def _create_project_directories(alfred_dir: Path) -> None:
    """Create the necessary project directories."""
    alfred_dir.mkdir(parents=True, exist_ok=True)
    (alfred_dir / "workspace").mkdir(exist_ok=True)
    (alfred_dir / "specs").mkdir(exist_ok=True)
    (alfred_dir / "tasks").mkdir(exist_ok=True)
    logger.info(f"Created project directories at {alfred_dir}")


def _copy_workflow_file(alfred_dir: Path) -> None:
    """Copy the default workflow file."""
    workflow_file = alfred_dir / settings.workflow_filename
    shutil.copyfile(settings.packaged_workflow_file, workflow_file)
    logger.info(f"Copied workflow file to {workflow_file}")


def _copy_default_templates(alfred_dir: Path) -> None:
    """Copy default templates to user workspace for customization."""
    try:
        shutil.copytree(settings.packaged_templates_dir, alfred_dir / "templates", dirs_exist_ok=True)
        logger.info(f"Copied templates to {alfred_dir / 'templates'}")
    except (OSError, shutil.Error) as e:
        msg = f"Failed to copy templates: {e}"
        raise OSError(msg) from e


def _setup_provider_configuration(provider_choice: str, alfred_dir: Path) -> dict:
    """Setup provider-specific configuration."""
    config_manager = ConfigManager(alfred_dir)

    if provider_choice == "jira":
        return _setup_jira_provider(config_manager, alfred_dir)
    if provider_choice == "linear":
        return _setup_linear_provider(config_manager, alfred_dir)
    if provider_choice == "local":
        return _setup_local_provider(config_manager, alfred_dir)

    return {"status": ResponseStatus.ERROR, "message": f"Unknown provider: {provider_choice}"}


def _setup_jira_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup Jira provider with MCP connectivity check."""
    if _validate_mcp_connectivity("jira"):
        config = config_manager.create_default()
        config.providers.task_provider = TaskProvider.JIRA
        config_manager.save(config)
        _setup_provider_resources("jira", alfred_dir)
        logger.info("Configured Jira provider")
        return {"status": ResponseStatus.SUCCESS}
    return {
        "status": ResponseStatus.ERROR,
        "message": "Could not connect to the Atlassian MCP server. Please ensure it is running and accessible.",
    }


def _setup_linear_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup Linear provider with MCP connectivity check."""
    if _validate_mcp_connectivity("linear"):
        config = config_manager.create_default()
        config.providers.task_provider = TaskProvider.LINEAR
        config_manager.save(config)
        _setup_provider_resources("linear", alfred_dir)
        logger.info("Configured Linear provider")
        return {"status": ResponseStatus.SUCCESS}
    return {
        "status": ResponseStatus.ERROR,
        "message": "Could not connect to the Linear MCP server. Please ensure it is running and accessible.",
    }


def _setup_local_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup local provider with tasks inbox and README."""
    # Create configuration
    config = config_manager.create_default()
    config.providers.task_provider = TaskProvider.LOCAL
    config_manager.save(config)

    # Setup provider resources
    _setup_provider_resources("local", alfred_dir)

    logger.info("Configured local provider")
    return {"status": ResponseStatus.SUCCESS}


def _setup_provider_resources(provider: str, alfred_dir: Path) -> None:
    """Setup provider-specific resources."""
    # Always create tasks directory for cache-first architecture
    tasks_dir = alfred_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    # Create README with provider-specific content
    readme_path = tasks_dir / "README.md"

    if provider == "local":
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

When you run `work_on("TASK-ID")`, Alfred will read the corresponding file and start the workflow.
"""
    else:
        # For Jira/Linear providers
        readme_content = f"""# Alfred Task Cache

This directory contains the local markdown representation of all tasks Alfred is aware of.

Since you're using the **{provider}** provider, this directory acts as a local cache. Tasks are fetched from {provider.capitalize()} and stored here before being worked on.

## Task Format

All cached tasks follow the same markdown format:

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

Tasks will be automatically cached here when you work on them using `work_on("TASK-ID")`.
"""

    readme_path.write_text(readme_content, encoding="utf-8")
    logger.info(f"Created {provider} provider resources at {tasks_dir}")


def _validate_mcp_connectivity(provider: str) -> bool:
    """Check if required MCP tools are available for the given provider.

    This is a placeholder for actual MCP connectivity validation.
    In a production system, this would attempt to call MCP tools
    to verify they are available and responding.
    """
    # TODO: Implement actual MCP tool availability check
    # For now, we'll simulate the check and return True
    logger.info(f"Simulating MCP connectivity check for {provider} provider")
    return True

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
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery

logger = get_logger(__name__)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool with unified state."""
    setup_task_logging(task_id)

    task = load_task(task_id)
    if not task:
        return ToolResponse(
            status="error", 
            message=f"Task '{task_id}' not found. Please ensure:\n"
                    f"1. Task file exists at .alfred/tasks/{task_id}.md\n"
                    f"2. Task file follows the correct format (see .alfred/tasks/README.md)\n"
                    f"3. Review .alfred/tasks/SAMPLE-FORMAT.md for a working example\n"
                    f"4. Check logs for specific parsing errors if file exists"
        )

    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
    else:
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
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

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Planning initiated for task '{task_id}'." if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value else f"Resumed planning for task '{task_id}' from state '{tool_instance.state}'."

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
from src.alfred.constants import ToolName, ArtifactKeys
from src.alfred.core.prompter import prompter
from src.alfred.core.context_builder import ContextBuilder
from src.alfred.lib.logger import cleanup_task_logging, get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


def _is_ai_review_state(state: str) -> bool:
    """Check if the current state is an AI review state."""
    return state.endswith("_awaiting_ai_review")


def _is_human_review_state(state: str) -> bool:
    """Check if the current state is a human review state."""
    return state.endswith("_awaiting_human_review")


def _is_autonomous_mode_enabled() -> bool:
    """Check if autonomous mode is enabled in configuration."""
    config_manager = ConfigManager(settings.alfred_dir)
    config = config_manager.load()
    return config.features.autonomous_mode


def _handle_rejection(active_tool, current_state: str) -> str:
    """Handle review rejection by transitioning back to previous state."""
    logger.info(f"Review rejected, transitioning back from '{current_state}'")
    active_tool.request_revision()
    logger.info(f"After revision, new state is '{active_tool.state}'")
    return "Revision requested. Returning to previous step."


def _handle_ai_review_approval(active_tool, task_id: str) -> str:
    """Handle AI review approval, checking for autonomous mode."""
    active_tool.ai_approve()

    if _is_autonomous_mode_enabled():
        logger.info(f"Autonomous mode enabled. Bypassing human review for task {task_id}.")
        active_tool.human_approve()
        return "AI review approved. Autonomous mode bypassed human review."

    return "AI review approved. Awaiting human review."


def _handle_human_review_approval(active_tool) -> str:
    """Handle human review approval."""
    active_tool.human_approve()
    return "Human review approved. Proceeding to next step."


def provide_review_impl(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Processes review feedback, advancing the active tool's State Machine."""
    # Try to get active tool or recover it from state
    if task_id not in orchestrator.active_tools:
        # Try to recover the tool from persisted state
        from src.alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            logger.info(f"Recovered tool for task {task_id} from persisted state")
        else:
            return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info(f"Processing review for task {task_id} in state '{current_state}', approved={is_approved}")

    if not is_approved:
        message = _handle_rejection(active_tool, current_state)
    else:
        if _is_ai_review_state(current_state):
            message = _handle_ai_review_approval(active_tool, task_id)
        elif _is_human_review_state(current_state):
            message = _handle_human_review_approval(active_tool)
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{active_tool.state}'.")

    state_manager.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        # The tool's internal workflow is DONE. Its ONLY job now is to hand off.
        tool_name = active_tool.tool_name
        logger.info(f"[DEBUG] Tool {tool_name} reached terminal state for task {task_id}")

        # 1. Save the tool's final, most important artifact to the persistent TaskState.
        #    This makes it available for approve_and_advance to archive.
        task_state = state_manager.load_or_create(task_id)
        final_artifact_state = active_tool.get_final_work_state()
        # CRITICAL FIX: Use centralized key generation to ensure consistency
        final_artifact_key = ArtifactKeys.get_artifact_key(final_artifact_state)

        # Debug logging
        logger.info(f"[DEBUG] Final artifact state: {final_artifact_state}")
        logger.info(f"[DEBUG] Looking for key: {final_artifact_key}")
        logger.info(f"[DEBUG] Context store keys: {list(active_tool.context_store.keys())}")

        final_artifact = active_tool.context_store.get(final_artifact_key)

        if final_artifact:
            # Save the RAW artifact object directly. This is the key change.
            logger.info(f"[DEBUG] Found final artifact of type: {type(final_artifact)}")
            task_state.completed_tool_outputs[tool_name] = final_artifact
            state_manager.save_task_state(task_state)
            logger.info(f"Saved final output artifact from '{tool_name}' to persistent state for task {task_id}.")
        else:
            logger.warning(f"[DEBUG] Final artifact key '{final_artifact_key}' not found in context store!")

        # 2. Clean up the ephemeral tool instance.
        state_manager.clear_tool_state(task_id)
        del orchestrator.active_tools[task_id]
        cleanup_task_logging(task_id)

        # 3. Create the handoff prompt.
        handoff_message = (
            f"The '{tool_name}' workflow has completed successfully. "
            f"The final artifact has been generated and reviewed.\n\n"
            f"To formally approve this phase, archive the results, and advance the task, "
            f"you MUST now call `alfred.approve_and_advance(task_id='{task_id}')`."
        )

        logger.info(f"Tool '{tool_name}' for task {task_id} finished. Awaiting final approval via approve_and_advance.")

        return ToolResponse(status="success", message=f"'{tool_name}' completed. Awaiting final approval.", next_prompt=handoff_message)
    else:
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
                feedback_notes,
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
            additional_context=additional_context,
        )
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)

``````
------ src/alfred/tools/review_task.py ------
``````
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import ReviewTaskTool
from src.alfred.core.prompter import prompter
from src.alfred.constants import ToolName

logger = get_logger(__name__)


async def review_task_impl(task_id: str) -> ToolResponse:
    """
    Review task entry point - handles the code review phase
    """
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
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status != TaskStatus.READY_FOR_REVIEW:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Review can only start on a 'ready_for_review' task.")

            tool_instance = ReviewTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_task_status(task_id, TaskStatus.IN_REVIEW)

            # Dispatch immediately to reviewing state
            tool_instance.dispatch()
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new review tool for task {task_id}")

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Code review initiated for task '{task_id}'."
    return ToolResponse(status="success", message=message, next_prompt=prompt)

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

    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
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
from src.alfred.state.manager import state_manager
from src.alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """Implements the logic for submitting a work artifact to the active tool."""
    # Try to get active tool or recover it from state
    if task_id not in orchestrator.active_tools:
        # Try to recover the tool from persisted state
        from src.alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            logger.info(f"Recovered tool for task {task_id} from persisted state")
        else:
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
    # For review states, we need the artifact as an object, not a string
    temp_context[ArtifactKeys.ARTIFACT_CONTENT_KEY] = validated_artifact

    next_prompt = prompter.generate_prompt(
        task=task,
        tool_name=active_tool.tool_name,
        state=next_state,
        additional_context=temp_context,
    )

    active_tool.context_store[artifact_key] = validated_artifact
    artifact_manager.append_to_scratchpad(task_id=task_id, state_name=current_state_val, artifact=validated_artifact)

    getattr(active_tool, trigger)()
    logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))

    state_manager.update_tool_state(task_id, active_tool)

    return ToolResponse(status=ResponseStatus.SUCCESS, message="Work submitted. Awaiting review.", next_prompt=next_prompt)

``````
------ src/alfred/tools/test_task.py ------
``````
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import TestTaskTool
from src.alfred.core.prompter import prompter
from src.alfred.constants import ToolName

logger = get_logger(__name__)


async def test_task_impl(task_id: str) -> ToolResponse:
    """
    Test task entry point - handles the testing phase
    """
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
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status != TaskStatus.READY_FOR_TESTING:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Testing can only start on a 'ready_for_testing' task.")

            tool_instance = TestTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_task_status(task_id, TaskStatus.IN_TESTING)

            # Dispatch immediately to testing state
            tool_instance.dispatch()
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new test tool for task {task_id}")

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Testing phase initiated for task '{task_id}'."
    return ToolResponse(status="success", message=message, next_prompt=prompt)

``````
------ src/alfred/tools/work_on.py ------
``````
from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.constants import ToolName
from src.alfred.lib.task_utils import does_task_exist_locally, write_task_to_markdown
from src.alfred.task_providers.factory import get_provider
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def work_on_impl(task_id: str) -> ToolResponse:
    # Step 1: Check if the task exists locally first (cache-first architecture)
    if not does_task_exist_locally(task_id):
        logger.info(f"Task '{task_id}' not found in local cache. Fetching from provider...")

        # Task is not in our local cache, fetch from provider
        provider = get_provider()

        try:
            # Delegate to the provider to fetch the task
            task = provider.get_task(task_id)

            if not task:
                return ToolResponse(
                    status="error", 
                    message=f"Task '{task_id}' could not be found. Please check:\n"
                            f"1. Task ID is correct (case-sensitive)\n"
                            f"2. For local tasks: File exists at .alfred/tasks/{task_id}.md\n"
                            f"3. For remote tasks: Task exists in your configured provider (Jira/Linear)\n"
                            f"4. Task file format is valid (see .alfred/tasks/README.md)\n"
                            f"5. Run 'alfred.get_next_task()' to see available tasks"
                )

            # Step 2: Cache the fetched task locally
            write_task_to_markdown(task)
            logger.info(f"Successfully cached task '{task_id}' from provider")

        except Exception as e:
            logger.error(f"Failed to fetch task from provider: {e}")
            return ToolResponse(status="error", message=f"Failed to fetch task '{task_id}' from provider: {str(e)}")

    # Step 3: Now that the task is guaranteed to be local, proceed with the
    # original "Smart Dispatch" logic
    task_state = state_manager.load_or_create_task_state(task_id)
    task_status = task_state.task_status

    handoff_tool_map = {
        TaskStatus.NEW: ToolName.PLAN_TASK,  # Start with creating spec for new epics
        TaskStatus.CREATING_SPEC: ToolName.CREATE_SPEC,
        TaskStatus.SPEC_COMPLETED: ToolName.CREATE_TASKS,
        TaskStatus.CREATING_TASKS: ToolName.CREATE_TASKS,
        TaskStatus.TASKS_CREATED: ToolName.PLAN_TASK,  # After tasks are created, plan the first one
        TaskStatus.PLANNING: ToolName.PLAN_TASK,
        TaskStatus.READY_FOR_DEVELOPMENT: ToolName.IMPLEMENT_TASK,
        TaskStatus.IN_DEVELOPMENT: ToolName.IMPLEMENT_TASK,
        TaskStatus.READY_FOR_REVIEW: ToolName.REVIEW_TASK,
        TaskStatus.IN_REVIEW: ToolName.REVIEW_TASK,
        TaskStatus.READY_FOR_TESTING: ToolName.TEST_TASK,
        TaskStatus.IN_TESTING: ToolName.TEST_TASK,
        TaskStatus.READY_FOR_FINALIZATION: ToolName.FINALIZE_TASK,
    }

    if task_status in handoff_tool_map:
        handoff_tool = handoff_tool_map[task_status]
        message = f"Task '{task_id}' is in status '{task_status.value}'. The next action is to use the '{handoff_tool}' tool."
        next_prompt = f"To proceed with task '{task_id}', call `alfred.{handoff_tool}(task_id='{task_id}')`."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)

    if task_status == TaskStatus.DONE:
        return ToolResponse(status="success", message=f"Task '{task_id}' is already done. No further action is required.")

    return ToolResponse(status="error", message=f"Unhandled status '{task_status.value}' for task '{task_id}'.")

``````
------ src/alfred/workflow.yml ------
``````
# Default Alfred Workflow Configuration
# This file can be customized per project by editing .alfred/workflow.yml

# Tool enable/disable settings
tools:
  # Core workflow tools
  create_spec:
    enabled: true
    description: "Create technical specification from PRD"
  
  create_tasks:
    enabled: true
    description: "Break down spec into actionable tasks"
  
  plan_task:
    enabled: true
    description: "Create detailed execution plan for a task"
    
  implement_task:
    enabled: true
    description: "Execute the planned implementation"
    
  review_task:
    enabled: true
    description: "Perform code review"
    
  test_task:
    enabled: true
    description: "Run and validate tests"
    
  finalize_task:
    enabled: true
    description: "Create commit and pull request"

# Workflow configuration
workflow:
  # Whether to require human approval at review gates
  require_human_approval: true
  
  # Whether to enable AI self-review steps
  enable_ai_review: true
  
  # Maximum thinking time for AI in seconds
  max_thinking_time: 300
  
  # Whether to create branches automatically
  auto_create_branches: true

# Provider-specific settings (overridden by .alfred/config.json)
providers:
  jira:
    # Jira-specific workflow settings
    transition_on_start: true
    transition_on_complete: true
    
  linear:
    # Linear-specific workflow settings
    update_status: true
    
  local:
    # Local provider settings
    task_file_pattern: "*.md"

# Debug settings
debug:
  # Whether to save detailed debug logs
  save_debug_logs: true
  
  # Whether to save state snapshots
  save_state_snapshots: true
  
  # Log level (DEBUG, INFO, WARNING, ERROR)
  log_level: INFO
``````
