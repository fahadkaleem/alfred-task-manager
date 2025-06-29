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
