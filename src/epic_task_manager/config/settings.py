"""
Configuration settings for Epic Task Manager using pydantic_settings
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from epic_task_manager.constants import TASKS_INBOX_DIR_NAME, WORKSPACE_DIR_NAME


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_prefix="EPIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra environment variables without errors
    )

    # Credential environment variables
    jira_api_token: str | None = None
    jira_user_email: str | None = None
    linear_api_key: str | None = None

    # Server configuration
    server_name: str = "epic-task-manager"
    version: str = "0.2.0"

    # Directory configuration
    epic_task_manager_dir_name: str = ".epictaskmanager"
    contexts_subdir: str = "contexts"
    state_filename: str = "state.json"
    config_filename: str = "config.json"

    # Base paths
    project_root: Path = Path.cwd()

    @property
    def templates_dir(self) -> Path:
        """Get the templates directory path"""
        return Path(__file__).parent.parent / "templates"

    @property
    def epic_task_manager_dir(self) -> Path:
        """Get the epic directory path"""
        return self.project_root / self.epic_task_manager_dir_name

    @property
    def contexts_dir(self) -> Path:
        """Get the contexts directory path"""
        return self.epic_task_manager_dir / self.contexts_subdir

    @property
    def state_file(self) -> Path:
        """Get the state file path"""
        return self.epic_task_manager_dir / self.state_filename

    @property
    def config_file(self) -> Path:
        """Get the config.json file path"""
        return self.epic_task_manager_dir / self.config_filename

    @property
    def workspace_dir(self) -> Path:
        """Get the workspace directory path (replaces old tasks directory)"""
        return self.epic_task_manager_dir / WORKSPACE_DIR_NAME

    @property
    def tasks_inbox_dir(self) -> Path:
        """Get the tasks inbox directory path for local markdown files"""
        return self.epic_task_manager_dir / TASKS_INBOX_DIR_NAME

    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory path for local template customization"""
        return self.epic_task_manager_dir / "prompts"


# Global settings instance
settings = Settings()
