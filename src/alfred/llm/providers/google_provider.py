"""
Google Gemini Provider Implementation for Alfred Task Manager

Following Alfred's principles:
- Data normalization to standard ModelResponse
- Uniform error mapping
- No provider-specific extensions
"""

import google.generativeai as genai
from typing import List, Optional, Dict, Any
from google.api_core import exceptions as google_exceptions

from .base import BaseAIProvider, ModelResponse, ModelInfo, ModelCapability, ProviderError, ModelNotFoundError, QuotaExceededError, AuthenticationError


class GoogleProvider(BaseAIProvider):
    """Google Gemini API provider implementation."""

    def __init__(self, api_key: str):
        try:
            genai.configure(api_key=api_key)
            self.api_key = api_key
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Google Gemini client: {e}")

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using Google Gemini models."""
        try:
            # Initialize the model
            model = genai.GenerativeModel(model_name)

            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Generate content
            response = model.generate_content(prompt, generation_config=generation_config)

            content = response.text if response.text else ""

            # Normalize usage data (Gemini doesn't always provide detailed usage)
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "input_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "output_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            # Provider-specific metadata
            metadata = {
                "finish_reason": getattr(response.candidates[0], "finish_reason", None) if response.candidates else None,
                "safety_ratings": [rating for candidate in response.candidates for rating in candidate.safety_ratings] if response.candidates else [],
            }

            return ModelResponse(content=content, model_name=model_name, usage=usage, metadata=metadata)

        except google_exceptions.PermissionDenied as e:
            raise AuthenticationError(f"Google API authentication failed: {e}")
        except google_exceptions.NotFound as e:
            raise ModelNotFoundError(f"Model {model_name} not found: {e}")
        except google_exceptions.ResourceExhausted as e:
            raise QuotaExceededError(f"Google API quota exceeded: {e}")
        except Exception as e:
            error_msg = str(e)
            if "API_KEY" in error_msg.upper():
                raise AuthenticationError(f"Google API key error: {error_msg}")
            else:
                raise ProviderError(f"Google API error: {error_msg}")

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using Google's token counting."""
        try:
            model = genai.GenerativeModel(model_name)
            response = model.count_tokens(text)
            return response.total_tokens

        except Exception as e:
            raise ProviderError(f"Token counting failed: {e}")

    def get_available_models(self) -> List[ModelInfo]:
        """Get available Google Gemini models."""
        # Static model definitions based on Gemini API
        models = [
            ModelInfo(
                name="gemini-1.5-pro",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=1048576,  # 1M tokens
                max_output_tokens=8192,
                cost_per_input_token=0.00125,  # Per 1K tokens
                cost_per_output_token=0.005,
            ),
            ModelInfo(
                name="gemini-1.5-flash",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=1048576,  # 1M tokens
                max_output_tokens=8192,
                cost_per_input_token=0.000075,  # Per 1K tokens
                cost_per_output_token=0.0003,
            ),
            ModelInfo(
                name="gemini-pro",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
                context_window=32768,
                max_output_tokens=8192,
                cost_per_input_token=0.0005,
                cost_per_output_token=0.0015,
            ),
            ModelInfo(
                name="gemini-1.5-flash-8b",
                provider="google",
                capabilities=[ModelCapability.TEXT_GENERATION],
                context_window=1048576,  # 1M tokens
                max_output_tokens=8192,
                cost_per_input_token=0.0000375,  # Per 1K tokens
                cost_per_output_token=0.00015,
            ),
        ]

        return models

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available."""
        try:
            model = genai.GenerativeModel(model_name)
            # Test with minimal request
            response = model.count_tokens("test")
            return response.total_tokens > 0
        except Exception:
            return False
