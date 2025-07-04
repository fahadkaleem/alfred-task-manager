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
