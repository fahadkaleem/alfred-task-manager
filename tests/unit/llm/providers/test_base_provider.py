"""
Tests for base AI provider interface and data models.

Tests the abstract base class interface compliance and data model validation
following Alfred's testing principles.
"""

import pytest
from abc import ABC
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from alfred.llm.providers.base import (
    BaseAIProvider,
    ModelResponse,
    ModelInfo,
    ModelCapability,
    ProviderError,
    ModelNotFoundError,
    QuotaExceededError,
    AuthenticationError,
)


class TestModelCapability:
    """Test ModelCapability enum."""

    def test_model_capability_values(self):
        """Test all model capability enum values."""
        assert ModelCapability.TEXT_GENERATION == "text_generation"
        assert ModelCapability.CODE_GENERATION == "code_generation"
        assert ModelCapability.REASONING == "reasoning"
        assert ModelCapability.ANALYSIS == "analysis"

    def test_model_capability_enum_membership(self):
        """Test enum membership."""
        assert "text_generation" in ModelCapability
        assert "code_generation" in ModelCapability
        assert "reasoning" in ModelCapability
        assert "analysis" in ModelCapability


class TestModelResponse:
    """Test ModelResponse data model."""

    def test_model_response_creation(self):
        """Test basic model response creation."""
        response = ModelResponse(content="Test content", model_name="test-model", usage={"input_tokens": 10, "output_tokens": 20}, metadata={"provider": "test"})

        assert response.content == "Test content"
        assert response.model_name == "test-model"
        assert response.usage == {"input_tokens": 10, "output_tokens": 20}
        assert response.metadata == {"provider": "test"}
        assert isinstance(response.timestamp, datetime)

    def test_model_response_default_values(self):
        """Test model response with default values."""
        response = ModelResponse(content="Test content", model_name="test-model")

        assert response.usage == {}
        assert response.metadata == {}
        assert isinstance(response.timestamp, datetime)

    def test_model_response_immutability(self):
        """Test that ModelResponse is immutable."""
        response = ModelResponse(content="Test content", model_name="test-model")

        # Pydantic raises ValidationError for frozen models
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            response.content = "Modified content"

        with pytest.raises(ValidationError):
            response.model_name = "modified-model"

    def test_model_response_timestamp_auto_generation(self):
        """Test that timestamp is automatically generated."""
        before = datetime.now(timezone.utc)
        response = ModelResponse(content="Test content", model_name="test-model")
        after = datetime.now(timezone.utc)

        assert before <= response.timestamp <= after

    def test_model_response_validation(self):
        """Test model response field validation."""
        # Missing required fields should raise validation error
        with pytest.raises(ValueError):
            ModelResponse(content="Test content")  # Missing model_name

        with pytest.raises(ValueError):
            ModelResponse(model_name="test-model")  # Missing content


class TestModelInfo:
    """Test ModelInfo data model."""

    def test_model_info_creation(self):
        """Test basic model info creation."""
        info = ModelInfo(
            name="test-model",
            provider="test-provider",
            capabilities=[ModelCapability.TEXT_GENERATION],
            context_window=4096,
            max_output_tokens=1024,
            cost_per_input_token=0.01,
            cost_per_output_token=0.02,
        )

        assert info.name == "test-model"
        assert info.provider == "test-provider"
        assert info.capabilities == [ModelCapability.TEXT_GENERATION]
        assert info.context_window == 4096
        assert info.max_output_tokens == 1024
        assert info.cost_per_input_token == 0.01
        assert info.cost_per_output_token == 0.02

    def test_model_info_optional_fields(self):
        """Test model info with optional fields."""
        info = ModelInfo(name="test-model", provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        assert info.max_output_tokens is None
        assert info.cost_per_input_token is None
        assert info.cost_per_output_token is None

    def test_model_info_immutability(self):
        """Test that ModelInfo is immutable."""
        info = ModelInfo(name="test-model", provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)

        # Pydantic raises ValidationError for frozen models
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            info.name = "modified-model"

        with pytest.raises(ValidationError):
            info.provider = "modified-provider"

    def test_model_info_multiple_capabilities(self):
        """Test model info with multiple capabilities."""
        info = ModelInfo(name="test-model", provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION, ModelCapability.REASONING], context_window=4096)

        assert len(info.capabilities) == 3
        assert ModelCapability.TEXT_GENERATION in info.capabilities
        assert ModelCapability.CODE_GENERATION in info.capabilities
        assert ModelCapability.REASONING in info.capabilities

    def test_model_info_validation(self):
        """Test model info field validation."""
        # Missing required fields should raise validation error
        with pytest.raises(ValueError):
            ModelInfo(provider="test-provider", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)  # Missing name

        with pytest.raises(ValueError):
            ModelInfo(name="test-model", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)  # Missing provider


