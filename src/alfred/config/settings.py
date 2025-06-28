"""
Configuration settings for Alfred using pydantic_settings
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_prefix="ALFRED_", case_sensitive=False)

    # Debugging flag
    debugging_mode: bool = True

    # Server configuration
    server_name: str = "alfred"
    version: str = "2.0.0"

    # Directory configuration
    alfred_dir_name: str = ".alfred"
    state_filename: str = "state.json"
    workflow_filename: str = "workflow.yml"

    # Base paths
    project_root: Path = Path.cwd()

    @property
    def alfred_dir(self) -> Path:
        """Get the .alfred directory path in the user's project."""
        return self.project_root / self.alfred_dir_name

    @property
    def state_file(self) -> Path:
        """Get the state file path."""
        return self.alfred_dir / self.state_filename

    @property
    def workflow_file(self) -> Path:
        """Get the project's workflow.yml file path."""
        return self.alfred_dir / self.workflow_filename

    @property
    def packaged_workflow_file(self) -> Path:
        """Get the path to the default workflow file inside the package."""
        return Path(__file__).parent.parent / "workflow.yml"

    @property
    def packaged_personas_dir(self) -> Path:
        """Get the path to the default personas directory inside the package."""
        return Path(__file__).parent.parent / "personas"

    @property
    def packaged_templates_dir(self) -> Path:
        """Get the path to the default templates directory inside the package."""
        return Path(__file__).parent.parent / "templates"

    @property
    def workspace_dir(self) -> Path:
        """Get the workspace directory path."""
        return self.alfred_dir / "workspace"


# Global settings instance
settings = Settings()
