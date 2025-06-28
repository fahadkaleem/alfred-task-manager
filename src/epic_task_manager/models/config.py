"""
Configuration models for Epic Task Manager
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TaskSource(StrEnum):
    """Supported task management systems"""

    ATLASSIAN = "atlassian"
    LINEAR = "linear"
    LOCAL = "local"


class ConnectionMethod(StrEnum):
    """Connection methods for task sources"""

    API = "api"  # Direct API calls
    MCP = "mcp"  # MCP-based connections
    WEBHOOK = "webhook"  # Future webhook support


class JiraConfig(BaseModel):
    """Configuration for Jira integration"""

    cloud_id: str | None = None
    project_key: str | None = None
    default_issue_type: str = "Task"
    base_url: str | None = None
    connection_method: ConnectionMethod = ConnectionMethod.MCP


class LinearConfig(BaseModel):
    """Configuration for Linear integration"""

    team_id: str | None = None
    workspace: str | None = None
    default_state_id: str | None = None
    connection_method: ConnectionMethod = ConnectionMethod.MCP


class FeatureFlags(BaseModel):
    """Feature flags for Epic Task Manager"""

    auto_assign: bool = True
    auto_transition: bool = True
    smart_context: bool = True
    yolo_mode: bool = Field(default=False, description="Enables autonomous mode, where the AI automatically approves its own work and advances to the next phase without human intervention.")
    scaffolding_mode: bool = Field(default=False, description="Enables an optional phase after planning where the AI first scaffolds the codebase with TODO comments based on the execution plan.")


class TaskSourceConfig(BaseModel):
    """Task source specific configuration"""

    jira: JiraConfig | None = None
    linear: LinearConfig | None = None


class ProvidersConfig(BaseModel):
    """Provider configuration under new structure"""

    task_source: TaskSource = TaskSource.LOCAL
    task_source_config: TaskSourceConfig = Field(default_factory=TaskSourceConfig)


class EpicConfig(BaseModel):
    """Main configuration for Epic Task Manager"""

    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = "1.0"

    def get_active_config(self) -> JiraConfig | LinearConfig | None:
        """Get the configuration for the active task source"""
        if self.providers.task_source == TaskSource.ATLASSIAN:
            return self.providers.task_source_config.jira
        if self.providers.task_source == TaskSource.LINEAR:
            return self.providers.task_source_config.linear
        return None

    def get_task_source(self) -> TaskSource:
        """Get the current task source"""
        return self.providers.task_source
