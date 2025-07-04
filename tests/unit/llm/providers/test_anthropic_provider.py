"""
Tests for Anthropic provider implementation.

Tests the Anthropic provider with mocked API calls following Alfred's testing principles.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from alfred.llm.providers.anthropic_provider import AnthropicProvider
from alfred.llm.providers.base import (
    ModelResponse,
    ModelInfo,
    ModelCapability,
    ProviderError,
    ModelNotFoundError,
    QuotaExceededError,
    AuthenticationError,
)


class TestAnthropicProviderInitialization:
    """Test Anthropic provider initialization."""

    @patch("alfred.llm.providers.anthropic_provider.anthropic.Anthropic")
    def test_successful_initialization(self, mock_anthropic):
        """Test successful provider initialization."""
        provider = AnthropicProvider(api_key="test-key")

        mock_anthropic.assert_called_once_with(api_key="test-key")
        assert provider.client is not None

    @patch("alfred.llm.providers.anthropic_provider.anthropic.Anthropic")
    def test_initialization_failure(self, mock_anthropic):
        """Test provider initialization failure."""
        mock_anthropic.side_effect = Exception("Invalid API key")

        with pytest.raises(AuthenticationError) as exc_info:
            AnthropicProvider(api_key="invalid-key")

        assert "Failed to initialize Anthropic client" in str(exc_info.value)


class TestAnthropicProviderGenerateContent:
    """Test content generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.anthropic_provider.anthropic.Anthropic"):
            self.provider = AnthropicProvider(api_key="test-key")

    def test_successful_content_generation(self):
        """Test successful content generation."""
        # Mock response object
        mock_content = Mock()
        mock_content.text = "Generated content"

        mock_usage = Mock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20

        mock_response = Mock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        mock_response.stop_reason = "end_turn"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.id = "msg_123"

        self.provider.client.messages.create = Mock(return_value=mock_response)

        result = self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022", temperature=0.7, max_tokens=100)

        assert isinstance(result, ModelResponse)
        assert result.content == "Generated content"
        assert result.model_name == "claude-3-5-sonnet-20241022"
        assert result.usage == {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
        assert result.metadata["stop_reason"] == "end_turn"
        assert result.metadata["model"] == "claude-3-5-sonnet-20241022"
        assert result.metadata["response_id"] == "msg_123"

        # Verify API call
        self.provider.client.messages.create.assert_called_once_with(model="claude-3-5-sonnet-20241022", max_tokens=100, temperature=0.7, messages=[{"role": "user", "content": "Test prompt"}])

    def test_content_generation_with_default_max_tokens(self):
        """Test content generation with default max_tokens."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Test")]
        mock_response.usage = None
        mock_response.stop_reason = "end_turn"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.id = "msg_123"

        self.provider.client.messages.create = Mock(return_value=mock_response)

        self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        # Verify default max_tokens is used
        self.provider.client.messages.create.assert_called_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,  # Default value
            temperature=0.5,  # Default temperature
            messages=[{"role": "user", "content": "Test prompt"}],
        )

    def test_content_generation_with_empty_response(self):
        """Test handling of empty content response."""
        mock_response = Mock()
        mock_response.content = []  # Empty content
        mock_response.usage = None
        mock_response.stop_reason = "length"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.id = "msg_123"

        self.provider.client.messages.create = Mock(return_value=mock_response)

        result = self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        assert result.content == ""
        assert result.usage == {}

    def test_content_generation_anthropic_authentication_error(self):
        """Test Anthropic authentication error handling."""
        import anthropic

        self.provider.client.messages.create = Mock(side_effect=anthropic.AuthenticationError("Invalid API key"))

        with pytest.raises(AuthenticationError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        assert "Anthropic authentication failed" in str(exc_info.value)

    def test_content_generation_anthropic_not_found_error(self):
        """Test Anthropic model not found error handling."""
        import anthropic

        self.provider.client.messages.create = Mock(side_effect=anthropic.NotFoundError("Model not found"))

        with pytest.raises(ModelNotFoundError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="invalid-model")

        assert "Model invalid-model not found" in str(exc_info.value)

    def test_content_generation_anthropic_rate_limit_error(self):
        """Test Anthropic rate limit error handling."""
        import anthropic

        self.provider.client.messages.create = Mock(side_effect=anthropic.RateLimitError("Rate limit exceeded"))

        with pytest.raises(QuotaExceededError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        assert "Anthropic rate limit exceeded" in str(exc_info.value)

    def test_content_generation_anthropic_api_error(self):
        """Test Anthropic API error handling."""
        import anthropic

        self.provider.client.messages.create = Mock(side_effect=anthropic.APIError("API error"))

        with pytest.raises(ProviderError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        assert "Anthropic API error" in str(exc_info.value)

    def test_content_generation_generic_api_key_error(self):
        """Test generic API key error handling."""
        self.provider.client.messages.create = Mock(side_effect=Exception("api_key is invalid"))

        with pytest.raises(AuthenticationError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        assert "Anthropic API key error" in str(exc_info.value)

    def test_content_generation_generic_error(self):
        """Test generic error handling."""
        self.provider.client.messages.create = Mock(side_effect=Exception("unknown error"))

        with pytest.raises(ProviderError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="claude-3-5-sonnet-20241022")

        assert "Anthropic error" in str(exc_info.value)


class TestAnthropicProviderTokenCounting:
    """Test token counting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.anthropic_provider.anthropic.Anthropic"):
            self.provider = AnthropicProvider(api_key="test-key")

    def test_token_counting_success(self):
        """Test successful token counting."""
        self.provider.client.count_tokens = Mock(return_value=42)

        result = self.provider.count_tokens("Hello world", "claude-3-5-sonnet-20241022")

        assert result == 42
        self.provider.client.count_tokens.assert_called_once_with("Hello world")

    def test_token_counting_fallback(self):
        """Test token counting fallback when API fails."""
        self.provider.client.count_tokens = Mock(side_effect=Exception("API error"))

        result = self.provider.count_tokens("Hello world test", "claude-3-5-sonnet-20241022")

        # Fallback: len(text) // 4 = 17 // 4 = 4
        assert result == 4

    def test_token_counting_fallback_calculation(self):
        """Test token counting fallback calculation accuracy."""
        self.provider.client.count_tokens = Mock(side_effect=Exception("API error"))

        # Test various text lengths
        test_cases = [
            ("a", 0),  # 1 // 4 = 0
            ("abcd", 1),  # 4 // 4 = 1
            ("hello world", 2),  # 11 // 4 = 2
            ("a" * 20, 5),  # 20 // 4 = 5
        ]

        for text, expected in test_cases:
            result = self.provider.count_tokens(text, "claude-3-5-sonnet-20241022")
            assert result == expected


class TestAnthropicProviderModelManagement:
    """Test model management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.anthropic_provider.anthropic.Anthropic"):
            self.provider = AnthropicProvider(api_key="test-key")

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.provider.get_available_models()

        assert len(models) == 4
        assert all(isinstance(model, ModelInfo) for model in models)

        model_names = [model.name for model in models]
        expected_models = ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        assert all(name in model_names for name in expected_models)

        # Test specific model properties
        sonnet_model = next(model for model in models if model.name == "claude-3-5-sonnet-20241022")
        assert sonnet_model.provider == "anthropic"
        assert ModelCapability.TEXT_GENERATION in sonnet_model.capabilities
        assert ModelCapability.REASONING in sonnet_model.capabilities
        assert ModelCapability.CODE_GENERATION in sonnet_model.capabilities
        assert ModelCapability.ANALYSIS in sonnet_model.capabilities
        assert sonnet_model.context_window == 200000
        assert sonnet_model.max_output_tokens == 8192

    def test_validate_model_success(self):
        """Test successful model validation."""
        mock_response = Mock()
        self.provider.client.messages.create = Mock(return_value=mock_response)

        result = self.provider.validate_model("claude-3-5-sonnet-20241022")

        assert result is True
        self.provider.client.messages.create.assert_called_once_with(model="claude-3-5-sonnet-20241022", max_tokens=1, messages=[{"role": "user", "content": "test"}])

    def test_validate_model_failure(self):
        """Test model validation failure."""
        self.provider.client.messages.create = Mock(side_effect=Exception("Model not found"))

        result = self.provider.validate_model("invalid-model")

        assert result is False


class TestAnthropicProviderIntegration:
    """Test provider integration and real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.anthropic_provider.anthropic.Anthropic"):
            self.provider = AnthropicProvider(api_key="test-key")

    def test_provider_interface_compliance(self):
        """Test that AnthropicProvider implements BaseAIProvider interface."""
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
            assert model.provider == "anthropic"
            assert len(model.capabilities) > 0
            assert model.context_window > 0
            assert model.max_output_tokens is not None
            assert model.cost_per_input_token is not None
            assert model.cost_per_output_token is not None

            # Validate capabilities are valid enums
            for capability in model.capabilities:
                assert capability in ModelCapability

    def test_model_capabilities_hierarchy(self):
        """Test that models have appropriate capability hierarchies."""
        models = self.provider.get_available_models()
        model_dict = {model.name: model for model in models}

        # Claude 3.5 Sonnet should have all capabilities
        sonnet_35 = model_dict["claude-3-5-sonnet-20241022"]
        assert len(sonnet_35.capabilities) == 4
        assert all(cap in sonnet_35.capabilities for cap in ModelCapability)

        # Claude 3 Opus should have all capabilities
        opus = model_dict["claude-3-opus-20240229"]
        assert len(opus.capabilities) == 4

        # Claude 3 Haiku should have fewer capabilities
        haiku = model_dict["claude-3-haiku-20240307"]
        assert len(haiku.capabilities) == 2
        assert ModelCapability.TEXT_GENERATION in haiku.capabilities
        assert ModelCapability.CODE_GENERATION in haiku.capabilities

    def test_error_handling_specificity(self):
        """Test that error handling is specific and appropriate."""
        # Test specific Anthropic exceptions
        import anthropic

        # Authentication error
        self.provider.client.messages.create = Mock(side_effect=anthropic.AuthenticationError("auth failed"))
        with pytest.raises(AuthenticationError):
            self.provider.generate_content("test", "claude-3-5-sonnet-20241022")

        # Not found error
        self.provider.client.messages.create = Mock(side_effect=anthropic.NotFoundError("not found"))
        with pytest.raises(ModelNotFoundError):
            self.provider.generate_content("test", "claude-3-5-sonnet-20241022")

        # Rate limit error
        self.provider.client.messages.create = Mock(side_effect=anthropic.RateLimitError("rate limit"))
        with pytest.raises(QuotaExceededError):
            self.provider.generate_content("test", "claude-3-5-sonnet-20241022")

        # API error
        self.provider.client.messages.create = Mock(side_effect=anthropic.APIError("api error"))
        with pytest.raises(ProviderError):
            self.provider.generate_content("test", "claude-3-5-sonnet-20241022")
