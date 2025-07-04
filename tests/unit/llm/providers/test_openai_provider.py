"""
Tests for OpenAI provider implementation.

Tests the OpenAI provider with mocked API calls following Alfred's testing principles.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from alfred.llm.providers.openai_provider import OpenAIProvider
from alfred.llm.providers.base import (
    ModelResponse,
    ModelInfo,
    ModelCapability,
    ProviderError,
    ModelNotFoundError,
    QuotaExceededError,
    AuthenticationError,
)


class TestOpenAIProviderInitialization:
    """Test OpenAI provider initialization."""

    @patch("alfred.llm.providers.openai_provider.OpenAI")
    @patch("alfred.llm.providers.openai_provider.AsyncOpenAI")
    def test_successful_initialization(self, mock_async_openai, mock_openai):
        """Test successful provider initialization."""
        provider = OpenAIProvider(api_key="test-key")

        mock_openai.assert_called_once_with(api_key="test-key", base_url=None)
        mock_async_openai.assert_called_once_with(api_key="test-key", base_url=None)
        assert provider.client is not None
        assert provider.async_client is not None

    @patch("alfred.llm.providers.openai_provider.OpenAI")
    @patch("alfred.llm.providers.openai_provider.AsyncOpenAI")
    def test_initialization_with_base_url(self, mock_async_openai, mock_openai):
        """Test provider initialization with custom base URL."""
        provider = OpenAIProvider(api_key="test-key", base_url="https://api.custom.com")

        mock_openai.assert_called_once_with(api_key="test-key", base_url="https://api.custom.com")
        mock_async_openai.assert_called_once_with(api_key="test-key", base_url="https://api.custom.com")

    @patch("alfred.llm.providers.openai_provider.OpenAI")
    def test_initialization_failure(self, mock_openai):
        """Test provider initialization failure."""
        mock_openai.side_effect = Exception("Invalid API key")

        with pytest.raises(AuthenticationError) as exc_info:
            OpenAIProvider(api_key="invalid-key")

        assert "Failed to initialize OpenAI client" in str(exc_info.value)


class TestOpenAIProviderGenerateContent:
    """Test content generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.openai_provider.OpenAI"), patch("alfred.llm.providers.openai_provider.AsyncOpenAI"):
            self.provider = OpenAIProvider(api_key="test-key")

    def test_successful_content_generation(self):
        """Test successful content generation."""
        # Mock response object
        mock_choice = Mock()
        mock_choice.message.content = "Generated content"
        mock_choice.finish_reason = "stop"

        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage
        mock_response.id = "response-123"
        mock_response.created = 1234567890

        self.provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = self.provider.generate_content(prompt="Test prompt", model_name="gpt-4", temperature=0.7, max_tokens=100)

        assert isinstance(result, ModelResponse)
        assert result.content == "Generated content"
        assert result.model_name == "gpt-4"
        assert result.usage == {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
        assert result.metadata["finish_reason"] == "stop"
        assert result.metadata["response_id"] == "response-123"
        assert result.metadata["created"] == 1234567890

        # Verify API call
        self.provider.client.chat.completions.create.assert_called_once_with(model="gpt-4", messages=[{"role": "user", "content": "Test prompt"}], temperature=0.7, max_tokens=100)

    def test_content_generation_with_empty_response(self):
        """Test handling of empty content response."""
        mock_choice = Mock()
        mock_choice.message.content = None
        mock_choice.finish_reason = "length"

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.usage = None
        mock_response.id = "response-123"
        mock_response.created = 1234567890

        self.provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = self.provider.generate_content(prompt="Test prompt", model_name="gpt-4")

        assert result.content == ""
        assert result.usage == {}

    def test_content_generation_model_not_found_error(self):
        """Test model not found error handling."""
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("model 'invalid-model' not found"))

        with pytest.raises(ModelNotFoundError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="invalid-model")

        assert "Model invalid-model not found" in str(exc_info.value)

    def test_content_generation_quota_exceeded_error(self):
        """Test quota exceeded error handling."""
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("rate limit exceeded"))

        with pytest.raises(QuotaExceededError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gpt-4")

        assert "OpenAI quota exceeded" in str(exc_info.value)

    def test_content_generation_authentication_error(self):
        """Test authentication error handling."""
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("invalid api_key provided"))

        with pytest.raises(AuthenticationError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gpt-4")

        assert "OpenAI authentication failed" in str(exc_info.value)

    def test_content_generation_generic_error(self):
        """Test generic error handling."""
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("unknown error"))

        with pytest.raises(ProviderError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gpt-4")

        assert "OpenAI API error" in str(exc_info.value)


class TestOpenAIProviderTokenCounting:
    """Test token counting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.openai_provider.OpenAI"), patch("alfred.llm.providers.openai_provider.AsyncOpenAI"):
            self.provider = OpenAIProvider(api_key="test-key")

    @patch("alfred.llm.providers.openai_provider.tiktoken.get_encoding")
    def test_token_counting_known_model(self, mock_get_encoding):
        """Test token counting for known models."""
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]  # 5 tokens
        mock_get_encoding.return_value = mock_encoding

        result = self.provider.count_tokens("Hello world", "gpt-4")

        assert result == 5
        mock_get_encoding.assert_called_once_with("cl100k_base")
        mock_encoding.encode.assert_called_once_with("Hello world")

    @patch("alfred.llm.providers.openai_provider.tiktoken.get_encoding")
    def test_token_counting_unknown_model(self, mock_get_encoding):
        """Test token counting for unknown models defaults to cl100k_base."""
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2, 3]  # 3 tokens
        mock_get_encoding.return_value = mock_encoding

        result = self.provider.count_tokens("Hello", "unknown-model")

        assert result == 3
        mock_get_encoding.assert_called_once_with("cl100k_base")

    @patch("alfred.llm.providers.openai_provider.tiktoken.get_encoding")
    def test_token_counting_error(self, mock_get_encoding):
        """Test token counting error handling."""
        mock_get_encoding.side_effect = Exception("Encoding error")

        with pytest.raises(ProviderError) as exc_info:
            self.provider.count_tokens("Hello", "gpt-4")

        assert "Token counting failed" in str(exc_info.value)

    @pytest.mark.parametrize(
        "model_name,expected_encoding",
        [
            ("gpt-4", "cl100k_base"),
            ("gpt-4-turbo", "cl100k_base"),
            ("gpt-3.5-turbo", "cl100k_base"),
            ("o3", "cl100k_base"),
            ("o3-mini", "cl100k_base"),
            ("o4-mini", "cl100k_base"),
        ],
    )
    @patch("alfred.llm.providers.openai_provider.tiktoken.get_encoding")
    def test_token_counting_model_encodings(self, mock_get_encoding, model_name, expected_encoding):
        """Test that all supported models use correct encodings."""
        mock_encoding = Mock()
        mock_encoding.encode.return_value = [1, 2]
        mock_get_encoding.return_value = mock_encoding

        self.provider.count_tokens("test", model_name)

        mock_get_encoding.assert_called_once_with(expected_encoding)


class TestOpenAIProviderModelManagement:
    """Test model management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.openai_provider.OpenAI"), patch("alfred.llm.providers.openai_provider.AsyncOpenAI"):
            self.provider = OpenAIProvider(api_key="test-key")

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.provider.get_available_models()

        assert len(models) == 6
        assert all(isinstance(model, ModelInfo) for model in models)

        model_names = [model.name for model in models]
        expected_models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "o3", "o3-mini", "o4-mini"]
        assert all(name in model_names for name in expected_models)

        # Test specific model properties
        gpt4_model = next(model for model in models if model.name == "gpt-4")
        assert gpt4_model.provider == "openai"
        assert ModelCapability.TEXT_GENERATION in gpt4_model.capabilities
        assert ModelCapability.REASONING in gpt4_model.capabilities
        assert gpt4_model.context_window == 8192
        assert gpt4_model.max_output_tokens == 4096

    def test_validate_model_success(self):
        """Test successful model validation."""
        mock_response = Mock()
        self.provider.client.chat.completions.create = Mock(return_value=mock_response)

        result = self.provider.validate_model("gpt-4")

        assert result is True
        self.provider.client.chat.completions.create.assert_called_once_with(model="gpt-4", messages=[{"role": "user", "content": "test"}], max_tokens=1)

    def test_validate_model_failure(self):
        """Test model validation failure."""
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("Model not found"))

        result = self.provider.validate_model("invalid-model")

        assert result is False


