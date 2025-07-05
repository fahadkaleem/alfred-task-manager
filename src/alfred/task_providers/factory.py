"""Task provider factory for instantiating the correct provider based on configuration."""

from alfred.models.alfred_config import TaskProvider as ProviderType
from alfred.lib.structured_logger import get_logger
from .base import BaseTaskProvider
from .local_provider import LocalTaskProvider
from .jira_provider import JiraTaskProvider

logger = get_logger(__name__)


def get_provider() -> BaseTaskProvider:
    """Factory function to instantiate the configured task provider.

    This function reads the current Alfred configuration and returns
    the appropriate task provider instance based on the configured
    provider type.

    Returns:
        BaseTaskProvider: An instance of the configured task provider

    Raises:
        NotImplementedError: If the configured provider is not yet implemented
    """
    # Import here to avoid circular dependency
    from alfred.config import ConfigManager
    from alfred.config.settings import settings

    try:
        # Load the current configuration
        config_manager = ConfigManager(settings.alfred_dir)
        config = config_manager.load()
        provider_type = config.provider.type

        logger.info(f"Instantiating task provider: {provider_type}")

        # Return the appropriate provider based on configuration
        if provider_type == ProviderType.LOCAL:
            return LocalTaskProvider()
        elif provider_type == ProviderType.JIRA:
            return JiraTaskProvider()
        elif provider_type == ProviderType.LINEAR:
            raise NotImplementedError(f"Linear task provider is not yet implemented. Please use 'local' provider for now.")
        else:
            raise NotImplementedError(f"Unknown task provider type: '{provider_type}'. Supported providers: local, jira (coming soon), linear (coming soon)")

    except Exception as e:
        logger.error(f"Failed to instantiate task provider: {e}")
        # Fall back to local provider as default
        logger.warning("Falling back to local task provider")
        return LocalTaskProvider()
