"""
Tests for LLM provider registry and factory.

Tests the central registry system for managing AI providers following Alfred's testing principles.
"""

import pytest
from unittest.mock import Mock, patch

from alfred.llm.registry import ModelProviderRegistry, get_model_registry
from alfred.llm.providers.base import (
    BaseAIProvider,
    ModelResponse,
    ModelInfo,
    ModelCapability,
    ModelNotFoundError,
    ProviderError,
)


class MockProvider(BaseAIProvider):
    """Mock provider for testing."""

    def __init__(self, name: str, models: list = None):
        self.name = name
        self.models = models or []

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens=None) -> ModelResponse:
        return ModelResponse(content="mock response", model_name=model_name)

    def count_tokens(self, text: str, model_name: str) -> int:
        return len(text.split())

    def get_available_models(self) -> list:
        return self.models

    def validate_model(self, model_name: str) -> bool:
        return any(model.name == model_name for model in self.models)


class TestModelProviderRegistry:
    """Test ModelProviderRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = ModelProviderRegistry()

        assert len(registry._providers) == 0
        assert len(registry._model_to_provider_map) == 0
        assert "openai" in registry._provider_classes
        assert "google" in registry._provider_classes
        assert "anthropic" in registry._provider_classes

    def test_register_provider_success(self):
        """Test successful provider registration."""
        registry = ModelProviderRegistry()

        mock_models = [
            ModelInfo(name="test-model-1", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096),
            ModelInfo(name="test-model-2", provider="test", capabilities=[ModelCapability.CODE_GENERATION], context_window=8192),
        ]

        provider = MockProvider("test", mock_models)
        registry.register_provider("test", provider)

        assert "test" in registry._providers
        assert registry._providers["test"] == provider
        assert registry._model_to_provider_map["test-model-1"] == "test"
        assert registry._model_to_provider_map["test-model-2"] == "test"

    def test_register_provider_duplicate_error(self):
        """Test error when registering duplicate provider."""
        registry = ModelProviderRegistry()
        provider = MockProvider("test")

        registry.register_provider("test", provider)

        with pytest.raises(ValueError) as exc_info:
            registry.register_provider("test", provider)

        assert "Provider test already registered" in str(exc_info.value)

    def test_register_provider_with_model_conflicts(self):
        """Test provider registration with conflicting model names."""
        registry = ModelProviderRegistry()

        model_info = ModelInfo(name="shared-model", provider="provider1", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        provider1 = MockProvider("provider1", [model_info])
        provider2 = MockProvider("provider2", [model_info])

        registry.register_provider("provider1", provider1)
        registry.register_provider("provider2", provider2)

        # First provider gets the model name directly
        assert registry._model_to_provider_map["shared-model"] == "provider1"
        # Second provider gets prefixed name
        assert registry._model_to_provider_map["provider2:shared-model"] == "provider2"

    def test_register_provider_with_enumeration_failure(self):
        """Test provider registration when model enumeration fails."""
        registry = ModelProviderRegistry()

        provider = Mock()
        provider.get_available_models.side_effect = Exception("Enumeration failed")

        # Should not raise exception
        registry.register_provider("test", provider)

        assert "test" in registry._providers
        assert len(registry._model_to_provider_map) == 0

    def test_create_provider_success(self):
        """Test successful provider creation."""
        registry = ModelProviderRegistry()

        mock_provider_class = Mock()
        mock_instance = Mock()
        mock_provider_class.return_value = mock_instance

        with patch.object(registry, "_provider_classes", {"openai": mock_provider_class}):
            result = registry.create_provider("openai", api_key="test-key")

            mock_provider_class.assert_called_once_with(api_key="test-key")
            assert result == mock_instance

    def test_create_provider_unknown_type(self):
        """Test error when creating unknown provider type."""
        registry = ModelProviderRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.create_provider("unknown", api_key="test")

        assert "Unknown provider type: unknown" in str(exc_info.value)

    def test_get_provider_for_model_direct_mapping(self):
        """Test getting provider for model with direct mapping."""
        registry = ModelProviderRegistry()

        model_info = ModelInfo(name="test-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        provider = MockProvider("test", [model_info])
        registry.register_provider("test", provider)

        result = registry.get_provider_for_model("test-model")
        assert result == provider

    def test_get_provider_for_model_prefixed(self):
        """Test getting provider for model with prefixed name."""
        registry = ModelProviderRegistry()

        model_info = ModelInfo(name="model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        provider = MockProvider("test", [model_info])
        registry.register_provider("test", provider)

        result = registry.get_provider_for_model("test:model")
        assert result == provider

    def test_get_provider_for_model_validation_fallback(self):
        """Test getting provider for model using validation fallback."""
        registry = ModelProviderRegistry()

        # Provider with no models in registry but validates the model
        provider = Mock()
        provider.validate_model.return_value = True

        registry.register_provider("test", provider)

        result = registry.get_provider_for_model("unknown-model")
        assert result == provider
        provider.validate_model.assert_called_once_with("unknown-model")

    def test_get_provider_for_model_not_found(self):
        """Test error when no provider found for model."""
        registry = ModelProviderRegistry()

        provider = Mock()
        provider.validate_model.return_value = False
        registry.register_provider("test", provider)

        with pytest.raises(ModelNotFoundError) as exc_info:
            registry.get_provider_for_model("nonexistent-model")

        assert "No provider found for model: nonexistent-model" in str(exc_info.value)

    def test_get_available_models(self):
        """Test getting all available models."""
        registry = ModelProviderRegistry()

        models1 = [ModelInfo(name="model1", provider="provider1", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)]

        models2 = [ModelInfo(name="model2", provider="provider2", capabilities=[ModelCapability.CODE_GENERATION], context_window=8192)]

        provider1 = MockProvider("provider1", models1)
        provider2 = MockProvider("provider2", models2)

        registry.register_provider("provider1", provider1)
        registry.register_provider("provider2", provider2)

        all_models = registry.get_available_models()

        assert len(all_models) == 2
        model_names = [model.name for model in all_models]
        assert "model1" in model_names
        assert "model2" in model_names

    def test_get_available_models_with_failure(self):
        """Test getting models when some providers fail."""
        registry = ModelProviderRegistry()

        models = [ModelInfo(name="working-model", provider="working", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)]

        working_provider = MockProvider("working", models)
        failing_provider = Mock()
        failing_provider.get_available_models.side_effect = Exception("Failed")

        registry.register_provider("working", working_provider)
        registry.register_provider("failing", failing_provider)

        all_models = registry.get_available_models()

        assert len(all_models) == 1
        assert all_models[0].name == "working-model"

    def test_get_registered_providers(self):
        """Test getting list of registered providers."""
        registry = ModelProviderRegistry()

        provider1 = MockProvider("provider1")
        provider2 = MockProvider("provider2")

        registry.register_provider("provider1", provider1)
        registry.register_provider("provider2", provider2)

        providers = registry.get_registered_providers()

        assert len(providers) == 2
        assert "provider1" in providers
        assert "provider2" in providers

    def test_is_provider_registered(self):
        """Test checking if provider is registered."""
        registry = ModelProviderRegistry()

        provider = MockProvider("test")

        assert not registry.is_provider_registered("test")

        registry.register_provider("test", provider)

        assert registry.is_provider_registered("test")

    def test_provider_classes_registration(self):
        """Test that all expected provider classes are registered."""
        registry = ModelProviderRegistry()

        expected_providers = ["openai", "google", "anthropic"]

        for provider_name in expected_providers:
            assert provider_name in registry._provider_classes

            # Verify we can access the class
            provider_class = registry._provider_classes[provider_name]
            assert issubclass(provider_class, BaseAIProvider)


class TestGlobalRegistry:
    """Test global registry functionality."""

    def test_get_model_registry_singleton(self):
        """Test that get_model_registry returns singleton."""
        registry1 = get_model_registry()
        registry2 = get_model_registry()

        assert registry1 is registry2
        assert isinstance(registry1, ModelProviderRegistry)

    def test_global_registry_persistence(self):
        """Test that global registry persists state."""
        from alfred.llm.registry import model_registry

        # Clear any existing state
        model_registry._providers.clear()
        model_registry._model_to_provider_map.clear()

        provider = MockProvider("test")
        model_registry.register_provider("test", provider)

        # Get registry through function - should have same state
        registry = get_model_registry()
        assert registry.is_provider_registered("test")
        assert registry._providers["test"] == provider


class TestRegistryIntegration:
    """Test registry integration scenarios."""

    def test_full_provider_lifecycle(self):
        """Test complete provider registration and usage lifecycle."""
        registry = ModelProviderRegistry()

        # Create mock provider with realistic models
        models = [
            ModelInfo(
                name="fast-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096, max_output_tokens=1024, cost_per_input_token=0.001, cost_per_output_token=0.002
            ),
            ModelInfo(
                name="smart-model",
                provider="test",
                capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=32768,
                max_output_tokens=4096,
                cost_per_input_token=0.01,
                cost_per_output_token=0.02,
            ),
        ]

        provider = MockProvider("test", models)

        # Register provider
        registry.register_provider("test", provider)

        # Verify registration
        assert registry.is_provider_registered("test")

        # Get provider for specific models
        fast_provider = registry.get_provider_for_model("fast-model")
        smart_provider = registry.get_provider_for_model("smart-model")
        assert fast_provider == provider
        assert smart_provider == provider

        # Get all models
        all_models = registry.get_available_models()
        assert len(all_models) == 2

        # Verify model details
        model_names = [model.name for model in all_models]
        assert "fast-model" in model_names
        assert "smart-model" in model_names

    def test_multiple_provider_coordination(self):
        """Test coordination between multiple providers."""
        registry = ModelProviderRegistry()

        # Provider 1: Fast, cheap models
        fast_models = [
            ModelInfo(name="fast-chat", provider="fast-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096, cost_per_input_token=0.0001, cost_per_output_token=0.0001)
        ]

        # Provider 2: Smart, expensive models
        smart_models = [
            ModelInfo(
                name="smart-chat",
                provider="smart-provider",
                capabilities=[ModelCapability.REASONING, ModelCapability.ANALYSIS],
                context_window=32768,
                cost_per_input_token=0.01,
                cost_per_output_token=0.01,
            )
        ]

        fast_provider = MockProvider("fast-provider", fast_models)
        smart_provider = MockProvider("smart-provider", smart_models)

        registry.register_provider("fast-provider", fast_provider)
        registry.register_provider("smart-provider", smart_provider)

        # Test model routing
        assert registry.get_provider_for_model("fast-chat") == fast_provider
        assert registry.get_provider_for_model("smart-chat") == smart_provider

        # Test provider enumeration
        providers = registry.get_registered_providers()
        assert len(providers) == 2
        assert "fast-provider" in providers
        assert "smart-provider" in providers

        # Test combined model list
        all_models = registry.get_available_models()
        assert len(all_models) == 2

        # Verify model routing by capability
        for model in all_models:
            if ModelCapability.REASONING in model.capabilities:
                assert registry.get_provider_for_model(model.name) == smart_provider
            else:
                assert registry.get_provider_for_model(model.name) == fast_provider
