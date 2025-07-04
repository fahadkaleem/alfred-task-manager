"""
Tests for Google provider implementation.

Tests the Google provider with mocked API calls following Alfred's testing principles.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from alfred.llm.providers.google_provider import GoogleProvider
from alfred.llm.providers.base import (
    ModelResponse,
    ModelInfo,
    ModelCapability,
    ProviderError,
    ModelNotFoundError,
    QuotaExceededError,
    AuthenticationError,
)


class TestGoogleProviderInitialization:
    """Test Google provider initialization."""

    @patch("alfred.llm.providers.google_provider.genai.configure")
    def test_successful_initialization(self, mock_configure):
        """Test successful provider initialization."""
        provider = GoogleProvider(api_key="test-key")

        mock_configure.assert_called_once_with(api_key="test-key")
        assert provider.api_key == "test-key"

    @patch("alfred.llm.providers.google_provider.genai.configure")
    def test_initialization_failure(self, mock_configure):
        """Test provider initialization failure."""
        mock_configure.side_effect = Exception("Invalid API key")

        with pytest.raises(AuthenticationError) as exc_info:
            GoogleProvider(api_key="invalid-key")

        assert "Failed to initialize Google Gemini client" in str(exc_info.value)


class TestGoogleProviderGenerateContent:
    """Test content generation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.google_provider.genai.configure"):
            self.provider = GoogleProvider(api_key="test-key")

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    @patch("alfred.llm.providers.google_provider.genai.types.GenerationConfig")
    def test_successful_content_generation(self, mock_generation_config, mock_model_class):
        """Test successful content generation."""
        # Mock model and response
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        # Mock candidate and safety rating
        mock_safety_rating = Mock()
        mock_candidate = Mock()
        mock_candidate.finish_reason = "STOP"
        mock_candidate.safety_ratings = [mock_safety_rating]

        # Mock usage metadata
        mock_usage = Mock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 20
        mock_usage.total_token_count = 30

        mock_response = Mock()
        mock_response.text = "Generated content"
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = mock_usage

        mock_model.generate_content.return_value = mock_response

        mock_config = Mock()
        mock_generation_config.return_value = mock_config

        result = self.provider.generate_content(prompt="Test prompt", model_name="gemini-1.5-pro", temperature=0.7, max_tokens=100)

        assert isinstance(result, ModelResponse)
        assert result.content == "Generated content"
        assert result.model_name == "gemini-1.5-pro"
        assert result.usage == {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30}
        assert result.metadata["finish_reason"] == "STOP"
        assert len(result.metadata["safety_ratings"]) == 1

        # Verify API calls
        mock_model_class.assert_called_once_with("gemini-1.5-pro")
        mock_generation_config.assert_called_once_with(temperature=0.7, max_output_tokens=100)
        mock_model.generate_content.assert_called_once_with("Test prompt", generation_config=mock_config)

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    @patch("alfred.llm.providers.google_provider.genai.types.GenerationConfig")
    def test_content_generation_with_empty_response(self, mock_generation_config, mock_model_class):
        """Test handling of empty content response."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        mock_response = Mock()
        mock_response.text = None  # Empty text
        mock_response.candidates = []
        mock_response.usage_metadata = None

        mock_model.generate_content.return_value = mock_response

        result = self.provider.generate_content(prompt="Test prompt", model_name="gemini-1.5-pro")

        assert result.content == ""
        assert result.usage == {}
        assert result.metadata["finish_reason"] is None
        assert result.metadata["safety_ratings"] == []

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_content_generation_permission_denied_error(self, mock_model_class):
        """Test Google permission denied error handling."""
        from google.api_core import exceptions as google_exceptions

        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = google_exceptions.PermissionDenied("Access denied")

        with pytest.raises(AuthenticationError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gemini-1.5-pro")

        assert "Google API authentication failed" in str(exc_info.value)

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_content_generation_not_found_error(self, mock_model_class):
        """Test Google not found error handling."""
        from google.api_core import exceptions as google_exceptions

        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = google_exceptions.NotFound("Model not found")

        with pytest.raises(ModelNotFoundError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="invalid-model")

        assert "Model invalid-model not found" in str(exc_info.value)

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_content_generation_resource_exhausted_error(self, mock_model_class):
        """Test Google resource exhausted error handling."""
        from google.api_core import exceptions as google_exceptions

        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = google_exceptions.ResourceExhausted("Quota exceeded")

        with pytest.raises(QuotaExceededError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gemini-1.5-pro")

        assert "Google API quota exceeded" in str(exc_info.value)

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_content_generation_api_key_error(self, mock_model_class):
        """Test API key error handling."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API_KEY is invalid")

        with pytest.raises(AuthenticationError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gemini-1.5-pro")

        assert "Google API key error" in str(exc_info.value)

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_content_generation_generic_error(self, mock_model_class):
        """Test generic error handling."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("unknown error")

        with pytest.raises(ProviderError) as exc_info:
            self.provider.generate_content(prompt="Test prompt", model_name="gemini-1.5-pro")

        assert "Google API error" in str(exc_info.value)


class TestGoogleProviderTokenCounting:
    """Test token counting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.google_provider.genai.configure"):
            self.provider = GoogleProvider(api_key="test-key")

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_token_counting_success(self, mock_model_class):
        """Test successful token counting."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        mock_response = Mock()
        mock_response.total_tokens = 42
        mock_model.count_tokens.return_value = mock_response

        result = self.provider.count_tokens("Hello world", "gemini-1.5-pro")

        assert result == 42
        mock_model_class.assert_called_once_with("gemini-1.5-pro")
        mock_model.count_tokens.assert_called_once_with("Hello world")

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_token_counting_error(self, mock_model_class):
        """Test token counting error handling."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.count_tokens.side_effect = Exception("Token counting error")

        with pytest.raises(ProviderError) as exc_info:
            self.provider.count_tokens("Hello world", "gemini-1.5-pro")

        assert "Token counting failed" in str(exc_info.value)


class TestGoogleProviderModelManagement:
    """Test model management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.google_provider.genai.configure"):
            self.provider = GoogleProvider(api_key="test-key")

    def test_get_available_models(self):
        """Test getting available models."""
        models = self.provider.get_available_models()

        assert len(models) == 4
        assert all(isinstance(model, ModelInfo) for model in models)

        model_names = [model.name for model in models]
        expected_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-1.5-flash-8b"]
        assert all(name in model_names for name in expected_models)

        # Test specific model properties
        pro_model = next(model for model in models if model.name == "gemini-1.5-pro")
        assert pro_model.provider == "google"
        assert ModelCapability.TEXT_GENERATION in pro_model.capabilities
        assert ModelCapability.REASONING in pro_model.capabilities
        assert ModelCapability.CODE_GENERATION in pro_model.capabilities
        assert ModelCapability.ANALYSIS in pro_model.capabilities
        assert pro_model.context_window == 1048576  # 1M tokens
        assert pro_model.max_output_tokens == 8192

    def test_model_context_windows(self):
        """Test that large context window models are properly configured."""
        models = self.provider.get_available_models()
        model_dict = {model.name: model for model in models}

        # Check 1M token context models
        large_context_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"]

        for model_name in large_context_models:
            model = model_dict[model_name]
            assert model.context_window == 1048576, f"{model_name} should have 1M context window"

        # Check smaller context model
        pro_model = model_dict["gemini-pro"]
        assert pro_model.context_window == 32768

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_validate_model_success(self, mock_model_class):
        """Test successful model validation."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        mock_response = Mock()
        mock_response.total_tokens = 5
        mock_model.count_tokens.return_value = mock_response

        result = self.provider.validate_model("gemini-1.5-pro")

        assert result is True
        mock_model_class.assert_called_once_with("gemini-1.5-pro")
        mock_model.count_tokens.assert_called_once_with("test")

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_validate_model_failure(self, mock_model_class):
        """Test model validation failure."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        mock_model.count_tokens.side_effect = Exception("Model not found")

        result = self.provider.validate_model("invalid-model")

        assert result is False

    @patch("alfred.llm.providers.google_provider.genai.GenerativeModel")
    def test_validate_model_zero_tokens(self, mock_model_class):
        """Test model validation with zero tokens response."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model

        mock_response = Mock()
        mock_response.total_tokens = 0  # Zero tokens should fail validation
        mock_model.count_tokens.return_value = mock_response

        result = self.provider.validate_model("gemini-1.5-pro")

        assert result is False


class TestGoogleProviderIntegration:
    """Test provider integration and real-world scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch("alfred.llm.providers.google_provider.genai.configure"):
            self.provider = GoogleProvider(api_key="test-key")

    def test_provider_interface_compliance(self):
        """Test that GoogleProvider implements BaseAIProvider interface."""
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
            assert model.provider == "google"
            assert len(model.capabilities) > 0
            assert model.context_window > 0
            assert model.max_output_tokens is not None
            assert model.cost_per_input_token is not None
            assert model.cost_per_output_token is not None

            # Validate capabilities are valid enums
            for capability in model.capabilities:
                assert capability in ModelCapability

    def test_model_capabilities_progression(self):
        """Test that model capabilities make logical sense."""
        models = self.provider.get_available_models()
        model_dict = {model.name: model for model in models}

        # Gemini 1.5 Pro should have most capabilities
        pro_model = model_dict["gemini-1.5-pro"]
        assert len(pro_model.capabilities) == 4

        # Flash models should have fewer capabilities than Pro
        flash_model = model_dict["gemini-1.5-flash"]
        assert len(flash_model.capabilities) == 3

        # 8B model should have fewest capabilities
        flash_8b_model = model_dict["gemini-1.5-flash-8b"]
        assert len(flash_8b_model.capabilities) == 1
        assert ModelCapability.TEXT_GENERATION in flash_8b_model.capabilities

    def test_usage_metadata_handling(self):
        """Test proper handling of usage metadata variations."""
        with patch("alfred.llm.providers.google_provider.genai.GenerativeModel") as mock_model_class, patch("alfred.llm.providers.google_provider.genai.types.GenerationConfig"):
            mock_model = Mock()
            mock_model_class.return_value = mock_model

            # Test with partial usage metadata
            mock_usage = Mock()
            mock_usage.prompt_token_count = 10
            # Missing candidates_token_count and total_token_count

            mock_response = Mock()
            mock_response.text = "test content"
            mock_response.candidates = []
            mock_response.usage_metadata = mock_usage

            mock_model.generate_content.return_value = mock_response

            result = self.provider.generate_content("test", "gemini-1.5-pro")

            assert result.usage["input_tokens"] == 10
            assert result.usage["output_tokens"] == 0  # Default when missing
            assert result.usage["total_tokens"] == 0  # Default when missing