class TestBaseAIProvider:
    """Test BaseAIProvider abstract base class."""

    def test_base_provider_is_abstract(self):
        """Test that BaseAIProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAIProvider()

    def test_base_provider_interface_methods(self):
        """Test that BaseAIProvider defines exactly 4 abstract methods."""
        abstract_methods = BaseAIProvider.__abstractmethods__
        expected_methods = {"generate_content", "count_tokens", "get_available_models", "validate_model"}

        assert abstract_methods == expected_methods
        assert len(abstract_methods) == 4

    def test_base_provider_inheritance(self):
        """Test BaseAIProvider inheritance from ABC."""
        assert issubclass(BaseAIProvider, ABC)

    def test_concrete_provider_implementation(self):
        """Test that concrete providers must implement all abstract methods."""

        class IncompleteProvider(BaseAIProvider):
            def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
                pass

            def count_tokens(self, text: str, model_name: str) -> int:
                pass

            def get_available_models(self) -> List[ModelInfo]:
                pass

            # Missing validate_model method

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_complete_provider_implementation(self):
        """Test that complete providers can be instantiated."""

        class CompleteProvider(BaseAIProvider):
            def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
                return ModelResponse(content="test", model_name=model_name)

            def count_tokens(self, text: str, model_name: str) -> int:
                return len(text.split())

            def get_available_models(self) -> List[ModelInfo]:
                return [ModelInfo(name="test-model", provider="test", capabilities=[ModelCapability.TEXT_GENERATION], context_window=4096)]

            def validate_model(self, model_name: str) -> bool:
                return model_name == "test-model"

        # Should not raise any exceptions
        provider = CompleteProvider()
        assert isinstance(provider, BaseAIProvider)


class TestProviderExceptions:
    """Test provider exception hierarchy."""

    def test_provider_error_hierarchy(self):
        """Test provider error inheritance."""
        assert issubclass(ProviderError, Exception)
        assert issubclass(ModelNotFoundError, ProviderError)
        assert issubclass(QuotaExceededError, ProviderError)
        assert issubclass(AuthenticationError, ProviderError)

    def test_provider_error_creation(self):
        """Test provider error creation."""
        error = ProviderError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_model_not_found_error(self):
        """Test ModelNotFoundError."""
        error = ModelNotFoundError("Model not found")
        assert str(error) == "Model not found"
        assert isinstance(error, ProviderError)

    def test_quota_exceeded_error(self):
        """Test QuotaExceededError."""
        error = QuotaExceededError("Quota exceeded")
        assert str(error) == "Quota exceeded"
        assert isinstance(error, ProviderError)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, ProviderError)

    def test_exception_catching(self):
        """Test that specific exceptions can be caught as ProviderError."""
        try:
            raise ModelNotFoundError("Model not found")
        except ProviderError as e:
            assert str(e) == "Model not found"

        try:
            raise QuotaExceededError("Quota exceeded")
        except ProviderError as e:
            assert str(e) == "Quota exceeded"

        try:
            raise AuthenticationError("Auth failed")
        except ProviderError as e:
            assert str(e) == "Auth failed"
