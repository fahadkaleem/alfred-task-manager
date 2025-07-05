"""Configuration manager for Alfred."""

import yaml
from pathlib import Path

from alfred.models.alfred_config import AlfredConfig


def _get_logger():
    """Lazy import to avoid circular dependencies."""
    from alfred.lib.structured_logger import get_logger
    return get_logger(__name__)


logger = None


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
            _get_logger().info("Configuration loaded successfully", extra={"config_path": str(self.config_path), "component": "config_manager"})
            return self._config
        except Exception as e:
            _get_logger().error("Failed to load configuration", extra={"config_path": str(self.config_path), "error": str(e), "component": "config_manager"}, exc_info=True)
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
            _get_logger().info("Configuration saved successfully", extra={"config_path": str(self.config_path), "component": "config_manager"})
        except Exception as e:
            _get_logger().error("Failed to save configuration", extra={"config_path": str(self.config_path), "error": str(e), "component": "config_manager"}, exc_info=True)
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
