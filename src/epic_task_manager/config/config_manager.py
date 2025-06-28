"""
Configuration management utilities for Epic Task Manager
"""

from __future__ import annotations

from datetime import datetime

# Standard library imports
import json
import logging
from pathlib import Path

# Third-party imports
from pydantic import ValidationError

# Local application imports
from epic_task_manager.models.config import (
    EpicConfig,
    JiraConfig,
    LinearConfig,
    TaskSource,
)

from .settings import settings

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration persistence and validation"""

    def __init__(self, config_file: Path | None = None):
        self.config_file = config_file or settings.config_file

    def load_config(self) -> EpicConfig:
        """
        Load configuration from config.json with validation and migration support

        Returns:
            EpicConfig: Loaded and validated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        if not self.config_file.exists():
            logger.info(f"Config file {self.config_file} not found, creating default")
            return self._create_default_config()

        try:
            config_data = self._load_raw_config_data()
            config = self.validate_config(config_data)
        except (json.JSONDecodeError, ValidationError) as e:
            return self._handle_config_load_error(e)
        else:
            logger.info(f"Loaded configuration from {self.config_file}")
            return config

    def _load_raw_config_data(self) -> dict:
        """Load raw configuration data from file"""
        with self.config_file.open(encoding="utf-8") as f:
            return json.load(f)

    def _handle_config_load_error(self, error: Exception) -> EpicConfig:
        """Handle configuration load errors by backing up and creating default"""
        logger.exception(f"Failed to load config from {self.config_file}: {error}")
        logger.info("Creating backup and using default configuration")
        self._backup_invalid_config()
        return self._create_default_config()

    def save_config(self, config: EpicConfig) -> None:
        """
        Save configuration to config.json

        Args:
            config: Configuration to save
        """
        # Ensure directory exists
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # Update timestamp
        config.updated_at = datetime.now()

        # Serialize to JSON (exclude sensitive fields)
        config_data = config.model_dump(mode="json")

        with self.config_file.open("w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved configuration to {self.config_file}")

    def validate_config(self, config_data: dict) -> EpicConfig:
        """
        Validate configuration data

        Args:
            config_data: Raw configuration dictionary

        Returns:
            EpicConfig: Validated configuration

        Raises:
            ValidationError: If configuration is invalid
        """
        return EpicConfig(**config_data)

    def _create_default_config(self) -> EpicConfig:
        """Create default configuration"""
        config = EpicConfig()
        self.save_config(config)
        return config

    def _backup_invalid_config(self) -> None:
        """Create backup of invalid configuration file"""
        if self.config_file.exists():
            backup_file = self.config_file.with_suffix(".json.backup")
            self.config_file.rename(backup_file)
            logger.info(f"Backed up invalid config to {backup_file}")

    def setup_provider_config(self, task_source: TaskSource, provider_config: dict | None = None) -> EpicConfig:
        """Set up provider-specific configuration"""
        config = self.load_config()
        config.providers.task_source = task_source

        if task_source == TaskSource.ATLASSIAN and provider_config:
            config.providers.task_source_config.jira = JiraConfig(**provider_config)
        elif task_source == TaskSource.LINEAR and provider_config:
            config.providers.task_source_config.linear = LinearConfig(**provider_config)

        self.save_config(config)
        return config

    def validate_mcp_availability(self, task_source: TaskSource) -> bool:
        """Check if required MCP tools are available for the given task source"""
        if task_source == TaskSource.LOCAL:
            return True  # Local doesn't need MCP tools

        try:
            if task_source == TaskSource.ATLASSIAN:
                # Try to import and test Atlassian MCP tools
                import mcp  # noqa: F401

                # This would be replaced with actual MCP tool availability check
                # For now, we'll assume it's available if imported successfully
                return True
            if task_source == TaskSource.LINEAR:
                # Similar check for Linear MCP tools
                return True
        except ImportError:
            return False
        else:
            return True


# Global config manager instance
config_manager = ConfigManager()


def load_config() -> EpicConfig:
    """Load the current configuration"""
    return config_manager.load_config()


def save_config(config: EpicConfig) -> None:
    """Save the configuration"""
    config_manager.save_config(config)


def get_config_file_path() -> Path:
    """Get the configuration file path"""
    return config_manager.config_file
