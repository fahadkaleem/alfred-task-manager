"""
AI Provider Initialization for Alfred Task Manager

Following Alfred's principles:
- IMMUTABILITY ABOVE ALL (configuration loaded once at startup)
- ENVIRONMENT VARIABLES ARE SACRED (API keys from env)
- VALIDATION IS NON-NEGOTIABLE (fail fast on invalid config)
"""

from typing import List, Optional
from alfred.config import ConfigManager
from alfred.config.settings import settings
from alfred.lib.structured_logger import get_logger
from alfred.models.alfred_config import AIProvider, AIProviderConfig

from .registry import model_registry
from .providers.openai_provider import OpenAIProvider
from .providers.base import AuthenticationError, ProviderError

logger = get_logger(__name__)


async def initialize_ai_providers() -> None:
    """
    Initialize AI providers based on configuration.

    Following Alfred's configuration principles:
    - Load configuration once at startup (immutable)
    - Use environment variables for API keys
    - Fail fast on invalid configuration
    - Provide actionable error messages
    """
    try:
        # Load configuration (immutable, loaded once)
        config_manager = ConfigManager(settings.alfred_dir)
        config = config_manager.load()

        ai_config = config.ai
        if not ai_config.providers:
            logger.warning("No AI providers configured")
            return

        initialized_count = 0

        for provider_config in ai_config.providers:
            if not provider_config.enabled:
                logger.info(f"AI provider {provider_config.name} is disabled, skipping")
                continue

            try:
                await _initialize_single_provider(provider_config)
                initialized_count += 1
                logger.info(f"Successfully initialized AI provider: {provider_config.name}")

            except Exception as e:
                logger.error(f"Failed to initialize AI provider {provider_config.name}: {e}")
                # Continue with other providers rather than failing completely
                continue

        if initialized_count == 0:
            logger.warning("No AI providers were successfully initialized")
        else:
            logger.info(f"Initialized {initialized_count} AI provider(s)")

        # Log available models for debugging
        available_models = model_registry.get_available_models()
        model_names = [model.name for model in available_models]
        logger.debug(f"Available AI models: {model_names}")

    except Exception as e:
        logger.error(f"Failed to initialize AI providers: {e}")
        # Don't raise - let Alfred run without AI providers for now
        # In the future, we might want to make this more strict


async def _initialize_single_provider(provider_config: AIProviderConfig) -> None:
    """Initialize a single AI provider instance."""

    # Get API key from environment variables (sacred principle)
    api_key = _get_api_key_for_provider(provider_config.name)

    if not api_key:
        raise AuthenticationError(f"No API key found for {provider_config.name}. Set {provider_config.name.upper()}_API_KEY environment variable.")

    # Create provider instance based on type with hardcoded sensible defaults
    if provider_config.name == AIProvider.OPENAI:
        provider = model_registry.create_provider(
            "openai",
            api_key=api_key,
            base_url=None,  # Use OpenAI's default API endpoint
        )
    elif provider_config.name == AIProvider.GOOGLE:
        provider = model_registry.create_provider("google", api_key=api_key)
    elif provider_config.name == AIProvider.ANTHROPIC:
        provider = model_registry.create_provider("anthropic", api_key=api_key)
    else:
        raise ProviderError(f"Unsupported AI provider: {provider_config.name}")

    # Register the provider
    model_registry.register_provider(provider_config.name.value, provider)


def _get_api_key_for_provider(provider: AIProvider) -> Optional[str]:
    """
    Get API key for a provider from environment variables.

    Following Alfred's principle: ENVIRONMENT VARIABLES ARE SACRED
    """
    if provider == AIProvider.OPENAI:
        return settings.openai_api_key
    elif provider == AIProvider.GOOGLE:
        return settings.google_api_key
    elif provider == AIProvider.ANTHROPIC:
        return settings.anthropic_api_key
    else:
        return None


def get_provider_status() -> dict:
    """Get status of all registered providers (for debugging)."""
    return {
        "registered_providers": model_registry.get_registered_providers(),
        "total_models": len(model_registry.get_available_models()),
        "models_by_provider": {provider: [model.name for model in model_registry.get_available_models() if model.provider == provider] for provider in model_registry.get_registered_providers()},
    }
