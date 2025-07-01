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
    MARK_SUBTASK_COMPLETE: Final[str] = "mark_subtask_complete"


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
from .prompter import prompt_library, generate_prompt

__all__ = ["BaseWorkflowTool", "PlanTaskTool", "PlanTaskState", "prompt_library", "generate_prompt"]

``````
------ src/alfred/core/prompter.py ------
``````
# src/alfred/core/prompter_new.py
import json
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class PromptTemplate:
    """A simple template wrapper that provides clear error messages."""

    def __init__(self, content: str, source_file: Path):
        self.content = content
        self.source_file = source_file
        self.template = Template(content)
        self._required_vars = self._extract_variables()

    def _extract_variables(self) -> Set[str]:
        """Extract all ${var} placeholders from template."""
        import re

        # Match ${var} but not $${var} (escaped)
        return set(re.findall(r"(?<!\$)\$\{(\w+)\}", self.content))

    def render(self, context: Dict[str, Any]) -> str:
        """Render the template with context."""
        # Check for missing required variables
        provided_vars = set(context.keys())
        missing_vars = self._required_vars - provided_vars

        if missing_vars:
            raise ValueError(f"Missing required variables for {self.source_file.name}: {', '.join(sorted(missing_vars))}\nProvided: {', '.join(sorted(provided_vars))}")

        try:
            # safe_substitute won't fail on extra vars
            return self.template.safe_substitute(**context)
        except Exception as e:
            raise RuntimeError(f"Failed to render template {self.source_file.name}: {e}")


class PromptLibrary:
    """Manages file-based prompt templates."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt library.

        Args:
            prompts_dir: Directory containing prompts. Defaults to checking
                        user customization first, then packaged prompts.
        """
        if prompts_dir is None:
            # Check for user customization first
            user_prompts = settings.alfred_dir / "templates" / "prompts"
            if user_prompts.exists():
                prompts_dir = user_prompts
                logger.info(f"Using user prompt templates from {user_prompts}")
            else:
                # Fall back to packaged prompts
                prompts_dir = Path(__file__).parent.parent / "templates" / "prompts"
                logger.info(f"Using default prompt templates from {prompts_dir}")

        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptTemplate] = {}
        self._load_all_prompts()

    def _load_all_prompts(self) -> None:
        """Pre-load all prompts for validation."""
        count = 0
        for prompt_file in self.prompts_dir.rglob("*.md"):
            if prompt_file.name.startswith("_"):
                continue  # Skip special files

            try:
                content = prompt_file.read_text(encoding="utf-8")
                # Build key from relative path
                key = self._path_to_key(prompt_file)
                self._cache[key] = PromptTemplate(content, prompt_file)
                count += 1
            except Exception as e:
                logger.error(f"Failed to load prompt {prompt_file}: {e}")

        logger.info(f"Loaded {count} prompt templates")

    def _path_to_key(self, path: Path) -> str:
        """Convert file path to prompt key."""
        # Remove .md extension and convert path to dot notation
        relative = path.relative_to(self.prompts_dir)
        parts = list(relative.parts[:-1]) + [relative.stem]
        return ".".join(parts)

    def get(self, prompt_key: str) -> PromptTemplate:
        """Get a prompt template by key.

        Args:
            prompt_key: Dot-separated path (e.g., "plan_task.contextualize")

        Returns:
            PromptTemplate instance

        Raises:
            KeyError: If prompt not found
        """
        if prompt_key not in self._cache:
            available = ", ".join(sorted(self._cache.keys()))
            raise KeyError(f"Prompt '{prompt_key}' not found.\nAvailable prompts: {available}")

        return self._cache[prompt_key]

    def get_prompt_key(self, tool_name: str, state: str) -> str:
        """Map tool and state to the correct prompt key."""
        # Handle dynamic review states
        if state.endswith("_awaiting_ai_review"):
            return "review.ai_review"
        elif state.endswith("_awaiting_human_review"):
            return "review.human_review"

        # Direct mapping
        direct_key = f"{tool_name}.{state}"

        # Check if it exists
        if direct_key in self._cache:
            return direct_key

        # Try without tool name for shared prompts
        if state in self._cache:
            return state

        # Default fallback
        return "errors.not_found"

    def render(self, prompt_key: str, context: Dict[str, Any], strict: bool = True) -> str:
        """Render a prompt with context.

        Args:
            prompt_key: The prompt to render
            context: Variables to substitute
            strict: If True, fail on missing variables

        Returns:
            Rendered prompt string
        """
        template = self.get(prompt_key)

        if not strict:
            # Add empty strings for missing vars
            for var in template._required_vars:
                if var not in context:
                    context[var] = ""

        return template.render(context)

    def list_prompts(self) -> Dict[str, Dict[str, Any]]:
        """List all available prompts with metadata."""
        result = {}
        for key, template in self._cache.items():
            result[key] = {"file": str(template.source_file.relative_to(self.prompts_dir)), "required_vars": sorted(template._required_vars), "size": len(template.content)}
        return result

    def reload(self) -> None:
        """Reload all prompts (useful for development)."""
        logger.info("Reloading prompt templates...")
        self._cache.clear()
        self._load_all_prompts()


# Global instance
prompt_library = PromptLibrary()


class PromptBuilder:
    """Helper class to build consistent prompt contexts."""

    def __init__(self, task_id: str, tool_name: str, state: str):
        self.context = {
            "task_id": task_id,
            "tool_name": tool_name,
            "current_state": state,
            "feedback_section": "",
        }

    def with_task(self, task) -> "PromptBuilder":
        """Add task information to context."""
        self.context.update(
            {
                "task_title": task.title,
                "task_context": task.context,
                "implementation_details": task.implementation_details,
                "acceptance_criteria": self._format_list(task.acceptance_criteria),
                "task_status": task.task_status.value if hasattr(task.task_status, "value") else str(task.task_status),
            }
        )
        return self

    def with_artifact(self, artifact: Any, as_json: bool = True) -> "PromptBuilder":
        """Add artifact to context."""
        if as_json:
            if hasattr(artifact, "model_dump"):
                artifact_data = artifact.model_dump()
            else:
                artifact_data = artifact

            self.context["artifact_json"] = json.dumps(artifact_data, indent=2, default=str)
            self.context["artifact_summary"] = self._summarize_artifact(artifact_data)
        else:
            self.context["artifact"] = artifact
        return self

    def with_feedback(self, feedback: str) -> "PromptBuilder":
        """Add feedback to context."""
        if feedback:
            # Format feedback as a complete markdown section
            feedback_section = f"\n## REVISION FEEDBACK\nThe previous submission was reviewed and requires changes:\n\n{feedback}\n\nPlease address this feedback and resubmit.\n"
            self.context["feedback_section"] = feedback_section
        else:
            self.context["feedback_section"] = ""

        # Keep raw feedback for compatibility
        self.context["feedback"] = feedback
        self.context["has_feedback"] = bool(feedback)
        return self

    def with_custom(self, **kwargs) -> "PromptBuilder":
        """Add custom context variables."""
        self.context.update(kwargs)
        return self

    def build(self) -> Dict[str, Any]:
        """Return the built context."""
        return self.context.copy()

    @staticmethod
    def _format_list(items: list) -> str:
        """Format a list for prompt display."""
        if not items:
            return "- None specified"
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _summarize_artifact(artifact: Any) -> str:
        """Create a summary of an artifact for human review."""
        if isinstance(artifact, dict):
            # Try to extract key information
            if "summary" in artifact:
                return artifact["summary"]
            elif "title" in artifact:
                return artifact["title"]
            else:
                # Show first few keys
                keys = list(artifact.keys())[:5]
                return f"Artifact with fields: {', '.join(keys)}"
        return str(artifact)[:200]


def generate_prompt(task_id: str, tool_name: str, state: str, task: Any, additional_context: Optional[Dict[str, Any]] = None) -> str:
    """Main function to generate prompts - backward compatible wrapper."""

    # Handle both Enum and string state values
    state_value = state.value if hasattr(state, "value") else state

    # Get the correct prompt key
    prompt_key = prompt_library.get_prompt_key(tool_name, state_value)

    # Build context using the builder
    builder = PromptBuilder(task_id, tool_name, state_value).with_task(task)

    # Add additional context
    if additional_context:
        if "artifact_content" in additional_context:
            builder.with_artifact(additional_context["artifact_content"])
        if "feedback_notes" in additional_context:
            builder.with_feedback(additional_context["feedback_notes"])

        # Add everything else
        remaining = {k: v for k, v in additional_context.items() if k not in ["artifact_content", "feedback_notes"]}
        builder.with_custom(**remaining)

    # Render the prompt
    try:
        return prompt_library.render(prompt_key, builder.build())
    except KeyError:
        # Fallback for missing prompts
        logger.warning(f"Prompt not found for {prompt_key}, using fallback")
        return f"# {tool_name} - {state_value}\n\nNo prompt configured for this state.\nTask: {task_id}"

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
import os
import re
import tempfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from src.alfred.config.settings import settings
from src.alfred.lib.structured_logger import get_logger
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
        
        # Create an empty scratchpad file to avoid "file not found" errors
        scratchpad_path = self._get_scratchpad_path(task_id)
        if not scratchpad_path.exists():
            scratchpad_path.touch()
            logger.debug("Created empty scratchpad at %(scratchpad_path)s", scratchpad_path=scratchpad_path)
            
        logger.info("Created workspace for task %(task_id)s at %(task_dir)s", task_id=task_id, task_dir=task_dir)

    def append_to_scratchpad(self, task_id: str, state_name: str = None, artifact: BaseModel = None, content: str = None):
        """Renders a structured artifact and atomically appends it to the scratchpad."""
        task_dir = self._get_task_dir(task_id)
        if not task_dir.exists():
            self.create_task_workspace(task_id)

        scratchpad_path = self._get_scratchpad_path(task_id)
        
        # If we get raw content (string), handle it atomically as well
        if content is not None:
            rendered_content = content
        else:
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

        # --- THIS IS THE FIX: Atomic Append ---
        # 1. Read the current content if it exists
        current_content = ""
        if scratchpad_path.exists() and scratchpad_path.stat().st_size > 0:
            current_content = scratchpad_path.read_text(encoding="utf-8")

        # 2. Prepare the new full content
        separator = "\n\n---\n\n" if current_content else ""
        full_new_content = current_content + separator + rendered_content

        # 3. Write to a temporary file then rename
        fd, temp_path_str = tempfile.mkstemp(dir=scratchpad_path.parent, prefix=".tmp_scratch_")
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(full_new_content)
            os.replace(temp_path, scratchpad_path)
            logger.info("Atomically updated scratchpad for task %(task_id)s", task_id=task_id)
        except Exception as e:
            logger.error("Failed to atomically update scratchpad for %(task_id)s: %(e)s", task_id=task_id, e=e)
            if temp_path.exists():
                os.remove(temp_path)
            raise

    def archive_scratchpad(self, task_id: str, tool_name: str, workflow_step: int):
        """Moves the current scratchpad to a versioned file in the archive and creates a new empty scratchpad."""
        scratchpad_path = self._get_scratchpad_path(task_id)
        if not scratchpad_path.exists():
            logger.warning("No scratchpad found for task %(task_id)s to archive.", task_id=task_id)
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
        logger.info("Wrote JSON artifact to %(json_path)s", json_path=json_path)

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
------ src/alfred/lib/fs_utils.py ------
``````
# src/alfred/lib/fs_utils.py
import fcntl
import os
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Generator

@contextmanager
def file_lock(lock_file_path: Path) -> Generator[None, None, None]:
    """A context manager for acquiring an exclusive file lock."""
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file: IO | None = None
    try:
        # Open with 'a+' to create if not exists, and not truncate
        lock_file = lock_file_path.open('a+')
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    except (IOError, OSError):
        raise BlockingIOError(f"Could not acquire lock on {lock_file_path}. Another Alfred process may be active.")
    finally:
        if lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            try:
                os.remove(lock_file_path)
            except OSError:
                pass
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
------ src/alfred/lib/structured_logger.py ------
``````
"""
Structured logging configuration for Alfred.

Provides a structured logging system with:
- JSON formatter for machine-readable logs
- Human-readable formatter for console output
- Context managers for request/task tracking
- Consistent field names across all logs
"""

