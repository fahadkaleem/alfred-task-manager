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
