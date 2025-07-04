"""
Tests for LLM provider initialization.

Tests the initialization system for AI providers following Alfred's testing principles.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from alfred.llm.initialization import (
    initialize_ai_providers,
    _initialize_single_provider,
    _get_api_key_for_provider,
    get_provider_status,
)
from alfred.models.alfred_config import AIProvider, AIProviderConfig
from alfred.llm.providers.base import AuthenticationError, ProviderError


class TestInitializeAIProviders:
    """Test main AI provider initialization function."""

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization._initialize_single_provider")
    async def test_successful_initialization(self, mock_init_single, mock_config_manager):
        """Test successful initialization of multiple providers."""
        # Mock configuration
        mock_config = Mock()
        mock_ai_config = Mock()

        provider_configs = [
            AIProviderConfig(name=AIProvider.OPENAI, enabled=True),
            AIProviderConfig(name=AIProvider.ANTHROPIC, enabled=True),
        ]
        mock_ai_config.providers = provider_configs
        mock_config.ai = mock_ai_config

        mock_config_manager_instance = Mock()
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance

        mock_init_single.return_value = None  # Successful initialization

        await initialize_ai_providers()

        # Verify config loading
        mock_config_manager.assert_called_once()
        mock_config_manager_instance.load.assert_called_once()

        # Verify both providers were initialized
        assert mock_init_single.call_count == 2
        mock_init_single.assert_any_call(provider_configs[0])
        mock_init_single.assert_any_call(provider_configs[1])

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization._initialize_single_provider")
    async def test_no_providers_configured(self, mock_init_single, mock_config_manager):
        """Test handling when no providers are configured."""
        # Mock configuration with no providers
        mock_config = Mock()
        mock_ai_config = Mock()
        mock_ai_config.providers = []
        mock_config.ai = mock_ai_config

        mock_config_manager_instance = Mock()
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance

        await initialize_ai_providers()

        # Should not try to initialize any providers
        mock_init_single.assert_not_called()

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization._initialize_single_provider")
    async def test_disabled_providers_skipped(self, mock_init_single, mock_config_manager):
        """Test that disabled providers are skipped."""
        # Mock configuration with disabled provider
        mock_config = Mock()
        mock_ai_config = Mock()

        provider_configs = [
            AIProviderConfig(name=AIProvider.OPENAI, enabled=True),
            AIProviderConfig(name=AIProvider.ANTHROPIC, enabled=False),  # Disabled
        ]
        mock_ai_config.providers = provider_configs
        mock_config.ai = mock_ai_config

        mock_config_manager_instance = Mock()
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance

        await initialize_ai_providers()

        # Only enabled provider should be initialized
        mock_init_single.assert_called_once_with(provider_configs[0])

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization._initialize_single_provider")
    async def test_partial_initialization_failure(self, mock_init_single, mock_config_manager):
        """Test that initialization continues even if some providers fail."""
        # Mock configuration
        mock_config = Mock()
        mock_ai_config = Mock()

        provider_configs = [
            AIProviderConfig(name=AIProvider.OPENAI, enabled=True),
            AIProviderConfig(name=AIProvider.ANTHROPIC, enabled=True),
        ]
        mock_ai_config.providers = provider_configs
        mock_config.ai = mock_ai_config

        mock_config_manager_instance = Mock()
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance

        # First provider succeeds, second fails
        mock_init_single.side_effect = [None, Exception("Provider initialization failed")]

        # Should not raise exception
        await initialize_ai_providers()

        # Both providers should have been attempted
        assert mock_init_single.call_count == 2

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization.model_registry")
    async def test_model_logging(self, mock_registry, mock_config_manager):
        """Test that available models are logged."""
        # Mock configuration with no providers (to skip initialization)
        mock_config = Mock()
        mock_ai_config = Mock()
        mock_ai_config.providers = []
        mock_config.ai = mock_ai_config

        mock_config_manager_instance = Mock()
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance

        # Mock registry models
        mock_models = [Mock(name="model1"), Mock(name="model2")]
        mock_registry.get_available_models.return_value = mock_models

        await initialize_ai_providers()

        # Verify models were queried for logging
        mock_registry.get_available_models.assert_called_once()

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    async def test_config_loading_failure(self, mock_config_manager):
        """Test graceful handling of configuration loading failure."""
        mock_config_manager.side_effect = Exception("Config load failed")

        # Should not raise exception
        await initialize_ai_providers()


class TestInitializeSingleProvider:
    """Test single provider initialization function."""

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization._get_api_key_for_provider")
    @patch("alfred.llm.initialization.model_registry")
    async def test_openai_provider_initialization(self, mock_registry, mock_get_api_key):
        """Test OpenAI provider initialization."""
        mock_get_api_key.return_value = "test-api-key"
        mock_provider = Mock()
        mock_registry.create_provider.return_value = mock_provider

        config = AIProviderConfig(name=AIProvider.OPENAI, enabled=True)

        await _initialize_single_provider(config)

        mock_registry.create_provider.assert_called_once_with("openai", api_key="test-api-key", base_url=None)
        mock_registry.register_provider.assert_called_once_with("openai", mock_provider)

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization._get_api_key_for_provider")
    @patch("alfred.llm.initialization.model_registry")
    async def test_google_provider_initialization(self, mock_registry, mock_get_api_key):
        """Test Google provider initialization."""
        mock_get_api_key.return_value = "test-api-key"
        mock_provider = Mock()
        mock_registry.create_provider.return_value = mock_provider

        config = AIProviderConfig(name=AIProvider.GOOGLE, enabled=True)

        await _initialize_single_provider(config)

        mock_registry.create_provider.assert_called_once_with("google", api_key="test-api-key")
        mock_registry.register_provider.assert_called_once_with("google", mock_provider)

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization._get_api_key_for_provider")
    @patch("alfred.llm.initialization.model_registry")
    async def test_anthropic_provider_initialization(self, mock_registry, mock_get_api_key):
        """Test Anthropic provider initialization."""
        mock_get_api_key.return_value = "test-api-key"
        mock_provider = Mock()
        mock_registry.create_provider.return_value = mock_provider

        config = AIProviderConfig(name=AIProvider.ANTHROPIC, enabled=True)

        await _initialize_single_provider(config)

        mock_registry.create_provider.assert_called_once_with("anthropic", api_key="test-api-key")
        mock_registry.register_provider.assert_called_once_with("anthropic", mock_provider)

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization._get_api_key_for_provider")
    async def test_missing_api_key_error(self, mock_get_api_key):
        """Test error when API key is missing."""
        mock_get_api_key.return_value = None

        config = AIProviderConfig(name=AIProvider.OPENAI, enabled=True)

        with pytest.raises(AuthenticationError) as exc_info:
            await _initialize_single_provider(config)

        assert "No API key found for openai" in str(exc_info.value)
        assert "OPENAI_API_KEY" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization._get_api_key_for_provider")
    async def test_unsupported_provider_error(self, mock_get_api_key):
        """Test error for unsupported provider type."""
        mock_get_api_key.return_value = "test-api-key"

        # Create a mock provider that's not in the supported list
        config = Mock()
        config.name = "unsupported_provider"
        config.name.value = "unsupported_provider"

        with pytest.raises(ProviderError) as exc_info:
            await _initialize_single_provider(config)

        assert "Unsupported AI provider" in str(exc_info.value)


class TestGetAPIKey:
    """Test API key retrieval function."""

    @patch("alfred.llm.initialization.settings")
    def test_openai_api_key(self, mock_settings):
        """Test OpenAI API key retrieval."""
        mock_settings.openai_api_key = "test-openai-key"

        result = _get_api_key_for_provider(AIProvider.OPENAI)

        assert result == "test-openai-key"

    @patch("alfred.llm.initialization.settings")
    def test_google_api_key(self, mock_settings):
        """Test Google API key retrieval."""
        mock_settings.google_api_key = "test-google-key"

        result = _get_api_key_for_provider(AIProvider.GOOGLE)

        assert result == "test-google-key"

    @patch("alfred.llm.initialization.settings")
    def test_anthropic_api_key(self, mock_settings):
        """Test Anthropic API key retrieval."""
        mock_settings.anthropic_api_key = "test-anthropic-key"

        result = _get_api_key_for_provider(AIProvider.ANTHROPIC)

        assert result == "test-anthropic-key"

    def test_unknown_provider(self):
        """Test unknown provider returns None."""
        # Mock an unknown provider
        unknown_provider = Mock()
        unknown_provider.name = "unknown"

        result = _get_api_key_for_provider(unknown_provider)

        assert result is None


class TestGetProviderStatus:
    """Test provider status function."""

    @patch("alfred.llm.initialization.model_registry")
    def test_provider_status(self, mock_registry):
        """Test getting provider status."""
        # Mock registry data
        mock_registry.get_registered_providers.return_value = ["openai", "anthropic"]

        mock_models = [
            Mock(name="gpt-4", provider="openai"),
            Mock(name="gpt-3.5-turbo", provider="openai"),
            Mock(name="claude-3-5-sonnet", provider="anthropic"),
        ]
        mock_registry.get_available_models.return_value = mock_models

        result = get_provider_status()

        expected = {"registered_providers": ["openai", "anthropic"], "total_models": 3, "models_by_provider": {"openai": ["gpt-4", "gpt-3.5-turbo"], "anthropic": ["claude-3-5-sonnet"]}}

        assert result == expected

    @patch("alfred.llm.initialization.model_registry")
    def test_provider_status_empty(self, mock_registry):
        """Test provider status with no providers."""
        mock_registry.get_registered_providers.return_value = []
        mock_registry.get_available_models.return_value = []

        result = get_provider_status()

        expected = {"registered_providers": [], "total_models": 0, "models_by_provider": {}}

        assert result == expected


class TestInitializationIntegration:
    """Test initialization integration scenarios."""

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization.model_registry")
    @patch("alfred.llm.initialization.settings")
    async def test_full_initialization_flow(self, mock_settings, mock_registry, mock_config_manager):
        """Test complete initialization flow with realistic configuration."""
        # Mock settings
        mock_settings.openai_api_key = "openai-key"
        mock_settings.anthropic_api_key = "anthropic-key"
        mock_settings.google_api_key = None  # Not configured

        # Mock configuration
        mock_config = Mock()
        mock_ai_config = Mock()

        provider_configs = [
            AIProviderConfig(name=AIProvider.OPENAI, enabled=True),
            AIProviderConfig(name=AIProvider.ANTHROPIC, enabled=True),
            AIProviderConfig(name=AIProvider.GOOGLE, enabled=True),  # Will fail due to missing key
        ]
        mock_ai_config.providers = provider_configs
        mock_config.ai = mock_ai_config

        mock_config_manager_instance = Mock()
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager.return_value = mock_config_manager_instance

        # Mock provider creation
        mock_openai_provider = Mock()
        mock_anthropic_provider = Mock()

        def create_provider_side_effect(provider_type, **kwargs):
            if provider_type == "openai":
                return mock_openai_provider
            elif provider_type == "anthropic":
                return mock_anthropic_provider
            else:
                raise Exception("Unexpected provider type")

        mock_registry.create_provider.side_effect = create_provider_side_effect
        mock_registry.get_available_models.return_value = []

        # Should not raise exception despite Google failing
        await initialize_ai_providers()

        # Verify successful providers were registered
        mock_registry.register_provider.assert_any_call("openai", mock_openai_provider)
        mock_registry.register_provider.assert_any_call("anthropic", mock_anthropic_provider)

        # Google should not have been registered (no API key)
        assert mock_registry.register_provider.call_count == 2

    @pytest.mark.asyncio
    @patch("alfred.llm.initialization.ConfigManager")
    @patch("alfred.llm.initialization.settings")
    async def test_environment_variable_precedence(self, mock_settings, mock_config_manager):
        """Test that environment variables take precedence for API keys."""
        # Mock settings with API keys
        mock_settings.openai_api_key = "env-openai-key"
        mock_settings.anthropic_api_key = None  # Not set

        # Test OpenAI key retrieval
        assert _get_api_key_for_provider(AIProvider.OPENAI) == "env-openai-key"

        # Test missing key
        assert _get_api_key_for_provider(AIProvider.ANTHROPIC) is None
