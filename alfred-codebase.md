------ src/alfred/__init__.py ------
``````

``````
------ src/alfred/config/__init__.py ------
``````
"""Alfred configuration module."""

from alfred.models.alfred_config import AlfredConfig, FeaturesConfig

from .manager import ConfigManager

__all__ = ["ConfigManager", "AlfredConfig", "FeaturesConfig"]

``````
------ src/alfred/config/manager.py ------
``````
"""Configuration manager for Alfred."""

import yaml
from pathlib import Path

from alfred.models.alfred_config import AlfredConfig
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages Alfred configuration."""

    CONFIG_FILENAME = "config.yml"

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
                data = yaml.safe_load(f)

            self._config = AlfredConfig(**data)
            logger.info("Configuration loaded successfully", extra={"config_path": str(self.config_path), "component": "config_manager"})
            return self._config
        except Exception as e:
            logger.error("Failed to load configuration", extra={"config_path": str(self.config_path), "error": str(e), "component": "config_manager"}, exc_info=True)
            raise

    def save(self, config: AlfredConfig) -> None:
        """Save configuration to disk.

        Args:
            config: Configuration to save
        """
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, "w") as f:
                yaml.dump(config.model_dump(mode="json"), f, default_flow_style=False, sort_keys=False)

            self._config = config
            logger.info("Configuration saved successfully", extra={"config_path": str(self.config_path), "component": "config_manager"})
        except Exception as e:
            logger.error("Failed to save configuration", extra={"config_path": str(self.config_path), "error": str(e), "component": "config_manager"}, exc_info=True)
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
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from alfred.constants import Paths


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_prefix="ALFRED_", case_sensitive=False, env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Debugging flag
    debugging_mode: bool = True

    # Server configuration
    server_name: str = "alfred"
    version: str = "2.0.0"

    # Directory configuration
    alfred_dir_name: str = Paths.ALFRED_DIR
    config_filename: str = Paths.CONFIG_FILE

    # Base paths
    project_root: Path = Path.cwd()

    # AI Provider API Keys (using standard env var names)
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

    @property
    def alfred_dir(self) -> Path:
        """Get the .alfred directory path in the user's project."""
        return self.project_root / self.alfred_dir_name

    @property
    def config_file(self) -> Path:
        """Get the project's config.yml file path."""
        return self.alfred_dir / self.config_filename

    @property
    def packaged_config_file(self) -> Path:
        """Get the path to the default config file inside the package."""
        return Path(__file__).parent.parent / Paths.CONFIG_FILE

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
------ src/alfred/config.yml ------
``````
version: "2.0.0"

provider:
  type: "local"

ai:
  providers:
    - name: "openai"
      enabled: true
    - name: "google"
      enabled: true
    - name: "anthropic"
      enabled: false
  default_provider: "openai"
  enable_token_tracking: true
  max_tokens_per_request: 8000
  default_temperature: 0.5
  default_model: "gpt-4"

features:
  scaffolding_mode: false
  autonomous_mode: false

tools:
  create_spec:
    enabled: true
    description: "Create technical specification from PRD"
  
  create_tasks_from_spec:
    enabled: true
    description: "Break down engineering spec into actionable tasks"
  
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

workflow:
  require_human_approval: true
  enable_ai_review: true
  max_thinking_time: 300
  auto_create_branches: true

providers:
  jira:
    transition_on_start: true
    transition_on_complete: true
    
  linear:
    update_status: true
    
  local:
    task_file_pattern: "*.md"

debug:
  save_debug_logs: true
  save_state_snapshots: true
  log_level: INFO
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
    CREATE_TASKS_FROM_SPEC: Final[str] = "create_tasks_from_spec"
    CREATE_TASKS: Final[str] = "create_tasks_from_spec"  # Alias for backward compatibility
    START_TASK: Final[str] = "start_task"
    PLAN_TASK: Final[str] = "plan_task"
    IMPLEMENT_TASK: Final[str] = "implement_task"
    REVIEW_TASK: Final[str] = "review_task"
    TEST_TASK: Final[str] = "test_task"
    FINALIZE_TASK: Final[str] = "finalize_task"
    WORK_ON: Final[str] = "work_on"
    WORK_ON_TASK: Final[str] = "work_on_task"
    APPROVE_AND_ADVANCE: Final[str] = "approve_and_advance"
    MARK_SUBTASK_COMPLETE: Final[str] = "mark_subtask_complete"
    CREATE_TASK: Final[str] = "create_task"
    GET_NEXT_TASK: Final[str] = "get_next_task"
    APPROVE_REVIEW: Final[str] = "approve_review"
    REQUEST_REVISION: Final[str] = "request_revision"
    INITIALIZE_PROJECT: Final[str] = "initialize_project"


# Directory and File Names
class Paths:
    """File system path constants."""

    # Directories
    ALFRED_DIR: Final[str] = ".alfred"
    WORKSPACE_DIR: Final[str] = "workspace"
    TEMPLATES_DIR: Final[str] = "templates"
    DEBUG_DIR: Final[str] = "debug"
    TASKS_DIR: Final[str] = "tasks"

    # Files
    SCRATCHPAD_FILE: Final[str] = "scratchpad.md"
    EXECUTION_PLAN_FILE: Final[str] = "execution_plan.json"
    TOOL_STATE_FILE: Final[str] = "tool_state.json"
    CONFIG_FILE: Final[str] = "config.yml"
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


# Plan Task State Names (as strings for transitions) - Discovery Planning
class PlanTaskStates:
    """Discovery planning state string constants."""

    DISCOVERY: Final[str] = "discovery"
    CLARIFICATION: Final[str] = "clarification"
    CONTRACTS: Final[str] = "contracts"
    IMPLEMENTATION_PLAN: Final[str] = "implementation_plan"
    VALIDATION: Final[str] = "validation"
    VERIFIED: Final[str] = "verified"


# Artifact Keys and Mappings
class ArtifactKeys:
    """Artifact storage key constants."""

    # State to artifact name mapping
    STATE_TO_ARTIFACT_MAP: Final[dict] = {
        # Discovery Planning states
        PlanTaskStates.DISCOVERY: "context_discovery",
        PlanTaskStates.CLARIFICATION: "clarification",
        PlanTaskStates.CONTRACTS: "contract_design",
        PlanTaskStates.IMPLEMENTATION_PLAN: "implementation_plan",
        PlanTaskStates.VALIDATION: "validation",
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
        PlanTaskStates.DISCOVERY: "Deep Context Discovery and Codebase Exploration",
        PlanTaskStates.CLARIFICATION: "Conversational Human-AI Clarification",
        PlanTaskStates.CONTRACTS: "Interface-First Design and Contracts",
        PlanTaskStates.IMPLEMENTATION_PLAN: "Self-Contained Subtask Creation",
        PlanTaskStates.VALIDATION: "Final Plan Validation and Coherence Check",
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
from .workflow import BaseWorkflowTool
from .discovery_workflow import PlanTaskTool, PlanTaskState
from .prompter import prompt_library, generate_prompt

__all__ = ["BaseWorkflowTool", "PlanTaskTool", "PlanTaskState", "prompt_library", "generate_prompt"]

``````
------ src/alfred/core/discovery_context.py ------
``````
"""Pure function context loaders for discovery planning."""

from typing import Any, Dict
from alfred.models.schemas import Task
from alfred.models.state import TaskState


def load_plan_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Pure function context loader for plan_task tool.

    Args:
        task: The task being planned
        task_state: Current task state with artifacts and context

    Returns:
        Context dictionary for prompt template rendering

    Raises:
        ValueError: If required dependencies are missing
    """
    # Check for re-planning context from active tool state
    restart_context = None
    context_store = {}
    if task_state.active_tool_state:
        restart_context = task_state.active_tool_state.context_store.get("restart_context")
        context_store = task_state.active_tool_state.context_store

    # Base context for all planning states
    context = {
        "task_title": task.title or "Untitled Task",
        "task_context": task.context or "",
        "implementation_details": task.implementation_details or "",
        "acceptance_criteria": task.acceptance_criteria or [],
        "restart_context": restart_context,
        "preserved_artifacts": context_store.get("preserved_artifacts", []),
        # Autonomous mode configuration
        "autonomous_mode": context_store.get("autonomous_mode", False),
        "autonomous_note": context_store.get("autonomous_note", "Running in interactive mode - human reviews are enabled for each phase"),
        "skip_contracts": context_store.get("skip_contracts", False),
        "complexity_note": context_store.get("complexity_note", ""),
    }

    # Add state-specific context
    current_state = None
    if task_state.active_tool_state:
        current_state = task_state.active_tool_state.current_state
        context["current_state"] = current_state

        # Add artifacts from previous states using context_store from active tool
        # Map the stored artifact keys to template variable names
        if current_state != "discovery":
            discovery_artifact = task_state.active_tool_state.context_store.get("context_discovery_artifact")
            if discovery_artifact:
                context["discovery_artifact"] = discovery_artifact
                # Flatten for template access
                if hasattr(discovery_artifact, "findings"):
                    context["discovery_findings"] = discovery_artifact.findings
                elif isinstance(discovery_artifact, dict) and "findings" in discovery_artifact:
                    context["discovery_findings"] = discovery_artifact["findings"]

                if hasattr(discovery_artifact, "questions"):
                    context["discovery_questions"] = "\n".join(f"- {q}" for q in discovery_artifact.questions)
                elif isinstance(discovery_artifact, dict) and "questions" in discovery_artifact:
                    questions = discovery_artifact.get("questions", [])
                    context["discovery_questions"] = "\n".join(f"- {q}" for q in questions)

        if current_state in ["contracts", "implementation_plan", "validation"]:
            clarification_artifact = task_state.active_tool_state.context_store.get("clarification_artifact")
            if clarification_artifact:
                context["clarification_artifact"] = clarification_artifact

        if current_state in ["implementation_plan", "validation"]:
            contracts_artifact = task_state.active_tool_state.context_store.get("contract_design_artifact")
            if contracts_artifact:
                context["contracts_artifact"] = contracts_artifact

        if current_state == "validation":
            implementation_artifact = task_state.active_tool_state.context_store.get("implementation_plan_artifact")
            if implementation_artifact:
                context["implementation_artifact"] = implementation_artifact

    return context


def load_simple_task_context(task: Task, task_state: TaskState) -> Dict[str, Any]:
    """Context loader for simple tasks that skip CONTRACTS state."""
    context = load_plan_task_context(task, task_state)
    context["skip_contracts"] = True
    return context

``````
------ src/alfred/core/discovery_workflow.py ------
``````
"""Discovery planning workflow state machine implementation."""

from enum import Enum
from typing import Any, Dict, List, Optional
from transitions.core import Machine

from alfred.constants import ToolName
from alfred.core.state_machine_builder import workflow_builder
from alfred.core.workflow import BaseWorkflowTool
from alfred.models.planning_artifacts import (
    ContextDiscoveryArtifact,
    ClarificationArtifact,
    ContractDesignArtifact,
    ImplementationPlanArtifact,
    ValidationArtifact,
)


class PlanTaskState(str, Enum):
    """State enumeration for the discovery planning workflow."""

    DISCOVERY = "discovery"
    CLARIFICATION = "clarification"
    CONTRACTS = "contracts"
    IMPLEMENTATION_PLAN = "implementation_plan"
    VALIDATION = "validation"
    VERIFIED = "verified"


class PlanTaskTool(BaseWorkflowTool):
    """Discovery planning tool with conversational, context-rich workflow."""

    def __init__(self, task_id: str, restart_context: Optional[Dict] = None, autonomous_mode: bool = False):
        super().__init__(task_id, tool_name=ToolName.PLAN_TASK)

        # Define artifact mapping
        self.artifact_map = {
            PlanTaskState.DISCOVERY: ContextDiscoveryArtifact,
            PlanTaskState.CLARIFICATION: ClarificationArtifact,
            PlanTaskState.CONTRACTS: ContractDesignArtifact,
            PlanTaskState.IMPLEMENTATION_PLAN: ImplementationPlanArtifact,
            PlanTaskState.VALIDATION: ValidationArtifact,
        }

        # Handle re-planning context
        if restart_context:
            initial_state = self._determine_restart_state(restart_context)
            self._load_preserved_artifacts(restart_context)
        else:
            initial_state = PlanTaskState.DISCOVERY

        # Initially include all states - we'll skip dynamically during transitions
        workflow_states = [PlanTaskState.DISCOVERY, PlanTaskState.CLARIFICATION, PlanTaskState.CONTRACTS, PlanTaskState.IMPLEMENTATION_PLAN, PlanTaskState.VALIDATION]

        # Use the builder to create state machine configuration
        machine_config = workflow_builder.build_workflow_with_reviews(
            work_states=workflow_states,
            terminal_state=PlanTaskState.VERIFIED,
            initial_state=initial_state,
        )

        # Create the state machine
        self.machine = Machine(model=self, states=machine_config["states"], transitions=machine_config["transitions"], initial=machine_config["initial"], auto_transitions=False)

        # Configuration flags
        self._skip_contracts = False
        self.autonomous_mode = autonomous_mode

        # Store autonomous mode in context for templates
        self.context_store["autonomous_mode"] = autonomous_mode
        if autonomous_mode:
            self.context_store["autonomous_note"] = "Running in autonomous mode - human reviews will be skipped"
        else:
            self.context_store["autonomous_note"] = "Running in interactive mode - human reviews are enabled for each phase"

    def get_final_work_state(self) -> str:
        """Return the final work state that produces the main artifact."""
        return PlanTaskState.VALIDATION.value

    def _determine_restart_state(self, restart_context: Dict) -> PlanTaskState:
        """Determine initial state for re-planning."""
        restart_from = restart_context.get("restart_from", "DISCOVERY")
        return PlanTaskState(restart_from.lower())

    def _load_preserved_artifacts(self, restart_context: Dict) -> None:
        """Load preserved artifacts from previous planning attempt."""
        preserved = restart_context.get("preserve_artifacts", [])
        for artifact_name in preserved:
            # Load preserved artifact into context_store
            self.context_store[f"preserved_{artifact_name}"] = restart_context.get(artifact_name)

    def _determine_workflow_states(self, discovery_artifact: Optional[ContextDiscoveryArtifact] = None) -> list:
        """Determine which states to include based on complexity."""
        base_states = [PlanTaskState.DISCOVERY, PlanTaskState.CLARIFICATION]

        # Only add CONTRACTS state for complex tasks
        if discovery_artifact and not self.should_skip_contracts(discovery_artifact):
            base_states.append(PlanTaskState.CONTRACTS)
        elif discovery_artifact is None:
            # If no discovery artifact yet (initial setup), include contracts
            # Will be validated later in the workflow
            base_states.append(PlanTaskState.CONTRACTS)

        base_states.extend([PlanTaskState.IMPLEMENTATION_PLAN, PlanTaskState.VALIDATION])

        return base_states

    def should_skip_contracts(self, discovery_artifact: ContextDiscoveryArtifact) -> bool:
        """Determine if CONTRACTS state should be skipped for simple tasks."""
        if not discovery_artifact:
            return False

        # Simple task criteria based on multiple factors
        complexity = getattr(discovery_artifact, "complexity_assessment", "MEDIUM")
        relevant_files = getattr(discovery_artifact, "relevant_files", [])
        integration_points = getattr(discovery_artifact, "integration_points", [])
        code_patterns = getattr(discovery_artifact, "code_patterns", [])

        # Skip contracts for simple tasks if:
        # 1. Complexity is explicitly LOW
        # 2. Few files affected (≤ 3)
        # 3. No new integration points
        # 4. Follows existing patterns (no new architecture)

        is_low_complexity = complexity == "LOW"
        few_files = len(relevant_files) <= 3
        no_new_integrations = len(integration_points) == 0
        follows_patterns = len(code_patterns) > 0  # Uses existing patterns

        # Skip if it's clearly a simple task
        should_skip = is_low_complexity and few_files and no_new_integrations

        return should_skip

    def check_complexity_after_clarification(self) -> None:
        """Check if we should skip contracts after clarification phase."""
        # Get discovery artifact from context store
        discovery_artifact = self.context_store.get("context_discovery_artifact")
        if discovery_artifact and self.should_skip_contracts(discovery_artifact):
            self._skip_contracts = True
            # Add note to context for templates
            self.context_store["skip_contracts"] = True
            self.context_store["complexity_note"] = "Skipping CONTRACTS phase due to LOW complexity assessment"

    def get_next_state_after_clarification(self) -> str:
        """Determine next state after clarification based on complexity."""
        if self._skip_contracts:
            return PlanTaskState.IMPLEMENTATION_PLAN.value
        return PlanTaskState.CONTRACTS.value

    def should_auto_approve(self) -> bool:
        """Check if we should automatically approve after AI review."""
        return self.autonomous_mode

    def get_autonomous_config(self) -> Dict[str, Any]:
        """Get configuration for autonomous mode."""
        return {"skip_human_reviews": self.autonomous_mode, "auto_approve_after_ai": self.autonomous_mode, "question_handling": "best_guess" if self.autonomous_mode else "interactive"}

    def initiate_replanning(self, trigger: str, restart_from: str, changes: str, preserve_artifacts: Optional[List[str]] = None) -> Dict[str, Any]:
        """Initiate re-planning with preserved context."""
        restart_context = {
            "trigger": trigger,  # "requirements_changed", "implementation_failed", "review_failed"
            "restart_from": restart_from,  # State to restart from
            "changes": changes,  # What changed
            "preserve_artifacts": preserve_artifacts or [],
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "previous_state": self.state,
        }

        # Store restart context for next planning session
        self.context_store["restart_context"] = restart_context

        return restart_context

    def can_restart_from_state(self, state: str) -> bool:
        """Check if we can restart planning from a given state."""
        valid_restart_states = [
            PlanTaskState.DISCOVERY.value,
            PlanTaskState.CLARIFICATION.value,
            PlanTaskState.CONTRACTS.value,
            PlanTaskState.IMPLEMENTATION_PLAN.value,
            PlanTaskState.VALIDATION.value,
        ]
        return state in valid_restart_states

``````
------ src/alfred/core/prompter.py ------
``````
# src/alfred/core/prompter_new.py
import json
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum

from alfred.config.settings import settings
from alfred.lib.structured_logger import get_logger
from alfred.lib.turn_manager import turn_manager

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
            prompts_dir: Directory containing prompts. Defaults to packaged prompts.
        """
        if prompts_dir is None:
            # Always use packaged prompts
            prompts_dir = Path(__file__).parent.parent / "templates" / "prompts"
            logger.info(f"Using packaged prompt templates from {prompts_dir}")

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

    def get(self, prompt_key: str, context: Dict[str, Any] = None) -> PromptTemplate:
        """
        Get a prompt template by key from .md files only.
        """
        # Check file-based cache
        if prompt_key in self._cache:
            return self._cache[prompt_key]

        # Explicit failure - no fallback
        available = ", ".join(sorted(self._cache.keys()))
        raise KeyError(f"Prompt '{prompt_key}' not found.\nAvailable file prompts: {available}")

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
        """Render a prompt with context - file-based only."""
        template = self.get(prompt_key, context)

        # File-based PromptTemplate only
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

    # Load turn-based context
    try:
        # Get latest artifacts from turn history
        latest_artifacts = turn_manager.get_latest_artifacts_by_state(task_id)

        # Add each state's artifact to context with flattened keys
        for state_name, artifact_data in latest_artifacts.items():
            # Add the entire artifact data under the state name
            builder.with_custom(**{state_name: artifact_data})

            # Also flatten specific fields for backward compatibility
            if isinstance(artifact_data, dict):
                for key, value in artifact_data.items():
                    # Create flattened keys like "discovery_findings", "clarification_decisions"
                    flattened_key = f"{state_name}_{key}"
                    builder.with_custom(**{flattened_key: value})
    except Exception as e:
        logger.warning(f"Could not load turn-based context for {task_id}: {e}")
        # Continue with traditional context loading

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
        context = builder.build()

        # Special handling for plan_task discovery template
        if prompt_key == "plan_task.discovery" and "autonomous_note" not in context:
            context["autonomous_note"] = "Running in interactive mode - human reviews are enabled for each phase"

        return prompt_library.render(prompt_key, context)
    except KeyError:
        # Fallback for missing prompts
        logger.warning(f"Prompt not found for {prompt_key}, using fallback")
        return f"# {tool_name} - {state_value}\n\nNo prompt configured for this state.\nTask: {task_id}"

``````
------ src/alfred/core/state_machine_builder.py ------
``````
"""
Centralized state machine builder for workflow tools.
Eliminates duplication of state machine creation logic.
"""

from enum import Enum
from typing import List, Dict, Any, Type, Optional, Union
from transitions import Machine

from alfred.constants import Triggers
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class WorkflowStateMachineBuilder:
    """
    Builder for creating workflow state machines with standardized review cycles.

    This builder encapsulates the common pattern used across all workflow tools:
    1. Work states that require review
    2. AI review state
    3. Human review state
    4. Transitions between states
    """

    def __init__(self):
        self.states: List[str] = []
        self.transitions: List[Dict[str, Any]] = []

    def create_review_transitions(self, source_state: str, success_destination_state: str, revision_destination_state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Creates a standard review cycle for a work state.

        This generates:
        1. work_state -> work_state_awaiting_ai_review (via submit trigger)
        2. ai_review -> human_review (via ai_approve trigger)
        3. ai_review -> work_state (via request_revision trigger)
        4. human_review -> next_state (via human_approve trigger)
        5. human_review -> work_state (via request_revision trigger)
        6. work_state -> work_state (via request_revision trigger)
        """
        if revision_destination_state is None:
            revision_destination_state = source_state

        # Generate state names
        ai_review_state = f"{source_state}_awaiting_ai_review"
        human_review_state = f"{source_state}_awaiting_human_review"

        return [
            # Submit work to enter review cycle
            {
                "trigger": Triggers.submit_trigger(source_state),
                "source": source_state,
                "dest": ai_review_state,
            },
            # AI approves
            {
                "trigger": Triggers.AI_APPROVE,
                "source": ai_review_state,
                "dest": human_review_state,
            },
            # AI requests revision
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": ai_review_state,
                "dest": revision_destination_state,
            },
            # Human approves
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
            # Working state requests revision (iterative refinement)
            {
                "trigger": Triggers.REQUEST_REVISION,
                "source": source_state,
                "dest": revision_destination_state,
            },
        ]

    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        return [f"{state}_awaiting_ai_review", f"{state}_awaiting_human_review"]

    def build_workflow_with_reviews(self, work_states: List[Union[str, Enum]], terminal_state: Union[str, Enum], initial_state: Union[str, Enum]) -> Dict[str, Any]:
        """
        Build a complete workflow with review cycles for each work state.

        Args:
            work_states: List of states that require review cycles
            terminal_state: Final state of the workflow
            initial_state: Starting state of the workflow

        Returns:
            Dictionary with 'states' and 'transitions' for Machine initialization
        """
        all_states = []
        all_transitions = []

        # Convert enums to strings if needed
        work_state_values = [s.value if hasattr(s, "value") else s for s in work_states]
        terminal_value = terminal_state.value if hasattr(terminal_state, "value") else terminal_state
        initial_value = initial_state.value if hasattr(initial_state, "value") else initial_state

        # Add all work states and their review states
        for i, state in enumerate(work_state_values):
            # Add the work state
            all_states.append(state)

            # Add review states
            review_states = self.get_review_states_for_state(state)
            all_states.extend(review_states)

            # Determine next state
            if i + 1 < len(work_state_values):
                next_state = work_state_values[i + 1]
            else:
                next_state = terminal_value

            # Create transitions for this state
            transitions = self.create_review_transitions(source_state=state, success_destination_state=next_state)
            all_transitions.extend(transitions)

        # Add terminal state
        all_states.append(terminal_value)

        return {"states": all_states, "transitions": all_transitions, "initial": initial_value}

    def build_simple_workflow(self, dispatch_state: Union[str, Enum], work_state: Union[str, Enum], terminal_state: Union[str, Enum], dispatch_trigger: str = "dispatch") -> Dict[str, Any]:
        """
        Build a simple workflow: dispatch -> work (with review) -> terminal.

        This is the pattern used by implement, review, test, and finalize tools.
        """
        dispatch_value = dispatch_state.value if hasattr(dispatch_state, "value") else dispatch_state
        work_value = work_state.value if hasattr(work_state, "value") else work_state
        terminal_value = terminal_state.value if hasattr(terminal_state, "value") else terminal_state

        states = [dispatch_value, work_value, f"{work_value}_awaiting_ai_review", f"{work_value}_awaiting_human_review", terminal_value]

        transitions = [{"trigger": dispatch_trigger, "source": dispatch_value, "dest": work_value}]

        # Add review transitions
        transitions.extend(self.create_review_transitions(source_state=work_value, success_destination_state=terminal_value))

        return {"states": states, "transitions": transitions, "initial": dispatch_value}


# Singleton instance for convenience
workflow_builder = WorkflowStateMachineBuilder()

``````
------ src/alfred/core/workflow.py ------
``````
# src/alfred/core/workflow.py
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from alfred.constants import ToolName, Triggers
from alfred.core.state_machine_builder import workflow_builder
from alfred.models.planning_artifacts import (
    BranchCreationArtifact,
    FinalizeArtifact,
    GitStatusArtifact,
    ImplementationManifestArtifact,
    PRDInputArtifact,
    ReviewArtifact,
    TaskCreationArtifact,
    TestResultArtifact,
)
from alfred.models.engineering_spec import EngineeringSpec


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
    """
    Stateless base class for workflow tools.
    
    No longer holds machine instance or state. Contains only static configuration
    and utility methods for workflow management.
    """
    def __init__(self, task_id: str, tool_name: str):
        self.task_id = task_id
        self.tool_name = tool_name
        self.artifact_map: Dict[Enum, Type[BaseModel]] = {}

    def get_review_states_for_state(self, state: str) -> List[str]:
        """Get the review states for a given work state."""
        # Delegate to builder
        return workflow_builder.get_review_states_for_state(state)

    def get_final_work_state(self) -> str:
        """Get the final work state that produces the main artifact.

        This method should be overridden by subclasses to return the state
        that produces the primary artifact for the tool.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement get_final_work_state()")


class StartTaskTool(BaseWorkflowTool):
    """Re-architected StartTaskTool with a streamlined state machine."""

    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.START_TASK)
        self.artifact_map = {
            StartTaskState.AWAITING_GIT_STATUS: GitStatusArtifact,
            StartTaskState.AWAITING_BRANCH_CREATION: BranchCreationArtifact,
        }

    def get_final_work_state(self) -> str:
        return StartTaskState.AWAITING_BRANCH_CREATION.value


class ImplementTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.IMPLEMENT_TASK)
        self.artifact_map = {
            ImplementTaskState.IMPLEMENTING: ImplementationManifestArtifact,
        }

    def get_final_work_state(self) -> str:
        return ImplementTaskState.IMPLEMENTING.value


class ReviewTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.REVIEW_TASK)
        self.artifact_map = {
            ReviewTaskState.REVIEWING: ReviewArtifact,
        }

    def get_final_work_state(self) -> str:
        return ReviewTaskState.REVIEWING.value


class TestTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.TEST_TASK)
        self.artifact_map = {
            TestTaskState.TESTING: TestResultArtifact,
        }

    def get_final_work_state(self) -> str:
        return TestTaskState.TESTING.value


class FinalizeTaskTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.FINALIZE_TASK)
        self.artifact_map = {
            FinalizeTaskState.FINALIZING: FinalizeArtifact,
        }

    def get_final_work_state(self) -> str:
        return FinalizeTaskState.FINALIZING.value


class CreateSpecTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_SPEC)
        self.artifact_map = {
            CreateSpecState.DRAFTING_SPEC: EngineeringSpec,
        }

    def get_final_work_state(self) -> str:
        return CreateSpecState.DRAFTING_SPEC.value


class CreateTasksTool(BaseWorkflowTool):
    def __init__(self, task_id: str):
        super().__init__(task_id, tool_name=ToolName.CREATE_TASKS_FROM_SPEC)
        self.artifact_map = {
            CreateTasksState.DRAFTING_TASKS: TaskCreationArtifact,
        }

    def get_final_work_state(self) -> str:
        return CreateTasksState.DRAFTING_TASKS.value

``````
------ src/alfred/core/workflow_engine.py ------
``````
"""
WorkflowEngine: Lightweight state machine manager for stateless workflow tools.

This engine operates on pure state dictionaries and provides state transition
functionality without maintaining any state itself.
"""

from typing import List, Dict, Any, TYPE_CHECKING
from transitions import Machine

from alfred.core.state_machine_builder import workflow_builder
from alfred.lib.structured_logger import get_logger

if TYPE_CHECKING:
    from alfred.tools.tool_definitions import ToolDefinition

logger = get_logger(__name__)


class WorkflowEngine:
    """
    Lightweight state machine engine operating on pure state dictionaries.
    
    This class is responsible for managing state machine transitions without
    holding any state itself. It operates on simple state strings and uses
    the existing ToolDefinition infrastructure.
    """
    
    def __init__(self, tool_definition: "ToolDefinition"):
        """
        Initialize with tool definition for state machine configuration.
        
        Args:
            tool_definition: The tool definition containing state machine config
        """
        self.tool_definition = tool_definition
        self._machine_config = self._build_machine_config()
        
    def _build_machine_config(self) -> Dict[str, Any]:
        """Build machine configuration from tool definition."""
        if len(self.tool_definition.work_states) > 1:
            # Multi-step workflow with reviews
            return workflow_builder.build_workflow_with_reviews(
                work_states=self.tool_definition.work_states,
                terminal_state=self.tool_definition.terminal_state,
                initial_state=self.tool_definition.initial_state
            )
        elif self.tool_definition.dispatch_state:
            # Simple workflow with dispatch
            return workflow_builder.build_simple_workflow(
                dispatch_state=self.tool_definition.dispatch_state,
                work_state=self.tool_definition.work_states[0] if self.tool_definition.work_states else None,
                terminal_state=self.tool_definition.terminal_state
            )
        else:
            # Minimal configuration
            states = [state.value if hasattr(state, 'value') else str(state) 
                     for state in self.tool_definition.work_states]
            if self.tool_definition.terminal_state:
                terminal = (self.tool_definition.terminal_state.value 
                           if hasattr(self.tool_definition.terminal_state, 'value') 
                           else str(self.tool_definition.terminal_state))
                states.append(terminal)
            
            return {
                "states": states,
                "transitions": [],
                "initial": states[0] if states else None
            }
    
    def execute_trigger(self, current_state: str, trigger: str) -> str:
        """
        Execute a state transition and return new state string.
        
        Args:
            current_state: Current state string
            trigger: Trigger name to execute
            
        Returns:
            New state string after transition
            
        Raises:
            ValueError: If transition is invalid
        """
        # Create a temporary state object for the machine
        state_obj = type('StateObj', (), {'state': current_state})()
        
        # Create machine with temporary object
        machine = Machine(
            model=state_obj,
            states=self._machine_config["states"],
            transitions=self._machine_config["transitions"],
            initial=current_state,
            auto_transitions=False
        )
        
        # Validate transition exists
        valid_transitions = machine.get_transitions(trigger=trigger, source=current_state)
        if not valid_transitions:
            raise ValueError(f"No valid transition for trigger '{trigger}' from state '{current_state}'")
        
        # Execute transition
        trigger_method = getattr(state_obj, trigger, None)
        if not trigger_method:
            raise ValueError(f"Trigger method '{trigger}' not found")
            
        trigger_method()
        
        return state_obj.state
    
    def get_valid_triggers(self, from_state: str) -> List[str]:
        """
        Get list of valid triggers from a given state.
        
        Args:
            from_state: State to get triggers for
            
        Returns:
            List of valid trigger names
        """
        # Create temporary machine to get transitions
        state_obj = type('StateObj', (), {'state': from_state})()
        machine = Machine(
            model=state_obj,
            states=self._machine_config["states"],
            transitions=self._machine_config["transitions"],
            initial=from_state,
            auto_transitions=False
        )
        
        # Get all transitions from this state
        triggers = set()
        for transition in self._machine_config["transitions"]:
            if transition.get("source") == from_state:
                triggers.add(transition.get("trigger"))
        
        return sorted(list(triggers))
    
    def is_terminal_state(self, state: str) -> bool:
        """
        Check if a state is terminal (workflow complete).
        
        Args:
            state: State string to check
            
        Returns:
            True if state is terminal, False otherwise
        """
        if self.tool_definition.terminal_state:
            terminal_value = (self.tool_definition.terminal_state.value
                            if hasattr(self.tool_definition.terminal_state, 'value')
                            else str(self.tool_definition.terminal_state))
            return state == terminal_value
        
        return False 
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

from alfred.config.settings import settings


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
    
    # Console handler - use stderr for MCP server compatibility
    console_handler = logging.StreamHandler(sys.stderr)
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

from alfred.models.schemas import Task
from alfred.lib.structured_logger import get_logger
from alfred.config.settings import settings

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
        from alfred.task_providers.factory import get_provider
        
        provider = get_provider()
        
        # Note: The root_dir parameter is preserved for backward compatibility
        # but is only relevant for local providers. Other providers (Jira, Linear)
        # will ignore this parameter.
        if root_dir:
            logger.warning("root_dir parameter provided but may be ignored by non-local providers", task_id=task_id, root_dir=str(root_dir))
        
        return provider.get_task(task_id)
        
    except Exception as e:
        logger.error("Failed to load task", task_id=task_id, error=str(e))
        return None


def load_task_with_error_details(task_id: str, root_dir: Optional[Path] = None) -> tuple[Task | None, str | None]:
    """
    Loads a Task using the configured task provider with detailed error information.

    Args:
        task_id: The ID of the task to load
        root_dir: Optional root directory (preserved for backward compatibility)
                 
    Returns:
        Tuple of (Task object if found or None, error message if failed or None)
    """
    try:
        # Use the task provider factory to get the configured provider
        from alfred.task_providers.factory import get_provider
        
        provider = get_provider()
        
        # Check if provider supports detailed error reporting
        if hasattr(provider, 'get_task_with_error_details'):
            return provider.get_task_with_error_details(task_id)
        
        # Fallback to standard method
        task = provider.get_task(task_id)
        if task is None:
            return None, f"Task '{task_id}' not found."
        return task, None
        
    except Exception as e:
        error_msg = f"Failed to load task {task_id}: {e}"
        logger.error("Failed to load task with error details", task_id=task_id, error=str(e))
        return None, error_msg


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
    
    logger.info("Wrote task to file", task_id=task.task_id, file_path=str(task_file))


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
------ src/alfred/lib/turn_manager.py ------
``````
# src/alfred/lib/turn_manager.py
"""Generic turn-based storage system for Alfred.

This module implements an event-sourced, append-only storage pattern
where each state transition is saved as an immutable turn file.
No JSON-to-Markdown conversions, just pure data storage.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

from alfred.lib.structured_logger import get_logger
from alfred.models.schemas import TaskStatus
from alfred.lib.task_utils import load_task
from alfred.constants import Paths

logger = get_logger(__name__)


class Turn(BaseModel):
    """Represents a single turn in the task history.
    
    Generic and state-agnostic - works for any workflow phase.
    """
    turn_number: int = Field(..., ge=1, description="Sequential turn number")
    state_name: str = Field(..., description="State/phase name when turn was created")
    tool_name: str = Field(..., description="Tool that created this turn")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When turn was created")
    artifact_data: Dict[str, Any] = Field(..., description="The actual artifact/data for this turn")
    
    # Optional metadata
    revision_of: Optional[int] = Field(None, description="If this revises a previous turn")
    revision_feedback: Optional[str] = Field(None, description="Feedback that prompted revision")


class TaskManifest(BaseModel):
    """Lightweight metadata for quick task access without loading all turns."""
    task_id: str
    created_at: datetime
    last_updated: datetime
    current_state: str
    total_turns: int
    latest_turns_by_state: Dict[str, int] = Field(
        default_factory=dict,
        description="Maps state names to their latest turn numbers"
    )


class TurnManager:
    """Manages turn-based storage for all Alfred workflows.
    
    Features:
    - Append-only turn storage (no modifications)
    - Atomic writes with tempfile + rename
    - Generic - works with any state/tool/artifact
    - No JSON-to-Markdown conversion
    - Efficient manifest for quick lookups
    """
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
    
    def _get_turns_dir(self, task_id: str) -> Path:
        """Get the turns directory for a task."""
        return self.workspace_root / task_id / "turns"
    
    def _get_manifest_path(self, task_id: str) -> Path:
        """Get the manifest file path for a task."""
        return self.workspace_root / task_id / "manifest.json"
    
    def _ensure_task_dir(self, task_id: str) -> None:
        """Ensure task directory structure exists."""
        turns_dir = self._get_turns_dir(task_id)
        turns_dir.mkdir(parents=True, exist_ok=True)
    
    def append_turn(
        self,
        task_id: str,
        state_name: str,
        tool_name: str,
        artifact_data: Dict[str, Any],
        revision_of: Optional[int] = None,
        revision_feedback: Optional[str] = None
    ) -> Turn:
        """Append a new turn to the task history.
        
        This is the ONLY way to add data to the system.
        Completely generic - works with any artifact structure.
        
        Args:
            task_id: Task identifier
            state_name: Current state/phase name
            tool_name: Tool creating this turn
            artifact_data: The actual data (any JSON-serializable dict)
            revision_of: If revising a previous turn, its number
            revision_feedback: Feedback that prompted the revision
            
        Returns:
            The created Turn object
        """
        self._ensure_task_dir(task_id)
        turns_dir = self._get_turns_dir(task_id)
        
        # Get next turn number
        existing_turns = sorted(turns_dir.glob("*.json"))
        turn_number = len(existing_turns) + 1
        
        # Create turn object
        turn = Turn(
            turn_number=turn_number,
            state_name=state_name,
            tool_name=tool_name,
            timestamp=datetime.now(timezone.utc),
            artifact_data=artifact_data,
            revision_of=revision_of,
            revision_feedback=revision_feedback
        )
        
        # Save with atomic write
        filename = f"{turn_number:03d}-{state_name}-{turn.timestamp.isoformat()}Z.json"
        filepath = turns_dir / filename
        
        # Atomic write using tempfile + rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=turns_dir,
            prefix=".tmp_turn_",
            suffix=".json"
        )
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                # Use model_dump with mode='json' to handle datetime serialization
                json.dump(turn.model_dump(mode='json'), f, indent=2)
            
            # Atomic rename
            os.replace(temp_path, filepath)
            logger.info("Appended turn", task_id=task_id, turn_number=turn_number, state_name=state_name, tool_name=tool_name)
        except Exception as e:
            logger.error("Failed to append turn", task_id=task_id, state_name=state_name, error=str(e))
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        
        # Update manifest
        self._update_manifest(task_id, state_name, turn_number)
        
        return turn
    
    def _update_manifest(self, task_id: str, state_name: str, turn_number: int) -> None:
        """Update the task manifest with latest turn info."""
        manifest_path = self._get_manifest_path(task_id)
        
        # Load or create manifest
        if manifest_path.exists():
            manifest_data = json.loads(manifest_path.read_text())
            manifest = TaskManifest.model_validate(manifest_data)
        else:
            manifest = TaskManifest(
                task_id=task_id,
                created_at=datetime.now(timezone.utc),
                last_updated=datetime.now(timezone.utc),
                current_state=state_name,
                total_turns=0
            )
        
        # Update manifest
        manifest.last_updated = datetime.now(timezone.utc)
        manifest.current_state = state_name
        manifest.total_turns = turn_number
        manifest.latest_turns_by_state[state_name] = turn_number
        
        # Atomic write
        temp_fd, temp_path = tempfile.mkstemp(
            dir=manifest_path.parent,
            prefix=".tmp_manifest_",
            suffix=".json"
        )
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(manifest.model_dump(mode='json'), f, indent=2)
            os.replace(temp_path, manifest_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
    
    def load_all_turns(self, task_id: str) -> List[Turn]:
        """Load all turns for a task in chronological order."""
        turns_dir = self._get_turns_dir(task_id)
        if not turns_dir.exists():
            return []
        
        turns = []
        for turn_file in sorted(turns_dir.glob("*.json")):
            try:
                data = json.loads(turn_file.read_text())
                turn = Turn.model_validate(data)
                turns.append(turn)
            except Exception as e:
                logger.warning("Skipping invalid turn file", task_id=task_id, turn_file=str(turn_file), error=str(e))
                continue
        
        return turns
    
    def get_latest_artifacts_by_state(self, task_id: str) -> Dict[str, Dict[str, Any]]:
        """Get the most recent artifact for each state.
        
        This handles revisions by taking the latest turn for each state.
        Skips revision_request turns as they're not actual work artifacts.
        
        Returns:
            Dict mapping state names to their latest artifact data
        """
        turns = self.load_all_turns(task_id)
        latest_by_state = {}
        
        for turn in turns:
            # Skip meta-turns like revision requests
            if turn.state_name == "revision_request":
                continue
            
            # Latest turn for each state wins
            latest_by_state[turn.state_name] = turn.artifact_data
        
        return latest_by_state
    
    def get_manifest(self, task_id: str) -> Optional[TaskManifest]:
        """Get the task manifest for quick metadata access."""
        manifest_path = self._get_manifest_path(task_id)
        if not manifest_path.exists():
            return None
        
        try:
            data = json.loads(manifest_path.read_text())
            return TaskManifest.model_validate(data)
        except Exception as e:
            logger.error("Failed to load manifest", task_id=task_id, error=str(e))
            return None
    
    def request_revision(
        self,
        task_id: str,
        state_to_revise: str,
        feedback: str,
        requested_by: str = "human"
    ) -> Turn:
        """Record a revision request as a special turn.
        
        This creates a revision_request turn that documents why
        a revision was needed, without modifying the original turn.
        
        Args:
            task_id: Task identifier
            state_to_revise: Which state needs revision
            feedback: Detailed feedback about what needs changing
            requested_by: Who requested the revision (human/ai)
            
        Returns:
            The revision request Turn
        """
        revision_artifact = {
            "state_to_revise": state_to_revise,
            "feedback": feedback,
            "requested_by": requested_by,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return self.append_turn(
            task_id=task_id,
            state_name="revision_request",
            tool_name="revision_system",
            artifact_data=revision_artifact
        )
    
    def generate_scratchpad(self, task_id: str) -> None:
        """Generate a human-readable scratchpad from turns.
        
        This creates a markdown view of the current task state based on
        the turn history. It shows only the latest state, not a full history.
        """
        scratchpad_path = self.workspace_root / task_id / Paths.SCRATCHPAD_FILE
        
        # Get all turns and latest artifacts
        all_turns = self.load_all_turns(task_id)
        if not all_turns:
            scratchpad_path.write_text(f"# Task {task_id}\n\nNo work completed yet.\n")
            return
        
        # Get latest artifacts by state
        latest_artifacts = self.get_latest_artifacts_by_state(task_id)
        
        # Load task for context
        task = load_task(task_id)
        
        # Get current state from manifest
        manifest = self.get_manifest(task_id)
        
        # Fix: Use task status for completed tasks, workflow state for active tasks
        if task and task.task_status.value == "done":
            current_state = "done"
        else:
            current_state = manifest.current_state if manifest else "unknown"
        
        # Build markdown content
        content_parts = [
            f"# {task_id}",
            "",
            f"## {task.title if task else 'Task Details'}",
            ""
        ]
        
        # Add status info as a simple table  
        formatted_status = self._format_status_display(task.task_status.value) if task else 'Unknown'
        formatted_state = self._format_state_display(current_state)
        
        content_parts.extend([
            f"| Status | {formatted_status} |",
            f"|:-------|:-------|",
            f"| Current State | {formatted_state} |",
            f"| Total Turns | {len(all_turns)} |",
            ""
        ])
        
        # Add task context
        if task:
            if task.context:
                content_parts.extend([
                    "### Context",
                    "",
                    task.context,
                    ""
                ])
            
            if task.implementation_details:
                content_parts.extend([
                    "### Implementation Details", 
                    "",
                    task.implementation_details,
                    ""
                ])
            
            # Handle acceptance criteria as a list
            if task.acceptance_criteria:
                content_parts.append("### Acceptance Criteria")
                content_parts.append("")
                if isinstance(task.acceptance_criteria, list):
                    for criterion in task.acceptance_criteria:
                        content_parts.append(f"- {criterion}")
                else:
                    content_parts.append(str(task.acceptance_criteria))
                content_parts.append("")
        
        # Add current work organized by phase
        if latest_artifacts:
            
            # Define phase groupings and their display names
            phase_groups = {
                "Planning": ["discovery", "clarification", "contracts", "implementation_plan", "validation"],
                "Implementation": ["implementing"],
                "Review": ["reviewing"],
                "Testing": ["testing"],
                "Finalization": ["finalizing"]
            }
            
            # Process each phase
            for phase_name, phase_states in phase_groups.items():
                phase_artifacts = {state: latest_artifacts[state] 
                                 for state in phase_states 
                                 if state in latest_artifacts}
                
                if not phase_artifacts:
                    continue
                    
                # Add phase header
                content_parts.extend([
                    "",
                    f"## {phase_name} Phase",
                    ""
                ])
                
                # Process each state in this phase
                for state, artifact in phase_artifacts.items():
                    self._add_state_section_improved(content_parts, state, artifact, phase_name)
        
        # Show recent revision requests if any
        revision_turns = [t for t in all_turns if t.state_name == "revision_request"]
        if revision_turns:
            content_parts.extend([
                "",
                "---",
                "",
                "## Revision History",
                ""
            ])
            for turn in revision_turns[-3:]:  # Show last 3 revisions
                rev_data = turn.artifact_data
                content_parts.extend([
                    f"### Revision at Turn {turn.turn_number}",
                    f"- **State to Revise:** `{rev_data.get('state_to_revise', 'Unknown')}`",
                    f"- **Requested by:** {rev_data.get('requested_by', 'Unknown')}",
                    f"- **Feedback:** {rev_data.get('feedback', 'No feedback')}",
                    ""
                ])
        
        # Write atomically
        temp_fd, temp_path = tempfile.mkstemp(
            dir=scratchpad_path.parent,
            prefix=".tmp_scratch_",
            suffix=".md"
        )
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content_parts))
            os.replace(temp_path, scratchpad_path)
            logger.info("Generated scratchpad", task_id=task_id)
        except Exception as e:
            logger.error("Failed to generate scratchpad", task_id=task_id, error=str(e))
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
    
    def _format_status_display(self, status: str) -> str:
        """Format status values for human-readable display."""
        status_map = {
            "new": "New",
            "planning": "Planning",
            "ready_for_development": "Ready for Development",
            "in_development": "In Development",
            "ready_for_review": "Ready for Review",
            "in_review": "In Review",
            "ready_for_testing": "Ready for Testing",
            "in_testing": "In Testing",
            "ready_for_finalization": "Ready for Finalization",
            "in_finalization": "In Finalization",
            "done": "Completed"
        }
        return status_map.get(status, status.replace('_', ' ').title())
    
    def _format_state_display(self, state: str) -> str:
        """Format state names for human-readable display."""
        # Handle special cases for task statuses vs workflow states
        if state == "done":
            return "Completed"
        # Simply capitalize first letter of each word for workflow states
        return state.replace('_', ' ').title()
    
    def _strip_markdown_headers(self, content: str) -> str:
        """Remove markdown headers from content to avoid duplication."""
        lines = content.split('\n')
        cleaned_lines = []
        skip_next_blank = False
        
        for line in lines:
            # Skip lines that are markdown headers
            if line.strip().startswith('#'):
                skip_next_blank = True
                continue
            # Skip blank line after a header
            if skip_next_blank and line.strip() == '':
                skip_next_blank = False
                continue
            skip_next_blank = False
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _add_state_section_improved(self, content_parts: List[str], state: str, artifact: Dict[str, Any], phase_name: str) -> None:
        """Add a section for a specific state to the scratchpad with improved formatting."""
        # Format state name
        state_title = state.replace('_', ' ').title()
        
        # Add state header
        content_parts.append(f"### {state_title}")
        content_parts.append("")
        
        # Handle different artifact structures based on state
        if isinstance(artifact, dict):
            # Discovery state
            if state == "discovery" and "findings" in artifact:
                cleaned_findings = self._strip_markdown_headers(artifact["findings"])
                if cleaned_findings:
                    content_parts.append(cleaned_findings)
                    content_parts.append("")
                
                if "questions" in artifact:
                    content_parts.append("**Questions to Consider:**")
                    for q in artifact["questions"]:
                        content_parts.append(f"- {q}")
                    content_parts.append("")
            
            # Clarification state
            elif state == "clarification" and "decisions" in artifact:
                content_parts.append("**Decisions Made:**")
                for d in artifact["decisions"]:
                    content_parts.append(f"- {d}")
                content_parts.append("")
            
            # Contracts state
            elif state == "contracts" and "interface_design" in artifact:
                # Add the content without headers
                cleaned_design = self._strip_markdown_headers(artifact["interface_design"])
                if cleaned_design:
                    content_parts.append(cleaned_design)
                    content_parts.append("")
            
            # Implementation Plan state
            elif state == "implementation_plan":
                if "implementation_plan" in artifact:
                    cleaned_plan = self._strip_markdown_headers(artifact["implementation_plan"])
                    if cleaned_plan:
                        content_parts.append(cleaned_plan)
                        content_parts.append("")
                
                if "subtasks" in artifact:
                    content_parts.append("## Subtasks")
                    content_parts.append("")
                    for subtask in artifact["subtasks"]:
                        if isinstance(subtask, dict):
                            subtask_id = subtask.get('subtask_id', 'unknown')
                            full_description = subtask.get('description', 'No description')
                            
                            # Extract title from description if it exists, otherwise use a default
                            lines = full_description.split('\n')
                            first_line = lines[0].strip() if lines else ''
                            if first_line.startswith('**Goal**:'):
                                # Extract the goal as the title
                                title = first_line.replace('**Goal**:', '').strip()
                            else:
                                title = 'Subtask Details'
                            
                            # Add section header
                            content_parts.append(f"### {subtask_id} - {title}")
                            content_parts.append("")
                            
                            # Add the full description content
                            content_parts.append(full_description)
                            content_parts.append("")
                        else:
                            content_parts.append(f"### {subtask}")
                            content_parts.append("")
                
                if "risks" in artifact:
                    content_parts.append("**Identified Risks:**")
                    for r in artifact["risks"]:
                        content_parts.append(f"- {r}")
                    content_parts.append("")
            
            # Validation state
            elif state == "validation":
                if "validation_summary" in artifact:
                    cleaned_summary = self._strip_markdown_headers(artifact["validation_summary"])
                    if cleaned_summary:
                        content_parts.append(cleaned_summary)
                        content_parts.append("")
                
                if "validations_performed" in artifact:
                    content_parts.append("**Validations Performed:**")
                    for v in artifact["validations_performed"]:
                        content_parts.append(f"- {v}")
                    content_parts.append("")
                
                if "issues_found" in artifact and artifact["issues_found"]:
                    content_parts.append("**Issues Found:**")
                    for issue in artifact["issues_found"]:
                        content_parts.append(f"- {issue}")
                    content_parts.append("")
                
                if "ready_for_implementation" in artifact:
                    status = "Ready for Implementation" if artifact["ready_for_implementation"] else "Not Ready"
                    content_parts.append(f"**Status:** {status}")
                    content_parts.append("")
            
            # Implementation state
            elif state == "implementing":
                if "summary" in artifact:
                    content_parts.append(f"**Summary:** {artifact['summary']}")
                    content_parts.append("")
                
                if "completed_subtasks" in artifact:
                    content_parts.append("**Completed Subtasks:**")
                    for s in artifact["completed_subtasks"]:
                        content_parts.append(f"- {s}")
                    content_parts.append("")
                
                if "testing_notes" in artifact:
                    content_parts.append(f"**Testing Notes:** {artifact['testing_notes']}")
                    content_parts.append("")
            
            # Review state
            elif state == "reviewing":
                if "summary" in artifact:
                    content_parts.append(f"**Summary:** {artifact['summary']}")
                    content_parts.append("")
                
                if "approved" in artifact:
                    status = "Approved" if artifact["approved"] else "Changes Requested"
                    content_parts.append(f"**Status:** {status}")
                    content_parts.append("")
                
                if "feedback" in artifact and artifact["feedback"]:
                    content_parts.append("**Feedback:**")
                    if isinstance(artifact["feedback"], list):
                        for item in artifact["feedback"]:
                            content_parts.append(f"- {item}")
                    else:
                        content_parts.append(artifact["feedback"])
                    content_parts.append("")
            
            # Testing state
            elif state == "testing":
                if "exit_code" in artifact:
                    status = "Passed" if artifact["exit_code"] == 0 else "Failed"
                    content_parts.append(f"**Test Status:** {status} (exit code: {artifact['exit_code']})")
                    content_parts.append("")
                
                if "output" in artifact:
                    content_parts.append("**Test Output:**")
                    content_parts.append("```")
                    content_parts.append(artifact["output"])
                    content_parts.append("```")
                    content_parts.append("")
            
            # Finalization state
            elif state == "finalizing":
                if "commit_hash" in artifact:
                    content_parts.append(f"**Commit:** `{artifact['commit_hash']}`")
                
                if "pr_url" in artifact:
                    content_parts.append(f"**Pull Request:** {artifact['pr_url']}")
                    content_parts.append("")
            
            # Generic handling for any other fields not covered above
            else:
                # Only add summary if not already handled
                if "summary" in artifact and state not in ["implementing", "reviewing"]:
                    content_parts.append(f"**Summary:** {artifact['summary']}")
                    content_parts.append("")
                
                # Add any other unhandled fields generically
                handled_fields = {
                    "summary", "findings", "questions", "decisions", "interface_design",
                    "implementation_plan", "subtasks", "risks", "completed_subtasks",
                    "approved", "feedback", "exit_code", "output", "commit_hash", "pr_url",
                    "validation_summary", "validations_performed", "issues_found",
                    "ready_for_implementation", "testing_notes"
                }
                
                for key, value in artifact.items():
                    if key not in handled_fields and value:
                        formatted_key = key.replace('_', ' ').title()
                        if isinstance(value, list):
                            content_parts.append(f"**{formatted_key}:**")
                            for item in value:
                                content_parts.append(f"- {item}")
                            content_parts.append("")
                        elif isinstance(value, (str, int, float, bool)):
                            content_parts.append(f"**{formatted_key}:** {value}")
                            content_parts.append("")
        else:
            # Fallback for non-dict artifacts
            content_parts.append(str(artifact))
            content_parts.append("")


# Global instance for easy access
turn_manager = TurnManager(Path(".alfred/workspace"))
``````
------ src/alfred/llm/__init__.py ------
``````
# AI Provider System for Alfred Task Manager

``````
------ src/alfred/llm/initialization.py ------
``````
"""
AI Provider Initialization for Alfred Task Manager

