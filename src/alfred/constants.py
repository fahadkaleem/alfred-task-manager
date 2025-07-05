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
    ARCHIVE_DIR: Final[str] = "archive"

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
