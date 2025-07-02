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
    config_filename: str = Paths.CONFIG_FILE

    # Base paths
    project_root: Path = Path.cwd()

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