Following Alfred's principles:
- IMMUTABILITY ABOVE ALL (configuration loaded once at startup)
- ENVIRONMENT VARIABLES ARE SACRED (API keys from env)
- VALIDATION IS NON-NEGOTIABLE (fail fast on invalid config)
"""

from typing import List, Optional
from alfred.config import ConfigManager
from alfred.config.settings import settings
from alfred.lib.structured_logger import get_logger
from alfred.models.alfred_config import AIProvider, AIProviderConfig

from .registry import model_registry
from .providers.openai_provider import OpenAIProvider
from .providers.base import AuthenticationError, ProviderError

logger = get_logger(__name__)


async def initialize_ai_providers() -> None:
    """
    Initialize AI providers based on configuration.

    Following Alfred's configuration principles:
    - Load configuration once at startup (immutable)
    - Use environment variables for API keys
    - Fail fast on invalid configuration
    - Provide actionable error messages
    """
    try:
        # Load configuration (immutable, loaded once)
        config_manager = ConfigManager(settings.alfred_dir)
        config = config_manager.load()

        ai_config = config.ai
        if not ai_config.providers:
            logger.warning("No AI providers configured")
            return

        initialized_count = 0

        for provider_config in ai_config.providers:
            if not provider_config.enabled:
                logger.info(f"AI provider {provider_config.name} is disabled, skipping")
                continue

            try:
                await _initialize_single_provider(provider_config)
                initialized_count += 1
                logger.info(f"Successfully initialized AI provider: {provider_config.name}")

            except Exception as e:
                logger.error(f"Failed to initialize AI provider {provider_config.name}: {e}")
                # Continue with other providers rather than failing completely
                continue

        if initialized_count == 0:
            logger.warning("No AI providers were successfully initialized")
        else:
            logger.info(f"Initialized {initialized_count} AI provider(s)")

        # Log available models for debugging
        available_models = model_registry.get_available_models()
        model_names = [model.name for model in available_models]
        logger.debug(f"Available AI models: {model_names}")

    except Exception as e:
        logger.error(f"Failed to initialize AI providers: {e}")
        # Don't raise - let Alfred run without AI providers for now
        # In the future, we might want to make this more strict


async def _initialize_single_provider(provider_config: AIProviderConfig) -> None:
    """Initialize a single AI provider instance."""

    # Get API key from environment variables (sacred principle)
    api_key = _get_api_key_for_provider(provider_config.name)

    if not api_key:
        raise AuthenticationError(f"No API key found for {provider_config.name}. Set {provider_config.name.upper()}_API_KEY environment variable.")

    # Create provider instance based on type with hardcoded sensible defaults
    if provider_config.name == AIProvider.OPENAI:
        provider = model_registry.create_provider(
            "openai",
            api_key=api_key,
            base_url=None,  # Use OpenAI's default API endpoint
        )
    elif provider_config.name == AIProvider.GOOGLE:
        provider = model_registry.create_provider("google", api_key=api_key)
    elif provider_config.name == AIProvider.ANTHROPIC:
        provider = model_registry.create_provider("anthropic", api_key=api_key)
    else:
        raise ProviderError(f"Unsupported AI provider: {provider_config.name}")

    # Register the provider
    model_registry.register_provider(provider_config.name.value, provider)


def _get_api_key_for_provider(provider: AIProvider) -> Optional[str]:
    """
    Get API key for a provider from environment variables.

    Following Alfred's principle: ENVIRONMENT VARIABLES ARE SACRED
    """
    if provider == AIProvider.OPENAI:
        return settings.openai_api_key
    elif provider == AIProvider.GOOGLE:
        return settings.google_api_key
    elif provider == AIProvider.ANTHROPIC:
        return settings.anthropic_api_key
    else:
        return None


def get_provider_status() -> dict:
    """Get status of all registered providers (for debugging)."""
    return {
        "registered_providers": model_registry.get_registered_providers(),
        "total_models": len(model_registry.get_available_models()),
        "models_by_provider": {provider: [model.name for model in model_registry.get_available_models() if model.provider == provider] for provider in model_registry.get_registered_providers()},
    }

``````
------ src/alfred/llm/providers/__init__.py ------
``````
# AI Provider implementations

``````
------ src/alfred/llm/providers/anthropic_provider.py ------
``````
"""
Anthropic Claude Provider Implementation for Alfred Task Manager

Following Alfred's principles:
- Data normalization to standard ModelResponse
- Uniform error mapping
- No provider-specific extensions
"""

import anthropic
from typing import List, Optional, Dict, Any

from .base import BaseAIProvider, ModelResponse, ModelInfo, ModelCapability, ProviderError, ModelNotFoundError, QuotaExceededError, AuthenticationError


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude API provider implementation."""

    def __init__(self, api_key: str):
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Anthropic client: {e}")

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using Anthropic Claude models."""
        try:
            # Claude uses a messages API format
            response = self.client.messages.create(model=model_name, max_tokens=max_tokens or 4096, temperature=temperature, messages=[{"role": "user", "content": prompt}])

            content = response.content[0].text if response.content else ""

            # Normalize usage data
            usage = {}
            if response.usage:
                usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens, "total_tokens": response.usage.input_tokens + response.usage.output_tokens}

            # Provider-specific metadata
            metadata = {"stop_reason": response.stop_reason, "model": response.model, "response_id": response.id}

            return ModelResponse(content=content, model_name=model_name, usage=usage, metadata=metadata)

        except anthropic.AuthenticationError as e:
            raise AuthenticationError(f"Anthropic authentication failed: {e}")
        except anthropic.NotFoundError as e:
            raise ModelNotFoundError(f"Model {model_name} not found: {e}")
        except anthropic.RateLimitError as e:
            raise QuotaExceededError(f"Anthropic rate limit exceeded: {e}")
        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API error: {e}")
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower():
                raise AuthenticationError(f"Anthropic API key error: {error_msg}")
            else:
                raise ProviderError(f"Anthropic error: {error_msg}")

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using Anthropic's token counting."""
        try:
            # Anthropic provides a count_tokens method
            count = self.client.count_tokens(text)
            return count

        except Exception as e:
            # Fallback: rough estimation (Claude uses similar tokenization to GPT)
            # This is approximate - about 4 characters per token
            return len(text) // 4

    def get_available_models(self) -> List[ModelInfo]:
        """Get available Anthropic Claude models."""
        # Static model definitions based on Anthropic API
        models = [
            ModelInfo(
                name="claude-3-5-sonnet-20241022",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=200000,
                max_output_tokens=8192,
                cost_per_input_token=0.003,  # Per 1K tokens
                cost_per_output_token=0.015,
            ),
            ModelInfo(
                name="claude-3-opus-20240229",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_input_token=0.015,  # Per 1K tokens
                cost_per_output_token=0.075,
            ),
            ModelInfo(
                name="claude-3-sonnet-20240229",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_input_token=0.003,
                cost_per_output_token=0.015,
            ),
            ModelInfo(
                name="claude-3-haiku-20240307",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_input_token=0.00025,
                cost_per_output_token=0.00125,
            ),
        ]

        return models

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available."""
        try:
            # Test with minimal request
            self.client.messages.create(model=model_name, max_tokens=1, messages=[{"role": "user", "content": "test"}])
            return True
        except Exception:
            return False

``````
------ src/alfred/llm/providers/base.py ------
``````
"""
Base AI Provider Interface for Alfred Task Manager

Following Alfred's Task Provider Principles:
- ONE INTERFACE TO RULE THEM ALL
- DATA NORMALIZATION IS SACRED
- NO PROVIDER LEAKAGE
- ERROR HANDLING IS UNIFORM
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ModelCapability(str, Enum):
    """Model capabilities for routing decisions."""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    ANALYSIS = "analysis"


class ModelResponse(BaseModel):
    """Normalized response from any AI provider."""

    content: str
    model_name: str
    usage: Dict[str, Any] = Field(default_factory=dict)  # {input_tokens: int, output_tokens: int, cost: float, etc.}
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Provider-specific data
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": True}  # Immutable value object


class ModelInfo(BaseModel):
    """Model information for registry."""

    name: str
    provider: str
    capabilities: List[ModelCapability]
    context_window: int
    max_output_tokens: Optional[int] = None
    cost_per_input_token: Optional[float] = None
    cost_per_output_token: Optional[float] = None

    model_config = {"frozen": True}


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI model providers.

    Following Task Provider Principles:
    - EXACTLY FOUR METHODS (like BaseTaskProvider)
    - Uniform behavior across all implementations
    - No provider-specific methods or extensions
    """

    @abstractmethod
    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using the specified model."""
        pass

    @abstractmethod
    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for a given model."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models from this provider."""
        pass

    @abstractmethod
    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available and accessible."""
        pass


class ProviderError(Exception):
    """Standard error for all provider operations."""

    pass


class ModelNotFoundError(ProviderError):
    """Model not found or not available."""

    pass


class QuotaExceededError(ProviderError):
    """API quota or rate limit exceeded."""

    pass


class AuthenticationError(ProviderError):
    """Provider authentication failed."""

    pass

``````
------ src/alfred/llm/providers/google_provider.py ------
``````
"""
Google Gemini Provider Implementation for Alfred Task Manager

Following Alfred's principles:
- Data normalization to standard ModelResponse
- Uniform error mapping
- No provider-specific extensions
"""

import google.generativeai as genai
from typing import List, Optional, Dict, Any
from google.api_core import exceptions as google_exceptions

from .base import BaseAIProvider, ModelResponse, ModelInfo, ModelCapability, ProviderError, ModelNotFoundError, QuotaExceededError, AuthenticationError


class GoogleProvider(BaseAIProvider):
    """Google Gemini API provider implementation."""

    def __init__(self, api_key: str):
        try:
            genai.configure(api_key=api_key)
            self.api_key = api_key
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Google Gemini client: {e}")

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using Google Gemini models."""
        try:
            # Initialize the model
            model = genai.GenerativeModel(model_name)

            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Generate content
            response = model.generate_content(prompt, generation_config=generation_config)

            content = response.text if response.text else ""

            # Normalize usage data (Gemini doesn't always provide detailed usage)
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            # Provider-specific metadata
            metadata = {
                "finish_reason": getattr(response.candidates[0], "finish_reason", None) if response.candidates else None,
                "safety_ratings": [rating for candidate in response.candidates for rating in candidate.safety_ratings] if response.candidates else [],
            }

            return ModelResponse(content=content, model_name=model_name, usage=usage, metadata=metadata)

        except google_exceptions.PermissionDenied as e:
            raise AuthenticationError(f"Google API authentication failed: {e}")
        except google_exceptions.NotFound as e:
            raise ModelNotFoundError(f"Model {model_name} not found: {e}")
        except google_exceptions.ResourceExhausted as e:
            raise QuotaExceededError(f"Google API quota exceeded: {e}")
        except Exception as e:
            error_msg = str(e)
            if "API_KEY" in error_msg.upper():
                raise AuthenticationError(f"Google API key error: {error_msg}")
            else:
                raise ProviderError(f"Google API error: {error_msg}")

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using Google's token counting."""
        try:
            model = genai.GenerativeModel(model_name)
            response = model.count_tokens(text)
            return response.total_tokens

        except Exception as e:
            raise ProviderError(f"Token counting failed: {e}")

    def get_available_models(self) -> List[ModelInfo]:
        """Get available Google Gemini models."""
        # Static model definitions based on Gemini API
        models = [
            ModelInfo(
                name="gemini-1.5-pro",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=1048576,  # 1M tokens
                max_output_tokens=8192,
                cost_per_input_token=0.00125,  # Per 1K tokens
                cost_per_output_token=0.005,
            ),
            ModelInfo(
                name="gemini-1.5-flash",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=1048576,  # 1M tokens
                max_output_tokens=8192,
                cost_per_input_token=0.000075,  # Per 1K tokens
                cost_per_output_token=0.0003,
            ),
            ModelInfo(
                name="gemini-pro",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
                context_window=32768,
                max_output_tokens=8192,
                cost_per_input_token=0.0005,
                cost_per_output_token=0.0015,
            ),
            ModelInfo(
                name="gemini-1.5-flash-8b",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION],
                context_window=1048576,  # 1M tokens
                max_output_tokens=8192,
                cost_per_input_token=0.0000375,  # Per 1K tokens
                cost_per_output_token=0.00015,
            ),
        ]

        return models

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available."""
        try:
            model = genai.GenerativeModel(model_name)
            # Test with minimal request
            response = model.count_tokens("test")
            return response.total_tokens > 0
        except Exception:
            return False

``````
------ src/alfred/llm/providers/openai_provider.py ------
``````
"""
OpenAI Provider Implementation for Alfred Task Manager

Following Alfred's principles:
- Data normalization to standard ModelResponse
- Uniform error mapping
- No provider-specific extensions
"""

import tiktoken
from typing import List, Optional, Dict, Any
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from .base import BaseAIProvider, ModelResponse, ModelInfo, ModelCapability, ProviderError, ModelNotFoundError, QuotaExceededError, AuthenticationError


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize OpenAI client: {e}")

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using OpenAI models."""
        try:
            response: ChatCompletion = self.client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=temperature, max_tokens=max_tokens)

            content = response.choices[0].message.content or ""

            # Normalize usage data
            usage = {}
            if response.usage:
                usage = {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens}

            # Provider-specific metadata
            metadata = {"finish_reason": response.choices[0].finish_reason, "response_id": response.id, "created": response.created}

            return ModelResponse(content=content, model_name=model_name, usage=usage, metadata=metadata)

        except Exception as e:
            # Map OpenAI errors to standard provider errors
            error_msg = str(e)
            if "model" in error_msg.lower() and "not found" in error_msg.lower():
                raise ModelNotFoundError(f"Model {model_name} not found")
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise QuotaExceededError(f"OpenAI quota exceeded: {error_msg}")
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                raise AuthenticationError(f"OpenAI authentication failed: {error_msg}")
            else:
                raise ProviderError(f"OpenAI API error: {error_msg}")

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using tiktoken."""
        try:
            # Map model names to tiktoken encodings
            encoding_map = {"gpt-4": "cl100k_base", "gpt-4-turbo": "cl100k_base", "gpt-3.5-turbo": "cl100k_base", "o3": "cl100k_base", "o3-mini": "cl100k_base", "o4-mini": "cl100k_base"}

            # Default to cl100k_base for unknown models
            encoding_name = encoding_map.get(model_name, "cl100k_base")
            encoding = tiktoken.get_encoding(encoding_name)

            return len(encoding.encode(text))

        except Exception as e:
            raise ProviderError(f"Token counting failed: {e}")

    def get_available_models(self) -> List[ModelInfo]:
        """Get available OpenAI models."""
        # Static model definitions (can be extended to fetch from API)
        models = [
            ModelInfo(
                name="gpt-4",
                provider="openai",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
                context_window=8192,
                max_output_tokens=4096,
                cost_per_input_token=0.00003,
                cost_per_output_token=0.00006,
            ),
            ModelInfo(
                name="gpt-4-turbo",
                provider="openai",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=128000,
                max_output_tokens=4096,
                cost_per_input_token=0.00001,
                cost_per_output_token=0.00003,
            ),
            ModelInfo(
                name="gpt-3.5-turbo",
                provider="openai",
                capabilities=[ModelCapability.TEXT_GENERATION],
                context_window=16385,
                max_output_tokens=4096,
                cost_per_input_token=0.0000005,
                cost_per_output_token=0.0000015,
            ),
            ModelInfo(
                name="o3",
                provider="openai",
                capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=200000,
                max_output_tokens=100000,
                cost_per_input_token=0.0001,  # Placeholder pricing
                cost_per_output_token=0.0002,
            ),
            ModelInfo(
                name="o3-mini",
                provider="openai",
                capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=65536,
                cost_per_input_token=0.00005,
                cost_per_output_token=0.0001,
            ),
            ModelInfo(
                name="o4-mini",
                provider="openai",
                capabilities=[ModelCapability.REASONING, ModelCapability.TEXT_GENERATION],
                context_window=200000,
                max_output_tokens=65536,
                cost_per_input_token=0.00005,
                cost_per_output_token=0.0001,
            ),
        ]

        return models

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available."""
        try:
            # Test with minimal request
            self.client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": "test"}], max_tokens=1)
            return True
        except Exception:
            return False

``````
------ src/alfred/llm/registry.py ------
``````
"""
AI Provider Registry and Factory for Alfred Task Manager

Following Alfred's principles:
- PROVIDER FACTORY IS IMMUTABLE
- ONE REGISTRY TO RULE THEM ALL
- NO PROVIDER LEAKAGE
- CONFIGURATION-DRIVEN
"""

from typing import Dict, List, Optional, Type
from functools import lru_cache

from .providers.base import BaseAIProvider, ModelInfo, ModelNotFoundError, ProviderError
from .providers.openai_provider import OpenAIProvider
from .providers.google_provider import GoogleProvider
from .providers.anthropic_provider import AnthropicProvider


class ModelProviderRegistry:
    """
    Central registry for AI providers and models.

    Following Task Provider principles:
    - Provider selection through configuration
    - Uniform model routing
    - No provider-specific logic exposed
    """

    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._model_to_provider_map: Dict[str, str] = {}
        self._provider_classes: Dict[str, Type[BaseAIProvider]] = {
            "openai": OpenAIProvider,
            "google": GoogleProvider,
            "anthropic": AnthropicProvider,
        }

    def register_provider(self, provider_name: str, provider_instance: BaseAIProvider) -> None:
        """Register a provider instance."""
        if provider_name in self._providers:
            raise ValueError(f"Provider {provider_name} already registered")

        self._providers[provider_name] = provider_instance

        # Build model mapping
        try:
            models = provider_instance.get_available_models()
            for model in models:
                if model.name in self._model_to_provider_map:
                    # Handle model name conflicts by prefixing with provider
                    prefixed_name = f"{provider_name}:{model.name}"
                    self._model_to_provider_map[prefixed_name] = provider_name
                else:
                    self._model_to_provider_map[model.name] = provider_name
        except Exception as e:
            # Don't fail registration if model enumeration fails
            # Provider may still work for specific model requests
            pass

    def create_provider(self, provider_name: str, **kwargs) -> BaseAIProvider:
        """Factory method to create provider instances."""
        if provider_name not in self._provider_classes:
            raise ValueError(f"Unknown provider type: {provider_name}")

        provider_class = self._provider_classes[provider_name]
        return provider_class(**kwargs)

    def get_provider_for_model(self, model_name: str) -> BaseAIProvider:
        """Get the provider that handles a specific model."""
        # Check direct model name mapping
        if model_name in self._model_to_provider_map:
            provider_name = self._model_to_provider_map[model_name]
            return self._providers[provider_name]

        # Check prefixed model name (provider:model)
        if ":" in model_name:
            provider_name, _ = model_name.split(":", 1)
            if provider_name in self._providers:
                return self._providers[provider_name]

        # Fallback: try each provider to see if they support the model
        for provider in self._providers.values():
            if provider.validate_model(model_name):
                return provider

        raise ModelNotFoundError(f"No provider found for model: {model_name}")

    def get_available_models(self) -> List[ModelInfo]:
        """Get all available models across all providers."""
        all_models = []
        for provider in self._providers.values():
            try:
                models = provider.get_available_models()
                all_models.extend(models)
            except Exception:
                # Skip providers that fail to enumerate models
                continue
        return all_models

    def get_registered_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())

    def is_provider_registered(self, provider_name: str) -> bool:
        """Check if a provider is registered."""
        return provider_name in self._providers


# Global registry instance (singleton)
model_registry = ModelProviderRegistry()


@lru_cache(maxsize=1)
def get_model_registry() -> ModelProviderRegistry:
    """Get the global model registry instance."""
    return model_registry

``````
------ src/alfred/models/__init__.py ------
``````

``````
------ src/alfred/models/alfred_config.py ------
``````
"""Configuration models for Alfred."""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TaskProvider(str, Enum):
    """Supported task provider types."""

    JIRA = "jira"
    LINEAR = "linear"
    LOCAL = "local"


class AIProvider(str, Enum):
    """Supported AI provider types."""

    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


class ToolConfig(BaseModel):
    """Configuration for individual tools."""

    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    description: str = Field(default="", description="Tool description")


class ProviderConfig(BaseModel):
    """Configuration for task provider."""

    type: TaskProvider = Field(default=TaskProvider.LOCAL, description="The task management system to use")


class FeaturesConfig(BaseModel):
    """Feature flags for Alfred."""

    scaffolding_mode: bool = Field(default=False, description="Enable scaffolding mode to generate TODO placeholders before implementation")
    autonomous_mode: bool = Field(default=False, description="Enable autonomous mode to bypass human review steps.")


class WorkflowConfig(BaseModel):
    """Workflow behavior configuration."""

    require_human_approval: bool = Field(default=True, description="Whether to require human approval at review gates")
    enable_ai_review: bool = Field(default=True, description="Whether to enable AI self-review steps")
    max_thinking_time: int = Field(default=300, description="Maximum thinking time for AI in seconds")
    auto_create_branches: bool = Field(default=True, description="Whether to create branches automatically")


class AIProviderConfig(BaseModel):
    """Configuration for individual AI providers."""

    name: AIProvider = Field(description="AI provider type")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")


class AIConfig(BaseModel):
    """AI provider configuration."""

    providers: List[AIProviderConfig] = Field(
        default_factory=lambda: [
            AIProviderConfig(name=AIProvider.OPENAI),
            AIProviderConfig(name=AIProvider.GOOGLE),
            AIProviderConfig(name=AIProvider.ANTHROPIC, enabled=False),
        ],
        description="List of configured AI providers",
    )
    default_provider: AIProvider = Field(default=AIProvider.OPENAI, description="Default provider to use")
    enable_token_tracking: bool = Field(default=True, description="Whether to track token usage")
    max_tokens_per_request: int = Field(default=8000, description="Maximum tokens per request")
    default_temperature: float = Field(default=0.5, description="Default temperature for AI requests")
    default_model: str = Field(default="gpt-4", description="Default model to use when not specified")


class ProvidersConfig(BaseModel):
    """Provider-specific workflow settings."""

    jira: Dict[str, Any] = Field(default_factory=lambda: {"transition_on_start": True, "transition_on_complete": True})
    linear: Dict[str, Any] = Field(default_factory=lambda: {"update_status": True})
    local: Dict[str, Any] = Field(default_factory=lambda: {"task_file_pattern": "*.md"})


class DebugConfig(BaseModel):
    """Debug settings."""

    save_debug_logs: bool = Field(default=True, description="Whether to save detailed debug logs")
    save_state_snapshots: bool = Field(default=True, description="Whether to save state snapshots")
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")


class AlfredConfig(BaseModel):
    """Main configuration model for Alfred."""

    version: str = Field(default="2.0.0", description="Configuration version")
    provider: ProviderConfig = Field(default_factory=ProviderConfig, description="Task provider configuration")
    ai: AIConfig = Field(default_factory=AIConfig, description="AI provider configuration")
    features: FeaturesConfig = Field(default_factory=FeaturesConfig, description="Feature flags")
    tools: Dict[str, ToolConfig] = Field(
        default_factory=lambda: {
            "create_spec": ToolConfig(enabled=True, description="Create technical specification from PRD"),
            "create_tasks_from_spec": ToolConfig(enabled=True, description="Break down engineering spec into actionable tasks"),
            "plan_task": ToolConfig(enabled=True, description="Create detailed execution plan for a task"),
            "implement_task": ToolConfig(enabled=True, description="Execute the planned implementation"),
            "review_task": ToolConfig(enabled=True, description="Perform code review"),
            "test_task": ToolConfig(enabled=True, description="Run and validate tests"),
            "finalize_task": ToolConfig(enabled=True, description="Create commit and pull request"),
        },
        description="Tool configurations",
    )
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig, description="Workflow behavior settings")
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig, description="Provider-specific settings")
    debug: DebugConfig = Field(default_factory=DebugConfig, description="Debug settings")

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
"""Simplified discovery artifacts for reduced cognitive load."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from alfred.models.schemas import Task


class ComplexityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ContextDiscoveryArtifact(BaseModel):
    """Simplified discovery artifact focusing on essentials."""

    # What we found (markdown formatted for readability)
    findings: str = Field(description="Markdown-formatted discovery findings")

    # Questions that need answers
    questions: List[str] = Field(description="Simple list of questions for clarification", default_factory=list)

    # Files that will be touched
    files_to_modify: List[str] = Field(description="List of files that need changes", default_factory=list)

    # Complexity assessment
    complexity: ComplexityLevel = Field(description="Overall complexity: LOW, MEDIUM, or HIGH", default=ComplexityLevel.MEDIUM)

    # Context bundle for implementation (free-form)
    implementation_context: Dict[str, Any] = Field(description="Any context needed for implementation", default_factory=dict)

    @field_validator("questions")
    @classmethod
    def questions_end_with_questionmark(cls, v):
        for q in v:
            if not q.strip().endswith("?"):
                raise ValueError(f'Question must end with "?": {q}')
        return v

    @field_validator("findings")
    @classmethod
    def findings_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Findings cannot be empty")
        return v


class ClarificationArtifact(BaseModel):
    """Simplified clarification results."""

    # Q&A in markdown format
    clarification_dialogue: str = Field(description="Markdown-formatted Q&A dialogue")

    # Key decisions made
    decisions: List[str] = Field(description="List of decisions made during clarification", default_factory=list)

    # Any new constraints discovered
    additional_constraints: List[str] = Field(description="New constraints or requirements discovered", default_factory=list)


class ContractDesignArtifact(BaseModel):
    """Simplified contracts/interface design."""

    # Interface design in markdown
    interface_design: str = Field(description="Markdown-formatted interface specifications")

    # Key APIs/contracts defined
    contracts_defined: List[str] = Field(description="List of main contracts/interfaces defined", default_factory=list)

    # Any additional notes
    design_notes: List[str] = Field(description="Important design decisions or notes", default_factory=list)


class SubtaskScope(BaseModel):
    """Optional minimal structure for complex subtasks."""

    files: List[str] = Field(default_factory=list, description="Files this subtask will modify or create")
    depends_on_subtasks: List[str] = Field(default_factory=list, description="Other subtask IDs this depends on")


class Subtask(BaseModel):
    """Structured subtask with ID and description."""

    subtask_id: str = Field(..., description="Unique identifier for the subtask (e.g., 'subtask-1', 'ST-001')")
    description: str = Field(..., description="Structured description using markdown format with Goal, Location, Approach, and Verify sections")
    scope: Optional[SubtaskScope] = Field(default=None, description="Optional scope information for complex tasks")


class ImplementationPlanArtifact(BaseModel):
    """Implementation plan with structured subtasks."""

    # Implementation plan in markdown
    implementation_plan: str = Field(description="Markdown-formatted implementation steps")

    # List of structured subtasks
    subtasks: List[Subtask] = Field(description="List of structured subtasks with IDs", default_factory=list)

    # Any risks or concerns
    risks: List[str] = Field(description="Potential risks or concerns", default_factory=list)


class ValidationArtifact(BaseModel):
    """Simplified validation results."""

    # Validation summary in markdown
    validation_summary: str = Field(description="Markdown-formatted validation results")

    # Checklist of validations performed
    validations_performed: List[str] = Field(description="List of validations performed", default_factory=list)

    # Any issues found
    issues_found: List[str] = Field(description="List of issues or concerns found", default_factory=list)

    # Ready for implementation?
    ready_for_implementation: bool = Field(description="Whether the plan is ready for implementation", default=True)


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

    def validate_against_plan(self, planned_subtasks: List[str]) -> Optional[str]:
        """Validate completed subtasks against the original plan.

        Args:
            planned_subtasks: List of subtask IDs from the original execution plan

        Returns:
            None if validation passes, error message if validation fails
        """
        planned_set = set(planned_subtasks)
        completed_set = set(self.completed_subtasks)

        missing = planned_set - completed_set
        extra = completed_set - planned_set

        if missing:
            completed_count = len(self.completed_subtasks)
            total_count = len(planned_subtasks)
            percentage = (completed_count / total_count * 100) if total_count > 0 else 0

            return (
                f"Implementation incomplete: {completed_count} of {total_count} subtasks completed ({percentage:.0f}%). "
                f"Missing: {sorted(missing)}. "
                f"\n\n**Next Action**: Complete the remaining subtasks and mark each one with "
                f"`alfred.mark_subtask_complete(task_id, subtask_id)` before submitting again."
            )

        if extra:
            # Extra subtasks are a warning, not an error
            pass

        return None


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

    task_id: str = Field(description="The unique identifier, e.g., 'TK-01'.")
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

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pydantic import BaseModel, Field

from alfred.models.schemas import TaskStatus


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
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TaskState(BaseModel):
    """
    The single state object for a task.
    This is the schema for the `task_state.json` file.
    """

    task_id: str
    task_status: TaskStatus = Field(default=TaskStatus.NEW)
    active_tool_state: Optional[WorkflowState] = Field(default=None)
    completed_tool_outputs: Dict[str, Any] = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

``````
------ src/alfred/orchestration/__init__.py ------
``````

``````
------ src/alfred/orchestration/orchestrator.py ------
``````
# src/alfred/orchestration/orchestrator.py
"""
Legacy orchestrator module - largely deprecated in stateless design.