import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from src.alfred.config.settings import settings


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, include_context: bool = True):
        """Initialize the formatter.
        
        Args:
            include_context: Whether to include context fields in logs
        """
        super().__init__()
        self.include_context = include_context
        self.hostname = None
        try:
            import socket
            self.hostname = socket.gethostname()
        except Exception:
            pass
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base fields
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
            "process": record.process,
        }
        
        # Add hostname if available
        if self.hostname:
            log_entry["hostname"] = self.hostname
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add custom context fields if enabled
        if self.include_context:
            # Add task context
            if hasattr(record, "task_id"):
                log_entry["task_id"] = record.task_id
            
            # Add tool context
            if hasattr(record, "tool_name"):
                log_entry["tool_name"] = record.tool_name
            
            # Add request context
            if hasattr(record, "request_id"):
                log_entry["request_id"] = record.request_id
            
            # Add any extra fields passed via extra parameter
            for key, value in record.__dict__.items():
                if key not in ["name", "msg", "args", "created", "filename", "funcName", 
                              "levelname", "levelno", "lineno", "module", "msecs", 
                              "pathname", "process", "processName", "relativeCreated", 
                              "thread", "threadName", "exc_info", "exc_text", "stack_info",
                              "task_id", "tool_name", "request_id", "getMessage"]:
                    log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter with color support."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def __init__(self, use_colors: bool = True):
        """Initialize the formatter.
        
        Args:
            use_colors: Whether to use ANSI colors
        """
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with optional colors."""
        # Add context to message if available
        context_parts = []
        
        if hasattr(record, "task_id"):
            context_parts.append(f"task_id={record.task_id}")
        
        if hasattr(record, "tool_name"):
            context_parts.append(f"tool={record.tool_name}")
        
        if hasattr(record, "request_id"):
            context_parts.append(f"req_id={record.request_id}")
        
        if context_parts:
            record.msg = f"[{', '.join(context_parts)}] {record.msg}"
        
        # Format the message
        formatted = super().format(record)
        
        # Add colors if enabled
        if self.use_colors and record.levelname in self.COLORS:
            formatted = f"{self.COLORS[record.levelname]}{formatted}{self.RESET}"
        
        return formatted


class ContextFilter(logging.Filter):
    """Filter that adds context fields to log records."""
    
    def __init__(self):
        super().__init__()
        self.context = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context fields to the record."""
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class StructuredLogger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, name: str):
        """Initialize the structured logger.
        
        Args:
            name: Logger name (typically __name__)
        """
        self.logger = logging.getLogger(name)
        self._context_filter = ContextFilter()
        self.logger.addFilter(self._context_filter)
    
    def _log(self, level: int, msg: str, *args, extra: Optional[Dict[str, Any]] = None, **kwargs):
        """Internal logging method with extra context support."""
        # Merge any provided extra with kwargs
        if extra is None:
            extra = {}
        extra.update(kwargs)
        
        # Remove 'exc_info' from extra if present (it's a special parameter)
        exc_info = extra.pop('exc_info', None)
        
        self.logger.log(level, msg, *args, extra=extra, exc_info=exc_info)
    
    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with optional context."""
        self._log(logging.DEBUG, msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        """Log info message with optional context."""
        self._log(logging.INFO, msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with optional context."""
        self._log(logging.WARNING, msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        """Log error message with optional context."""
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with optional context."""
        self._log(logging.CRITICAL, msg, *args, **kwargs)
    
    def exception(self, msg: str, *args, **kwargs):
        """Log exception with traceback."""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, msg, *args, **kwargs)
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager to add fields to all logs within the context.
        
        Example:
            with logger.context(task_id="123", tool_name="plan_task"):
                logger.info("Processing task")
        """
        old_context = self._context_filter.context.copy()
        self._context_filter.context.update(kwargs)
        try:
            yield
        finally:
            self._context_filter.context = old_context
    
    def bind(self, **kwargs) -> "StructuredLogger":
        """Create a new logger instance with bound context fields.
        
        Example:
            task_logger = logger.bind(task_id="123")
            task_logger.info("Task started")
        """
        new_logger = StructuredLogger(self.logger.name)
        new_logger._context_filter.context.update(self._context_filter.context)
        new_logger._context_filter.context.update(kwargs)
        return new_logger


# Global logging configuration
_logging_configured = False
_task_handlers: Dict[str, logging.Handler] = {}


def configure_logging(
    level: Union[str, int] = "INFO",
    format_type: str = "human",
    log_to_file: bool = True,
    log_dir: Optional[Path] = None
) -> None:
    """Configure global logging settings.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Log format type ("json" or "human")
        log_to_file: Whether to log to files
        log_dir: Directory for log files (defaults to settings.alfred_dir / "logs")
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    # Convert string level to int
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if format_type == "json":
        console_handler.setFormatter(StructuredFormatter(include_context=True))
    else:
        console_handler.setFormatter(HumanReadableFormatter(use_colors=True))
    
    root_logger.addHandler(console_handler)
    
    # File handler (JSON format for files)
    if log_to_file:
        if log_dir is None:
            log_dir = settings.alfred_dir / "logs"
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Main application log
        app_log_file = log_dir / "alfred.log"
        file_handler = logging.FileHandler(app_log_file, mode="a")
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter(include_context=True))
        root_logger.addHandler(file_handler)
        
        # Error log (errors and above)
        error_log_file = log_dir / "errors.log"
        error_handler = logging.FileHandler(error_log_file, mode="a")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(StructuredFormatter(include_context=True))
        root_logger.addHandler(error_handler)
    
    _logging_configured = True


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        StructuredLogger instance
    """
    # Ensure logging is configured
    if not _logging_configured:
        configure_logging()
    
    return StructuredLogger(name)


def setup_task_logging(task_id: str) -> None:
    """Set up task-specific logging.
    
    Args:
        task_id: Task ID to set up logging for
    """
    if not settings.debugging_mode or task_id in _task_handlers:
        return
    
    # Create the debug directory for the task
    debug_dir = settings.alfred_dir / "debug" / task_id
    debug_dir.mkdir(parents=True, exist_ok=True)
    log_file = debug_dir / "alfred.log"
    
    # Create a file handler with JSON format for task logs
    handler = logging.FileHandler(log_file, mode="a")
    handler.setFormatter(StructuredFormatter(include_context=True))
    handler.setLevel(logging.DEBUG)  # Capture all logs for debugging
    
    # Add filter to only log messages with this task_id
    class TaskFilter(logging.Filter):
        def filter(self, record):
            return getattr(record, 'task_id', None) == task_id
    
    handler.addFilter(TaskFilter())
    
    # Add the handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    
    _task_handlers[task_id] = handler


def cleanup_task_logging(task_id: str) -> None:
    """Remove task-specific log handler.
    
    Args:
        task_id: Task ID to clean up logging for
    """
    if task_id in _task_handlers:
        handler = _task_handlers.pop(task_id)
        logging.getLogger().removeHandler(handler)
        handler.close()


@contextmanager
def log_duration(logger: StructuredLogger, operation: str, level: int = logging.INFO, **context):
    """Context manager to log operation duration.
    
    Args:
        logger: Logger instance
        operation: Description of the operation
        level: Log level to use
        **context: Additional context fields
    
    Example:
        with log_duration(logger, "database_query", query="SELECT * FROM users"):
            # perform query
    """
    start_time = time.time()
    context['operation'] = operation
    context['start_time'] = datetime.now(timezone.utc).isoformat()
    
    logger._log(level, f"{operation} started", **context)
    
    try:
        yield
    except Exception as e:
        duration = time.time() - start_time
        context['duration_ms'] = int(duration * 1000)
        context['error'] = str(e)
        context['success'] = False
        logger.error(f"{operation} failed", **context, exc_info=True)
        raise
    else:
        duration = time.time() - start_time
        context['duration_ms'] = int(duration * 1000)
        context['success'] = True
        logger._log(level, f"{operation} completed", **context)
``````
------ src/alfred/lib/task_utils.py ------
``````
# src/alfred/lib/task_utils.py
from pathlib import Path
from typing import Optional

from src.alfred.models.schemas import Task
from src.alfred.lib.structured_logger import get_logger
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
        logger.error("Failed to load task %(task_id)s: %(e)s", task_id=task_id, e=e)
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
    
    logger.info("Wrote task %(task_task_id)s to %(task_file)s", task_task_id=task.task_id, task_file=task_file)


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
    IN_FINALIZATION = "in_finalization"
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
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.core.prompter import prompt_library  # Import the prompt library
from src.alfred.lib.logger import get_logger
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.tools.approve_and_advance import approve_and_advance_impl
from src.alfred.constants import ToolName
from src.alfred.tools.registry import tool_registry
from src.alfred.tools.create_spec import create_spec_impl
from src.alfred.tools.create_tasks import create_tasks_impl
from src.alfred.tools.finalize_task import finalize_task_impl, FinalizeTaskHandler, finalize_task_handler
from src.alfred.tools.get_next_task import get_next_task_impl
from src.alfred.tools.implement_task import implement_task_impl, ImplementTaskHandler, implement_task_handler
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl, PlanTaskHandler
from src.alfred.core.workflow import PlanTaskTool, ImplementTaskTool, ReviewTaskTool, TestTaskTool, FinalizeTaskTool
from src.alfred.tools.progress import mark_subtask_complete_impl, mark_subtask_complete_handler
from src.alfred.tools.approve_review import approve_review_impl
from src.alfred.tools.request_revision import request_revision_impl
from src.alfred.tools.review_task import ReviewTaskHandler, review_task_handler
from src.alfred.tools.submit_work import submit_work_handler
from src.alfred.tools.test_task import TestTaskHandler, test_task_handler
from src.alfred.tools.work_on import work_on_impl

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifespan context manager for FastMCP server."""
    # Startup
    logger.info(f"Starting Alfred server with {len(prompt_library._cache)} prompts loaded")

    yield

    # Shutdown (if needed in the future)
    logger.info("Server shutting down")


app = FastMCP(settings.server_name, lifespan=lifespan)


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


# THIS IS THE FIX for Blocker #2
@app.tool()
@tool_registry.register(
    name=ToolName.PLAN_TASK, handler_class=PlanTaskHandler, tool_class=PlanTaskTool, entry_status_map={TaskStatus.NEW: TaskStatus.PLANNING, TaskStatus.PLANNING: TaskStatus.PLANNING}
)
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
    handler = PlanTaskHandler()
    return await handler.execute(task_id)


@app.tool()
@log_tool_transaction(submit_work_handler.execute)
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step of a workflow tool.

    - Generic state-advancing tool for any active workflow (plan, implement, review, test)
    - Automatically determines correct state transition based on current state
    - Validates artifact structure against expected schema for current state
    - Advances the tool's state machine to next step or review phase
    - Works with all workflow tools: plan_task, implement_task, review_task, test_task

    The artifact structure varies by tool and state:
    - **Planning states**: context_analysis, strategy, design, subtasks
    - **Implementation**: progress updates, completion status
    - **Review**: findings, issues, recommendations
    - **Testing**: test results, coverage, validation status

    Parameters:
        task_id (str): The unique identifier for the task (e.g., "AL-01", "TS-123")
        artifact (dict): Structured data matching the current state's expected schema

    Returns:
        ToolResponse: Contains:
            - success: Whether submission was accepted
            - data.next_action: The next tool/action to take
            - data.state: New state after transition
            - data.prompt: Next prompt for user interaction

    Examples:
        # Planning context submission
        submit_work("AL-01", {
            "understanding": "Task requires refactoring auth module...",
            "constraints": ["Must maintain backward compatibility"],
            "risks": ["Potential breaking changes to API"]
        })

        # Implementation progress
        submit_work("AL-02", {
            "progress": "Completed authentication refactor",
            "subtasks_completed": ["subtask-1", "subtask-2"]
        })

    Next Actions:
        - If in review state: Use approve_review or request_revision
        - If advancing to new phase: Tool will indicate next tool to use
        - If complete: No further action needed
    """
    return await submit_work_handler.execute(task_id, artifact=artifact)


@app.tool()
@log_tool_transaction(approve_review_impl)
async def approve_review(task_id: str) -> ToolResponse:
    """
    Approves the artifact in the current review step and advances the workflow.

    - Approves work in any review state (AI self-review or human review)
    - Advances workflow to next phase or completion
    - Works with all review states across all workflow tools
    - Automatically determines next state based on current workflow phase

    Applicable States:
    - **Planning**: review_context, review_strategy, review_design, review_plan
    - **Implementation**: awaiting_human_review after completion
    - **Review**: awaiting_ai_review, awaiting_human_review
    - **Testing**: awaiting_ai_review, awaiting_human_review

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether approval was successful
            - data.next_action: Next tool to use (if any)
            - data.new_state: State after approval
            - data.message: Guidance for next steps

    Examples:
        # Approve planning context analysis
        approve_review("AL-01")  # Advances to strategy phase

        # Approve final implementation
        approve_review("AL-02")  # Advances to review phase

    Next Actions:
        - Planning phases: Continues to next planning step via submit_work
        - Phase transitions: Use the indicated next tool (review_task, test_task, etc.)
        - Final approval: Task moves to completed state

    Preconditions:
        - Must be in a review state (awaiting_ai_review or awaiting_human_review)
        - Artifact must have been submitted for current state
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(request_revision_impl)
async def request_revision(task_id: str, feedback_notes: str) -> ToolResponse:
    """
    Rejects the artifact in the current review step and sends it back for revision.

    - Requests revision for work in any review state
    - Sends workflow back to previous working state for improvements
    - Requires detailed, actionable feedback for the implementer
    - Preserves revision history for audit trail

    Feedback Guidelines:
    - Be specific about what needs improvement
    - Provide concrete examples when possible
    - Suggest specific solutions or approaches
    - Focus on actionable items, not vague concerns
    - Prioritize critical issues over minor improvements

    Parameters:
        task_id (str): The unique identifier for the task
        feedback_notes (str): Detailed, actionable feedback explaining required changes

    Returns:
        ToolResponse: Contains:
            - success: Whether revision request was processed
            - data.state: State returned to for revision
            - data.prompt: Updated prompt including feedback
            - data.feedback: The feedback provided for reference

    Examples:
        # Request planning revision
        request_revision("AL-01",
            "The context analysis is missing critical dependency information. "
            "Please add: 1) List of dependent services, 2) API contracts that "
            "might be affected, 3) Database schema dependencies"
        )

        # Request implementation fixes
        request_revision("AL-02",
            "The error handling is incomplete. Specifically: "
            "1) No timeout handling in API calls (add 30s timeout), "
            "2) Missing rollback logic for failed transactions, "
            "3) No retry mechanism for transient failures"
        )

    Next Actions:
        - Implementer should address feedback using submit_work
        - After revision, work returns to review state
        - Process repeats until approved

    Good Feedback Examples:
        - "Add input validation for email field using regex pattern"
        - "Refactor calculateTotal() to handle null values in items array"
        - "Add unit tests for error cases in auth middleware"

    Poor Feedback Examples:
        - "Code needs improvement" (too vague)
        - "Don't like the approach" (not actionable)
        - "Try again" (no guidance)
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(mark_subtask_complete_handler.execute)
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
@tool_registry.register(
    name=ToolName.IMPLEMENT_TASK,
    handler_class=ImplementTaskHandler,
    tool_class=ImplementTaskTool,
    # THIS IS FIX #6: Add self-map for IN_DEVELOPMENT
    entry_status_map={
        TaskStatus.READY_FOR_DEVELOPMENT: TaskStatus.IN_DEVELOPMENT,
        TaskStatus.IN_DEVELOPMENT: TaskStatus.IN_DEVELOPMENT,
    },
)
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
    return await implement_task_handler.execute(task_id)


@app.tool()
@tool_registry.register(
    name=ToolName.REVIEW_TASK,
    handler_class=ReviewTaskHandler,
    tool_class=ReviewTaskTool,
    entry_status_map={
        TaskStatus.READY_FOR_REVIEW: TaskStatus.IN_REVIEW,
        TaskStatus.IN_REVIEW: TaskStatus.IN_REVIEW,
    },
)
async def review_task(task_id: str) -> ToolResponse:
    """
    Initiates the code review phase for a task that has completed implementation.

    - Comprehensive code review against requirements and best practices
    - Checks implementation completeness, quality, and correctness
    - Validates against original task requirements and acceptance criteria
    - Reviews code style, patterns, error handling, and edge cases
    - Ensures tests are present and passing

    Review Criteria:
    - **Functionality**: Does the code fulfill all requirements?
    - **Completeness**: Are all subtasks from the plan implemented?
    - **Code Quality**: Follows project patterns and best practices?
    - **Error Handling**: Proper error handling and edge cases?
    - **Testing**: Adequate test coverage for new functionality?
    - **Performance**: No obvious performance issues?
    - **Security**: No security vulnerabilities introduced?

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether review was initiated
            - data.prompt: Review checklist and guidance
            - data.state: Current review state
            - data.requirements: Original requirements for reference

    Examples:
        review_task("AL-01")  # Starts comprehensive code review

    Review Process:
    1. Tool loads implementation details and original requirements
    2. Presents comprehensive review checklist
    3. Reviewer performs thorough code review
    4. Reviewer submits findings via submit_work
    5. AI reviews the human review for completeness
    6. Final approval/revision via approve_review or request_revision

    Next Actions:
        - Use submit_work to provide review findings
        - After review submission, use approve_review or request_revision
        - If approved, advances to test_task

    Preconditions:
        - Task must be in READY_FOR_REVIEW status
        - Implementation must be complete
        - All subtasks should be marked complete
    """
    return await review_task_handler.execute(task_id)


@app.tool()
@tool_registry.register(
    name=ToolName.TEST_TASK,
    handler_class=TestTaskHandler,
    tool_class=TestTaskTool,
    entry_status_map={
        TaskStatus.READY_FOR_TESTING: TaskStatus.IN_TESTING,
        TaskStatus.IN_TESTING: TaskStatus.IN_TESTING,
    },
)
async def test_task(task_id: str) -> ToolResponse:
    """
    Initiates the testing phase for a task that has passed code review.

    - Executes comprehensive test suite for the implementation
    - Runs unit tests, integration tests, and validation checks
    - Verifies implementation against acceptance criteria
    - Checks for regressions in existing functionality
    - Validates edge cases and error scenarios

    Testing Scope:
    - **Unit Tests**: Test individual functions/methods
    - **Integration Tests**: Test component interactions
    - **Regression Tests**: Ensure no existing functionality broken
    - **Edge Cases**: Validate boundary conditions
    - **Error Scenarios**: Test error handling paths
    - **Performance**: Basic performance validation
    - **Manual Testing**: UI/UX validation if applicable

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether testing was initiated
            - data.prompt: Testing checklist and guidance
            - data.test_requirements: What needs to be tested
            - data.acceptance_criteria: Original criteria to validate

    Examples:
        test_task("AL-01")  # Starts comprehensive testing phase

    Testing Process:
    1. Tool provides testing checklist and requirements
    2. Tester runs automated test suites
    3. Tester performs manual validation if needed
    4. Tester documents results via submit_work
    5. Results are reviewed for completeness
    6. Approval/revision via approve_review or request_revision

    Test Result Structure (for submit_work):
        {
            "test_summary": "All tests passing with 95% coverage",
            "unit_tests": {"passed": 45, "failed": 0},
            "integration_tests": {"passed": 12, "failed": 0},
            "manual_tests": ["UI responsive on mobile", "Forms validate correctly"],
            "issues_found": [],
            "coverage": "95%"
        }

    Next Actions:
        - Use submit_work to provide test results
        - After submission, use approve_review or request_revision
        - If approved, advances to finalize_task

    Preconditions:
        - Task must be in READY_FOR_TESTING status
        - Code review must be complete and approved
        - Implementation should be stable
    """
    return await test_task_handler.execute(task_id)


@app.tool()
@tool_registry.register(
    name=ToolName.FINALIZE_TASK,
    handler_class=FinalizeTaskHandler,
    tool_class=FinalizeTaskTool,
    entry_status_map={
        TaskStatus.READY_FOR_FINALIZATION: TaskStatus.IN_FINALIZATION,
        TaskStatus.IN_FINALIZATION: TaskStatus.IN_FINALIZATION,
    },
)
@log_tool_transaction(finalize_task_impl)
async def finalize_task(task_id: str) -> ToolResponse:
    """
    Completes the task by creating a commit and pull request.

    - Creates comprehensive git commit with all changes
    - Generates pull request with detailed description
    - Links PR to original task/issue
    - Updates task status to completed
    - Archives all task artifacts and history

    Finalization Process:
    1. **Commit Creation**:
       - Stages all modified files
       - Creates descriptive commit message
       - Includes task ID and summary

    2. **Pull Request**:
       - Auto-generates PR description from task history
       - Includes implementation summary
       - Lists all changes made
       - References original requirements
       - Adds testing notes

    3. **Task Completion**:
       - Updates task status to COMPLETED
       - Archives all workflow artifacts
       - Preserves audit trail

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether finalization succeeded
            - data.commit_sha: Git commit hash
            - data.pr_url: Pull request URL
            - data.pr_number: PR number for reference
            - data.summary: Summary of completed work

    Examples:
        finalize_task("AL-01")
        # Creates commit and PR with:
        # - Title: "AL-01: Implement user authentication refactor"
        # - Description: Auto-generated from task history
        # - Links: References to original issue/task

    PR Description Includes:
        - Task summary and objectives
        - List of changes made
        - Testing performed
        - Any breaking changes
        - Deployment notes

    Next Actions:
        - Review pull request in version control system
        - Merge PR when approved by reviewers
        - Deploy changes according to process
        - Close related issues/tickets

    Preconditions:
        - Task must be in READY_FOR_FINALIZATION status
        - All tests must be passing
        - All reviews must be approved
        - No uncommitted changes in working directory

    Note: This tool does NOT push to remote or merge the PR.
    Manual review and merge is required per team process.
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(approve_and_advance_impl)
async def approve_and_advance(task_id: str) -> ToolResponse:
    """
    Approves the current phase and advances to the next phase in the workflow.

    - Convenience tool combining approve_review + automatic phase transition
    - Skips intermediate approval states for faster workflow
    - Ideal for when you're confident in the current work
    - Automatically determines and initiates next phase

    Phase Transitions:
    - **Planning** → Implementation (via implement_task)
    - **Implementation** → Review (via review_task)
    - **Review** → Testing (via test_task)
    - **Testing** → Finalization (via finalize_task)
    - **Finalization** → Completed (task done)

    This tool handles:
    1. Approves current review state
    2. Determines next logical phase
    3. Automatically initiates next phase
    4. Returns guidance for next steps

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether advancement succeeded
            - data.from_phase: Phase completed
            - data.to_phase: New phase started
            - data.next_tool: Tool to use for new phase
            - data.prompt: Guidance for next phase

    Examples:
        # After planning completion
        approve_and_advance("AL-01")
        # Approves plan and starts implement_task

        # After implementation
        approve_and_advance("AL-02")
        # Approves implementation and starts review_task

    When to Use:
        - You've reviewed the work and it's ready to proceed
        - You want to skip manual approval steps
        - You're confident no revisions are needed

    When NOT to Use:
        - You need to review the work carefully first
        - You might need revisions
        - You want to pause between phases

    Next Actions:
        - Follow the guidance for the next phase
        - Use the indicated tool for the new phase
        - Continue workflow until task completion

    Preconditions:
        - Must be in a review state
        - Current phase work must be submitted
        - Cannot skip required phases

    Note: This tool enforces the standard workflow order.
    You cannot skip phases or move backward.
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
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from src.alfred.lib.fs_utils import file_lock
from src.alfred.lib.logger import get_logger
from src.alfred.models.state import TaskState
from src.alfred.state.unit_of_work import StateUnitOfWork
from src.alfred.models.schemas import TaskStatus

logger = get_logger(__name__)


class StateManager:
    """Manages the persistence layer for TaskState objects."""

    def _get_task_dir(self, task_id: str) -> Path:
        from src.alfred.config.settings import settings

        return settings.workspace_dir / task_id

    def _get_task_state_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "task_state.json"

    def _get_lock_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / ".state.lock"

    def _atomic_write(self, state: TaskState):
        """Internal atomic file write, assumes lock is held."""
        state_file = self._get_task_state_file(state.task_id)
        state.updated_at = datetime.utcnow().isoformat()

        # Create the complete workspace structure
        task_dir = state_file.parent
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create archive directory
        archive_dir = task_dir / "archive"
        archive_dir.mkdir(exist_ok=True)

        # Create empty scratchpad.md if it doesn't exist
        scratchpad_path = task_dir / "scratchpad.md"
        if not scratchpad_path.exists():
            scratchpad_path.touch(mode=0o600)  # Create with restricted permissions

        fd, temp_path_str = tempfile.mkstemp(dir=state_file.parent, prefix=".tmp_")
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(fd, "w") as f:
                f.write(state.model_dump_json(indent=2))
            os.replace(temp_path, state_file)
        except Exception:
            if temp_path.exists():
                os.remove(temp_path)
            raise

    def load_or_create(self, task_id: str, lock: bool = True) -> TaskState:
        """Loads a task's state from disk, creating it if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)

        def _load():
            if not state_file.exists():
                logger.info(f"No state file for task {task_id}. Creating new state.")
                return TaskState(task_id=task_id)

            try:
                return TaskState.model_validate_json(state_file.read_text())
            except Exception as e:
                logger.error(f"Failed to load or validate state for task {task_id}, creating new. Error: {e}")
                return TaskState(task_id=task_id)

        if lock:
            with file_lock(self._get_lock_file(task_id)):
                return _load()
        return _load()

    @contextmanager
    def transaction(self):
        """Provides a transactional unit of work for state modifications."""
        uow = StateUnitOfWork(self)
        try:
            yield uow
            uow.commit()
        except Exception as e:
            logger.error(f"State transaction failed, rolling back. Error: {e}", exc_info=True)
            uow.rollback()
            raise

    # --- Thin Wrappers for Backward Compatibility ---
    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        with self.transaction() as uow:
            uow.update_task_status(task_id, new_status)

    def update_tool_state(self, task_id: str, tool: Any) -> None:
        with self.transaction() as uow:
            uow.update_tool_state(task_id, tool)

    def clear_tool_state(self, task_id: str) -> None:
        with self.transaction() as uow:
            uow.clear_tool_state(task_id)

    def add_completed_output(self, task_id: str, tool_name: str, artifact: Any) -> None:
        with self.transaction() as uow:
            uow.add_completed_output(task_id, tool_name, artifact)

    def load_or_create_task_state(self, task_id: str) -> TaskState:
        return self.load_or_create(task_id)

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        from src.alfred.constants import Paths

        archive_path = self._get_task_dir(task_id) / Paths.ARCHIVE_DIR
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
------ src/alfred/state/unit_of_work.py ------
``````
# src/alfred/state/unit_of_work.py
from __future__ import annotations
import json
import os
import tempfile
from typing import Any, Dict, TYPE_CHECKING

from pydantic import BaseModel

from src.alfred.lib.fs_utils import file_lock
from src.alfred.lib.logger import get_logger
from src.alfred.models.state import TaskState, WorkflowState

if TYPE_CHECKING:
    from src.alfred.core.workflow import BaseWorkflowTool
    from src.alfred.models.schemas import TaskStatus
    from src.alfred.state.manager import StateManager

logger = get_logger(__name__)


class StateUnitOfWork:
    """Implements the Unit of Work pattern for atomic state updates."""

    def __init__(self, state_manager: "StateManager"):
        self.state_manager = state_manager
        self._pending_changes: Dict[str, TaskState] = {}
        self._loaded_states: Dict[str, TaskState] = {}

    def _get_current_state(self, task_id: str) -> TaskState:
        """Gets the current state, loading it from disk or cache if necessary."""
        if task_id in self._pending_changes:
            return self._pending_changes[task_id]
        if task_id in self._loaded_states:
            return self._loaded_states[task_id]

        state = self.state_manager.load_or_create(task_id, lock=False)
        self._loaded_states[task_id] = state
        return state

    def update_task_status(self, task_id: str, status: "TaskStatus"):
        """Stage a status update."""
        state = self._get_current_state(task_id)
        state.task_status = status
        self._pending_changes[task_id] = state

    def update_tool_state(self, task_id: str, tool: "BaseWorkflowTool"):
        """Stage a tool state update."""
        state = self._get_current_state(task_id)
        serializable_context = {key: value.model_dump() if isinstance(value, BaseModel) else value for key, value in tool.context_store.items()}
        tool_state_data = WorkflowState(task_id=task_id, tool_name=tool.tool_name, current_state=str(tool.state), context_store=serializable_context)
        state.active_tool_state = tool_state_data
        self._pending_changes[task_id] = state

    def clear_tool_state(self, task_id: str):
        """Stage the clearing of a tool state."""
        state = self._get_current_state(task_id)
        state.active_tool_state = None
        self._pending_changes[task_id] = state

    def add_completed_output(self, task_id: str, tool_name: str, artifact: Any):
        """Stage the addition of a completed tool's output."""
        state = self._get_current_state(task_id)
        serializable_artifact = artifact.model_dump() if isinstance(artifact, BaseModel) else artifact
        state.completed_tool_outputs[tool_name] = serializable_artifact
        self._pending_changes[task_id] = state

    def commit(self):
        """Atomically commit all pending changes for all tasks."""
        if not self._pending_changes:
            logger.debug("No pending state changes to commit.")
            return

        for task_id, state in self._pending_changes.items():
            lock_file = self.state_manager._get_lock_file(task_id)
            with file_lock(lock_file):
                self.state_manager._atomic_write(state)

        logger.info(f"Committed state changes for tasks: {list(self._pending_changes.keys())}")
        self._pending_changes.clear()
        self._loaded_states.clear()

    def rollback(self):
        """Discard all pending changes."""
        if self._pending_changes:
            logger.warning(f"Rolling back pending state changes for tasks: {list(self._pending_changes.keys())}")
        self._pending_changes.clear()
        self._loaded_states.clear()

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
            if not task_data.get("task_id"):
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
------ src/alfred/templates/CLAUDE.md ------
``````
# **ALFRED TEMPLATE SYSTEM PRINCIPLES**

## **CORE PHILOSOPHY**
Templates are **DATA, not CODE**. They should be as static and predictable as possible.

## **THE GOLDEN RULES**

### **1. NEVER MODIFY TEMPLATE STRUCTURE**
- Templates follow a **STRICT SECTION FORMAT** - do not add, remove, or reorder sections
- The sections are: CONTEXT → OBJECTIVE → BACKGROUND → INSTRUCTIONS → CONSTRAINTS → OUTPUT → EXAMPLES
- If a section doesn't apply, leave it empty - DO NOT REMOVE IT

### **2. TEMPLATES ARE WRITE-ONCE**
- Once a template file is created, its **variables** are FROZEN
- You can edit the text content, but NEVER add new `${variables}`
- If you need new data, pass it through existing variables or create a NEW template

### **3. ONE FILE = ONE PURPOSE**
- Each template file serves **exactly one** state/purpose
- No conditional logic inside templates
- No dynamic content generation
- If you need different content for different scenarios, create separate template files

### **4. VARIABLE NAMING IS SACRED**
```
Standard variables (NEVER RENAME THESE):
- ${task_id}          - The task identifier
- ${tool_name}        - Current tool name  
- ${current_state}    - Current workflow state
- ${task_title}       - Task title
- ${task_context}     - Task goal/context
- ${implementation_details} - Implementation overview
- ${acceptance_criteria}    - Formatted AC list
- ${artifact_json}    - JSON representation of artifacts
- ${feedback}         - Review feedback
```

### **5. NO LOGIC IN TEMPLATES**
- **FORBIDDEN**: `{% if %}`, `{% for %}`, complex Jinja2
- **ALLOWED**: Simple `${variable}` substitution only
- If you need logic, handle it in Python and pass the result as a variable

### **6. EXPLICIT PATHS ONLY**
- Template location = `prompts/{tool_name}/{state}.md`
- No dynamic path construction
- No fallback chains
- If a template doesn't exist, it's an ERROR - don't silently fall back

## **WHEN WORKING WITH TEMPLATES**

### **DO:**
- ✅ Edit prompt text to improve AI behavior
- ✅ Clarify instructions within existing structure  
- ✅ Add examples in the EXAMPLES section
- ✅ Improve formatting for readability
- ✅ Fix typos and grammar

### **DON'T:**
- ❌ Add new variables to existing templates
- ❌ Create dynamic template paths
- ❌ Add conditional logic
- ❌ Merge multiple templates into one
- ❌ Create "smart" template loading logic
- ❌ Mix templates with code generation

## **ADDING NEW FUNCTIONALITY**

### **Need a new prompt?**
1. Create a new file at the correct path: `prompts/{tool_name}/{state}.md`
2. Use ONLY the standard variables listed above
3. Follow the EXACT section structure
4. Test that it renders with standard context

### **Need new data in a prompt?**
1. **STOP** - Can you use existing variables?
2. If absolutely necessary, document the new variable in the template header
3. Update the PromptBuilder to provide this variable
4. Update THIS DOCUMENT with the new standard variable

### **Need conditional behavior?**
1. Create separate template files for each condition
2. Handle the logic in Python code
3. Choose which template to load based on the condition

## **TEMPLATE HEADER REQUIREMENT**

Every template MUST start with this header:

```markdown
<!--
Template: {tool_name}.{state}
Purpose: [One line description]
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  [List ALL variables used in this template]
-->
```

## **TESTING TEMPLATES**

Before committing ANY template change:

1. **Variable Check**: List all `${variables}` in the template
2. **Render Test**: Ensure it renders with standard context
3. **No Logic Check**: Confirm no `{% %}` tags exist
4. **Structure Check**: Verify all sections are present

```python
# Test snippet to include in your tests
def verify_template(template_path):
    content = template_path.read_text()
    
    # No Jinja2 logic
    assert '{%' not in content, "No logic allowed in templates"
    
    # Has all sections
    required_sections = ['# CONTEXT', '# OBJECTIVE', '# BACKGROUND', 
                        '# INSTRUCTIONS', '# CONSTRAINTS', '# OUTPUT']
    for section in required_sections:
        assert section in content, f"Missing {section}"
    
    # Extract variables
    import re
    variables = re.findall(r'\$\{(\w+)\}', content)
    
    # All variables are standard
    standard_vars = {'task_id', 'tool_name', 'current_state', 'task_title',
                    'task_context', 'implementation_details', 'acceptance_criteria',
                    'artifact_json', 'feedback'}
    
    unknown_vars = set(variables) - standard_vars
    assert not unknown_vars, f"Unknown variables: {unknown_vars}"
```

## **ERROR MESSAGES**

When templates fail, the error should be:
- **SPECIFIC**: "Missing required variable 'task_id' in template plan_task.contextualize"
- **ACTIONABLE**: Show what variables were provided vs required
- **TRACEABLE**: Include the template file path

Never:
- Silently fall back to a default
- Generate templates dynamically
- Guess at missing variables

## **THE MAINTENANCE PLEDGE**

*"I will treat templates as immutable contracts. I will not add complexity to make them 'smarter'. I will keep logic in code and content in templates. When in doubt, I will create a new template rather than make an existing one more complex."*

---

**Remember**: Every time you add logic to a template, somewhere a production system breaks at 3 AM. Keep templates simple, predictable, and boring. Boring templates are reliable templates.
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
------ src/alfred/templates/prompts/_schema.md ------
``````
# Alfred Prompt Template Guidelines

## Structure
Every prompt should follow the standard sections:
1. CONTEXT - Current state and task information
2. OBJECTIVE - Clear, single-sentence goal
3. BACKGROUND - Necessary context and previous work
4. INSTRUCTIONS - Step-by-step guide
5. CONSTRAINTS - Limitations and requirements
6. OUTPUT - Expected format and action
7. EXAMPLES (optional) - Good/bad examples

## Variables
Standard variables available in all prompts:
- `${task_id}` - The task identifier
- `${tool_name}` - Current tool name
- `${current_state}` - Current workflow state
- `${task_title}` - Task title
- `${task_context}` - Task goal/context
- `${implementation_details}` - Implementation overview
- `${acceptance_criteria}` - Formatted AC list

## Writing Guidelines
1. **Be explicit** - State exactly what you want
2. **Use consistent tone** - Professional but conversational
3. **Number instructions** - Makes them easy to follow
4. **Include examples** - When behavior might be ambiguous
5. **Specify output format** - Be clear about expected structure
6. **End with action** - Always specify the required function call

## Testing Your Prompts
1. Check all variables are defined
2. Verify instructions are clear and ordered
3. Ensure output format is unambiguous
4. Test with edge cases
5. Review generated outputs for quality
``````
------ src/alfred/templates/prompts/create_spec/drafting_spec.md ------
``````
# Review Your Engineering Specification

You previously created an engineering specification. Please review it carefully and consider if any improvements are needed.

## Task ID: ${task_id}

## Your Engineering Specification

${task_artifact_content}

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

## Task ID: ${task_id}

## Product Requirements Document

```
${task_prd_content}
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
------ src/alfred/templates/prompts/create_tasks/create_tasks_from_spec.md ------
``````
# ROLE: Senior Principal Engineer & Project Planner

# OBJECTIVE
Your sole mission is to deconstruct the provided Engineering Specification into a comprehensive and logical list of atomic development tasks. Each task must be a self-contained unit of work that a developer can execute. The final output must be a valid JSON object containing a list of `Task` objects.

---
### **ENGINEERING SPECIFICATION (Source of Truth)**
```json
${spec_content}
```
---
### **THINKING METHODOLOGY: Chain-of-Thought Deconstruction**

Before generating the final JSON output, you MUST work through the following analysis steps internally. This is your internal monologue and will not be in the final output.

#### **Step 1: Ingest and Synthesize**
- Read the entire `EngineeringSpec` from top to bottom.
- Synthesize the `Overview`, `Definition of Success`, and `Requirements` sections to form a deep understanding of the project's core goals. What is the "why" behind this work?

#### **Step 2: Deconstruct the Design into Epics**
- Analyze the `Design` section (`Major Design Considerations`, `API`, `Data Storage`, etc.).
- Mentally group the work into logical high-level "epics" or themes. Examples: "API Endpoint Creation," "Database Schema Migration," "Frontend Component Refactor," "New Observability Stack."

#### **Step 3: Decompose Epics into Atomic Tasks**
- For each "epic" you identified, break it down into the smallest possible, independently testable tasks.
- A good task is something one developer can complete in a reasonable timeframe (e.g., a few hours to a day).
- **Example Decomposition:**
    - **Epic:** "API Endpoint Creation"
    - **Tasks:**
        - `Create Pydantic models for API request/response.`
        - `Implement GET /resource endpoint logic.`
        - `Implement POST /resource endpoint logic.`
        - `Add unit tests for GET endpoint.`
        - `Add unit tests for POST endpoint.`
        - `Add integration test for API resource lifecycle.`
        - `Update OpenAPI/Swagger documentation for new endpoints.`

#### **Step 4: Establish Dependency Chains**
- Review your full list of atomic tasks.
- For each task, identify its direct prerequisites. A task can only depend on other tasks you have defined in this plan.
- Establish a clear, logical sequence. For example, you cannot write tests for an API endpoint (`ST-4`) before the endpoint itself is created (`ST-2`). Therefore, `ST-4` must have a dependency on `ST-2`.

#### **Step 5: Final Review and Formatting**
- Review your complete list of `Task` objects.
- Ensure that every functional and non-functional requirement from the original spec is covered by at least one task.
- Verify that your output is a single, valid JSON object containing a list of tasks, with no additional text or explanations.

---
### **REQUIRED OUTPUT: JSON Task List**

Your final output MUST be a single, valid JSON object. It must be an array of `Task` objects. Adhere strictly to the following schema for each task:

```json
[
  {
    "task_id": "TS-XX", // You will generate this, starting from the next available number.
    "title": "Clear, concise title for the task.",
    "priority": "critical | high | medium | low",
    "dependencies": ["TS-YY", "TS-ZZ"], // List of task_ids this task depends on.
    "context": "A 1-2 sentence explanation of how this task fits into the larger project, referencing the spec.",
    "implementation_details": "Specific, actionable instructions for the developer. Reference file paths, function names, or design patterns from the spec.",
    "dev_notes": "Optional notes, hints, or warnings for the developer.",
    "acceptance_criteria": [
      "A specific, measurable outcome.",
      "Another specific, measurable outcome."
    ],
    "ac_verification_steps": [
      "A concrete command or action to verify the AC, e.g., 'Run `pytest tests/test_new_feature.py` and confirm all tests pass.'",
      "Another concrete verification step."
    ]
  }
]
```

**CRITICAL:** Do not include any text, explanations, or markdown formatting before or after the final JSON array. Your entire response must be the JSON object itself.
``````
------ src/alfred/templates/prompts/create_tasks/drafting_tasks.md ------
``````
# Review Your Task Breakdown

You previously created a task breakdown from the technical specification. Please review it carefully.

## Task ID: ${task_id}

## Your Task List

${task_artifact_content}

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
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Break down an Engineering Specification into individual, actionable tasks that cover the entire implementation.

# BACKGROUND
You have an approved Engineering Specification that needs to be decomposed into manageable tasks. Each task should be:
- **Atomic**: A single, focused piece of work
- **Actionable**: Clear about what needs to be done
- **Measurable**: Has clear completion criteria
- **Ordered**: Consider dependencies between tasks

**Engineering Specification Available:**
${artifact_json}

# INSTRUCTIONS
1. Analyze the technical specification thoroughly
2. Identify all work that needs to be done across:
   - Data model/schema changes
   - API endpoints
   - Business logic
   - UI components
   - Testing
   - Documentation
   - DevOps/Infrastructure
3. Create tasks with appropriate granularity (1-3 days of work each)
4. Establish logical dependencies between tasks
5. Ensure complete coverage of the specification

Don't forget to include tasks for:
- Database migrations
- API documentation
- Unit and integration tests
- Error handling
- Logging and monitoring
- Security implementation
- Performance optimizations

# CONSTRAINTS
- Every aspect of the spec must be covered by at least one task
- Tasks should be independent when possible
- Dependencies should be clearly stated
- Estimates should be realistic

# OUTPUT
Create a TaskCreationArtifact containing an array of Task objects. Each task should have:
- `id`: Unique identifier (e.g., "TASK-001", "TASK-002")
- `title`: Clear, concise title
- `description`: Detailed description of work
- `acceptance_criteria`: List of completion criteria
- `dependencies`: List of task IDs this depends on
- `estimated_effort`: "Small", "Medium", or "Large"
- `technical_notes`: Any technical considerations

**Required Action:** Call `alfred.submit_work` with a `TaskCreationArtifact`

# EXAMPLES
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
``````
------ src/alfred/templates/prompts/errors/not_found.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
No prompt template was found for the current tool and state combination.

# BACKGROUND
This is a fallback prompt that indicates a missing template configuration. The system attempted to find a prompt for tool "${tool_name}" in state "${current_state}" but could not locate the appropriate template file.

# INSTRUCTIONS
1. This is likely a configuration error
2. Check that the prompt file exists at the expected location
3. Verify the tool and state names are correct
4. Contact the development team if this persists

# CONSTRAINTS
- This is not a normal operational state
- Do not attempt to proceed with the workflow

# OUTPUT
No action can be taken. Please resolve the missing template issue.
``````
------ src/alfred/templates/prompts/finalize_task/dispatching.md ------
``````
# TASK: ${task_id}
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

You are now finalizing task ${task_id}.

## Finalization Steps

Create a commit and pull request for the completed work.

## Required Information

Create a `FinalizeArtifact` with:
- **commit_message**: Clear, descriptive commit message
- **pr_title**: Pull request title
- **pr_description**: Detailed pull request description

Call `submit_work` with your finalization details.
``````
------ src/alfred/templates/prompts/implement_task/dispatching.md ------
``````
# TASK: ${task_id}
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
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Execute the implementation phase by completing all subtasks from the approved execution plan.

# BACKGROUND
You are now in the implementation phase. An execution plan with detailed subtasks has been created and approved. Your role is to:
- Work through each subtask systematically
- Track progress as you complete each one
- Ensure all acceptance criteria are met
- Create a comprehensive implementation manifest when done

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

**Execution Plan:**
${artifact_json}

# INSTRUCTIONS
1. Review the execution plan and subtasks
2. Implement each subtask in order, following the LOST specifications
3. After completing each subtask, call `alfred.mark_subtask_complete` with the task_id and subtask_id
4. Test your implementation as you go
5. Once all subtasks are complete, create an implementation manifest
6. Submit the final manifest for review

# CONSTRAINTS
- Follow the execution plan precisely
- Each subtask must be fully completed before moving to the next
- Maintain code quality and follow project conventions
- Ensure all tests pass before marking subtasks complete

# OUTPUT
When all subtasks are complete, create an ImplementationManifestArtifact with:
- `summary`: Brief summary of what was implemented
- `completed_subtasks`: List of completed subtask IDs
- `testing_notes`: Any notes about testing or validation

**Required Action:** Call `alfred.submit_work` with your `ImplementationManifestArtifact`
``````
------ src/alfred/templates/prompts/plan_task/contextualize.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Analyze the existing codebase and identify any ambiguities or questions that need clarification before planning can begin.

# BACKGROUND
You are beginning the planning process for a new task. Before creating a technical strategy, you must understand:
- The current codebase structure and relevant components
- Any existing patterns or conventions to follow
- Potential areas of ambiguity that need clarification

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Analyze the codebase starting from the project root
2. Identify all files and components relevant to this task
3. Note any existing patterns or conventions that should be followed
4. Create a list of specific questions about any ambiguities or unclear requirements
5. Prepare a comprehensive context analysis

# CONSTRAINTS
- Focus only on understanding, not designing solutions yet
- Questions should be specific and actionable
- Identify actual ambiguities, not hypothetical issues
- Consider both technical and business context

# OUTPUT
Create a ContextAnalysisArtifact with:
- `context_summary`: Your understanding of the existing code and how the new feature will integrate
- `affected_files`: List of files that will likely need modification
- `questions_for_developer`: Specific questions that need answers before proceeding

**Required Action:** Call `alfred.submit_work` with a `ContextAnalysisArtifact`

# EXAMPLES
Good question: "Should the new authentication system integrate with the existing UserService or create a separate AuthService?"
Bad question: "How should I implement this?" (too vague)
``````
------ src/alfred/templates/prompts/plan_task/design.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Translate the approved technical strategy into a detailed, file-level implementation design.

# BACKGROUND
The technical strategy has been approved and provides the high-level approach. You must now create a comprehensive design that:
- Breaks down the strategy into specific file changes
- Provides clear implementation guidance for each component
- Ensures all acceptance criteria can be met
- Maintains consistency with the existing codebase

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Review the approved strategy and task requirements
2. For each component in the strategy, determine the specific files that need to be created or modified
3. For each file, provide a clear summary of the required changes
4. Ensure the design covers all acceptance criteria
5. Consider the order of implementation and any dependencies between changes
6. Create a comprehensive design document

# CONSTRAINTS
- Be specific about file paths and change details
- Ensure consistency with existing code patterns
- Consider backward compatibility where applicable
- Design should be implementable without ambiguity

# OUTPUT
Create a DesignArtifact with:
- `design_summary`: Overview of the implementation approach
- `file_breakdown`: Array of file changes, each containing:
  - `file_path`: Full path to the file
  - `change_summary`: Description of changes needed
  - `operation`: Either "create" or "modify"

**Required Action:** Call `alfred.submit_work` with a `DesignArtifact`
``````
------ src/alfred/templates/prompts/plan_task/generate_subtasks.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Transform the approved design into precision-engineered subtasks that can be executed independently by different agents without ambiguity.

# BACKGROUND
You are creating an execution plan where each subtask must be so precise, complete, and independent that any developer or AI agent could execute it in complete isolation without questions or ambiguity.

**Critical Mindset - The Isolation Principle:**
Imagine each subtask will be executed by a different agent who:
- Has NEVER seen the other subtasks
- Has NO access to project context beyond what you provide
- Cannot ask questions or seek clarification
- Must produce code that integrates perfectly with others' work

## The Deep LOST Philosophy

LOST is a methodology for eliminating ambiguity through systematic precision:

### L - Location (The Context Anchor)
- **Activates Language Context**: `src/models/user.py` tells the agent "Python, likely SQLAlchemy/Django"
- **Implies Conventions**: `src/components/UserAvatar.tsx` signals "React, TypeScript, component patterns"
- **Defines Boundaries**: Precise paths prevent accidental modifications to wrong files
- **Creates Namespace**: Helps avoid naming conflicts between parallel implementations

### O - Operation (The Precision Verb)
**Foundation Operations** (Create structure):
- `CREATE` - Generate new file/class/module from scratch
- `DEFINE` - Establish interfaces, types, schemas
- `ESTABLISH` - Set up configuration, constants

**Implementation Operations** (Add logic):
- `IMPLEMENT` - Fill in method/function body
- `INTEGRATE` - Connect components
- `EXTEND` - Add capabilities to existing code

**Modification Operations** (Change existing):
- `MODIFY` - Alter existing code behavior
- `REFACTOR` - Restructure without changing behavior
- `ENHANCE` - Add features to existing functionality

### S - Specification (The Contract)
Must include:
1. **Exact Signatures**: "Define method authenticate(email: str, password: str) -> Union[User, None]"
2. **Precise Types**: "Accept config: Dict[str, Union[str, int, bool]] with keys: 'timeout' (int), 'retry' (bool)"
3. **Explicit Contracts**: "Returns User object with populated 'id', 'email', 'role' fields on success, None on failure"
4. **Clear Dependencies**: "Imports: from src.models.user import User; from src.utils.crypto import hash_password"
5. **Exact Integration Points**: "Registers route POST /api/auth/login with AuthRouter instance from src/routes/auth.py"

### T - Test (The Proof)
Must be executable commands or verifiable conditions:
1. **Concrete Execution**: "Run: python -m pytest tests/test_auth.py::test_authenticate_valid -xvs"
2. **Specific Validation**: "Verify: curl -X POST http://localhost:8000/api/auth/login -d '{"email":"test@example.com","password":"123"}' returns 401"
3. **Integration Verification**: "Confirm: from src.auth.handler import authenticate; result = authenticate('test@example.com', 'password'); assert result is None"

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Review the approved design and break it down into atomic units of work
2. Order subtasks by dependency (interfaces before implementations)
3. For each subtask, create a LOST-formatted specification with:
   - Precise location (exact file path)
   - Specific operation verb
   - Detailed specification with all imports, signatures, types
   - Executable test commands
4. Ensure each subtask ends with: "Call alfred.mark_subtask_complete with task_id='${task_id}' and subtask_id='ST-X'"
5. Use subtask IDs in format: ST-1, ST-2, etc.

# CONSTRAINTS
- Each subtask must be executable in complete isolation
- No assumptions about context beyond what's explicitly stated
- All types, imports, and dependencies must be specified
- Tests must be runnable commands, not descriptions
- Avoid circular dependencies between subtasks

# OUTPUT
Create an ExecutionPlan artifact with an array of subtasks, each containing:
- `subtask_id`: Format "ST-X" 
- `title`: Precise description of atomic work
- `summary`: Optional extended description
- `location`: Exact file path
- `operation`: Specific verb from LOST framework
- `specification`: Array of precise implementation steps
- `test`: Array of executable verification commands

**Required Action:** Call `alfred.submit_work` with an `ExecutionPlan` artifact

# EXAMPLES

## ✅ GOOD Example - Define Interface First:
```json
{
  "subtask_id": "ST-1",
  "title": "Define IAuthService interface with method signatures",
  "location": "src/interfaces/auth.interface.ts",
  "operation": "CREATE",
  "specification": [
    "Create new file src/interfaces/auth.interface.ts",
    "Define TypeScript interface IAuthService with methods:",
    "- authenticate(email: string, password: string): Promise<AuthResult>",
    "- validateToken(token: string): Promise<TokenValidation>",
    "Define type AuthResult = { success: boolean; user?: User; tokens?: AuthTokens; error?: string }",
    "Export all interfaces and types",
    "Call alfred.mark_subtask_complete with task_id='${task_id}' and subtask_id='ST-1'"
  ],
  "test": [
    "File src/interfaces/auth.interface.ts exists",
    "Run: npx tsc src/interfaces/auth.interface.ts --noEmit",
    "Verify interface has all methods with correct signatures"
  ]
}
```

## ❌ BAD Example - Vague and Interdependent:
```json
{
  "subtask_id": "subtask-1",
  "title": "Create user authentication",
  "location": "src/auth/",
  "operation": "CREATE",
  "specification": [
    "Create authentication system",
    "Add login and registration",
    "Handle tokens and sessions"
  ],
  "test": [
    "Test that users can log in"
  ]
}
```
Problems: Wrong ID format, vague location, multiple operations, no precise contracts
``````
------ src/alfred/templates/prompts/plan_task/review_context.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Manage a clarification dialogue with the human developer to get answers to all questions identified during context analysis.

# BACKGROUND
The initial context analysis has generated a list of questions that must be answered before planning can proceed. You need to:
- Present these questions clearly to the human developer
- Track which questions have been answered
- Continue prompting for missing information until all questions are resolved

**Questions to be answered:**
${artifact_summary}

# INSTRUCTIONS
1. Maintain a checklist of the questions in your context
2. Present the unanswered questions to the human developer in a clear, conversational manner
3. Receive their response (they may not answer all questions at once)
4. Check your list - if any questions remain unanswered, re-prompt the user for only the missing information
5. Repeat until all questions are answered
6. Once all questions are answered, compile a complete summary of questions and answers

# CONSTRAINTS
- Be patient and persistent in getting all questions answered
- Keep track of which questions have been answered
- Only ask for missing information, don't repeat answered questions
- Be clear and conversational in your communication

# OUTPUT
Once all questions have been answered, approve the context review with a complete summary.

**Required Action:** When all questions are answered, call `alfred.provide_review` with:
- `is_approved=true`
- `feedback_notes` containing a complete summary of all questions and their final, confirmed answers
``````
------ src/alfred/templates/prompts/plan_task/strategize.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create a high-level technical strategy that will guide the detailed design and implementation of the task.

# BACKGROUND
Context has been verified and any necessary clarifications have been provided. You must now develop a technical strategy that:
- Defines the overall approach to solving the problem
- Identifies key components that need to be created or modified
- Considers dependencies and potential risks
- Serves as the foundation for detailed design

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

# INSTRUCTIONS
1. Review the verified context and requirements
2. Define the overall technical approach (e.g., "Create a new microservice," "Refactor the existing UserService," "Add a new middleware layer")
3. List the major components, classes, or modules that will be created or modified
4. Identify any new third-party libraries or dependencies required
5. Analyze potential risks or important architectural trade-offs
6. Create a concise technical strategy document

# CONSTRAINTS
- Focus on high-level approach, not implementation details
- Ensure the strategy aligns with existing architecture patterns
- Consider scalability, maintainability, and performance
- Be realistic about risks and trade-offs

# OUTPUT
Create a StrategyArtifact with:
- `high_level_strategy`: Overall technical approach description
- `key_components`: List of major new or modified components
- `new_dependencies`: Optional list of new third-party libraries
- `risk_analysis`: Optional analysis of potential risks or trade-offs

**Required Action:** Call `alfred.submit_work` with a `StrategyArtifact`
``````
------ src/alfred/templates/prompts/review/ai_review.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
Perform a critical self-review of the submitted artifact to ensure it meets quality standards before human review.

# BACKGROUND
An artifact has been submitted for the current workflow step. As an AI reviewer, you must evaluate whether this artifact:
- Meets all requirements for the current step
- Contains complete and accurate information
- Follows established patterns and conventions
- Is ready for human review

# INSTRUCTIONS
1. Review the submitted artifact below
2. Check against the original requirements for this step
3. Evaluate completeness, clarity, and correctness
4. Determine if any critical issues need to be addressed
5. Provide your review decision

**Submitted Artifact:**
```json
${artifact_json}
```

# CONSTRAINTS
- Be objective and thorough in your review
- Focus on substantive issues, not minor formatting
- Consider whether a human reviewer would find this acceptable
- If rejecting, provide specific, actionable feedback

# OUTPUT
Make a review decision:
- If the artifact meets all quality standards, approve it
- If there are issues that must be fixed, request revision with specific feedback

**Required Action:** Call `alfred.provide_review` with your decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with detailed `feedback_notes`
``````
------ src/alfred/templates/prompts/review/human_review.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
Present the artifact to the human developer for final review and approval.

# BACKGROUND
The artifact has passed AI self-review and is now ready for human validation. The human will provide a simple approval decision or request specific changes.

**Artifact Summary:** ${artifact_summary}

# INSTRUCTIONS
1. Present the complete artifact below to the human developer
2. Wait for their review decision
3. If they approve, proceed with approval
4. If they request changes, capture their exact feedback
5. Submit the review decision

**Artifact for Review:**
```json
${artifact_json}
```

# CONSTRAINTS
- Present the artifact clearly and completely
- Capture human feedback verbatim if changes are requested
- Do not modify or interpret the human's feedback

# OUTPUT
Process the human's review decision:
- If approved, advance the workflow
- If changes requested, return to the previous step with feedback

**Required Action:** Call `alfred.provide_review` with the human's decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with their exact feedback in `feedback_notes`
``````
------ src/alfred/templates/prompts/review_task/dispatching.md ------
``````
# TASK: ${task_id}
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

You are now reviewing the implementation for task ${task_id}.

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
------ src/alfred/templates/prompts/start_task/awaiting_branch_creation.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create and switch to a new feature branch for the task implementation.

# BACKGROUND
The human operator has approved the branch creation. You must now:
- Create a new feature branch named `feature/${task_id}`
- Switch to this branch
- Verify the operation was successful

This ensures all work for this task is isolated in its own branch.

# INSTRUCTIONS
1. Execute the git command to create and switch to the new branch:
   ```bash
   git checkout -b feature/${task_id}
   ```
2. If the branch already exists, use:
   ```bash
   git checkout feature/${task_id}
   ```
3. Capture the command output
4. Verify you are now on the correct branch
5. Report the outcome in a structured artifact

# CONSTRAINTS
- Use the exact branch naming convention: `feature/${task_id}`
- Handle both cases: branch creation and switching to existing branch
- Accurately report success or failure

# OUTPUT
Create a BranchCreationArtifact with:
- `branch_name`: String - The name of the branch (should be `feature/${task_id}`)
- `success`: Boolean - True if the command executed without errors
- `details`: String - The output from the git command

**Required Action:** Call `alfred.submit_work` with a `BranchCreationArtifact`
``````
------ src/alfred/templates/prompts/start_task/awaiting_git_status.md ------
``````
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Assess the current git repository state to ensure a clean working environment before starting the task.

# BACKGROUND
Before beginning work on a new task, we must establish that:
- The working directory is clean (no uncommitted changes)
- We know the current branch
- Any existing changes are properly handled

This prevents accidental mixing of changes between different tasks.

# INSTRUCTIONS
1. Execute `git status` to check the repository state
2. Analyze the output to determine:
   - Whether the working directory is clean
   - The name of the current branch
   - List of any uncommitted files
3. Report the findings in a structured artifact
4. The workflow will determine next steps based on the repository state

# CONSTRAINTS
- Accurately report the git status
- Do not make any changes to the repository at this stage
- List all uncommitted files if any exist

# OUTPUT
Create a GitStatusArtifact with:
- `is_clean`: Boolean - True if working directory has no uncommitted changes
- `current_branch`: String - The name of the current git branch
- `uncommitted_changes`: List[String] - List of files with uncommitted changes, if any

**Required Action:** Call `alfred.submit_work` with a `GitStatusArtifact`
``````
------ src/alfred/templates/prompts/test_task/dispatching.md ------
``````
# TASK: ${task_id}
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

You are now in the testing phase for task ${task_id}.

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
------ src/alfred/tools/approve_review.py ------
``````
# src/alfred/tools/approve_review.py
from src.alfred.tools.provide_review_logic import provide_review_logic
from src.alfred.models.schemas import ToolResponse


async def approve_review_impl(task_id: str) -> ToolResponse:
    """Approves the work for the current review step."""
    return await provide_review_logic(task_id=task_id, is_approved=True)

``````
------ src/alfred/tools/base_tool_handler.py ------
``````
# src/alfred/tools/base_tool_handler.py
from abc import ABC, abstractmethod
from typing import Optional, Type, Any

from src.alfred.core.prompter import generate_prompt
from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.lib.logger import get_logger, setup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.tools.registry import tool_registry

logger = get_logger(__name__)


class BaseToolHandler(ABC):
    """Base handler for all tool implementations using the Template Method pattern."""

    def __init__(
        self,
        tool_name: str,
        tool_class: Optional[Type[BaseWorkflowTool]],
        required_status: Optional[TaskStatus] = None,
    ):
        self.tool_name = tool_name
        self.tool_class = tool_class
        self.required_status = required_status

    async def execute(self, task_id: str, **kwargs: Any) -> ToolResponse:
        """Template method defining the algorithm structure for all tools."""
        setup_task_logging(task_id)

        task = load_task(task_id)
        if not task:
            return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

        get_tool_result = self._get_or_create_tool(task_id, task)
        if isinstance(get_tool_result, ToolResponse):
            return get_tool_result
        tool_instance = get_tool_result

        # The setup_tool hook is now responsible for initial state dispatch if needed
        setup_response = await self._setup_tool(tool_instance, task, **kwargs)
        if setup_response and isinstance(setup_response, ToolResponse):
            return setup_response

        return self._generate_response(tool_instance, task)

    def _get_or_create_tool(self, task_id: str, task: Task) -> BaseWorkflowTool | ToolResponse:
        """Common tool recovery and creation logic."""
        if task_id in orchestrator.active_tools:
            logger.info(f"Found active tool '{self.tool_name}' for task {task_id}.")
            return orchestrator.active_tools[task_id]

        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool '{self.tool_name}' for task {task_id}.")
            return tool_instance

        if self.required_status and task.task_status != self.required_status:
            return ToolResponse(
                status="error",
                message=f"Task '{task_id}' has status '{task.task_status.value}'. Tool '{self.tool_name}' requires status to be '{self.required_status.value}'.",
            )

        # Use the factory method for instantiation
        new_tool = self._create_new_tool(task_id, task)
        orchestrator.active_tools[task_id] = new_tool

        # Get the tool config from the registry to determine status transition
        tool_config = tool_registry.get_tool_config(self.tool_name)
        if tool_config and task.task_status in tool_config.entry_status_map:
            new_status = tool_config.entry_status_map[task.task_status]
            state_manager.update_task_status(task_id, new_status)

        # Persist the initial state of the newly created tool
        state_manager.update_tool_state(task_id, new_tool)

        logger.info(f"Created new '{self.tool_name}' tool for task {task_id}.")
        return new_tool

    def _generate_response(self, tool_instance: BaseWorkflowTool, task: Task) -> ToolResponse:
        """Common logic for generating the final prompt and tool response."""
        try:
            prompt = generate_prompt(
                task_id=task.task_id,
                tool_name=tool_instance.tool_name,
                state=tool_instance.state,
                task=task,
                additional_context=tool_instance.context_store.copy(),
            )
            message = f"Initiated tool '{self.tool_name}' for task '{task.task_id}'. Current state: {tool_instance.state}."
            return ToolResponse(status="success", message=message, next_prompt=prompt)
        except (ValueError, RuntimeError, KeyError) as e:
            # Handle errors from the new prompter
            logger.error(f"Prompt generation failed: {e}", exc_info=True)
            return ToolResponse(status="error", message=f"A critical error occurred while preparing the next step: {e}")

    @abstractmethod
    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method for creating a new tool instance. Subclasses must implement."""
        pass

    @abstractmethod
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Hook for subclasses to perform tool-specific setup, including initial state dispatch."""
        pass

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
    from src.alfred.core.prompter import generate_prompt
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

    prompt = generate_prompt(
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
    from src.alfred.core.prompter import generate_prompt
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

    prompt = generate_prompt(
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
from typing import Optional, Any

from src.alfred.models.schemas import ToolResponse, TaskStatus, Task
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import BaseWorkflowTool, FinalizeTaskTool, FinalizeTaskState
from src.alfred.core.prompter import generate_prompt
from src.alfred.constants import ToolName
from src.alfred.tools.base_tool_handler import BaseToolHandler

logger = get_logger(__name__)


class FinalizeTaskHandler(BaseToolHandler):
    """Handler for the finalize_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.FINALIZE_TASK,
            tool_class=FinalizeTaskTool,
            required_status=TaskStatus.READY_FOR_FINALIZATION,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate FinalizeTaskTool."""
        return FinalizeTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Loads test results and dispatches the tool to the 'finalizing' state."""
        if tool_instance.state == FinalizeTaskState.DISPATCHING.value:
            task_state = state_manager.load_or_create(task.task_id)

            # Load test results if available
            test_results = task_state.completed_tool_outputs.get(ToolName.TEST_TASK)
            if test_results:
                tool_instance.context_store["test_results"] = test_results

            # Dispatch to finalizing state
            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


finalize_task_handler = FinalizeTaskHandler()


async def finalize_task_impl(task_id: str) -> ToolResponse:
    """Finalize task entry point - handles the completion phase"""
    return await finalize_task_handler.execute(task_id)

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
# src/alfred/tools/implement_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, ImplementTaskTool, ImplementTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ImplementTaskHandler(BaseToolHandler):
    """Handler for the implement_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.IMPLEMENT_TASK,
            tool_class=ImplementTaskTool,
            required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate ImplementTaskTool."""
        return ImplementTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Loads the execution plan and dispatches the tool to the 'implementing' state."""
        # Use the Enum for comparison
        if tool_instance.state == ImplementTaskState.DISPATCHING.value:
            task_state = state_manager.load_or_create(task.task_id)
            execution_plan = task_state.completed_tool_outputs.get(ToolName.PLAN_TASK)

            if not execution_plan:
                return ToolResponse(
                    status="error", message=f"CRITICAL: Cannot start implementation. Execution plan from 'plan_task' not found for task '{task.task_id}'. Please run 'plan_task' first."
                )

            tool_instance.context_store["execution_plan"] = execution_plan

            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


implement_task_handler = ImplementTaskHandler()


# Keep the old implementation function for backward compatibility
async def implement_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the implement_task tool."""
    return await implement_task_handler.execute(task_id)

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
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, PlanTaskTool, PlanTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager


class PlanTaskHandler(BaseToolHandler):
    """Handler for the plan_task tool."""

    def __init__(self):
        # THIS IS THE FIX for Blocker #1
        super().__init__(
            tool_name=ToolName.PLAN_TASK,
            tool_class=PlanTaskTool,
            required_status=None,  # Validation is handled in _setup_tool
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate PlanTaskTool."""
        # PlanTaskTool does not require special args for its __init__
        return PlanTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Validate status and handle initial dispatch."""
        if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
            return ToolResponse(
                status="error",
                message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task.",
            )

        # Status update is now handled by BaseToolHandler via ToolRegistry

        # This is the crucial fix for Blocker #1.
        # If the tool is in its initial state, we perform no action,
        # as the initial prompt is already correct. The user will call
        # `submit_work` to advance it.
        if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value:
            # No dispatch needed, we are already in the correct starting state.
            pass

        return None


plan_task_handler = PlanTaskHandler()


# Keep the old implementation function for backward compatibility
async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool with unified state."""
    return await plan_task_handler.execute(task_id)

``````
------ src/alfred/tools/progress.py ------
``````
# src/alfred/tools/progress.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, ImplementTaskTool
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.lib.logger import get_logger
from src.alfred.orchestration.orchestrator import orchestrator

logger = get_logger(__name__)


class MarkSubtaskCompleteHandler(BaseToolHandler):
    """Handler for the mark_subtask_complete tool."""

    def __init__(self):
        # This tool doesn't create a new workflow, it interacts with an existing one.
        # So, it doesn't need a tool_class or status maps.
        super().__init__(
            tool_name=ToolName.MARK_SUBTASK_COMPLETE,
            tool_class=None,  # Not a workflow-initiating tool
            required_status=None,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        # This should never be called for this type of tool.
        raise NotImplementedError("mark_subtask_complete does not create a new workflow tool.")

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """This is the core logic for the tool."""
        subtask_id = kwargs.get("subtask_id")
        if not subtask_id:
            return ToolResponse(status="error", message="`subtask_id` is a required argument.")

        # Ensure we are operating on an active ImplementTaskTool
        if not isinstance(tool_instance, ImplementTaskTool):
            return ToolResponse(status="error", message=f"Progress can only be marked during the '{ToolName.IMPLEMENT_TASK}' workflow.")

        # Optional: Enforce task status validation
        if task.task_status != TaskStatus.IN_DEVELOPMENT:
            return ToolResponse(status="error", message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Progress can only be marked for tasks in 'in_development' status.")

        # Validate subtask_id against the plan
        execution_plan = tool_instance.context_store.get("execution_plan_artifact", {}).get("subtasks", [])
        valid_subtask_ids = {st["subtask_id"] for st in execution_plan}
        if subtask_id not in valid_subtask_ids:
            return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'. It does not exist in the execution plan.")

        # Update the list of completed subtasks
        completed_subtasks = set(tool_instance.context_store.get("completed_subtasks", []))
        if subtask_id in completed_subtasks:
            return ToolResponse(status="success", message=f"Subtask '{subtask_id}' was already marked as complete.")

        completed_subtasks.add(subtask_id)
        tool_instance.context_store["completed_subtasks"] = sorted(list(completed_subtasks))  # Store sorted for consistency

        # Persist the updated tool state
        with state_manager.transaction() as uow:
            uow.update_tool_state(task.task_id, tool_instance)

        # Generate a progress report message
        completed_count = len(completed_subtasks)
        total_count = len(valid_subtask_ids)
        progress = (completed_count / total_count) * 100 if total_count > 0 else 0

        message = f"Acknowledged: Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%)."
        logger.info(message)

        # This tool does not return a next_prompt, as the AI should continue its work.
        return ToolResponse(status="success", message=message, data={"completed_count": completed_count, "total_count": total_count})

    def _get_or_create_tool(self, task_id: str, task: Task) -> BaseWorkflowTool | ToolResponse:
        """For this handler, we ONLY get an existing tool. We never create one."""
        if task_id in orchestrator.active_tools:
            return orchestrator.active_tools[task_id]

        # This tool requires an active workflow, so recovery is essential
        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            return recovered_tool

        return ToolResponse(status="error", message=f"No active workflow found for task '{task_id}'. Cannot mark progress.")


mark_subtask_complete_handler = MarkSubtaskCompleteHandler()


# Keep the implementation function for decorator use
def mark_subtask_complete_impl(task_id: str, subtask_id: str) -> ToolResponse:
    """Marks a specific subtask as complete during the implementation phase."""
    # Note: This synchronous wrapper calls the async handler
    import asyncio

    return asyncio.run(mark_subtask_complete_handler.execute(task_id, subtask_id=subtask_id))

``````
------ src/alfred/tools/provide_review_logic.py ------
``````
# src/alfred/tools/provide_review_logic.py
from src.alfred.core.prompter import generate_prompt
from src.alfred.lib.logger import get_logger, cleanup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import ToolResponse
from src.alfred.constants import Triggers
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.constants import ArtifactKeys
from src.alfred.config.manager import ConfigManager
from src.alfred.config.settings import settings

logger = get_logger(__name__)


async def provide_review_logic(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    if task_id not in orchestrator.active_tools:
        from src.alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if not recovered_tool:
            return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")
        orchestrator.active_tools[task_id] = recovered_tool

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    current_state = active_tool.state
    logger.info(f"Processing review for task {task_id} in state '{current_state}', approved={is_approved}")

    if not is_approved:
        active_tool.trigger(Triggers.REQUEST_REVISION)
        message = "Revision requested. Returning to previous step."
    else:
        if current_state.endswith("_awaiting_ai_review"):
            active_tool.trigger(Triggers.AI_APPROVE)
            message = "AI review approved. Awaiting human review."
            try:
                if ConfigManager(settings.alfred_dir).load().features.autonomous_mode:
                    logger.info(f"Autonomous mode enabled. Bypassing human review for task {task_id}.")
                    active_tool.trigger(Triggers.HUMAN_APPROVE)
                    message = "AI review approved. Autonomous mode bypassed human review."
            except FileNotFoundError:
                logger.warning("Config file not found; autonomous mode unchecked.")
        elif current_state.endswith("_awaiting_human_review"):
            active_tool.trigger(Triggers.HUMAN_APPROVE)
            message = "Human review approved. Proceeding to next step."
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{current_state}'.")

    with state_manager.transaction() as uow:
        uow.update_tool_state(task_id, active_tool)

    if active_tool.is_terminal:
        tool_name = active_tool.tool_name
        final_state = active_tool.get_final_work_state()
        key = ArtifactKeys.get_artifact_key(final_state)
        artifact = active_tool.context_store.get(key)

        with state_manager.transaction() as uow:
            if artifact:
                uow.add_completed_output(task_id, tool_name, artifact)
            uow.clear_tool_state(task_id)

        orchestrator.active_tools.pop(task_id, None)
        cleanup_task_logging(task_id)

        handoff = f"The '{tool_name}' workflow has completed successfully. To formally approve this phase, call `alfred.approve_and_advance(task_id='{task_id}')`."
        return ToolResponse(status="success", message=f"'{tool_name}' completed. Awaiting final approval.", next_prompt=handoff)

    if not is_approved and feedback_notes:
        # Build feedback context
        ctx = active_tool.context_store.copy()
        ctx["feedback_notes"] = feedback_notes
    else:
        # Use standard context from tool
        ctx = active_tool.context_store.copy()

    prompt = generate_prompt(
        task_id=task.task_id,
        tool_name=active_tool.tool_name,
        state=active_tool.state,
        task=task,
        additional_context=ctx,
    )
    return ToolResponse(status="success", message=message, next_prompt=prompt)

``````
------ src/alfred/tools/registry.py ------
``````
# src/alfred/tools/registry.py
from typing import Dict, Optional, Type, Callable, Coroutine, Any, List, TYPE_CHECKING
from dataclasses import dataclass
import inspect

from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.lib.logger import get_logger

# THIS IS THE FIX for Blocker #3
if TYPE_CHECKING:
    from src.alfred.tools.base_tool_handler import BaseToolHandler

logger = get_logger(__name__)


class DuplicateToolError(Exception):
    """Raised when a tool name is registered more than once."""

    pass


@dataclass(frozen=True)
class ToolConfig:
    """Immutable configuration for a registered tool."""

    name: str
    handler_class: Type["BaseToolHandler"]  # Use forward reference
    tool_class: Type[BaseWorkflowTool]
    entry_status_map: Dict[TaskStatus, TaskStatus]
    implementation: Callable[..., Coroutine[Any, Any, ToolResponse]]


class ToolRegistry:
    """Self-registering tool system using decorators."""

    def __init__(self):
        self._tools: Dict[str, ToolConfig] = {}

    def register(
        self,
        name: str,
        handler_class: Type["BaseToolHandler"],  # Use forward reference
        tool_class: Type[BaseWorkflowTool],
        entry_status_map: Dict[TaskStatus, TaskStatus],
    ):
        """Decorator to register a tool with its full configuration."""
        if name in self._tools:
            raise DuplicateToolError(f"Tool '{name}' is already registered.")

        def decorator(func: Callable[..., Coroutine[Any, Any, ToolResponse]]):
            config = ToolConfig(name=name, handler_class=handler_class, tool_class=tool_class, entry_status_map=entry_status_map, implementation=func)
            self._tools[name] = config
            logger.info(f"Registered tool: '{name}'")
            return func

        return decorator

    def get_tool_config(self, name: str) -> Optional[ToolConfig]:
        return self._tools.get(name)

    def get_all_tools(self) -> List[ToolConfig]:
        """Returns all registered tools, sorted alphabetically by name."""
        return sorted(self._tools.values(), key=lambda tc: tc.name)


# Global singleton instance
tool_registry = ToolRegistry()

``````
------ src/alfred/tools/request_revision.py ------
``````
# src/alfred/tools/request_revision.py
from src.alfred.tools.provide_review_logic import provide_review_logic
from src.alfred.models.schemas import ToolResponse


async def request_revision_impl(task_id: str, feedback_notes: str) -> ToolResponse:
    """Requests revisions for the work in the current review step."""
    return await provide_review_logic(task_id=task_id, is_approved=False, feedback_notes=feedback_notes)

``````
------ src/alfred/tools/review_task.py ------
``````
# src/alfred/tools/review_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, ReviewTaskTool, ReviewTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class ReviewTaskHandler(BaseToolHandler):
    """Handler for the review_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.REVIEW_TASK,
            tool_class=ReviewTaskTool,
            required_status=TaskStatus.READY_FOR_REVIEW,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate ReviewTaskTool."""
        return ReviewTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Dispatches the tool to the 'reviewing' state."""
        # Guard against incorrect status
        if task.task_status != TaskStatus.READY_FOR_REVIEW and tool_instance.state == ReviewTaskState.DISPATCHING.value:
            logger.warning(f"Task {task.task_id} is not in READY_FOR_REVIEW status. Current status: {task.task_status}")
            return ToolResponse(status="error", message=f"Task '{task.task_id}' must be in READY_FOR_REVIEW status to start review.")

        if tool_instance.state == ReviewTaskState.DISPATCHING.value:
            # Load context from the previous (implementation) phase
            task_state = state_manager.load_or_create(task.task_id)
            implementation_manifest = task_state.completed_tool_outputs.get(ToolName.IMPLEMENT_TASK)

            if not implementation_manifest:
                logger.warning(f"Implementation manifest not found for task '{task.task_id}'. Review may lack context.")

            tool_instance.context_store["implementation_manifest"] = implementation_manifest

            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


review_task_handler = ReviewTaskHandler()

``````
------ src/alfred/tools/start_task.py ------
``````
# src/alfred/tools/start_task.py
"""
The start_task tool, re-architected as a stateful workflow tool.
"""

from src.alfred.core.prompter import generate_prompt
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

    prompt = generate_prompt(
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
from typing import Optional, Any
from pydantic import ValidationError

from src.alfred.core.prompter import generate_prompt
from src.alfred.core.workflow import BaseWorkflowTool
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import Task, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


class SubmitWorkHandler(BaseToolHandler):
    """Handler for the generic submit_work tool."""

    def __init__(self):
        super().__init__(
            tool_name="submit_work",  # Not from constants, as it's a generic name
            tool_class=None,
            required_status=None,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        raise NotImplementedError("submit_work does not create new workflow tools.")

    def _get_or_create_tool(self, task_id: str, task: Task) -> BaseWorkflowTool | ToolResponse:
        """For submit_work, we only get an existing tool."""
        if task_id in orchestrator.active_tools:
            return orchestrator.active_tools[task_id]
        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            return recovered_tool
        return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """The core logic for submitting an artifact and transitioning state."""
        artifact = kwargs.get("artifact")
        if artifact is None:
            return ToolResponse(status=ResponseStatus.ERROR, message="`artifact` is a required argument for submit_work.")

        current_state_enum = tool_instance.state
        current_state_val = tool_instance.state.value if hasattr(tool_instance.state, "value") else tool_instance.state

        # 1. Validate the artifact against the model for the current state
        artifact_model = tool_instance.artifact_map.get(current_state_enum)
        if artifact_model:
            try:
                validated_artifact = artifact_model.model_validate(artifact)
                logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state_val, model=artifact_model.__name__))
            except ValidationError as e:
                error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state_val)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
                return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
        else:
            validated_artifact = artifact  # No model to validate against

        # 2. Store artifact and update scratchpad
        artifact_key = ArtifactKeys.get_artifact_key(current_state_val)
        tool_instance.context_store[artifact_key] = validated_artifact
        # For review states, we need the artifact as an object, not a string
        tool_instance.context_store[ArtifactKeys.ARTIFACT_CONTENT_KEY] = validated_artifact
        # Store the last state for generic templates
        tool_instance.context_store["last_state"] = current_state_val
        artifact_manager.append_to_scratchpad(task.task_id, current_state_val, validated_artifact)

        # 3. Determine the correct trigger and fire it
        trigger_name = Triggers.submit_trigger(current_state_val)
        if not hasattr(tool_instance, trigger_name):
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger_name}' exists.")

        # Check if transition is valid
        next_transitions = tool_instance.machine.get_transitions(source=tool_instance.state, trigger=trigger_name)
        if not next_transitions:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger_name}' from state '{tool_instance.state}'.")

        getattr(tool_instance, trigger_name)()
        logger.info(LogMessages.STATE_TRANSITION.format(task_id=task.task_id, trigger=trigger_name, state=tool_instance.state))

        # 4. Persist the new state
        with state_manager.transaction() as uow:
            uow.update_tool_state(task.task_id, tool_instance)

        # This handler's job is done; we return None to let the main execute method generate the response
        return None


submit_work_handler = SubmitWorkHandler()


# Keep the legacy function for backwards compatibility if needed
def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """Legacy implementation - redirects to the handler."""
    import asyncio

    return asyncio.run(submit_work_handler.execute(task_id, artifact=artifact))

``````
------ src/alfred/tools/test_task.py ------
``````
# src/alfred/tools/test_task.py
from typing import Optional, Any

from src.alfred.core.workflow import BaseWorkflowTool, TestTaskTool, TestTaskState
from src.alfred.models.schemas import Task, TaskStatus, ToolResponse
from src.alfred.tools.base_tool_handler import BaseToolHandler
from src.alfred.constants import ToolName
from src.alfred.state.manager import state_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class TestTaskHandler(BaseToolHandler):
    """Handler for the test_task tool."""

    def __init__(self):
        super().__init__(
            tool_name=ToolName.TEST_TASK,
            tool_class=TestTaskTool,
            required_status=TaskStatus.READY_FOR_TESTING,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Factory method to correctly instantiate TestTaskTool."""
        return TestTaskTool(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Dispatches the tool to the 'testing' state."""
        if tool_instance.state == TestTaskState.DISPATCHING.value:
            # Load context from the original task definition for verification steps
            tool_instance.context_store["ac_verification_steps"] = getattr(task, "ac_verification_steps", [])

            tool_instance.dispatch()

            with state_manager.transaction() as uow:
                uow.update_tool_state(task.task_id, tool_instance)

            logger.info(f"Dispatched '{self.tool_name}' for task {task.task_id} to state '{tool_instance.state}'.")

        return None


test_task_handler = TestTaskHandler()

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
                    f"5. Run 'alfred.get_next_task()' to see available tasks",
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