class TestOpenAIProviderIntegration:
    """Test provider integration and real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.openai_provider.OpenAI"), patch("alfred.llm.providers.openai_provider.AsyncOpenAI"):
            self.provider = OpenAIProvider(api_key="test-key")

    def test_provider_interface_compliance(self):
        """Test that OpenAIProvider implements BaseAIProvider interface."""
        from alfred.llm.providers.base import BaseAIProvider

        assert isinstance(self.provider, BaseAIProvider)

        # Check all required methods exist
        assert hasattr(self.provider, "generate_content")
        assert hasattr(self.provider, "count_tokens")
        assert hasattr(self.provider, "get_available_models")
        assert hasattr(self.provider, "validate_model")

    def test_model_info_completeness(self):
        """Test that all model info is complete and valid."""
        models = self.provider.get_available_models()

        for model in models:
            assert model.name
            assert model.provider == "openai"
            assert len(model.capabilities) > 0
            assert model.context_window > 0
            assert model.max_output_tokens is not None
            assert model.cost_per_input_token is not None
            assert model.cost_per_output_token is not None

            # Validate capabilities are valid enums
            for capability in model.capabilities:
                assert capability in ModelCapability

    def test_error_mapping_consistency(self):
        """Test that error mapping is consistent across methods."""
        # Model not found
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("model 'test' not found"))

        with pytest.raises(ModelNotFoundError):
            self.provider.generate_content("test", "invalid-model")

        # Quota exceeded
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("quota exceeded"))

        with pytest.raises(QuotaExceededError):
            self.provider.generate_content("test", "gpt-4")

        # Authentication error
        self.provider.client.chat.completions.create = Mock(side_effect=Exception("authentication failed"))

        with pytest.raises(AuthenticationError):
            self.provider.generate_content("test", "gpt-4")