The orchestrator previously managed active tool sessions but this functionality
has been replaced by the stateless WorkflowEngine pattern where StateManager
is the single source of truth.
"""

from alfred.config import ConfigManager
from alfred.config.settings import settings
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    """
    Legacy orchestrator class - deprecated in favor of stateless design.
    
    Previously managed active tool sessions but this functionality has been
    replaced by WorkflowEngine + StateManager pattern. Kept for backwards
    compatibility but no longer holds any state.
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
        self.config_manager = ConfigManager(settings.alfred_dir)
        self._initialized = True
        logger.info("Orchestrator initialized (legacy mode - stateless design active)", 
                   orchestrator_type="legacy_deprecated", 
                   alfred_dir=str(settings.alfred_dir))


# Global singleton instance - kept for backwards compatibility
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

from alfred.config.settings import settings
from alfred.core.prompter import prompt_library  # Import the prompt library
from alfred.lib.structured_logger import get_logger
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.constants import ToolName
from alfred.tools.registry import tool_registry
from alfred.tools.progress import mark_subtask_complete_handler
from alfred.tools.submit_work import submit_work_handler
from alfred.tools.tool_factory import get_tool_handler
from alfred.llm.initialization import initialize_ai_providers

logger = get_logger(__name__)


# Create a helper function to register tools
def register_tool_from_definition(app: FastMCP, tool_name: str):
    """Register a tool using its definition."""
    # Local import to avoid circular dependency
    from alfred.tools.tool_definitions import get_tool_definition
    definition = get_tool_definition(tool_name)
    handler = get_tool_handler(tool_name)

    @tool_registry.register(name=tool_name, handler_class=lambda: handler, tool_class=definition.tool_class, entry_status_map=definition.get_entry_status_map())
    def tool_impl(**kwargs):
        return handler.execute(**kwargs)

    return tool_impl


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifespan context manager for FastMCP server."""
    # Startup
    logger.info("Starting Alfred server", server_name=settings.server_name, prompts_loaded=len(prompt_library._cache))

    # Initialize AI providers (following Alfred's immutable startup principle)
    await initialize_ai_providers()

    yield

    # Shutdown (if needed in the future)
    logger.info("Server shutting down", server_name=settings.server_name)


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

            # Log tool execution start with structured context
            logger.info("Tool execution started", task_id=task_id, tool_name=tool_name, request_params=list(request_data.keys()))

            try:
                # Call the implementation function (handle both async and sync)
                if inspect.iscoroutinefunction(impl_func):
                    response = await impl_func(**kwargs)
                else:
                    response = impl_func(**kwargs)

                # Log successful completion
                logger.info("Tool execution completed", task_id=task_id, tool_name=tool_name, status=response.status)

                # Log the detailed transaction with structured context
                with logger.context(task_id=task_id, tool_name=tool_name):
                    logger.info("Tool transaction completed", request_params=request_data, response_status=response.status, response_message=response.message)

                return response
            except Exception as e:
                # Log tool execution error with structured context
                logger.error("Tool execution failed", task_id=task_id, tool_name=tool_name, error=str(e), exc_info=True)
                raise

        return wrapper

    return decorator


@app.tool()
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
    handler = get_tool_handler(ToolName.INITIALIZE_PROJECT)
    return await handler.execute(provider=provider)


@app.tool()
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
    handler = get_tool_handler(ToolName.GET_NEXT_TASK)
    return await handler.execute()


@app.tool()
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
        task_id (str): The unique identifier for the task (e.g., "TK-01", "PROJ-123")

    Returns:
        ToolResponse: Contains routing guidance to the appropriate specialized tool

    Example:
        work_on_task("TK-01") -> Guides to plan_task if task is new
        work_on_task("TK-02") -> Guides to implement_task if planning is complete
    """
    handler = get_tool_handler(ToolName.WORK_ON_TASK)
    return await handler.execute(task_id=task_id)


@app.tool()
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
    handler = get_tool_handler(ToolName.CREATE_SPEC)
    return await handler.execute(task_id=task_id, prd_content=prd_content)


@app.tool()
async def create_tasks_from_spec(task_id: str) -> ToolResponse:
    """
    Creates a list of actionable tasks from a completed engineering specification.

    This is the second tool in the "idea-to-code" pipeline. It takes a completed
    engineering specification and breaks it down into individual Task objects that
    can be tracked, assigned, and implemented independently.

    The tool guides through creating tasks that are:
    - Atomic and focused
    - Properly ordered with dependencies
    - Sized appropriately (1-3 days of work)
    - Complete with acceptance criteria

    Args:
        task_id (str): The unique identifier for the epic/feature with a completed engineering spec

    Returns:
        ToolResponse: Contains the first prompt to guide task breakdown

    Preconditions:
        - Engineering specification must be completed (via create_spec)
        - Task status must be "spec_completed"

    Example:
        create_tasks_from_spec("EPIC-01") -> Guides creation of task list from spec
    """
    handler = get_tool_handler(ToolName.CREATE_TASKS_FROM_SPEC)
    return await handler.execute(task_id=task_id)


@app.tool()
async def create_task(task_content: str) -> ToolResponse:
    """
    Creates a new task in the Alfred system using the standardized task template format.

    This tool provides the standard way to create tasks within Alfred, ensuring proper
    format validation and consistent task structure. It validates the task content
    against the required template format and saves it to the .alfred/tasks directory.

    The tool validates and requires:
    - **First line format**: Must be '# TASK: <task_id>'
    - **Required sections**: Title, Context, Implementation Details, Acceptance Criteria
    - **Section headers**: All sections must use '##' markdown headers
    - **Non-empty content**: Task content cannot be empty
    - **Unique task_id**: Task ID must not already exist

    Template Format (copy and modify this exact structure):
    ```markdown
    # TASK: YOUR-TASK-ID

    ## Title
    Brief descriptive title for the task

    ## Context
    Background information explaining why this task is needed, business context,
    and any relevant background that helps understand the requirements.

    ## Implementation Details
    Detailed description of what needs to be implemented, technical approach,
    and specific requirements for the implementation.

    ## Acceptance Criteria
    - Clear, testable criteria that define when the task is complete
    - Each criterion should be specific and measurable
    - Use bullet points for each criterion

    ## AC Verification
    - Optional section describing how to verify each acceptance criterion
    - Testing steps or validation procedures

    ## Dev Notes
    - Optional section for additional development notes
    - Architecture considerations, gotchas, or helpful context
    ```

    Args:
        task_content (str): Raw markdown content following the exact template format above

    Returns:
        ToolResponse: Contains:
            - success: Whether task was created successfully
            - data.task_id: The extracted task ID
            - data.file_path: Path where task was saved
            - data.task_title: The task title
            - data.template: Full template format (if validation fails)
            - data.help: Specific guidance on format requirements

    Examples:
        # Valid task creation
        create_task('''# TASK: AUTH-001

        ## Title
        Implement user authentication system

        ## Context
        Need to add secure user login functionality to support multiple user roles.

        ## Implementation Details
        Create JWT-based authentication with role-based access control.

        ## Acceptance Criteria
        - Users can login with email/password
        - JWT tokens are properly validated
        - Role-based permissions are enforced
        ''')

    Validation Errors:
        If the format is incorrect, the tool returns the complete template format
        with specific error guidance. Common issues:
        - Missing '# TASK: <task_id>' first line
        - Missing required sections (Title, Context, Implementation Details, Acceptance Criteria)
        - Incorrect section headers (must use '##')
        - Empty content
        - Duplicate task_id

    Next Actions:
        After successful creation, use work_on_task(task_id) to start working on the task.

    Note: This tool enforces the exact template format to ensure consistency across
    all tasks in the Alfred system. The template format is non-negotiable and must
    be followed precisely for successful task creation.
    """
    handler = get_tool_handler(ToolName.CREATE_TASK)
    return await handler.execute(task_content=task_content)


@app.tool()
async def plan_task(task_id: str) -> ToolResponse:
    """
    Initiates the detailed technical planning for a specific task.

    This is the primary tool for transforming a high-level task or user story
    into a concrete, machine-executable 'Execution Plan' composed of Subtasks.
    A Subtask (based on LOST framework) is an atomic unit of work.

    This tool manages a multi-step, interactive discovery planning process:
    1. **Discovery**: Deep context discovery and codebase exploration
    2. **Clarification**: Conversational human-AI clarification
    3. **Contracts**: Interface-first design and contracts
    4. **Implementation Plan**: Self-contained subtask creation
    5. **Validation**: Final plan validation and coherence check

    Each step includes AI self-review followed by human approval gates to ensure quality.
    The final output is a validated execution plan ready for implementation.

    Args:
        task_id (str): The unique identifier for the task (e.g., "TK-01", "PROJ-123")

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
    handler = get_tool_handler(ToolName.PLAN_TASK)
    return await handler.execute(task_id)


# Register with tool registry
register_tool_from_definition(app, ToolName.PLAN_TASK)


@app.tool()
@log_tool_transaction(submit_work_handler.execute)
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step of a workflow tool.

    This tool advances any active workflow (plan, implement, review, test) by submitting
    the completed work for the current state. It automatically validates the artifact
    structure and transitions to the next appropriate state in the workflow.

    The artifact structure varies by workflow tool and current state:
    - **Planning states**: context_discovery, clarification, contract_design, implementation_plan, validation
    - **Implementation**: progress updates, completion status
    - **Review**: findings, issues, recommendations
    - **Testing**: test results, coverage, validation status

    ## Parameters
    - **task_id** `[string]`: The unique identifier for the task (e.g., "AL-01", "TK-123")
    - **artifact** `[object]`: Structured data matching the current state's expected schema

    ## Examples
    ```
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
    ```

    ## Next Actions
    - If in review state: Use approve_review or request_revision
    - If advancing to new phase: Tool will indicate next tool to use
    - If complete: No further action needed
    """
    return await submit_work_handler.execute(task_id, artifact=artifact)


@app.tool()
async def approve_review(task_id: str) -> ToolResponse:
    """
    Approves the artifact in the current review step and advances the workflow.

    - Approves work in any review state (AI self-review or human review)
    - Advances workflow to next phase or completion
    - Works with all review states across all workflow tools
    - Automatically determines next state based on current workflow phase

    Applicable States:
    - **Planning**: discovery_awaiting_ai_review, clarification_awaiting_ai_review, contracts_awaiting_ai_review, implementation_plan_awaiting_ai_review, validation_awaiting_ai_review
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
    handler = get_tool_handler(ToolName.APPROVE_REVIEW)
    return await handler.execute(task_id=task_id)


@app.tool()
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
    handler = get_tool_handler(ToolName.REQUEST_REVISION)
    return await handler.execute(task_id=task_id, feedback_notes=feedback_notes)


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
        task_id (str): The unique identifier for the task (e.g., "TK-01", "PROJ-123")
        subtask_id (str): The subtask identifier to mark as complete (e.g., "subtask-1")

    Returns:
        ToolResponse: Success/error status with progress information including:
            - Current progress percentage
            - Number of completed vs total subtasks
            - List of remaining subtasks

    Example:
        mark_subtask_complete("TK-01", "subtask-1")
        # Returns progress update showing 1/5 subtasks complete (20%)
    """
    pass  # Implementation handled by decorator


@app.tool()
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
        task_id (str): The unique identifier for the task (e.g., "TK-01", "PROJ-123")

    Returns:
        ToolResponse: Contains success/error status and implementation guidance

    Example:
        implement_task("TK-01") -> Starts implementation of planned task
    """
    handler = get_tool_handler(ToolName.IMPLEMENT_TASK)
    return await handler.execute(task_id)


# Register with tool registry
register_tool_from_definition(app, ToolName.IMPLEMENT_TASK)


@app.tool()
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
    handler = get_tool_handler(ToolName.REVIEW_TASK)
    return await handler.execute(task_id)


# Register with tool registry
register_tool_from_definition(app, ToolName.REVIEW_TASK)


@app.tool()
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
    handler = get_tool_handler(ToolName.TEST_TASK)
    return await handler.execute(task_id)


# Register with tool registry
register_tool_from_definition(app, ToolName.TEST_TASK)


@app.tool()
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
    handler = get_tool_handler(ToolName.FINALIZE_TASK)
    return await handler.execute(task_id)


# Register with tool registry
register_tool_from_definition(app, ToolName.FINALIZE_TASK)


@app.tool()
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
    handler = get_tool_handler(ToolName.APPROVE_AND_ADVANCE)
    return await handler.execute(task_id=task_id)


if __name__ == "__main__":
    app.run()

``````
------ src/alfred/state/__init__.py ------
``````
"""
State management package.

