"""
AI Provider Registry and Factory for Alfred Task Manager

Following Alfred's principles:
- PROVIDER FACTORY IS IMMUTABLE
- ONE REGISTRY TO RULE THEM ALL
- NO PROVIDER LEAKAGE
- CONFIGURATION-DRIVEN
"""

from typing import Dict, List, Optional, Type
from functools import lru_cache

from .providers.base import BaseAIProvider, ModelInfo, ModelNotFoundError, ProviderError
from .providers.openai_provider import OpenAIProvider
from .providers.google_provider import GoogleProvider
from .providers.anthropic_provider import AnthropicProvider


class ModelProviderRegistry:
    """
    Central registry for AI providers and models.

    Following Task Provider principles:
    - Provider selection through configuration
    - Uniform model routing
    - No provider-specific logic exposed
    """

    def __init__(self):
        self._providers: Dict[str, BaseAIProvider] = {}
        self._model_to_provider_map: Dict[str, str] = {}
        self._provider_classes: Dict[str, Type[BaseAIProvider]] = {
            "openai": OpenAIProvider,
            "google": GoogleProvider,
            "anthropic": AnthropicProvider,
        }

    def register_provider(self, provider_name: str, provider_instance: BaseAIProvider) -> None:
        """Register a provider instance."""
        if provider_name in self._providers:
            raise ValueError(f"Provider {provider_name} already registered")

        self._providers[provider_name] = provider_instance

        # Build model mapping
        try:
            models = provider_instance.get_available_models()
            for model in models:
                if model.name in self._model_to_provider_map:
                    # Handle model name conflicts by prefixing with provider
                    prefixed_name = f"{provider_name}:{model.name}"
                    self._model_to_provider_map[prefixed_name] = provider_name
                else:
                    self._model_to_provider_map[model.name] = provider_name
        except Exception as e:
            # Don't fail registration if model enumeration fails
            # Provider may still work for specific model requests
            pass

    def create_provider(self, provider_name: str, **kwargs) -> BaseAIProvider:
        """Factory method to create provider instances."""
        if provider_name not in self._provider_classes:
            raise ValueError(f"Unknown provider type: {provider_name}")

        provider_class = self._provider_classes[provider_name]
        return provider_class(**kwargs)

    def get_provider_for_model(self, model_name: str) -> BaseAIProvider:
        """Get the provider that handles a specific model."""
        # Check direct model name mapping
        if model_name in self._model_to_provider_map:
            provider_name = self._model_to_provider_map[model_name]
            return self._providers[provider_name]

        # Check prefixed model name (provider:model)
        if ":" in model_name:
            provider_name, _ = model_name.split(":", 1)
            if provider_name in self._providers:
                return self._providers[provider_name]

        # Fallback: try each provider to see if they support the model
        for provider in self._providers.values():
            if provider.validate_model(model_name):
                return provider

        raise ModelNotFoundError(f"No provider found for model: {model_name}")

    def get_available_models(self) -> List[ModelInfo]:
        """Get all available models across all providers."""
        all_models = []
        for provider in self._providers.values():
            try:
                models = provider.get_available_models()
                all_models.extend(models)
            except Exception:
                # Skip providers that fail to enumerate models
                continue
        return all_models

    def get_registered_providers(self) -> List[str]:
        """Get list of registered provider names."""
        return list(self._providers.keys())

    def is_provider_registered(self, provider_name: str) -> bool:
        """Check if a provider is registered."""
        return provider_name in self._providers


# Global registry instance (singleton)
model_registry = ModelProviderRegistry()


@lru_cache(maxsize=1)
def get_model_registry() -> ModelProviderRegistry:
    """Get the global model registry instance."""
    return model_registry