This package provides the state management infrastructure for Alfred,
including the StateManager for task state persistence.
"""

from alfred.state.manager import StateManager, state_manager

__all__ = ["StateManager", "state_manager"]

``````
------ src/alfred/state/manager.py ------
``````
# src/alfred/state/manager.py
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Dict, TYPE_CHECKING

from alfred.lib.fs_utils import file_lock

if TYPE_CHECKING:
    from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.structured_logger import get_logger
from alfred.models.state import TaskState, WorkflowState
from alfred.models.schemas import TaskStatus
from alfred.config.settings import settings
from pydantic import BaseModel

logger = get_logger(__name__)


class StateManager:
    """
    Simplified state manager with direct methods instead of UoW pattern.

    Each method handles its own locking and atomic writes.
    """

    def _get_task_dir(self, task_id: str) -> Path:
        return settings.workspace_dir / task_id

    def _get_task_state_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / "task_state.json"

    def _get_lock_file(self, task_id: str) -> Path:
        return self._get_task_dir(task_id) / ".state.lock"

    def _atomic_write(self, state: TaskState) -> None:
        """Atomically write state to disk. Assumes lock is already held."""
        state_file = self._get_task_state_file(state.task_id)
        state.updated_at = datetime.now(timezone.utc).isoformat()

        # Ensure directory structure exists
        task_dir = state_file.parent
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create empty scratchpad if it doesn't exist
        scratchpad_path = task_dir / "scratchpad.md"
        if not scratchpad_path.exists():
            scratchpad_path.touch(mode=0o600)

        # Atomic write using temp file
        fd, temp_path_str = tempfile.mkstemp(dir=state_file.parent, prefix=".tmp_state_", suffix=".json")
        temp_path = Path(temp_path_str)

        try:
            with os.fdopen(fd, "w") as f:
                f.write(state.model_dump_json(indent=2))
            os.replace(temp_path, state_file)
            logger.debug("Atomically wrote state", task_id=state.task_id)
        except Exception:
            if temp_path.exists():
                os.remove(temp_path)
            raise

    def load_or_create(self, task_id: str) -> TaskState:
        """Load task state from disk, creating if it doesn't exist."""
        state_file = self._get_task_state_file(task_id)

        if not state_file.exists():
            logger.info("No state file found, creating new state", task_id=task_id)
            return TaskState(task_id=task_id)

        try:
            with state_file.open("r") as f:
                data = json.load(f)
            return TaskState.model_validate(data)
        except Exception as e:
            logger.error("Failed to load or validate state, creating new", task_id=task_id, error=str(e))
            return TaskState(task_id=task_id)

    # Backward compatibility alias
    def load_or_create_task_state(self, task_id: str) -> TaskState:
        """Alias for backward compatibility."""
        return self.load_or_create(task_id)

    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        """Update task status with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            old_status = state.task_status
            state.task_status = new_status
            self._atomic_write(state)

        logger.info("Updated task status", task_id=task_id, old_status=old_status.value, new_status=new_status.value)

        # Update scratchpad to reflect the new status
        from alfred.lib.turn_manager import turn_manager

        try:
            turn_manager.generate_scratchpad(task_id)
            logger.debug("Updated scratchpad after status change", task_id=task_id, new_status=new_status.value)
        except Exception as e:
            logger.error("Failed to update scratchpad after status change", task_id=task_id, error=str(e))

    def update_tool_state(self, task_id: str, tool: Any) -> None:
        """Update tool state with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)

            # Serialize context store
            serializable_context = {}
            for key, value in tool.context_store.items():
                if isinstance(value, BaseModel):
                    serializable_context[key] = value.model_dump()
                else:
                    serializable_context[key] = value

            # Create workflow state
            tool_state = WorkflowState(task_id=task_id, tool_name=tool.tool_name, current_state=str(tool.state), context_store=serializable_context)

            state.active_tool_state = tool_state
            self._atomic_write(state)

        logger.debug("Updated tool state", task_id=task_id, tool_name=tool.tool_name)

    def clear_tool_state(self, task_id: str) -> None:
        """Clear active tool state with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            state.active_tool_state = None
            self._atomic_write(state)

        logger.info("Cleared tool state", task_id=task_id)

    def add_completed_output(self, task_id: str, tool_name: str, artifact: Any) -> None:
        """Add completed tool output with proper locking."""
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)

            # Serialize artifact
            if isinstance(artifact, BaseModel):
                serializable_artifact = artifact.model_dump()
            else:
                serializable_artifact = artifact

            state.completed_tool_outputs[tool_name] = serializable_artifact
            self._atomic_write(state)

        logger.info("Added completed output", task_id=task_id, tool_name=tool_name)

    @contextmanager
    def complex_update(self, task_id: str):
        """
        Context manager for complex updates that need multiple field changes.

        This is only needed when you need to update multiple fields atomically.
        For single field updates, use the direct methods above.

        Example:
            with state_manager.complex_update(task_id) as state:
                state.task_status = TaskStatus.IN_PROGRESS
                state.active_tool_state = tool_state
                # Changes are automatically saved on context exit
        """
        with file_lock(self._get_lock_file(task_id)):
            state = self.load_or_create(task_id)
            original_data = state.model_dump_json()

            try:
                yield state
                # Only write if state actually changed
                if state.model_dump_json() != original_data:
                    self._atomic_write(state)
                    logger.debug("Complex update completed", task_id=task_id)
            except Exception as e:
                logger.error("Complex update failed", task_id=task_id, error=str(e), exc_info=True)
                raise

    def get_archive_path(self, task_id: str) -> Path:
        """Get the archive directory path for a task."""
        from alfred.constants import Paths

        archive_path = self._get_task_dir(task_id) / Paths.ARCHIVE_DIR
        archive_path.mkdir(parents=True, exist_ok=True)
        return archive_path

    def register_tool(self, task_id: str, tool: "BaseWorkflowTool") -> None:
        """Register a tool with the orchestrator and update state."""
        from alfred.orchestration.orchestrator import orchestrator

        orchestrator.active_tools[task_id] = tool
        self.update_tool_state(task_id, tool)
        logger.info("Registered tool", task_id=task_id, tool_name=tool.tool_name)


# Singleton instance
state_manager = StateManager()

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

from alfred.models.schemas import Task, ToolResponse


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

from alfred.models.alfred_config import TaskProvider as ProviderType
from alfred.lib.structured_logger import get_logger
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
    from alfred.orchestration.orchestrator import orchestrator

    try:
        # Load the current configuration
        config = orchestrator.config_manager.load()
        provider_type = config.provider.type

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

from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.lib.structured_logger import get_logger
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
            task_id: The Jira issue key (e.g., "TK-01")

        Returns:
            Task object if found, None otherwise
        """
        # Placeholder implementation - return hardcoded task for testing
        if task_id == "TK-01":
            logger.info(f"Returning placeholder Jira task for {task_id}")
            return Task(
                task_id="TK-01",
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

from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.lib.md_parser import MarkdownTaskParser
from alfred.lib.structured_logger import get_logger
from alfred.config.settings import settings
from alfred.state.manager import state_manager
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

    def get_task_with_error_details(self, task_id: str) -> tuple[Optional[Task], Optional[str]]:
        """Fetches the details for a single task with detailed error information.

        Args:
            task_id: The unique identifier for the task

        Returns:
            Tuple of (Task object if found or None, error message if failed or None)
        """
        task_md_path = self.tasks_dir / f"{task_id}.md"

        if not task_md_path.exists():
            # Read the template content to show the user
            template_path = Path(__file__).parent.parent / "templates" / "task_template.md"
            template_content = ""
            if template_path.exists():
                template_content = template_path.read_text()
                # Replace the sample task ID with the requested one
                template_content = template_content.replace("SAMPLE-001", task_id)

            error_msg = f"Task '{task_id}' doesn't exist.\n\n"
            error_msg += f"To create it, save this content as:\n{task_md_path}\n\n"
            error_msg += f"--- TEMPLATE ---\n{template_content}\n--- END TEMPLATE ---"
            return None, error_msg

        try:
            # Read and validate the markdown file
            content = task_md_path.read_text()

            # Validate format first
            is_valid, error_msg = self.parser.validate_format(content)
            if not is_valid:
                # Read the template content to show the user
                template_path = Path(__file__).parent.parent / "templates" / "task_template.md"
                template_content = ""
                if template_path.exists():
                    template_content = template_path.read_text()
                    # Replace the sample task ID with the requested one
                    template_content = template_content.replace("SAMPLE-001", task_id)

                detailed_error = f"Task file has invalid format: {error_msg}\n\n"
                detailed_error += f"File location: {task_md_path}\n\n"
                detailed_error += f"Expected format:\n"
                detailed_error += f"--- TEMPLATE ---\n{template_content}\n--- END TEMPLATE ---"
                return None, detailed_error

            # Parse the markdown file
            task_data = self.parser.parse(content)

            # Validate required fields and provide helpful error if missing
            if not task_data.get("task_id"):
                error_msg = f"Task file is missing task_id.\n\n"
                error_msg += f"Expected format: '# TASK: {task_id}'\n"
                error_msg += f"Current first line: {content.split('\\n')[0] if content else 'Empty file'}\n"
                error_msg += f"File location: {task_md_path}"
                return None, error_msg

            task_model = Task(**task_data)

            # Load and merge the dynamic state
            task_state = state_manager.load_or_create(task_id)
            task_model.task_status = task_state.task_status

            return task_model, None
        except ValueError as e:
            detailed_error = f"Task file has invalid format: {e}\n\n"
            detailed_error += f"File location: {task_md_path}\n"
            detailed_error += f"Template reference: src/alfred/templates/task_template.md"
            return None, detailed_error
        except Exception as e:
            error_msg = f"Failed to load task {task_id} from {task_md_path}: {e}"
            return None, error_msg

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
------ src/alfred/templates/prompts/create_tasks_from_spec/create_tasks_from_spec.md ------
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
    "task_id": "TK-XX", // You will generate this, starting from the next available number.
    "title": "Clear, concise title for the task.",
    "priority": "critical | high | medium | low",
    "dependencies": ["TK-YY", "TK-ZZ"], // List of task_ids this task depends on.
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
------ src/alfred/templates/prompts/create_tasks_from_spec/drafting_tasks.md ------
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
------ src/alfred/templates/prompts/create_tasks_from_spec/drafting_tasks_initial.md ------
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
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Create a git commit and pull request for the completed implementation.

# BACKGROUND
The implementation has been completed and tested. Now create the final commit and pull request to complete the task workflow.

# INSTRUCTIONS
1. Create a descriptive git commit with all changes
2. Push the changes to a new branch or existing feature branch
3. Create a pull request with proper description
4. Capture the actual commit hash and PR URL

# CONSTRAINTS
- Use descriptive commit messages following project standards
- Include the task ID in commit message and PR title
- Ensure all changes are committed before creating PR

# OUTPUT
Create a FinalizeArtifact with these exact fields:
- **commit_hash**: The actual git SHA hash of the created commit
- **pr_url**: The actual URL of the created pull request

**Required Action:** Call `alfred.submit_work` with a `FinalizeArtifact`

# EXAMPLES
```json
{
  "commit_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "pr_url": "https://github.com/user/repo/pull/123"
}
```

```json
{
  "commit_hash": "f9e8d7c6b5a4958372615048392817465029384756",
  "pr_url": "https://github.com/myorg/myproject/pull/456"
}
```
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
5. **IMPORTANT**: Only after ALL subtasks show 100% completion, create your implementation manifest
6. Submit the final manifest ONLY when you see the message "All X subtasks are now finished!"

# CONSTRAINTS
- Follow the execution plan precisely
- Each subtask must be fully completed before moving to the next
- Maintain code quality and follow project conventions
- Ensure all tests pass before marking subtasks complete

# OUTPUT
When all subtasks are complete, create an ImplementationManifestArtifact with:
- `summary`: Brief summary of what was implemented
- `completed_subtasks`: List of completed subtask IDs (must match ALL planned subtasks)
- `testing_notes`: Any notes about testing or validation

**Required Action:** Call `alfred.submit_work` with your `ImplementationManifestArtifact`

**Warning**: If you submit before completing all subtasks, you'll get an error showing completion percentage and missing subtasks.
``````
------ src/alfred/templates/prompts/plan_task/clarification.md ------
``````
<!--
Template: plan_task.clarification
Purpose: Get answers to discovery questions
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - discovery_findings: Flattened findings from discovery
  - discovery_questions: Flattened questions from discovery
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Get answers to the questions discovered during exploration.

# DISCOVERY SUMMARY
${discovery_findings}

# QUESTIONS TO CLARIFY
${discovery_questions}

# INSTRUCTIONS
1. Present each question with its full context from discovery
2. Have a natural, multi-turn conversation with the human
3. **IMPORTANT: Track your progress internally** - humans may answer only some questions at a time:
   - Keep a mental list of which questions have been answered
   - Which questions remain unanswered
   - If human skips questions or only partially answers, acknowledge what you learned and continue asking the remaining questions
   - Do NOT submit work until ALL questions are resolved
4. Be conversational - ask follow-ups, seek clarification, ensure you truly understand
5. Document the entire dialogue in markdown format
6. Extract key decisions and new constraints discovered

# OUTPUT
Submit a simple artifact with:
- **clarification_dialogue**: Markdown Q&A conversation
- **decisions**: List of key decisions
- **additional_constraints**: Any new requirements discovered

## Example
```json
{
  "clarification_dialogue": "## Clarification Discussion\n\n**AI**: I found 3 ambiguities during discovery. Let me ask about each:\n\n1. Should priority be required or optional with default?\n2. Where does priority rank in the task selection algorithm?\n3. Should we migrate existing tasks or handle missing priority?\n\n**Human**: Make it optional with MEDIUM default. We have existing tasks.\n\n**AI**: Thank you! That answers questions 1 and 3. For question 2, where should priority rank in the selection algorithm?\n\n**Human**: After in-progress status but before ready status.\n\n**AI**: Perfect! All questions are now answered. Let me summarize what I've learned...",
  
  "decisions": [
    "Priority will be optional with default=MEDIUM",
    "Priority ranks second in algorithm after in-progress"
  ],
  
  "additional_constraints": [
    "Must maintain backward compatibility",
    "No migration needed for existing tasks"
  ]
}
```

**CRITICAL**: Only call `alfred.submit_work` when ALL questions have been answered. If any questions remain, continue the conversation.

``````
------ src/alfred/templates/prompts/plan_task/clarification_complex.md ------
``````
<!--
Template: plan_task.clarification
Purpose: Conversational clarification of discovered ambiguities
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - context_discovery_artifact: Results from discovery phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Engage in conversational clarification with the human to resolve all discovered ambiguities and gain domain knowledge not available in training data.

# BACKGROUND
Context discovery has been completed and ambiguities have been identified. Now you must engage in real conversation with the human to:
- Resolve all discovered ambiguities with their domain expertise
- Understand business context and decisions not captured in code
- Clarify requirements and expectations
- Gain domain knowledge that will inform the design

**Note**: After clarification, the workflow will automatically determine if this task is simple enough to skip the CONTRACTS phase and proceed directly to implementation planning. This is based on complexity assessment from discovery.

This is a CONVERSATIONAL phase - engage in natural dialogue, ask follow-up questions, and seek clarification until all ambiguities are resolved.

**Discovery Results:**
- Complexity: ${context_discovery_artifact.complexity_assessment}
- Files Affected: ${context_discovery_artifact.relevant_files}
- Ambiguities Found: ${context_discovery_artifact.ambiguities_discovered}

${feedback_section}

# INSTRUCTIONS
1. **Present Ambiguities**: Show each discovered ambiguity with full context from your exploration
2. **Conversational Dialogue**: Engage in natural conversation - ask follow-ups, seek examples, clarify nuances
3. **Domain Knowledge Transfer**: Learn from human expertise about business logic, edge cases, and decisions
4. **Requirement Refinement**: Update and clarify requirements based on conversation
5. **Question Everything Unclear**: Don't make assumptions - if something is unclear, ask
6. **Document Conversation**: Keep track of what you learn for future reference

# CONSTRAINTS
- This is conversational, not just Q&A - engage naturally
- Focus on resolving ambiguities that impact design decisions
- Don't ask implementation details - focus on requirements and approach
- Seek domain knowledge that's not available in the codebase
- Be specific with your questions and provide context

# OUTPUT
Create a ClarificationArtifact with the following structure:

## Schema Documentation

### ResolvedAmbiguity Object
```json
{
  "original_question": "string",      // The question from discovery phase
  "human_response": "string",         // What the human answered
  "clarification": "string",          // Your understanding of the resolution
  "follow_up_questions": ["string"],  // Any follow-up questions you asked
  "final_decision": "string"          // The actionable decision (min 10 chars)
}
```

### RequirementUpdate Object
```json
{
  "original_requirement": "string",   // What the requirement was before
  "updated_requirement": "string",    // What it is now after clarification
  "reason_for_change": "string"       // Why this change was needed
}
```

### ConversationEntry Object
```json
{
  "speaker": "enum",                  // MUST be "AI" or "Human"
  "message": "string",                // The message content
  "timestamp": "string"               // Optional timestamp
}
```

### Complete ClarificationArtifact Structure
```json
{
  "resolved_ambiguities": [           // List of ResolvedAmbiguity objects
    // See ResolvedAmbiguity schema above
  ],
  "updated_requirements": [           // List of RequirementUpdate objects
    // See RequirementUpdate schema above
  ],
  "domain_knowledge_gained": [        // List of key insights (strings)
    "Business rule: Orders over $1000 require manager approval",
    "Edge case: Cancelled orders must retain audit trail for 7 years"
  ],
  "conversation_log": [               // List of ConversationEntry objects
    // See ConversationEntry schema above
  ],
  "business_context": {               // Dict of business decisions
    "key": "Business context that impacts technical approach"
  },
  "additional_constraints": [         // List of new constraints discovered
    "Must integrate with legacy billing system",
    "Response time must be under 200ms"
  ]
}
```

**Required Action:** Call `alfred.submit_work` with a `ClarificationArtifact`

# EXAMPLES

## Complete Example: Resolving Priority Implementation Ambiguity

### Good ResolvedAmbiguity Example
```json
{
  "original_question": "Should priority be a required field or optional with a default value?",
  "human_response": "Make it optional with MEDIUM as default. We have hundreds of existing tasks.",
  "clarification": "Priority will be an optional field defaulting to MEDIUM to maintain backward compatibility with existing tasks",
  "follow_up_questions": [
    "Should existing tasks display as MEDIUM priority or show 'No priority set'?",
    "Do you want a migration script to set all existing tasks to MEDIUM explicitly?"
  ],
  "final_decision": "Priority field will be Optional[TaskPriority] with default=TaskPriority.MEDIUM. Existing tasks will transparently show as MEDIUM priority without migration."
}
```

### Good ConversationEntry Example
```json
{
  "speaker": "AI",
  "message": "I found that the ranking algorithm currently considers: 1) in-progress status, 2) ready status, 3) task age. Where should priority fit in this hierarchy?",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Good RequirementUpdate Example
```json
{
  "original_requirement": "Have the system consider priority when recommending next tasks",
  "updated_requirement": "Priority should be the second factor after in-progress status but before ready status in task recommendations",
  "reason_for_change": "Human clarified that we shouldn't interrupt in-progress work but should respect priority for new task selection"
}
```

### Example Conversation Flow
1. AI: "I discovered two auth systems. Which one needs updating?"
2. Human: "Focus on OAuth2Service, that's our main auth now."
3. AI: "Got it. Should we deprecate LegacyAuthService as part of this?"
4. Human: "No, keep it for now. Some internal tools still use it."
5. AI: "Understood. I'll only modify OAuth2Service and ensure no breaking changes to legacy system."
``````
------ src/alfred/templates/prompts/plan_task/contracts.md ------
``````
<!--
Template: plan_task.contracts
Purpose: Design interfaces and contracts
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Design the interfaces and contracts for this task.

# BACKGROUND
We've discovered the codebase structure and clarified requirements. Now design the interfaces before implementation.

# INSTRUCTIONS
1. Define key interfaces/APIs in markdown
2. List the main contracts being created
3. Note any important design decisions

# OUTPUT
Submit a simple artifact with:
- **interface_design**: Markdown describing interfaces
- **contracts_defined**: List of main contracts
- **design_notes**: Any important notes

## Example
```json
{
  "interface_design": "## Interface Design\n\n### TaskPriority Enum\n- HIGH = 'high'\n- MEDIUM = 'medium'\n- LOW = 'low'\n\n### Task Model\n- priority: Optional[TaskPriority] = MEDIUM\n\n### Parser Updates\n- Parse '## Priority' section\n- Case-insensitive\n\n### Ranking Algorithm\n- New tuple: (in_progress, priority, ready, age)",
  
  "contracts_defined": [
    "TaskPriority enum with 3 levels",
    "Task.priority optional field",
    "Parser handles Priority section",
    "Ranking considers priority score"
  ],
  
  "design_notes": [
    "Backward compatible via default value",
    "No migration needed"
  ]
}
```

**Action**: Call `alfred.submit_work` with interface design
``````
------ src/alfred/templates/prompts/plan_task/contracts_complex.md ------
``````
<!--
Template: plan_task.contracts
Purpose: Interface-first design of all APIs and contracts
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - context_discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Design all interfaces, method signatures, data models, and contracts before any implementation details. This is contract-first design.

# BACKGROUND
Context has been discovered and ambiguities resolved. Now you must design the complete interface layer:
- Method signatures with exact parameters and return types
- Data models with validation and relationships
- API contracts for external interfaces
- Integration contracts for component interactions
- Error handling strategies and exception types

This is ARCHITECTURAL design - focus on WHAT interfaces exist and HOW they interact, not implementation details.

**Previous Phase Results:**
- Discovery: ${context_discovery_artifact}
- Clarifications: ${clarification_artifact}

${feedback_section}

# INSTRUCTIONS
1. **Method Contract Design**: Define all new methods with exact signatures, parameters, return types, and error conditions
2. **Data Model Specification**: Create or update data structures, validation rules, and relationships
3. **API Contract Definition**: Specify external interfaces, request/response schemas, and error responses
4. **Integration Contracts**: Define how components will interact, dependencies, and communication patterns
5. **Error Handling Strategy**: Design exception types, error codes, and recovery patterns
6. **Testing Interface Design**: Consider how each contract will be tested and validated

# CONSTRAINTS
- Focus on interfaces and contracts, not implementation
- Follow existing patterns discovered in codebase exploration
- Ensure all contracts are testable and verifiable
- Consider error cases and edge conditions
- Design for the requirements clarified in previous phase

# OUTPUT
Create a ContractDesignArtifact with:
- `method_contracts`: All method signatures with specifications
- `data_models`: Data structure definitions and validation rules
- `api_contracts`: External interface specifications
- `integration_contracts`: Component interaction specifications
- `error_handling_strategy`: Exception types and error patterns

**Required Action:** Call `alfred.submit_work` with a `ContractDesignArtifact`

# EXAMPLES
Good method contract:
```
class_name: "UserAuthService"
method_name: "authenticate"
signature: "authenticate(email: str, password: str) -> AuthResult"
purpose: "Authenticate user credentials and return auth result"
error_handling: ["ValidationError for invalid input", "AuthenticationError for failed auth"]
test_approach: "Unit tests with mock credentials, integration tests with test users"
```

Good data model:
```
name: "AuthResult"
fields: [{"name": "user", "type": "User", "required": true}, {"name": "token", "type": "str", "required": true}]
validation_rules: [{"field": "token", "rule": "JWT format validation"}]
relationships: [{"field": "user", "references": "User model"}]
```
``````
------ src/alfred/templates/prompts/plan_task/discovery.md ------
``````
<!--
Template: plan_task.discovery
Purpose: Explore codebase and discover what needs to be done
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Explore the codebase to understand what needs to be done for this task.

# TASK REQUIREMENTS
**Goal**: ${task_context}

**Implementation Notes**: ${implementation_details}

**Success Criteria**:
${acceptance_criteria}

# INSTRUCTIONS
1. Use Glob/Grep/Read tools to explore relevant code
2. Document what you find in markdown
3. Note any questions you need answered
4. List files that need changes
5. Assess complexity (LOW/MEDIUM/HIGH)

# OUTPUT
Submit a simple artifact with:
- **findings**: Your discoveries in markdown format
- **questions**: List of questions (must end with ?)
- **files_to_modify**: List of file paths
- **complexity**: LOW, MEDIUM, or HIGH
- **implementation_context**: Any code/patterns for later use

## Example
```json
{
  "findings": "## Discovery Results\n\n### Current State\n- Task model is in `schemas.py` with Pydantic\n- Uses string-based enums for JSON compatibility\n- No priority field exists currently\n\n### Patterns Found\n- All enums inherit from (str, Enum)\n- Models use Field() for validation\n- Error handling returns ToolResponse",
  
  "questions": [
    "Should priority be required or optional with default?",
    "Where should priority rank in the recommendation algorithm?"
  ],
  
  "files_to_modify": [
    "src/alfred/models/schemas.py",
    "src/alfred/lib/md_parser.py",
    "src/alfred/task_providers/local_provider.py"
  ],
  
  "complexity": "MEDIUM",
  
  "implementation_context": {
    "enum_pattern": "class TaskStatus(str, Enum):\n    NEW = \"new\"",
    "validation_example": "Field(default=TaskStatus.NEW)"
  }
}
```

**Action**: Call `alfred.submit_work` with your discovery results

``````
------ src/alfred/templates/prompts/plan_task/discovery_complex.md ------
``````
<!--
Template: plan_task.discovery
Purpose: Deep context discovery and codebase exploration
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
  - restart_context: Re-planning context (if any)
  - autonomous_mode: Whether running in autonomous mode
  - autonomous_note: Note about autonomous mode behavior
  - feedback_section: Review feedback (if any)
-->

# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform comprehensive context discovery by exploring the codebase in parallel using all available tools to build deep understanding before planning begins.

# BACKGROUND
You are beginning the discovery phase of planning. This is the foundation phase where you must:
- Use multiple tools simultaneously (Glob, Grep, Read, Task) for parallel exploration
- Understand existing patterns, architectures, and conventions
- Identify all files and components that will be affected
- Discover integration points and dependencies
- Collect ambiguities for later clarification (don't ask questions yet)
- Extract code snippets and context that will be needed for self-contained subtasks

**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}

${autonomous_note}

# INSTRUCTIONS
1. **Parallel Exploration**: Use Glob, Grep, Read, and Task tools simultaneously to explore the codebase
   - **If tool unavailable/fails**: Use available alternatives or provide best-effort analysis based on context
   - **Fallback strategy**: Document what exploration was attempted vs. what succeeded
2. **Pattern Recognition**: Identify existing coding patterns, architectural decisions, and conventions to follow
3. **Impact Analysis**: Map out all files, classes, and methods that will be affected by this task
4. **Dependency Mapping**: Understand how the new functionality will integrate with existing code
5. **Context Extraction**: Gather code snippets, method signatures, and examples that subtasks will need
6. **Ambiguity Collection**: Note questions and unclear requirements (don't ask yet - just collect)
7. **Complexity Assessment**: Determine if this is LOW/MEDIUM/HIGH complexity based on scope
8. **Tool Error Handling**: If exploration tools fail, document limitations and proceed with available information

# CONSTRAINTS
- Use multiple tools in parallel for maximum efficiency
- Focus on understanding, not designing solutions yet
- Collect ambiguities for later clarification phase
- Extract sufficient context for completely self-contained subtasks
- Follow existing codebase patterns and conventions

# OUTPUT
Create a ContextDiscoveryArtifact with the following structure:

## Schema Documentation

### CodePattern Object
```json
{
  "pattern_type": "string",        // e.g., "error_handling", "validation", "service_pattern"
  "example_code": "string",        // Actual code snippet showing the pattern
  "usage_context": "string",       // When/how this pattern is used
  "file_locations": ["string"]     // List of file paths where pattern is found
}
```

### IntegrationPoint Object
```json
{
  "component_name": "string",      // Name of component to integrate with
  "integration_type": "enum",      // MUST be one of the following values:
    // External integrations:
    // - "API_ENDPOINT"           // For REST API endpoints
    // - "DATABASE"               // For database operations
    // - "SERVICE_CALL"           // For service-to-service calls
    // - "FILE_SYSTEM"            // For file system operations
    // - "EXTERNAL_API"           // For third-party API calls
    
    // Code structure integrations:
    // - "DATA_MODEL_EXTENSION"   // Adding fields to existing models
    // - "PARSER_EXTENSION"       // Extending parser functionality
    // - "ALGORITHM_MODIFICATION" // Modifying existing algorithms
    // - "TEMPLATE_ADDITION"      // Adding new templates
    // - "CLASS_INHERITANCE"      // Inheriting from existing classes
    // - "INTERFACE_IMPLEMENTATION" // Implementing interfaces
    // - "METHOD_OVERRIDE"        // Overriding existing methods
    // - "CONFIGURATION_UPDATE"   // Updating configuration
    // - "WORKFLOW_EXTENSION"     // Extending workflow states
    // - "STATE_MACHINE_UPDATE"   // Updating state machines
    
  "interface_signature": "string", // Method signature or API endpoint
  "dependencies": ["string"],      // List of required dependencies
  "examples": ["string"]          // List of usage examples (MUST be array!)
}
```

### AmbiguityItem Object
```json
{
  "question": "string",           // MUST end with "?" and be specific
  "context": "string",            // Code/context related to ambiguity
  "impact_if_wrong": "string",    // Consequences of wrong assumption
  "discovery_source": "string"    // Where this was discovered
}
```

### Complete ContextDiscoveryArtifact Structure
```json
{
  "codebase_understanding": {     // Free-form dict with your findings
    "any_key": "any_value"        // Document what you discovered
  },
  "code_patterns": [              // List of CodePattern objects
    // See CodePattern schema above
  ],
  "integration_points": [         // List of IntegrationPoint objects
    // See IntegrationPoint schema above - USE VALID ENUM VALUES!
  ],
  "relevant_files": [             // Simple list of file paths
    "src/file1.py",
    "src/file2.py"
  ],
  "existing_components": {        // Dict mapping names to purposes
    "ComponentName": "What it does"
  },
  "ambiguities_discovered": [     // List of AmbiguityItem objects
    // See AmbiguityItem schema above
  ],
  "extracted_context": {          // Free-form dict with code snippets
    "any_key": "any_value"        // Include reusable code/patterns
  },
  "complexity_assessment": "enum", // MUST be: "LOW", "MEDIUM", or "HIGH"
  "discovery_notes": [            // List of strings
    "Note about what was discovered",
    "Note about tool limitations"
  ]
}
```

**Required Action:** Call `alfred.submit_work` with a `ContextDiscoveryArtifact`

# EXAMPLES

## Complete Example: Adding Priority Field to Task Model

### Good IntegrationPoint Example (CORRECT)
```json
{
  "component_name": "Task Model",
  "integration_type": "DATA_MODEL_EXTENSION",  // Valid enum value!
  "interface_signature": "Task(**task_data)",
  "dependencies": ["pydantic.BaseModel", "TaskPriority enum"],
  "examples": [                                // Array format required!
    "Add priority field with TaskPriority type",
    "Set default value to TaskPriority.MEDIUM"
  ]
}
```

### Bad IntegrationPoint Example (WRONG)
```json
{
  "component_name": "Task Model",
  "integration_type": "data_model",            // WRONG: Not a valid enum
  "interface_signature": "Task(**task_data)",
  "dependencies": ["pydantic.BaseModel"],
  "examples": "Add priority field"             // WRONG: Must be array!
}
```

### Good CodePattern Example
```json
{
  "pattern_type": "enum_definition",
  "example_code": "class TaskStatus(str, Enum):\n    NEW = \"new\"\n    PLANNING = \"planning\"\n    DONE = \"done\"",
  "usage_context": "String-based enums for JSON serialization compatibility",
  "file_locations": ["src/alfred/models/schemas.py:20-39"]
}
```

### Good AmbiguityItem Example
```json
{
  "question": "Should priority be required or optional with a default value?",
  "context": "Task model could enforce priority as required, but this breaks existing tasks. Optional with default=MEDIUM maintains compatibility.",
  "impact_if_wrong": "If required: All existing tasks fail to load. If optional: Smooth migration.",
  "discovery_source": "Analysis of Task model and existing task files"
}
```

### Common Integration Types by Use Case
- Extending a parser? Use `"PARSER_EXTENSION"`
- Adding model fields? Use `"DATA_MODEL_EXTENSION"`
- Modifying algorithms? Use `"ALGORITHM_MODIFICATION"`
- Overriding methods? Use `"METHOD_OVERRIDE"`
- Adding templates? Use `"TEMPLATE_ADDITION"`
- Updating configs? Use `"CONFIGURATION_UPDATE"`
``````
------ src/alfred/templates/prompts/plan_task/implementation_plan.md ------
``````
<!--
Template: plan_task.implementation_plan
Purpose: Create implementation plan
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - contracts_artifact: Results from contracts phase (if available)
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Create a detailed implementation plan with clear subtasks.

# BACKGROUND
We've explored the codebase, clarified requirements, and designed interfaces. Now create the implementation roadmap.

# INSTRUCTIONS

## For Simple Tasks (1-2 subtasks):
1. Break down the work into clear, self-contained subtasks
2. Write implementation steps in markdown overview
3. For each subtask, use structured description format (see below)
4. Identify any risks or concerns

## For Complex Tasks (3+ subtasks or HIGH complexity):
Use parallel sub-agents for deeper, more thorough specifications:

1. Create a high-level outline with subtask IDs and titles
2. For EACH subtask, call the Task tool in parallel (CRITICAL: You MUST launch ALL Task tools in a SINGLE message to achieve true parallelism - do NOT call them sequentially):
   ```
   Task(
     description="Create detailed spec for ST-001: [subtask title]",
     prompt='''You are a specialist focused on creating a complete specification for ONE subtask.

CONTEXT: Working on ST-001 - [subtask title]

CONTEXT FROM DISCOVERY:
[Include relevant discovery findings for this subtask]

KEY DECISIONS:
[Include relevant decisions from clarification]

YOUR MISSION: Create an exhaustive specification in this format:

**Goal**: [One line describing what to achieve]

**Location**: `path/to/file.py` → `ClassName` or `function_name`

**Methods to Implement**:
- [ ] `method_name(params) -> ReturnType`
- [ ] [List all methods with exact signatures]

**Dependencies**:
- [Other subtask dependencies]
- [External package dependencies]

**Implementation Steps**:
1. [Detailed step-by-step guide]
2. [Include specific patterns to follow]
3. [Reference decisions and discoveries]

**Testing Requirements**:
- File: `tests/path/to/test_file.py`
- [Specific test cases needed]
- [Mocks required]

**Verification**:
- [ ] [Checklist of completion criteria]
- [ ] [How to verify integration with other subtasks]
'''
   )
   ```
3. Execute all Task calls IN PARALLEL for maximum speed
4. Collect and validate all specifications
5. Submit the combined result as your artifact

This ensures each subtask gets focused, deep attention while maintaining speed through parallelism.

# OUTPUT
Submit a simple artifact with:
- **implementation_plan**: Markdown overview of the implementation approach
- **subtasks**: List of subtask objects with `subtask_id` and structured `description`
- **risks**: Potential risks or concerns

## Subtask Description Format
Each subtask description should use this structured markdown format:

```
**Goal**: One line describing what to achieve

**Location**: `path/to/file.py` → `ClassName` or `function_name`

**Approach**:
- Key implementation steps
- Reference patterns: "Follow pattern in `file.py:ClassName`"
- Reference decisions: "Per decision: use X approach [CLARIFICATION]"
- Reference discoveries: "Integration point: `file.py:method` [DISCOVERY]"

**Verify**: How to know it's done (test approach or verification steps)
```

Keep each subtask description concise (under 10 lines).
For 5+ subtasks, be increasingly brief.
Reference discoveries, decisions, and patterns rather than copying code.

## Example for Simple Task (1-2 subtasks)
```json
{
  "implementation_plan": "## Implementation Plan\n\n### Overview\nAdd task priority support in three phases:\n1. Extend Task model with priority field\n2. Update parser to handle Priority sections\n3. Integrate priority into task ranking algorithm\n\n### Key Decisions from Planning\n- Priority is optional with MEDIUM default\n- No migration needed for existing tasks\n- Priority ranks after status but before age",
  
  "subtasks": [
    {
      "subtask_id": "ST-001",
      "description": "**Goal**: Add priority field to Task model\n\n**Location**: `src/alfred/models/schemas.py` → `Task` class\n\n**Approach**:\n- Create TaskPriority enum (pattern: see TaskStatus in same file)\n- Add field: `priority: Optional[TaskPriority] = Field(default=TaskPriority.MEDIUM)`\n- Per decision: \"Priority optional with MEDIUM default\" [CLARIFICATION]\n\n**Verify**: Existing tasks load without error, new tasks get MEDIUM by default"
    },
    {
      "subtask_id": "ST-002", 
      "description": "**Goal**: Add Priority section parser\n\n**Location**: `src/alfred/lib/md_parser.py` → `parse_task` function\n\n**Approach**:\n- Add Priority section parsing after Status section\n- Map string values to TaskPriority enum\n- Handle missing section gracefully (return None)\n- Pattern: follow Status section parsing approach\n\n**Verify**: Can parse '## Priority\\nHIGH' correctly"
    },
    {
      "subtask_id": "ST-003",
      "description": "**Goal**: Update task ranking algorithm\n\n**Location**: `src/alfred/tools/get_next_task.py` → `_calculate_rank` function\n\n**Approach**:\n- Add priority to ranking tuple after status\n- Per decision: \"Priority ranks after in-progress but before ready\" [CLARIFICATION]\n- Integration: Use task.priority.value for numeric comparison\n\n**Verify**: HIGH priority tasks rank above MEDIUM when status equal"
    }
  ],
  
  "risks": [
    "Existing tasks need graceful handling when priority is None",
    "Parser must handle case variations (High, HIGH, high)"
  ]
}
```

## Example for Complex Task (3+ subtasks) using Parallel Sub-Agents

First, create the outline:
```json
{
  "subtask_outline": [
    {"subtask_id": "ST-001", "title": "Create User model and database schema"},
    {"subtask_id": "ST-002", "title": "Implement UserRepository"},
    {"subtask_id": "ST-003", "title": "Create AuthService with JWT"},
    {"subtask_id": "ST-004", "title": "Add authentication middleware"},
    {"subtask_id": "ST-005", "title": "Create login/logout endpoints"}
  ]
}
```

Then launch ALL Task tools IN ONE MESSAGE (for true parallelism):
```
Task(description="Create detailed spec for ST-001: Create User model and database schema", prompt="...")
Task(description="Create detailed spec for ST-002: Implement UserRepository", prompt="...")
Task(description="Create detailed spec for ST-003: Create AuthService with JWT", prompt="...")
Task(description="Create detailed spec for ST-004: Add authentication middleware", prompt="...")
Task(description="Create detailed spec for ST-005: Create login/logout endpoints", prompt="...")
```

After collecting all parallel results:
```json
{
  "implementation_plan": "## Implementation Plan\n\n### Overview\nImplement complete authentication system...",
  
  "subtasks": [
    {
      "subtask_id": "ST-001",
      "description": "[Detailed specification from sub-agent 1]"
    },
    {
      "subtask_id": "ST-002", 
      "description": "[Detailed specification from sub-agent 2]"
    },
    // ... all subtasks with detailed specs from parallel agents
  ],
  
  "risks": [
    "Token security requires careful key management",
    "Database migrations needed for existing users"
  ]
}
```

**Action**: Call `alfred.submit_work` with implementation plan
``````
------ src/alfred/templates/prompts/plan_task/validation.md ------
``````
<!--
Template: plan_task.validation
Purpose: Final plan validation
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - contracts_artifact: Results from contracts phase (if available)
  - implementation_artifact: Results from implementation planning phase
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Validate the complete plan before implementation.

# BACKGROUND
All planning phases are complete. Review the plan end-to-end to ensure it's ready for implementation.

# INSTRUCTIONS
1. Summarize the complete plan
2. Check what validations were performed
3. Identify any remaining issues
4. Confirm if ready for implementation

# OUTPUT
Submit a simple artifact with:
- **validation_summary**: Markdown summary of validation results
- **validations_performed**: List of checks performed
- **issues_found**: Any issues or concerns found
- **ready_for_implementation**: Boolean (true/false)

## Example
```json
{
  "validation_summary": "## Validation Complete\n\nThe plan for adding task priority is comprehensive and ready:\n- Task model changes are backward compatible\n- Parser handles missing Priority section gracefully\n- Ranking algorithm integration is well-designed\n- Test coverage is adequate",
  
  "validations_performed": [
    "Verified all acceptance criteria are covered",
    "Checked backward compatibility approach",
    "Validated interface consistency",
    "Reviewed risk mitigation strategies"
  ],
  
  "issues_found": [],
  
  "ready_for_implementation": true
}
```

**Action**: Call `alfred.submit_work` with validation results
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
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform code review and provide structured feedback on the implementation.

# BACKGROUND
Review the completed implementation for code quality, correctness, and adherence to requirements. The implementation details and acceptance criteria are available for reference.

# INSTRUCTIONS
1. Review the implementation thoroughly
2. Check for code quality, bugs, performance, and security issues
3. Determine if the implementation meets the requirements
4. Provide specific feedback if changes are needed

# CONSTRAINTS
- Be thorough but focus on substantive issues
- Provide actionable feedback if requesting changes
- Base approval decision on code quality and completeness

# OUTPUT
Create a ReviewArtifact with these exact fields:
- **summary**: Overall assessment of the implementation quality
- **approved**: Boolean - true if code passes review, false if changes needed  
- **feedback**: Array of specific feedback strings (empty array if approved)

**Required Action:** Call `alfred.submit_work` with a `ReviewArtifact`

# EXAMPLES
```json
{
  "summary": "Implementation looks good with proper error handling",
  "approved": true,
  "feedback": []
}
```

```json
{
  "summary": "Several issues found that need to be addressed",
  "approved": false,
  "feedback": [
    "Add input validation for user email field",
    "Fix potential null pointer exception in line 45",
    "Add unit tests for error handling scenarios"
  ]
}
```
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
# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Execute tests and report the results in a structured format.

# BACKGROUND
Run the test suite to validate the implementation and capture the complete results. This includes unit tests, integration tests, and any manual validation required.

# INSTRUCTIONS
1. Execute the appropriate test command for this codebase
2. Capture the complete output including any error messages
3. Record the exact command used and exit code
4. Report all results in the required format

# CONSTRAINTS
- Use the standard test command for this project
- Capture the complete output, not just a summary
- Report actual exit codes (0 = success, non-zero = failure)

# OUTPUT
Create a TestResultArtifact with these exact fields:
- **command**: The exact test command that was executed
- **exit_code**: Integer exit code from test execution (0 = success)
- **output**: Complete text output from the test execution

**Required Action:** Call `alfred.submit_work` with a `TestResultArtifact`

# EXAMPLES
```json
{
  "command": "python -m pytest tests/",
  "exit_code": 0,
  "output": "===== test session starts =====\ncollected 15 items\n\ntests/test_auth.py ........\ntests/test_api.py .......\n\n===== 15 passed in 2.34s ====="
}
```

```json
{
  "command": "npm test",
  "exit_code": 1,
  "output": "FAIL src/components/Button.test.js\n  ✓ renders correctly (5ms)\n  ✗ handles click events (12ms)\n\n1 test failed, 1 test passed"
}
```
``````
------ src/alfred/templates/prompts/verified.md ------
``````
# Task Complete

Task `{{ task_id }}` has been successfully completed.

The work has been verified and is ready for the next phase of the workflow.

This is an informational prompt. No further action is required.
``````
------ src/alfred/templates/task_template.md ------
``````
# TASK: SAMPLE-001

## Title
Example task demonstrating the correct format

## Context
This is a sample task file that demonstrates the correct markdown format expected by Alfred. It shows all required and optional sections that can be used when creating tasks.

## Implementation Details
Create a well-formatted markdown file that follows the exact structure expected by the MarkdownTaskParser. The file should include all required sections and demonstrate optional sections as well.

## Acceptance Criteria
- Task file must start with "# TASK: <task_id>" format
- Must include Title, Context, Implementation Details, and Acceptance Criteria sections
- Should follow the exact section headers expected by the parser
- Must be parseable by the MarkdownTaskParser without errors

## AC Verification
- Verify that the md_parser can successfully parse the file
- Confirm all required fields are extracted correctly
- Test that the Task pydantic model can be created from parsed data
- Ensure no validation errors occur during task loading

## Dev Notes
This file serves as both documentation and a working example. When creating new tasks, copy this format and modify the content as needed.
``````
------ src/alfred/tools/__init__.py ------
``````

``````
------ src/alfred/tools/approve_and_advance.py ------
``````
from alfred.state.manager import state_manager
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.tools.workflow_utils import get_phase_info, get_next_status
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
def approve_and_advance_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for approve_and_advance compatible with GenericWorkflowHandler."""
    """Approve current phase and advance to next using centralized workflow config."""
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status

    # Check if there's an active workflow tool with sub-states
    workflow_state = task_state.active_tool_state
    if workflow_state:
        # Check if we're in a sub-state (not a main workflow phase)
        state_value = workflow_state.current_state

        # If the state contains underscores or special suffixes, it's likely a sub-state
        if "_" in state_value or state_value.endswith("awaiting_ai_review") or state_value.endswith("awaiting_human_review"):
            return ToolResponse(
                status="error",
                message=f"Cannot use approve_and_advance while in sub-state '{state_value}'. "
                f"The workflow tool '{workflow_state.tool_name}' has internal states that must be completed first.\n\n"
                f"**Next Action**: Call `alfred.approve_review(task_id='{task_id}')` to continue through the current workflow.\n\n"
                f"**Note**: approve_and_advance is only for moving between major phases (e.g., implementation → review), "
                f"not for approving sub-states within a workflow.",
            )

        # Check if we need to verify completion against known states
        # Import tool definitions to check if tool is complete
        from alfred.tools.tool_definitions import tool_definitions
        
        tool_definition = tool_definitions.get_tool_definition(workflow_state.tool_name)
        if tool_definition:
            # Local import to avoid circular dependency
            from alfred.core.workflow_engine import WorkflowEngine
            engine = WorkflowEngine(tool_definition)
            
            # Check if current state is terminal
            if not engine.is_terminal_state(state_value):
                # Create temporary tool instance to get final work state
                tool_class = tool_definition.tool_class
                temp_tool = tool_class(task_id=task_id)
                final_state = temp_tool.get_final_work_state()
                
                return ToolResponse(
                    status="error",
                    message=f"The workflow tool '{workflow_state.tool_name}' is not complete. "
                    f"Current state: '{state_value}', but needs to reach '{final_state}' before advancing phases. "
                    f"Use 'approve_review' or 'submit_work' to continue through the workflow.",
                )

            # Additional check for specific workflow tools with known sub-states
            if workflow_state.tool_name == "plan_task" and state_value not in ["verified", "validation"]:
                states_remaining = []
                if state_value == "discovery":
                    states_remaining = ["clarification", "contracts", "implementation_plan", "validation"]
                elif state_value == "clarification":
                    states_remaining = ["contracts", "implementation_plan", "validation"]
                elif state_value == "contracts":
                    states_remaining = ["implementation_plan", "validation"]
                elif state_value == "implementation_plan":
                    states_remaining = ["validation"]

                if states_remaining:
                    return ToolResponse(
                        status="error",
                        message=f"Cannot skip planning sub-states. Currently in '{state_value}' but still need to complete: {', '.join(states_remaining)}. "
                        f"Use 'submit_work' to submit artifacts and 'approve_review' to advance through each planning phase.",
                    )

    # Get next status using simplified workflow utilities
    next_status = get_next_status(current_status)
    if not next_status:
        return ToolResponse(status="error", message=f"No next status defined for '{current_status.value}'.")

    # Check if current status is terminal (cannot advance from DONE)
    if current_status == TaskStatus.DONE:
        return ToolResponse(status="error", message=f"Cannot advance from terminal status '{current_status.value}'.")

    # Note: Archiving is no longer needed with turn-based storage system
    # All artifacts are already stored as immutable turns

    # Advance to next status using direct status mapping
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
from alfred.tools.provide_review_logic import provide_review_logic
from alfred.models.schemas import ToolResponse


# New logic function for GenericWorkflowHandler
async def approve_review_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for approve_review compatible with GenericWorkflowHandler."""
    return await provide_review_logic(task_id=task_id, is_approved=True)


# Legacy approve_review_impl function removed - now using approve_review_logic with GenericWorkflowHandler

``````
------ src/alfred/tools/base_tool_handler.py ------
``````
# src/alfred/tools/base_tool_handler.py
from abc import ABC, abstractmethod
from typing import Optional, Type, Any

from alfred.core.prompter import generate_prompt
from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.structured_logger import get_logger, setup_task_logging
from alfred.lib.task_utils import load_task, load_task_with_error_details
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.orchestration.orchestrator import orchestrator
from alfred.state.manager import state_manager
from alfred.tools.registry import tool_registry

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

        task, error_msg = load_task_with_error_details(task_id)
        if not task:
            return ToolResponse(status="error", message=error_msg or f"Task '{task_id}' not found.")

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
        """Legacy tool recovery and creation logic - mostly replaced by stateless pattern."""
        if task_id in orchestrator.active_tools:
            logger.info("Found active tool", task_id=task_id, tool_name=self.tool_name)
            return orchestrator.active_tools[task_id]

        # Note: ToolRecovery has been removed in favor of stateless design
        # This path should not be used with the new GenericWorkflowHandler stateless implementation
        
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

        # Note: This method is deprecated in favor of stateless design
        # New tools should use WorkflowState via StateManager directly
        logger.warning("Using deprecated stateful tool creation path", task_id=task_id, tool_name=self.tool_name)

        logger.info("Created new tool", task_id=task_id, tool_name=self.tool_name)
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
            logger.error("Prompt generation failed", task_id=task.task_id, tool_name=tool_instance.tool_name, error=str(e), exc_info=True)
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
from alfred.models.schemas import ToolResponse
from alfred.constants import ToolName
from alfred.core.workflow import CreateSpecTool
from alfred.models.planning_artifacts import PRDInputArtifact
from alfred.models.engineering_spec import EngineeringSpec
from alfred.state.manager import state_manager


# New logic function for GenericWorkflowHandler
async def create_spec_logic(task_id: str, prd_content: str, **kwargs) -> ToolResponse:
    """Logic function for create_spec compatible with GenericWorkflowHandler."""
    return await create_spec_impl(task_id, prd_content)


# Note: create_spec_impl is still used as it contains workflow-specific logic


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
    from alfred.models.schemas import TaskStatus

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
    from alfred.core.prompter import generate_prompt
    from alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the spec creation phase
        from alfred.models.schemas import Task

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
------ src/alfred/tools/create_task.py ------
``````
"""
Create Task Tool - Standardized task creation within Alfred
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from alfred.lib.structured_logger import get_logger
from alfred.lib.md_parser import MarkdownTaskParser
from alfred.models.schemas import ToolResponse
from alfred.config.settings import settings

logger = get_logger(__name__)

TASK_TEMPLATE = """## Title
Example task demonstrating the correct format

## Context
This is a sample task file that demonstrates the correct markdown format expected by Alfred. It shows all required and optional sections that can be used when creating tasks.

## Implementation Details
Create a well-formatted markdown file that follows the exact structure expected by the MarkdownTaskParser. The file should include all required sections and demonstrate optional sections as well.

## Acceptance Criteria
- Must include Title, Context, Implementation Details, and Acceptance Criteria sections
- Should follow the exact section headers expected by the parser
- Must be parseable by the MarkdownTaskParser without errors

## AC Verification
- Verify that the md_parser can successfully parse the file
- Confirm all required fields are extracted correctly
- Test that the Task pydantic model can be created from parsed data
- Ensure no validation errors occur during task loading

## Dev Notes
This file serves as both documentation and a working example. Task IDs are now automatically generated by Alfred in the format TK-XX."""


# New logic function for GenericWorkflowHandler
def create_task_logic(task_content: str, **kwargs) -> ToolResponse:
    """Logic function for create_task compatible with GenericWorkflowHandler."""
    try:
        # Generate the next task ID
        task_id = generate_next_task_id()

        # Prepend the task ID to the content
        full_task_content = f"# TASK: {task_id}\n\n{task_content.strip()}"

        # Initialize parser
        parser = MarkdownTaskParser()

        # Validate format of the full content
        is_valid, error_msg = parser.validate_format(full_task_content)
        if not is_valid:
            # If validation fails, we need to decrement the counter
            # This is a bit hacky but necessary to maintain consistency
            tasks_dir = Path(settings.alfred_dir) / "tasks"
            counter_file = tasks_dir / "task_counter.json"
            if counter_file.exists():
                with open(counter_file, "r") as f:
                    counter_data = json.load(f)
                counter_data["last_task_number"] -= 1
                with open(counter_file, "w") as f:
                    json.dump(counter_data, f, indent=2)

            return ToolResponse(
                status="error",
                message="Task content format is invalid.",
                data={
                    "validation_error": error_msg,
                    "template": TASK_TEMPLATE,
                    "help": "Your task content must follow the exact template format shown above. Key requirements:\n"
                    "1. Must include sections: Title, Context, Implementation Details, Acceptance Criteria\n"
                    "2. Sections must use '##' headers\n"
                    "3. Content cannot be empty\n"
                    "Note: Task IDs are now automatically generated!",
                },
            )

        # Parse to validate structure
        try:
            parsed_data = parser.parse(full_task_content)
        except Exception as e:
            # Decrement counter on failure
            tasks_dir = Path(settings.alfred_dir) / "tasks"
            counter_file = tasks_dir / "task_counter.json"
            if counter_file.exists():
                with open(counter_file, "r") as f:
                    counter_data = json.load(f)
                counter_data["last_task_number"] -= 1
                with open(counter_file, "w") as f:
                    json.dump(counter_data, f, indent=2)

            return ToolResponse(
                status="error", message="Failed to parse task content.", data={"parse_error": str(e), "template": TASK_TEMPLATE, "help": "Ensure your task content follows the exact template format."}
            )

        # Ensure .alfred/tasks directory exists
        tasks_dir = Path(settings.alfred_dir) / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)

        # Create task file path
        task_file_path = tasks_dir / f"{task_id}.md"

        # Write the task file with the full content including task ID
        task_file_path.write_text(full_task_content, encoding="utf-8")

        logger.info(f"Created new task file: {task_file_path}")

        return ToolResponse(
            status="success",
            message=f"Task '{task_id}' created successfully.",
            data={
                "task_id": task_id,
                "file_path": str(task_file_path),
                "task_title": parsed_data.get("title", ""),
                "next_action": f"Use work_on_task('{task_id}') to start working on this task.",
                "note": "Task ID was automatically generated.",
            },
        )

    except Exception as e:
        logger.error(f"Error creating task: {e}")
        # Decrement counter on any failure
        try:
            tasks_dir = Path(settings.alfred_dir) / "tasks"
            counter_file = tasks_dir / "task_counter.json"
            if counter_file.exists():
                with open(counter_file, "r") as f:
                    counter_data = json.load(f)
                counter_data["last_task_number"] -= 1
                with open(counter_file, "w") as f:
                    json.dump(counter_data, f, indent=2)
        except Exception as counter_err:
            logger.error(f"Failed to decrement counter: {counter_err}")

        return ToolResponse(
            status="error",
            message="An unexpected error occurred while creating the task.",
            data={"error": str(e), "template": TASK_TEMPLATE, "help": "Please check the task content format and try again."},
        )


def generate_next_task_id() -> str:
    """
    Generates the next task ID by reading and incrementing the counter in task_counter.json

    Returns:
        str: The next task ID in format TK-XX
    """
    tasks_dir = Path(settings.alfred_dir) / "tasks"
    counter_file = tasks_dir / "task_counter.json"

    # Ensure directory exists
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # Read current counter or initialize
    if counter_file.exists():
        with open(counter_file, "r") as f:
            counter_data = json.load(f)
    else:
        counter_data = {"last_task_number": 0, "prefix": "TS", "created_at": "2025-07-04", "description": "Tracks the last assigned task number for auto-incrementing task IDs"}

    # Increment counter
    counter_data["last_task_number"] += 1
    next_number = counter_data["last_task_number"]

    # Save updated counter
    with open(counter_file, "w") as f:
        json.dump(counter_data, f, indent=2)

    # Generate task ID with zero-padding
    task_id = f"{counter_data['prefix']}-{next_number:02d}"

    logger.info(f"Generated new task ID: {task_id}")
    return task_id


# Legacy create_task_impl function removed - now using create_task_logic with GenericWorkflowHandler

``````
------ src/alfred/tools/create_tasks_from_spec.py ------
``````
# src/alfred/tools/create_tasks_from_spec.py
from alfred.models.schemas import ToolResponse
from alfred.constants import ToolName
from alfred.core.workflow import CreateTasksTool
from alfred.models.engineering_spec import EngineeringSpec
from alfred.lib.structured_logger import get_logger
from alfred.state.manager import state_manager

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
async def create_tasks_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for create_tasks_from_spec compatible with GenericWorkflowHandler."""
    return await create_tasks_from_spec_impl(task_id)


# Note: create_tasks_from_spec_impl is still used as it contains workflow-specific logic


async def create_tasks_from_spec_impl(task_id: str) -> ToolResponse:
    """
    Creates a list of actionable tasks from a completed engineering specification.

    This is the second tool in the "idea-to-code" pipeline. It takes a completed
    engineering specification and breaks it down into individual Task objects that
    can be tracked, assigned, and implemented independently.

    The tool guides through creating tasks that are:
    - Atomic and focused
    - Properly ordered with dependencies
    - Sized appropriately (1-3 days of work)
    - Complete with acceptance criteria

    Args:
        task_id: The unique identifier for the epic/feature with a completed engineering spec

    Returns:
        ToolResponse containing the first prompt to guide task breakdown

    Preconditions:
        - Engineering specification must be completed (via create_spec)
        - Task status must be "spec_completed"
    """
    # Load the task state
    task_state = state_manager.load_or_create_task_state(task_id)

    from alfred.models.schemas import TaskStatus

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

    # Initialize the create_tasks_from_spec tool
    tool = CreateTasksTool(task_id)

    # Store the technical spec in context
    tool.context_store["technical_spec"] = tech_spec

    # Register the tool
    state_manager.register_tool(task_id, tool)

    # Dispatch immediately to drafting state
    tool.dispatch()
    state_manager.update_tool_state(task_id, tool)

    # Load the drafting prompt with the technical spec
    from alfred.core.prompter import generate_prompt
    from alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the task creation phase
        from alfred.models.schemas import Task

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
"""Finalize task implementation."""

from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName

# Get the handler from factory
finalize_task_handler = get_tool_handler(ToolName.FINALIZE_TASK)


async def finalize_task_impl(task_id: str) -> ToolResponse:
    """Finalize task entry point - handles the completion phase"""
    return await finalize_task_handler.execute(task_id)

``````
------ src/alfred/tools/generic_handler.py ------
``````
"""
Generic workflow handler that replaces all individual tool handlers.
"""

import inspect
from typing import Optional, Any

from alfred.core.workflow import BaseWorkflowTool
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.tools.workflow_config import WorkflowToolConfig
from alfred.state.manager import state_manager
from alfred.core.prompter import generate_prompt
from alfred.lib.structured_logger import get_logger, setup_task_logging
from alfred.lib.task_utils import load_task_with_error_details

logger = get_logger(__name__)


class GenericWorkflowHandler(BaseToolHandler):
    """
    A single, configurable handler that replaces all individual workflow tool handlers.

    This handler uses configuration to determine behavior and operates using the new
    stateless WorkflowEngine pattern, eliminating the need for stateful tool instances.
    """

    def __init__(self, config: WorkflowToolConfig):
        """Initialize with a workflow configuration."""
        super().__init__(
            tool_name=config.tool_name,
            tool_class=config.tool_class,
            required_status=config.required_status,
        )
        self.config = config

    async def execute(self, task_id: str = None, **kwargs: Any) -> ToolResponse:
        """Enhanced execute method supporting both workflow and simple tools."""
        # Simple tool path (tool_class == None)
        if self.config.tool_class is None:
            return await self._execute_simple_tool(task_id=task_id, **kwargs)

        # New stateless workflow path using WorkflowEngine
        return await self._execute_stateless_workflow(task_id, **kwargs)

    async def _execute_simple_tool(self, **kwargs: Any) -> ToolResponse:
        """Execute simple tool via context_loader function."""
        if self.config.context_loader is None:
            return ToolResponse(status="error", message=f"Tool {self.config.tool_name} has no tool_class and no context_loader")

        try:
            # Call the logic function with all arguments
            if inspect.iscoroutinefunction(self.config.context_loader):
                return await self.config.context_loader(**kwargs)
            else:
                return self.config.context_loader(**kwargs)
        except Exception as e:
            logger.error("Simple tool execution failed", tool_name=self.config.tool_name, error=str(e))
            return ToolResponse(status="error", message=f"Tool execution failed: {str(e)}")

    async def _execute_stateless_workflow(self, task_id: str, **kwargs: Any) -> ToolResponse:
        """Execute stateless workflow using WorkflowEngine pattern."""
        setup_task_logging(task_id)

        task, error_msg = load_task_with_error_details(task_id)
        if not task:
            return ToolResponse(status="error", message=error_msg or f"Task '{task_id}' not found.")

        # Load or create task state
        task_state = state_manager.load_or_create(task_id)
        
        # Check required status
        if self.required_status and task.task_status != self.required_status:
            return ToolResponse(
                status="error",
                message=f"Task '{task_id}' has status '{task.task_status.value}'. Tool '{self.tool_name}' requires status to be '{self.required_status.value}'.",
            )

        # Special validation for plan_task
        if self.config.tool_name == "plan_task":
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task.",
                )

        # Get or create workflow state
        workflow_state = self._get_or_create_workflow_state(task_state, task_id)
        
        # Create stateless tool instance for configuration access
        tool_instance = self.config.tool_class(task_id=task_id)
        
        # Setup context and handle dispatch
        setup_response = await self._setup_stateless_tool(workflow_state, tool_instance, task, **kwargs)
        if setup_response:
            return setup_response

        # Generate response using current state
        return self._generate_stateless_response(workflow_state, tool_instance, task)

    def _get_or_create_workflow_state(self, task_state: TaskState, task_id: str) -> WorkflowState:
        """Get or create workflow state for this tool."""
        # Check if we already have an active workflow state for this tool
        if (task_state.active_tool_state and 
            task_state.active_tool_state.tool_name == self.config.tool_name):
            return task_state.active_tool_state
        
        # Create new workflow state (local import to avoid circular dependency)
        from alfred.tools.tool_definitions import tool_definitions
        tool_definition = tool_definitions.get_tool_definition(self.config.tool_name)
        if not tool_definition:
            raise ValueError(f"No tool definition found for {self.config.tool_name}")
        
        initial_state = (tool_definition.initial_state.value 
                        if hasattr(tool_definition.initial_state, 'value')
                        else str(tool_definition.initial_state))
        
        workflow_state = WorkflowState(
            task_id=task_id,
            tool_name=self.config.tool_name,
            current_state=initial_state,
            context_store={}
        )
        
        # Update task state with new workflow state
        task_state.active_tool_state = workflow_state
        state_manager.save_task_state(task_state)
        
        logger.info("Created new workflow state", task_id=task_id, tool_name=self.config.tool_name, state=initial_state)
        return workflow_state

    async def _setup_stateless_tool(self, workflow_state: WorkflowState, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Setup context and handle dispatch using stateless pattern."""
        
        # Load context if configured
        if self.config.context_loader:
            # Load task state for context
            task_state = state_manager.load_or_create(task.task_id)

            try:
                context = self.config.context_loader(task, task_state)
                # Update workflow state context_store with context loader values
                for key, value in context.items():
                    workflow_state.context_store[key] = value
            except ValueError as e:
                # Context loader can raise ValueError for missing dependencies
                return ToolResponse(status="error", message=str(e))
            except Exception as e:
                logger.error("Context loader failed", task_id=task.task_id, tool_name=self.config.tool_name, error=str(e))
                return ToolResponse(status="error", message=f"Failed to load required context for {self.config.tool_name}: {str(e)}")

        # Handle auto-dispatch if configured
        if self.config.dispatch_on_init and workflow_state.current_state == self.config.dispatch_state_attr:
            try:
                # Local import to avoid circular dependency
                from alfred.core.workflow_engine import WorkflowEngine
                
                # Use WorkflowEngine for state transition (local import to avoid circular dependency)
                from alfred.tools.tool_definitions import tool_definitions
                tool_definition = tool_definitions.get_tool_definition(self.config.tool_name)
                engine = WorkflowEngine(tool_definition)
                
                # Execute dispatch transition
                new_state = engine.execute_trigger(workflow_state.current_state, self.config.target_state_method)
                workflow_state.current_state = new_state
                
                # Persist the state change
                task_state = state_manager.load_or_create(task.task_id)
                task_state.active_tool_state = workflow_state
                state_manager.save_task_state(task_state)

                logger.info("Dispatched tool to state", task_id=task.task_id, tool_name=self.config.tool_name, state=new_state)
                
            except Exception as e:
                logger.error("Auto-dispatch failed", task_id=task.task_id, tool_name=self.config.tool_name, error=str(e))
                return ToolResponse(status="error", message=f"Failed to dispatch tool: {str(e)}")

        return None

    def _generate_stateless_response(self, workflow_state: WorkflowState, tool_instance: BaseWorkflowTool, task: Task) -> ToolResponse:
        """Generate response using stateless pattern."""
        try:
            prompt = generate_prompt(
                task_id=task.task_id,
                tool_name=workflow_state.tool_name,
                state=workflow_state.current_state,
                task=task,
                additional_context=workflow_state.context_store.copy(),
            )
            message = f"Initiated tool '{self.config.tool_name}' for task '{task.task_id}'. Current state: {workflow_state.current_state}."
            return ToolResponse(status="success", message=message, next_prompt=prompt)
        except (ValueError, RuntimeError, KeyError) as e:
            # Handle errors from the new prompter
            logger.error("Prompt generation failed", task_id=task.task_id, tool_name=workflow_state.tool_name, error=str(e), exc_info=True)
            return ToolResponse(status="error", message=f"A critical error occurred while preparing the next step: {e}")

    # Legacy methods kept for BaseToolHandler compatibility but not used in stateless path
    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        """Legacy factory method - not used in stateless workflow path."""
        return self.config.tool_class(task_id=task_id)

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Legacy setup method - not used in stateless workflow path."""
        return None

``````
------ src/alfred/tools/get_next_task.py ------
``````
"""Get next task implementation using the task provider factory."""

from alfred.models.schemas import ToolResponse
from alfred.task_providers.factory import get_provider
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
async def get_next_task_logic(**kwargs) -> ToolResponse:
    """Logic function for get_next_task compatible with GenericWorkflowHandler.

    Gets the next recommended task using the configured provider.
    This tool doesn't require a task_id parameter.
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
"""Implement task implementation."""

from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName

# Get the handler from factory
implement_task_handler = get_tool_handler(ToolName.IMPLEMENT_TASK)


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

from pathlib import Path
import shutil

from alfred.config.manager import ConfigManager
from alfred.config.settings import settings
from alfred.constants import ResponseStatus
from alfred.lib.structured_logger import get_logger
from alfred.models.alfred_config import TaskProvider
from alfred.models.schemas import ToolResponse

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
def initialize_project_logic(provider: str | None = None, **kwargs) -> ToolResponse:
    """Logic function for initialize_project compatible with GenericWorkflowHandler."""
    return initialize_project(provider)


# Note: initialize_project function already exists and is the main implementation


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
    return alfred_dir.exists() and (alfred_dir / "config.yml").exists()


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

    # Copy default config file
    _copy_config_file(alfred_dir)

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
    logger.info("Created project directories", extra={"alfred_dir": str(alfred_dir), "component": "initialize", "action": "create_directories"})


def _copy_config_file(alfred_dir: Path) -> None:
    """Copy the default config file."""
    config_file = alfred_dir / settings.config_filename
    shutil.copyfile(settings.packaged_config_file, config_file)
    logger.info("Copied config file", extra={"config_file": str(config_file), "source": str(settings.packaged_config_file), "component": "initialize", "action": "copy_config"})


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
        config.provider.type = TaskProvider.JIRA
        config_manager.save(config)
        _setup_provider_resources("jira", alfred_dir)
        logger.info("Configured Jira provider", extra={"provider": "jira", "alfred_dir": str(alfred_dir), "component": "initialize", "action": "setup_provider"})
        return {"status": ResponseStatus.SUCCESS}
    return {
        "status": ResponseStatus.ERROR,
        "message": "Could not connect to the Atlassian MCP server. Please ensure it is running and accessible.",
    }


def _setup_linear_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup Linear provider with MCP connectivity check."""
    if _validate_mcp_connectivity("linear"):
        config = config_manager.create_default()
        config.provider.type = TaskProvider.LINEAR
        config_manager.save(config)
        _setup_provider_resources("linear", alfred_dir)
        logger.info("Configured Linear provider", extra={"provider": "linear", "alfred_dir": str(alfred_dir), "component": "initialize", "action": "setup_provider"})
        return {"status": ResponseStatus.SUCCESS}
    return {
        "status": ResponseStatus.ERROR,
        "message": "Could not connect to the Linear MCP server. Please ensure it is running and accessible.",
    }


def _setup_local_provider(config_manager: ConfigManager, alfred_dir: Path) -> dict:
    """Setup local provider with tasks inbox and README."""
    # Create configuration
    config = config_manager.create_default()
    config.provider.type = TaskProvider.LOCAL
    config_manager.save(config)

    # Setup provider resources
    _setup_provider_resources("local", alfred_dir)

    logger.info("Configured local provider", extra={"provider": "local", "alfred_dir": str(alfred_dir), "component": "initialize", "action": "setup_provider"})
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
    logger.info("Created provider resources", extra={"provider": provider, "tasks_dir": str(tasks_dir), "readme_path": str(readme_path), "component": "initialize", "action": "setup_resources"})


def _validate_mcp_connectivity(provider: str) -> bool:
    """Check if required MCP tools are available for the given provider.

    This is a placeholder for actual MCP connectivity validation.
    In a production system, this would attempt to call MCP tools
    to verify they are available and responding.
    """
    # TODO: Implement actual MCP tool availability check
    # For now, we'll simulate the check and return True
    logger.info("Simulating MCP connectivity check", extra={"provider": provider, "component": "initialize", "action": "validate_mcp"})
    return True

``````
------ src/alfred/tools/plan_task.py ------
``````
"""Discovery planning tool implementation."""

from typing import Optional, Dict, Any
from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName


async def plan_task_impl(task_id: str, restart_context: Optional[Dict[str, Any]] = None) -> ToolResponse:
    """Implementation logic for the discovery planning tool.

    Args:
        task_id: The unique identifier for the task to plan
        restart_context: Optional context for re-planning scenarios

    Returns:
        ToolResponse with next action guidance
    """
    # Get the handler from factory (uses GenericWorkflowHandler)
    handler = get_tool_handler(ToolName.PLAN_TASK)

    # Execute with restart context if provided
    if restart_context:
        return await handler.execute(task_id=task_id, restart_context=restart_context)
    else:
        return await handler.execute(task_id=task_id)

``````
------ src/alfred/tools/progress.py ------
``````
# src/alfred/tools/progress.py
from typing import Optional, Any

from alfred.core.workflow import BaseWorkflowTool, ImplementTaskTool
from alfred.models.schemas import Task, TaskStatus, ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.constants import ToolName
from alfred.state.manager import state_manager
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class MarkSubtaskCompleteHandler(BaseToolHandler):
    """Handler for the mark_subtask_complete tool using stateless pattern."""

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

    async def execute(self, task_id: str = None, **kwargs: Any) -> ToolResponse:
        """Execute mark_subtask_complete using stateless pattern."""
        from alfred.lib.task_utils import load_task
        
        task = load_task(task_id)
        if not task:
            return ToolResponse(status="error", message=f"Task '{task_id}' not found.")
        
        # Load task state
        task_state = state_manager.load_or_create(task_id)
        
        # Check if we have an active workflow state
        if not task_state.active_tool_state:
            error_msg = f"""No active implementation workflow found for task '{task_id}'. 

**Current Status**: {task.task_status.value}

**Possible Reasons**:
- Implementation phase has already completed
- Task is in a different phase (planning, review, testing, etc.)
- No implementation workflow was started

**What to do**:
- If implementation is complete: Use `alfred.review_task('{task_id}')` to start code review
- If you need to restart implementation: Contact support (this shouldn't happen)
- To see current status: Use `alfred.work_on_task('{task_id}')`

Cannot mark subtask progress without an active implementation workflow."""
            return ToolResponse(status="error", message=error_msg)

        workflow_state = task_state.active_tool_state
        
        # Ensure we are operating on an ImplementTaskTool
        if workflow_state.tool_name != ToolName.IMPLEMENT_TASK:
            return ToolResponse(status="error", message=f"Progress can only be marked during the '{ToolName.IMPLEMENT_TASK}' workflow.")

        # Execute the core logic
        return await self._execute_subtask_complete(task, task_state, workflow_state, **kwargs)

    async def _execute_subtask_complete(self, task: Task, task_state: TaskState, workflow_state: WorkflowState, **kwargs: Any) -> ToolResponse:
        """Core logic for marking subtask complete using stateless pattern."""
        subtask_id = kwargs.get("subtask_id")
        if not subtask_id:
            return ToolResponse(status="error", message="`subtask_id` is a required argument.")

        # Optional: Enforce task status validation
        if task.task_status != TaskStatus.IN_DEVELOPMENT:
            return ToolResponse(status="error", message=f"Task '{task.task_id}' has status '{task.task_status.value}'. Progress can only be marked for tasks in 'in_development' status.")

        # Validate subtask_id against the plan
        execution_plan = workflow_state.context_store.get("artifact_content", {}).get("subtasks", [])
        valid_subtask_ids = {st["subtask_id"] for st in execution_plan}
        if subtask_id not in valid_subtask_ids:
            return ToolResponse(status="error", message=f"Invalid subtask_id '{subtask_id}'. It does not exist in the execution plan.")

        # Update the list of completed subtasks
        completed_subtasks = set(workflow_state.context_store.get("completed_subtasks", []))
        if subtask_id in completed_subtasks:
            return ToolResponse(status="success", message=f"Subtask '{subtask_id}' was already marked as complete.")

        completed_subtasks.add(subtask_id)
        workflow_state.context_store["completed_subtasks"] = sorted(list(completed_subtasks))  # Store sorted for consistency

        # Persist the updated workflow state
        task_state.active_tool_state = workflow_state
        state_manager.save_task_state(task_state)

        # Generate a progress report message
        completed_count = len(completed_subtasks)
        total_count = len(valid_subtask_ids)
        progress = (completed_count / total_count) * 100 if total_count > 0 else 0
        remaining = total_count - completed_count

        # Create an encouraging message based on progress
        if completed_count == total_count:
            message = (
                f"🎉 Excellent! Subtask '{subtask_id}' is complete. All {total_count} subtasks are now finished! "
                f"\n\n**Next Action**: Call `alfred.submit_work` with your ImplementationManifestArtifact to complete the implementation phase."
            )
        elif progress >= 80:
            message = (
                f"Great progress! Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%). "
                f"Almost there - only {remaining} subtask{'s' if remaining > 1 else ''} left!"
            )
        elif progress >= 50:
            message = f"Good work! Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%). You're over halfway done!"
        else:
            message = f"✓ Subtask '{subtask_id}' is complete. Progress: {completed_count}/{total_count} ({progress:.0f}%). Keep going - {remaining} subtasks remaining."

        logger.info(f"Subtask '{subtask_id}' marked complete for task {task.task_id}")

        # This tool does not return a next_prompt, as the AI should continue its work.
        return ToolResponse(status="success", message=message, data={"completed_count": completed_count, "total_count": total_count})

    # Legacy methods for BaseToolHandler compatibility - not used in stateless path
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Legacy setup method - not used in stateless path."""
        return None


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
from alfred.core.prompter import generate_prompt
from alfred.lib.structured_logger import get_logger, cleanup_task_logging
from alfred.lib.task_utils import load_task
from alfred.lib.turn_manager import turn_manager
from alfred.models.schemas import ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.constants import Triggers, ToolName
from alfred.state.manager import state_manager
from alfred.constants import ArtifactKeys
from alfred.config.manager import ConfigManager
from alfred.config.settings import settings

logger = get_logger(__name__)


async def provide_review_logic(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """Provide review logic using stateless WorkflowEngine pattern."""
    
    # Load task and task state
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")
    
    task_state = state_manager.load_or_create(task_id)
    
    # Check if we have an active workflow state
    if not task_state.active_tool_state:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'.")

    workflow_state = task_state.active_tool_state
    current_state = workflow_state.current_state
    
    logger.info("Processing review", task_id=task_id, tool_name=workflow_state.tool_name, state=current_state, approved=is_approved)

    # Get tool definition and engine for state transitions (local import to avoid circular dependency)
    from alfred.tools.tool_definitions import tool_definitions
    tool_definition = tool_definitions.get_tool_definition(workflow_state.tool_name)
    if not tool_definition:
        return ToolResponse(status="error", message=f"No tool definition found for {workflow_state.tool_name}")
    
    # Local import to avoid circular dependency
    from alfred.core.workflow_engine import WorkflowEngine
    engine = WorkflowEngine(tool_definition)

    if not is_approved:
        # Record revision request as a turn
        if feedback_notes:
            state_to_revise = current_state.replace("_awaiting_ai_review", "").replace("_awaiting_human_review", "")
            revision_turn = turn_manager.request_revision(task_id=task_id, state_to_revise=state_to_revise, feedback=feedback_notes, requested_by="human")
            # Store the revision turn number in context for next submission
            workflow_state.context_store["revision_turn_number"] = revision_turn.turn_number

        # Execute revision transition
        try:
            new_state = engine.execute_trigger(current_state, Triggers.REQUEST_REVISION)
            workflow_state.current_state = new_state
        except Exception as e:
            logger.error("Revision transition failed", task_id=task_id, error=str(e))
            return ToolResponse(status="error", message=f"Failed to process revision: {str(e)}")
        
        message = "Revision requested. Returning to previous step."
    else:
        # Clear any previous feedback when approving
        if "feedback_notes" in workflow_state.context_store:
            del workflow_state.context_store["feedback_notes"]

        # Determine the appropriate approval trigger
        if current_state.endswith("_awaiting_ai_review"):
            trigger = Triggers.AI_APPROVE
            message = "AI review approved. Awaiting human review."
            
            try:
                new_state = engine.execute_trigger(current_state, trigger)
                workflow_state.current_state = new_state
                
                # Check for autonomous mode to bypass human review
                try:
                    if ConfigManager(settings.alfred_dir).load().features.autonomous_mode:
                        logger.info("Autonomous mode enabled, bypassing human review", task_id=task_id, tool_name=workflow_state.tool_name)
                        # Execute another transition for human approve
                        new_state = engine.execute_trigger(workflow_state.current_state, Triggers.HUMAN_APPROVE)
                        workflow_state.current_state = new_state
                        message = "AI review approved. Autonomous mode bypassed human review."
                except FileNotFoundError:
                    logger.warning("Config file not found; autonomous mode unchecked.")
                    
            except Exception as e:
                logger.error("AI approval transition failed", task_id=task_id, error=str(e))
                return ToolResponse(status="error", message=f"Failed to process AI approval: {str(e)}")
                
        elif current_state.endswith("_awaiting_human_review"):
            trigger = Triggers.HUMAN_APPROVE
            message = "Human review approved. Proceeding to next step."
            
            try:
                new_state = engine.execute_trigger(current_state, trigger)
                workflow_state.current_state = new_state
            except Exception as e:
                logger.error("Human approval transition failed", task_id=task_id, error=str(e))
                return ToolResponse(status="error", message=f"Failed to process human approval: {str(e)}")
        else:
            return ToolResponse(status="error", message=f"Cannot provide review from non-review state '{current_state}'.")

    # Persist the updated workflow state
    task_state.active_tool_state = workflow_state
    state_manager.save_task_state(task_state)

    # Check if we've reached a terminal state
    is_terminal = engine.is_terminal_state(workflow_state.current_state)
    
    if is_terminal:
        # Handle terminal state completion
        tool_name = workflow_state.tool_name
        
        # Create temporary tool instance to get final work state
        tool_class = tool_definition.tool_class
        temp_tool = tool_class(task_id=task_id)
        final_state = temp_tool.get_final_work_state()
        
        key = ArtifactKeys.get_artifact_key(final_state)
        artifact = workflow_state.context_store.get(key)

        if artifact:
            state_manager.add_completed_output(task_id, tool_name, artifact)
        
        # Clear active tool state
        task_state.active_tool_state = None
        state_manager.save_task_state(task_state)
        
        cleanup_task_logging(task_id)

        # Import here to avoid circular dependency
        from alfred.models.schemas import TaskStatus
        from alfred.tools.workflow_utils import get_next_status

        # Update task status using workflow utilities for direct exit_status mapping
        current_task_status = task.task_status
        next_status = get_next_status(current_task_status)

        if next_status:
            state_manager.update_task_status(task_id, next_status)
            logger.info("Tool completed, status updated", task_id=task_id, tool_name=tool_name, old_status=current_task_status.value, new_status=next_status.value)

            if tool_name == ToolName.PLAN_TASK:
                handoff = f"""The planning workflow has completed successfully!

Task '{task_id}' is now ready for development.

**Next Action:**
Call `alfred.work_on_task(task_id='{task_id}')` to start implementation."""
            else:
                handoff = f"""The '{tool_name}' workflow has completed successfully! 

**Next Actions:**
1. Call `alfred.work_on_task(task_id='{task_id}')` to check the current status and see what phase comes next
2. Then use the suggested tool for the next phase (e.g., `review_task`, `test_task`, etc.)

**Quick Option:** If you're confident and want to skip the status check, call `alfred.approve_and_advance(task_id='{task_id}')` to automatically advance to the next phase.

**Note**: approve_and_advance only works after a workflow is fully complete, not during sub-states."""
        else:
            # Fallback if no next status defined
            handoff = f"""The '{tool_name}' workflow has completed successfully! 

**Next Action:**
Call `alfred.work_on_task(task_id='{task_id}')` to check the current status."""

        return ToolResponse(status="success", message=f"'{tool_name}' completed.", next_prompt=handoff)

    if not is_approved and feedback_notes:
        # Store feedback in the workflow state's context for persistence
        workflow_state.context_store["feedback_notes"] = feedback_notes
        # Persist the updated workflow state with feedback
        task_state.active_tool_state = workflow_state
        state_manager.save_task_state(task_state)

    # Always use the workflow state's context (which now includes feedback if present)
    ctx = workflow_state.context_store.copy()

    prompt = generate_prompt(
        task_id=task.task_id,
        tool_name=workflow_state.tool_name,
        state=workflow_state.current_state,
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

from alfred.core.workflow import BaseWorkflowTool
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.lib.structured_logger import get_logger

# THIS IS THE FIX for Blocker #3
if TYPE_CHECKING:
    from alfred.tools.base_tool_handler import BaseToolHandler

logger = get_logger(__name__)


class DuplicateToolError(Exception):
    """Raised when a tool name is registered more than once."""

    pass


@dataclass(frozen=True)
class ToolConfig:
    """Immutable configuration for a registered tool."""

    name: str
    handler_class: Any  # Can be Type or Callable returning instance
    tool_class: Type[BaseWorkflowTool]
    entry_status_map: Dict[TaskStatus, TaskStatus]
    implementation: Callable[..., Coroutine[Any, Any, ToolResponse]]

    def get_handler(self):
        """Get handler instance, handling both class and instance cases."""
        if callable(self.handler_class):
            return self.handler_class()
        return self.handler_class


class ToolRegistry:
    """Self-registering tool system using decorators."""

    def __init__(self):
        self._tools: Dict[str, ToolConfig] = {}

    def register(
        self,
        name: str,
        handler_class: Any,  # Can be Type or Callable returning instance
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
from alfred.tools.provide_review_logic import provide_review_logic
from alfred.models.schemas import ToolResponse


# New logic function for GenericWorkflowHandler
async def request_revision_logic(task_id: str, feedback_notes: str, **kwargs) -> ToolResponse:
    """Logic function for request_revision compatible with GenericWorkflowHandler."""
    return await provide_review_logic(task_id=task_id, is_approved=False, feedback_notes=feedback_notes)


# Legacy request_revision_impl function removed - now using request_revision_logic with GenericWorkflowHandler

``````
------ src/alfred/tools/review_task.py ------
``````
"""Review task implementation."""

from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName

# Get the handler from factory
review_task_handler = get_tool_handler(ToolName.REVIEW_TASK)


async def review_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the review_task tool."""
    return await review_task_handler.execute(task_id)

``````
------ src/alfred/tools/start_task.py ------
``````
# src/alfred/tools/start_task.py
"""Implementation of the start_task logic."""

from alfred.lib.structured_logger import get_logger
from alfred.lib.task_utils import load_task
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.state.manager import state_manager

logger = get_logger(__name__)


def start_task_impl(task_id: str) -> ToolResponse:
    """
    Simple task start using stateless design.
    
    This function has been simplified to use the stateless workflow pattern.
    The actual workflow management is handled by GenericWorkflowHandler.
    """
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    task_state = state_manager.load_or_create(task_id)
    
    # Check if task is already started
    if task_state.active_tool_state:
        return ToolResponse(
            status="error", 
            message=f"Task '{task_id}' already has an active workflow: {task_state.active_tool_state.tool_name}. "
            f"Use `alfred.work_on_task('{task_id}')` to continue the current workflow."
        )

    # Check task status
    if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
        return ToolResponse(
            status="error",
            message=f"Task '{task_id}' has status '{task.task_status.value}'. "
            f"start_task can only be used on tasks with 'new' or 'planning' status."
        )

    # Note: The actual workflow creation is handled by the tool registry and GenericWorkflowHandler
    # This function just validates that the task can be started
    
    return ToolResponse(
        status="success",
        message=f"Task '{task_id}' is ready to start. Use the appropriate workflow tool to begin.",
        next_prompt=f"Call `alfred.work_on_task('{task_id}')` to begin working on this task."
    )

``````
------ src/alfred/tools/submit_work.py ------
``````
# src/alfred/tools/submit_work.py
from typing import Optional, Any
from pydantic import ValidationError

from alfred.core.prompter import generate_prompt
from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.turn_manager import turn_manager
from alfred.lib.structured_logger import get_logger
from alfred.lib.task_utils import load_task
from alfred.models.schemas import Task, ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.state.manager import state_manager
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


class SubmitWorkHandler(BaseToolHandler):
    """Handler for the generic submit_work tool using stateless WorkflowEngine pattern."""

    def __init__(self):
        super().__init__(
            tool_name="submit_work",  # Not from constants, as it's a generic name
            tool_class=None,
            required_status=None,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        raise NotImplementedError("submit_work does not create new workflow tools.")

    async def execute(self, task_id: str = None, **kwargs: Any) -> ToolResponse:
        """Execute submit_work using stateless WorkflowEngine pattern."""
        task = load_task(task_id)
        if not task:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Task '{task_id}' not found.")

        # Load task state
        task_state = state_manager.load_or_create(task_id)
        
        # Check if we have an active workflow state
        if not task_state.active_tool_state:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

        workflow_state = task_state.active_tool_state
        
        # Execute the submit work logic
        return await self._execute_submit_work(task, task_state, workflow_state, **kwargs)

    async def _execute_submit_work(self, task: Task, task_state: TaskState, workflow_state: WorkflowState, **kwargs: Any) -> ToolResponse:
        """The core logic for submitting an artifact and transitioning state using stateless pattern."""
        artifact = kwargs.get("artifact")
        if artifact is None:
            return ToolResponse(status=ResponseStatus.ERROR, message="`artifact` is a required argument for submit_work.")

        current_state_val = workflow_state.current_state

        # 1. Normalize artifact fields before validation
        normalized_artifact = self._normalize_artifact(artifact)

        # 2. Create stateless tool instance for artifact validation (local import to avoid circular dependency)
        from alfred.tools.tool_definitions import tool_definitions
        tool_definition = tool_definitions.get_tool_definition(workflow_state.tool_name)
        if not tool_definition:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No tool definition found for {workflow_state.tool_name}")
        
        # Create temporary tool instance for artifact_map access
        tool_class = tool_definition.tool_class
        temp_tool = tool_class(task_id=task.task_id)

        # 3. Validate the artifact against the model for the current state
        # Convert state string back to enum for artifact_map lookup
        current_state_enum = None
        for state_enum in temp_tool.artifact_map.keys():
            if (hasattr(state_enum, 'value') and state_enum.value == current_state_val) or str(state_enum) == current_state_val:
                current_state_enum = state_enum
                break

        artifact_model = temp_tool.artifact_map.get(current_state_enum) if current_state_enum else None
        if artifact_model:
            try:
                validated_artifact = artifact_model.model_validate(normalized_artifact)
                logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state_val, model=artifact_model.__name__))

                # Additional validation for ImplementationManifestArtifact
                from alfred.models.planning_artifacts import ImplementationManifestArtifact

                if isinstance(validated_artifact, ImplementationManifestArtifact):
                    # Get the planned subtasks from the execution plan in context_store
                    execution_plan = workflow_state.context_store.get("artifact_content", {})
                    planned_subtasks = [st["subtask_id"] for st in execution_plan.get("subtasks", [])]

                    if planned_subtasks:
                        validation_error = validated_artifact.validate_against_plan(planned_subtasks)
                        if validation_error:
                            return ToolResponse(status=ResponseStatus.ERROR, message=f"Implementation validation failed: {validation_error}")

                        # Log successful validation
                        completed_count = len(validated_artifact.completed_subtasks)
                        total_count = len(planned_subtasks)
                        logger.info(f"Implementation validation passed: {completed_count}/{total_count} subtasks completed")

            except ValidationError as e:
                error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state_val)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
                return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
        else:
            validated_artifact = normalized_artifact  # No model to validate against

        # 4. Store artifact and update context_store
        artifact_key = ArtifactKeys.get_artifact_key(current_state_val)
        workflow_state.context_store[artifact_key] = validated_artifact
        # For review states, we need the artifact as an object, not a string
        workflow_state.context_store[ArtifactKeys.ARTIFACT_CONTENT_KEY] = validated_artifact
        # Store the last state for generic templates
        workflow_state.context_store["last_state"] = current_state_val

        # Use the turn-based storage system
        tool_name = temp_tool.__class__.__name__

        # Check if this is a revision (has revision_turn_number in context)
        revision_of = workflow_state.context_store.get("revision_turn_number")
        revision_feedback = workflow_state.context_store.get("revision_feedback")
        if revision_of:
            # Clear revision context after use so it doesn't persist to next submissions
            del workflow_state.context_store["revision_turn_number"]
            if revision_feedback and "revision_feedback" in workflow_state.context_store:
                del workflow_state.context_store["revision_feedback"]

        # Convert Pydantic models to dict for storage
        if hasattr(validated_artifact, "model_dump"):
            artifact_dict = validated_artifact.model_dump()
        else:
            artifact_dict = validated_artifact if isinstance(validated_artifact, dict) else {"content": str(validated_artifact)}

        turn_manager.append_turn(task_id=task.task_id, state_name=current_state_val, tool_name=tool_name, artifact_data=artifact_dict, revision_of=revision_of, revision_feedback=revision_feedback)

        # Generate human-readable scratchpad from turns
        turn_manager.generate_scratchpad(task.task_id)

        # 5. Use WorkflowEngine for state transition
        trigger_name = Triggers.submit_trigger(current_state_val)
        
        try:
            # Local import to avoid circular dependency
            from alfred.core.workflow_engine import WorkflowEngine
            
            # Create WorkflowEngine and execute transition
            engine = WorkflowEngine(tool_definition)
            
            # Check if transition is valid
            valid_triggers = engine.get_valid_triggers(current_state_val)
            if trigger_name not in valid_triggers:
                return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger_name}' from state '{current_state_val}'.")
            
            # Execute the transition
            new_state = engine.execute_trigger(current_state_val, trigger_name)
            workflow_state.current_state = new_state
            
            logger.info(LogMessages.STATE_TRANSITION.format(task_id=task.task_id, trigger=trigger_name, state=new_state))

        except Exception as e:
            logger.error("State transition failed", task_id=task.task_id, trigger=trigger_name, error=str(e))
            return ToolResponse(status=ResponseStatus.ERROR, message=f"State transition failed: {str(e)}")

        # 6. Persist the new state
        task_state.active_tool_state = workflow_state
        state_manager.save_task_state(task_state)

        # 7. Generate response
        try:
            prompt = generate_prompt(
                task_id=task.task_id,
                tool_name=workflow_state.tool_name,
                state=workflow_state.current_state,
                task=task,
                additional_context=workflow_state.context_store.copy(),
            )
            message = f"Work submitted successfully for task '{task.task_id}'. Transitioned to state: {workflow_state.current_state}."
            return ToolResponse(status=ResponseStatus.SUCCESS, message=message, next_prompt=prompt)
        except Exception as e:
            logger.error("Prompt generation failed", task_id=task.task_id, error=str(e))
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Work submitted but failed to generate next prompt: {str(e)}")

    def _normalize_artifact(self, artifact: dict) -> dict:
        """Normalize artifact fields to handle case-insensitive inputs."""
        if not isinstance(artifact, dict):
            return artifact

        normalized = artifact.copy()

        # Normalize file_breakdown operations (for ContractDesignArtifact and ImplementationPlanArtifact from discovery planning)
        if "file_breakdown" in normalized and isinstance(normalized["file_breakdown"], list):
            for file_change in normalized["file_breakdown"]:
                if isinstance(file_change, dict) and "operation" in file_change:
                    # Normalize operation to uppercase
                    file_change["operation"] = file_change["operation"].upper()

        # Normalize subtasks operations (for ImplementationPlanArtifact)
        if "subtasks" in normalized and isinstance(normalized["subtasks"], list):
            for subtask in normalized["subtasks"]:
                if isinstance(subtask, dict) and "operation" in subtask:
                    # Normalize operation to uppercase
                    subtask["operation"] = subtask["operation"].upper()

        return normalized

    # Legacy methods for BaseToolHandler compatibility - not used in stateless path
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Legacy setup method - not used in stateless path."""
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
"""Test task implementation."""

from alfred.models.schemas import ToolResponse
from alfred.tools.tool_factory import get_tool_handler
from alfred.constants import ToolName

# Get the handler from factory
test_task_handler = get_tool_handler(ToolName.TEST_TASK)


async def test_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the test_task tool."""
    return await test_task_handler.execute(task_id)

``````
------ src/alfred/tools/tool_commands.py ------
``````
"""
Utility commands for tool management.
"""

from typing import List, Dict, Any

from alfred.tools.tool_definitions import TOOL_DEFINITIONS
from alfred.tools.tool_factory import ToolFactory


def list_tools() -> List[Dict[str, Any]]:
    """List all available tools with their information."""
    return [ToolFactory.get_tool_info(name) for name in sorted(TOOL_DEFINITIONS.keys())]


def validate_tools() -> Dict[str, List[str]]:
    """Validate all tool definitions and return any issues."""
    issues = {}

    for name, definition in TOOL_DEFINITIONS.items():
        tool_issues = []

        # Check for common issues
        if not definition.description:
            tool_issues.append("Missing description")

        if definition.work_states and not definition.terminal_state:
            tool_issues.append("Has work states but no terminal state")

        if definition.entry_statuses and not definition.exit_status:
            tool_issues.append("Has entry statuses but no exit status")

        # Try to create handler
        try:
            ToolFactory.create_handler(name)
        except Exception as e:
            tool_issues.append(f"Handler creation failed: {e}")

        if tool_issues:
            issues[name] = tool_issues

    return issues


def generate_tool_documentation() -> str:
    """Generate markdown documentation for all tools."""
    lines = ["# Alfred Tools Documentation\n"]

    for name in sorted(TOOL_DEFINITIONS.keys()):
        definition = TOOL_DEFINITIONS[name]
        info = ToolFactory.get_tool_info(name)

        lines.append(f"## {name}\n")
        lines.append(f"{definition.description}\n")
        lines.append(f"- **Entry Statuses**: {', '.join(info['entry_statuses'])}")
        lines.append(f"- **Required Status**: {info['required_status'] or 'None'}")
        lines.append(f"- **Work States**: {', '.join(info['work_states'])}")
        lines.append(f"- **Auto-dispatch**: {info['dispatch_on_init']}")
        lines.append("")

    return "\n".join(lines)

``````
------ src/alfred/tools/tool_definitions.py ------
``````
"""
Declarative tool definition system for Alfred.

This module contains all tool definitions in a single place,
making it trivial to add new tools or modify existing ones.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Type, Optional, Callable, Any
from enum import Enum

from alfred.core.workflow import (
    BaseWorkflowTool,
    StartTaskTool,
    StartTaskState,
    ImplementTaskTool,
    ImplementTaskState,
    ReviewTaskTool,
    ReviewTaskState,
    TestTaskTool,
    TestTaskState,
    FinalizeTaskTool,
    FinalizeTaskState,
    CreateSpecTool,
    CreateSpecState,
    CreateTasksTool,
    CreateTasksState,
)
from alfred.core.discovery_workflow import PlanTaskTool, PlanTaskState
from alfred.core.discovery_context import load_plan_task_context
from alfred.models.schemas import TaskStatus
from alfred.constants import ToolName

# Import logic functions for simple tools
from alfred.tools.get_next_task import get_next_task_logic
from alfred.tools.work_on import work_on_logic
from alfred.tools.create_task import create_task_logic
from alfred.tools.approve_review import approve_review_logic
from alfred.tools.request_revision import request_revision_logic
from alfred.tools.approve_and_advance import approve_and_advance_logic
from alfred.tools.initialize import initialize_project_logic
from alfred.tools.create_spec import create_spec_logic
from alfred.tools.create_tasks_from_spec import create_tasks_logic


@dataclass
class ToolDefinition:
    """Complete definition of a workflow tool."""

    # Basic info
    name: str
    tool_class: Type[BaseWorkflowTool]
    description: str

    # States
    work_states: List[Enum] = field(default_factory=list)
    dispatch_state: Optional[Enum] = None
    terminal_state: Optional[Enum] = None
    initial_state: Optional[Enum] = None

    # Status mapping
    entry_statuses: List[TaskStatus] = field(default_factory=list)
    exit_status: Optional[TaskStatus] = None
    required_status: Optional[TaskStatus] = None

    # Behavior flags
    dispatch_on_init: bool = False
    produces_artifacts: bool = True
    requires_artifact_from: Optional[str] = None

    # Context loading
    context_loader: Optional[Callable[[Any, Any], Dict[str, Any]]] = None

    # Validation
    custom_validator: Optional[Callable[[Any], Optional[str]]] = None

    def get_entry_status_map(self) -> Dict[TaskStatus, TaskStatus]:
        """Build entry status map from definition."""
        if not self.exit_status:
            return {}

        return {entry: self.exit_status for entry in self.entry_statuses}

    def get_all_states(self) -> List[str]:
        """Get all states including review states."""
        states = []

        # Add dispatch state if exists
        if self.dispatch_state:
            states.append(self.dispatch_state.value)

        # Add work states and their review states
        for state in self.work_states:
            state_value = state.value if hasattr(state, "value") else str(state)
            states.append(state_value)
            states.append(f"{state_value}_awaiting_ai_review")
            states.append(f"{state_value}_awaiting_human_review")

        # Add terminal state
        if self.terminal_state:
            states.append(self.terminal_state.value)

        return states

    def validate(self) -> None:
        """Enhanced validation supporting simple tools."""
        # Case 1: Workflow tool (existing logic)
        if self.tool_class is not None:
            if self.dispatch_on_init and not self.dispatch_state:
                raise ValueError(f"Tool {self.name} has dispatch_on_init=True but no dispatch_state")

            if self.work_states and not self.terminal_state:
                raise ValueError(f"Tool {self.name} has work states but no terminal state")

            if self.entry_statuses and not self.exit_status:
                raise ValueError(f"Tool {self.name} has entry statuses but no exit status")

        # Case 2: Simple tool (new logic)
        elif self.tool_class is None:
            if self.context_loader is None:
                raise ValueError(f"Simple tool {self.name} must have context_loader as logic function")

            if any([self.work_states, self.dispatch_state, self.terminal_state, self.initial_state]):
                raise ValueError(f"Simple tool {self.name} cannot have workflow states")

            if self.dispatch_on_init:
                raise ValueError(f"Simple tool {self.name} cannot use dispatch_on_init")

        else:
            raise ValueError(f"Tool {self.name} must have either tool_class or context_loader")


# Context loaders
def load_execution_plan_context(task, task_state):
    """Load execution plan for implement_task."""
    from alfred.lib.turn_manager import turn_manager

    # Get the implementation_plan artifact from turns
    latest_artifacts = turn_manager.get_latest_artifacts_by_state(task.task_id)

    # Get the implementation_plan artifact specifically (which contains subtasks)
    implementation_plan = latest_artifacts.get("implementation_plan")
    if not implementation_plan:
        raise ValueError(f"CRITICAL: Cannot start implementation. Implementation plan not found for task '{task.task_id}'.")

    # Return the implementation plan with subtasks
    return {"artifact_content": implementation_plan}


def load_implementation_context(task, task_state):
    """Load implementation manifest for review_task."""
    manifest = task_state.completed_tool_outputs.get(ToolName.IMPLEMENT_TASK)
    return {"implementation_manifest": manifest}


def load_test_context(task, task_state):
    """Load test context from task."""
    return {"ac_verification_steps": getattr(task, "ac_verification_steps", [])}


def load_finalize_context(task, task_state):
    """Load test results for finalize_task."""
    test_results = task_state.completed_tool_outputs.get(ToolName.TEST_TASK)
    return {"test_results": test_results} if test_results else {}


def load_spec_context(task, task_state):
    """Load technical spec for create_tasks."""
    # This is loaded from archive, not task state
    return {}  # Handled specially in create_tasks_impl


# Custom validators
def validate_plan_task_status(task) -> Optional[str]:
    """Validate that task is in correct status for planning."""
    if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
        return f"Task '{task.task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' or resume a 'planning' task."
    return None


# Define all tools declaratively
TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
    ToolName.PLAN_TASK: ToolDefinition(
        name=ToolName.PLAN_TASK,
        tool_class=PlanTaskTool,
        description="""
        Interactive planning with deep context discovery and conversational clarification.
        
        This tool implements a comprehensive planning workflow that mirrors how expert developers 
        actually approach complex tasks:
        
        1. DISCOVERY: Deep context gathering using all available tools in parallel
        2. CLARIFICATION: Conversational Q&A to resolve ambiguities  
        3. CONTRACTS: Interface-first design of all APIs and data models
        4. IMPLEMENTATION_PLAN: Self-contained subtask creation with full context
        5. VALIDATION: Final coherence check and human approval
        
        Features:
        - Context saturation before planning begins
        - Real human-AI conversation for ambiguity resolution
        - Contract-first design approach
        - Self-contained subtasks with no rediscovery needed
        - Re-planning support for changing requirements
        - Complexity adaptation (can skip contracts for simple tasks)
        """,
        work_states=[
            PlanTaskState.DISCOVERY,
            PlanTaskState.CLARIFICATION,
            PlanTaskState.CONTRACTS,
            PlanTaskState.IMPLEMENTATION_PLAN,
            PlanTaskState.VALIDATION,
        ],
        terminal_state=PlanTaskState.VERIFIED,
        initial_state=PlanTaskState.DISCOVERY,
        entry_statuses=[TaskStatus.NEW, TaskStatus.PLANNING, TaskStatus.TASKS_CREATED],
        exit_status=TaskStatus.READY_FOR_DEVELOPMENT,
        dispatch_on_init=False,
        context_loader=load_plan_task_context,
        custom_validator=validate_plan_task_status,
    ),
    ToolName.START_TASK: ToolDefinition(
        name=ToolName.START_TASK,
        tool_class=StartTaskTool,
        description="Setup git environment for task",
        work_states=[
            StartTaskState.AWAITING_GIT_STATUS,
            StartTaskState.AWAITING_BRANCH_CREATION,
        ],
        terminal_state=StartTaskState.VERIFIED,
        initial_state=StartTaskState.AWAITING_GIT_STATUS,
        entry_statuses=[TaskStatus.NEW, TaskStatus.PLANNING],
        exit_status=TaskStatus.PLANNING,
        dispatch_on_init=False,
    ),
    ToolName.IMPLEMENT_TASK: ToolDefinition(
        name=ToolName.IMPLEMENT_TASK,
        tool_class=ImplementTaskTool,
        description="Execute the planned implementation",
        work_states=[ImplementTaskState.IMPLEMENTING],
        dispatch_state=ImplementTaskState.DISPATCHING,
        terminal_state=ImplementTaskState.VERIFIED,
        initial_state=ImplementTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.IN_DEVELOPMENT],
        exit_status=TaskStatus.READY_FOR_REVIEW,
        required_status=TaskStatus.READY_FOR_DEVELOPMENT,
        dispatch_on_init=True,
        requires_artifact_from=ToolName.PLAN_TASK,
        context_loader=load_execution_plan_context,
    ),
    ToolName.REVIEW_TASK: ToolDefinition(
        name=ToolName.REVIEW_TASK,
        tool_class=ReviewTaskTool,
        description="Perform code review",
        work_states=[ReviewTaskState.REVIEWING],
        dispatch_state=ReviewTaskState.DISPATCHING,
        terminal_state=ReviewTaskState.VERIFIED,
        initial_state=ReviewTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_REVIEW, TaskStatus.IN_REVIEW],
        exit_status=TaskStatus.READY_FOR_TESTING,
        required_status=TaskStatus.READY_FOR_REVIEW,
        dispatch_on_init=True,
        context_loader=load_implementation_context,
    ),
    ToolName.TEST_TASK: ToolDefinition(
        name=ToolName.TEST_TASK,
        tool_class=TestTaskTool,
        description="Run and validate tests",
        work_states=[TestTaskState.TESTING],
        dispatch_state=TestTaskState.DISPATCHING,
        terminal_state=TestTaskState.VERIFIED,
        initial_state=TestTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_TESTING, TaskStatus.IN_TESTING],
        exit_status=TaskStatus.READY_FOR_FINALIZATION,
        required_status=TaskStatus.READY_FOR_TESTING,
        dispatch_on_init=True,
        context_loader=load_test_context,
    ),
    ToolName.FINALIZE_TASK: ToolDefinition(
        name=ToolName.FINALIZE_TASK,
        tool_class=FinalizeTaskTool,
        description="Create commit and pull request",
        work_states=[FinalizeTaskState.FINALIZING],
        dispatch_state=FinalizeTaskState.DISPATCHING,
        terminal_state=FinalizeTaskState.VERIFIED,
        initial_state=FinalizeTaskState.DISPATCHING,
        entry_statuses=[TaskStatus.READY_FOR_FINALIZATION, TaskStatus.IN_FINALIZATION],
        exit_status=TaskStatus.DONE,
        required_status=TaskStatus.READY_FOR_FINALIZATION,
        dispatch_on_init=True,
        context_loader=load_finalize_context,
    ),
    ToolName.CREATE_SPEC: ToolDefinition(
        name=ToolName.CREATE_SPEC,
        tool_class=CreateSpecTool,
        description="Create technical specification from PRD",
        work_states=[CreateSpecState.DRAFTING_SPEC],
        dispatch_state=CreateSpecState.DISPATCHING,
        terminal_state=CreateSpecState.VERIFIED,
        initial_state=CreateSpecState.DISPATCHING,
        entry_statuses=[TaskStatus.NEW, TaskStatus.CREATING_SPEC],
        exit_status=TaskStatus.CREATING_SPEC,
        dispatch_on_init=True,
    ),
    ToolName.CREATE_TASKS_FROM_SPEC: ToolDefinition(
        name=ToolName.CREATE_TASKS_FROM_SPEC,
        tool_class=CreateTasksTool,
        description="Break down spec into actionable tasks",
        work_states=[CreateTasksState.DRAFTING_TASKS],
        dispatch_state=CreateTasksState.DISPATCHING,
        terminal_state=CreateTasksState.VERIFIED,
        initial_state=CreateTasksState.DISPATCHING,
        entry_statuses=[TaskStatus.SPEC_COMPLETED, TaskStatus.CREATING_TASKS],
        exit_status=TaskStatus.CREATING_TASKS,
        required_status=TaskStatus.SPEC_COMPLETED,
        dispatch_on_init=True,
        context_loader=load_spec_context,
    ),
    # Simple tools (tool_class=None, logic in context_loader)
    ToolName.GET_NEXT_TASK: ToolDefinition(
        name=ToolName.GET_NEXT_TASK,
        tool_class=None,
        description="Intelligently determines and recommends the next task to work on",
        context_loader=get_next_task_logic,
    ),
    ToolName.WORK_ON_TASK: ToolDefinition(
        name=ToolName.WORK_ON_TASK,
        tool_class=None,
        description="Primary entry point for working on any task - Smart Dispatch model",
        context_loader=work_on_logic,
    ),
    ToolName.CREATE_TASK: ToolDefinition(
        name=ToolName.CREATE_TASK,
        tool_class=None,
        description="Creates a new task in the Alfred system using standardized template format",
        context_loader=create_task_logic,
    ),
    ToolName.APPROVE_REVIEW: ToolDefinition(
        name=ToolName.APPROVE_REVIEW,
        tool_class=None,
        description="Approves the artifact in the current review step and advances the workflow",
        context_loader=approve_review_logic,
    ),
    ToolName.REQUEST_REVISION: ToolDefinition(
        name=ToolName.REQUEST_REVISION,
        tool_class=None,
        description="Rejects the artifact in the current review step and sends it back for revision",
        context_loader=request_revision_logic,
    ),
    ToolName.APPROVE_AND_ADVANCE: ToolDefinition(
        name=ToolName.APPROVE_AND_ADVANCE,
        tool_class=None,
        description="Approves the current phase and advances to the next phase in the workflow",
        context_loader=approve_and_advance_logic,
    ),
    ToolName.INITIALIZE_PROJECT: ToolDefinition(
        name=ToolName.INITIALIZE_PROJECT,
        tool_class=None,
        description="Initializes the project workspace for Alfred",
        context_loader=initialize_project_logic,
    ),
}


# Validate all definitions on module load
for tool_def in TOOL_DEFINITIONS.values():
    tool_def.validate()


def get_tool_definition(tool_name: str) -> ToolDefinition:
    """Get tool definition by name."""
    if tool_name not in TOOL_DEFINITIONS:
        raise ValueError(f"Unknown tool: {tool_name}")
    return TOOL_DEFINITIONS[tool_name]


def get_all_tool_names() -> List[str]:
    """Get all registered tool names."""
    return sorted(TOOL_DEFINITIONS.keys())

``````
------ src/alfred/tools/tool_factory.py ------
``````
"""
Factory for creating tools from definitions.
"""

from typing import Dict, Any, Optional

from alfred.tools.tool_definitions import TOOL_DEFINITIONS, ToolDefinition
from alfred.tools.generic_handler import GenericWorkflowHandler
from alfred.tools.workflow_config import WorkflowToolConfig
from alfred.models.schemas import ToolResponse
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


class ToolFactory:
    """Factory for creating tool handlers from definitions."""

    @staticmethod
    def create_handler(tool_name: str) -> GenericWorkflowHandler:
        """Create a handler for the given tool."""
        definition = TOOL_DEFINITIONS.get(tool_name)
        if not definition:
            raise ValueError(f"No definition found for tool: {tool_name}")

        # Convert ToolDefinition to WorkflowToolConfig
        config = WorkflowToolConfig(
            tool_name=definition.name,
            tool_class=definition.tool_class,
            required_status=definition.required_status,
            entry_status_map=definition.get_entry_status_map(),
            dispatch_on_init=definition.dispatch_on_init,
            dispatch_state_attr=(definition.dispatch_state.value if definition.dispatch_state and hasattr(definition.dispatch_state, "value") else None),
            context_loader=definition.context_loader,
            requires_artifact_from=definition.requires_artifact_from,
        )

        return GenericWorkflowHandler(config)

    @staticmethod
    async def execute_tool(tool_name: str, **kwargs) -> ToolResponse:
        """Execute a tool by name with the given arguments."""
        try:
            handler = ToolFactory.create_handler(tool_name)
            return await handler.execute(**kwargs)
        except Exception as e:
            logger.error(f"Failed to execute tool {tool_name}: {e}", exc_info=True)
            return ToolResponse(status="error", message=f"Failed to execute tool {tool_name}: {str(e)}")

    @staticmethod
    def get_tool_info(tool_name: str) -> Dict[str, Any]:
        """Get information about a tool."""
        definition = TOOL_DEFINITIONS.get(tool_name)
        if not definition:
            return {"error": f"Unknown tool: {tool_name}"}

        return {
            "name": definition.name,
            "description": definition.description,
            "entry_statuses": [s.value for s in definition.entry_statuses],
            "required_status": definition.required_status.value if definition.required_status else None,
            "produces_artifacts": definition.produces_artifacts,
            "work_states": [s.value for s in definition.work_states],
            "dispatch_on_init": definition.dispatch_on_init,
        }


# Create singleton handlers for backward compatibility
_tool_handlers: Dict[str, GenericWorkflowHandler] = {}


def get_tool_handler(tool_name: str) -> GenericWorkflowHandler:
    """Get or create a singleton handler for a tool."""
    if tool_name not in _tool_handlers:
        _tool_handlers[tool_name] = ToolFactory.create_handler(tool_name)
    return _tool_handlers[tool_name]

``````
------ src/alfred/tools/work_on.py ------
``````
from alfred.state.manager import state_manager
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.tools.workflow_utils import get_tool_for_status, get_phase_info, is_terminal_status
from alfred.lib.task_utils import does_task_exist_locally, write_task_to_markdown
from alfred.task_providers.factory import get_provider
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
def work_on_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for work_on_task compatible with GenericWorkflowHandler.

    Smart dispatch using centralized workflow configuration.
    """
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

    # Step 3: Use workflow utilities for smart dispatch
    task_state = state_manager.load_or_create_task_state(task_id)
    task_status = task_state.task_status

    # Get the appropriate tool from workflow utilities
    next_tool = get_tool_for_status(task_status)

    if next_tool:
        phase_info = get_phase_info(task_status)
        message = f"Task '{task_id}' is in status '{task_status.value}'. The next action is to use the '{next_tool}' tool."

        if phase_info and phase_info.get("description"):
            message += f"\nPhase: {phase_info['description']}"

        next_prompt = f"To proceed with task '{task_id}', call `alfred.{next_tool}(task_id='{task_id}')`."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)

    # Check if task is done
    if is_terminal_status(task_status):
        return ToolResponse(status="success", message=f"Task '{task_id}' is already done. No further action is required.")

    # Unknown status
    return ToolResponse(status="error", message=f"Unhandled status '{task_status.value}' for task '{task_id}'. This may be a configuration error.")

``````
------ src/alfred/tools/workflow_config.py ------
``````
"""
Workflow tool configuration system for eliminating handler duplication.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Type, Callable, Any
from enum import Enum

from alfred.core.workflow import BaseWorkflowTool
from alfred.models.schemas import TaskStatus


@dataclass
class WorkflowToolConfig:
    """Configuration for a workflow tool, replacing individual handlers."""

    # Basic configuration
    tool_name: str
    tool_class: Type[BaseWorkflowTool]
    required_status: Optional[TaskStatus] = None

    # Entry status mapping (for status transitions on tool creation)
    entry_status_map: Dict[TaskStatus, TaskStatus] = None

    # Dispatch configuration
    dispatch_on_init: bool = False
    dispatch_state_attr: Optional[str] = None  # e.g., "DISPATCHING"
    target_state_method: str = "dispatch"  # method to call for state transition

    # Context loading configuration
    context_loader: Optional[Callable[[Any, Any], Dict[str, Any]]] = None

    # Validation
    requires_artifact_from: Optional[str] = None  # e.g., ToolName.PLAN_TASK

    def __post_init__(self):
        """Validate configuration consistency."""
        if self.dispatch_on_init and not self.dispatch_state_attr:
            raise ValueError(f"Tool {self.tool_name} has dispatch_on_init=True but no dispatch_state_attr")

        if self.entry_status_map is None:
            self.entry_status_map = {}


# NOTE: Individual tool configurations have been moved to tool_definitions.py
# This file now only contains the WorkflowToolConfig class for backward compatibility.

``````
------ src/alfred/tools/workflow_utils.py ------
``````
"""
Workflow utility functions using TOOL_DEFINITIONS.

This module provides workflow resolution functions that replace the obsolete
WorkflowConfiguration system with direct TOOL_DEFINITIONS lookups.
"""

from typing import Optional, Dict, Any

from alfred.models.schemas import TaskStatus


def get_tool_for_status(task_status: TaskStatus) -> Optional[str]:
    """Find tool that handles the given task status.

    Args:
        task_status: The current task status

    Returns:
        Tool name that can handle this status, or None if no tool found
    """
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    for tool_name, tool_def in TOOL_DEFINITIONS.items():
        if task_status in tool_def.entry_statuses:
            return tool_name
    return None


def get_phase_info(task_status: TaskStatus) -> Optional[Dict[str, Any]]:
    """Get phase information for a status from ToolDefinition.

    Args:
        task_status: The current task status

    Returns:
        Dictionary with phase info (status, tool_name, description, exit_status)
        or None if no matching tool found
    """
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    tool_def = next((td for td in TOOL_DEFINITIONS.values() if task_status in td.entry_statuses), None)
    if tool_def:
        return {"status": task_status, "tool_name": tool_def.name, "description": tool_def.description.strip(), "exit_status": tool_def.exit_status}
    return None


def is_terminal_status(task_status: TaskStatus) -> bool:
    """Check if status is terminal (TaskStatus.DONE).

    Args:
        task_status: The task status to check

    Returns:
        True if status is TaskStatus.DONE, False otherwise
    """
    return task_status == TaskStatus.DONE


def get_next_status(current_status: TaskStatus) -> Optional[TaskStatus]:
    """Get next status from current tool's exit_status.

    Args:
        current_status: The current task status

    Returns:
        Next TaskStatus from tool's exit_status, or None if no tool found
    """
    from alfred.tools.tool_definitions import TOOL_DEFINITIONS

    tool_def = next((td for td in TOOL_DEFINITIONS.values() if current_status in td.entry_statuses), None)
    return tool_def.exit_status if tool_def else None

``````
    