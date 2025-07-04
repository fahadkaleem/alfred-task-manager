"""
OpenAI Provider Implementation for Alfred Task Manager

Following Alfred's principles:
- Data normalization to standard ModelResponse
- Uniform error mapping
- No provider-specific extensions
"""

import tiktoken
from typing import List, Optional, Dict, Any
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion

from .base import BaseAIProvider, ModelResponse, ModelInfo, ModelCapability, ProviderError, ModelNotFoundError, QuotaExceededError, AuthenticationError


class OpenAIProvider(BaseAIProvider):
    """OpenAI API provider implementation."""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize OpenAI client: {e}")

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using OpenAI models."""
        try:
            response: ChatCompletion = self.client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}], temperature=temperature, max_tokens=max_tokens)

            content = response.choices[0].message.content or ""

            # Normalize usage data
            usage = {}
            if response.usage:
                usage = {"input_tokens": response.usage.prompt_tokens, "output_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens}

            # Provider-specific metadata
            metadata = {"finish_reason": response.choices[0].finish_reason, "response_id": response.id, "created": response.created}

            return ModelResponse(content=content, model_name=model_name, usage=usage, metadata=metadata)

        except Exception as e:
            # Map OpenAI errors to standard provider errors
            error_msg = str(e)
            if "model" in error_msg.lower() and "not found" in error_msg.lower():
                raise ModelNotFoundError(f"Model {model_name} not found")
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise QuotaExceededError(f"OpenAI quota exceeded: {error_msg}")
            elif "authentication" in error_msg.lower() or "api_key" in error_msg.lower():
                raise AuthenticationError(f"OpenAI authentication failed: {error_msg}")
            else:
                raise ProviderError(f"OpenAI API error: {error_msg}")

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using tiktoken."""
        try:
            # Map model names to tiktoken encodings
            encoding_map = {"gpt-4": "cl100k_base", "gpt-4-turbo": "cl100k_base", "gpt-3.5-turbo": "cl100k_base", "o3": "cl100k_base", "o3-mini": "cl100k_base", "o4-mini": "cl100k_base"}

            # Default to cl100k_base for unknown models
            encoding_name = encoding_map.get(model_name, "cl100k_base")
            encoding = tiktoken.get_encoding(encoding_name)

            return len(encoding.encode(text))

        except Exception as e:
            raise ProviderError(f"Token counting failed: {e}")

    def get_available_models(self) -> List[ModelInfo]:
        """Get available OpenAI models."""
        # Static model definitions (can be extended to fetch from API)
        models = [
            ModelInfo(
                name="gpt-4",
                provider="openai",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING],
                context_window=8192,
                max_output_tokens=4096,
                cost_per_input_token=0.00003,
                cost_per_output_token=0.00006,
            ),
            ModelInfo(
                name="gpt-4-turbo",
                provider="openai",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=128000,
                max_output_tokens=4096,
                cost_per_input_token=0.00001,
                cost_per_output_token=0.00003,
            ),
            ModelInfo(
                name="gpt-3.5-turbo",
                provider="openai",
                capabilities=[ModelCapability.TEXT_GENERATION],
                context_window=16385,
                max_output_tokens=4096,
                cost_per_input_token=0.0000005,
                cost_per_output_token=0.0000015,
            ),
            ModelInfo(
                name="o3",
                provider="openai",
                capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=200000,
                max_output_tokens=100000,
                cost_per_input_token=0.0001,  # Placeholder pricing
                cost_per_output_token=0.0002,
            ),
            ModelInfo(
                name="o3-mini",
                provider="openai",
                capabilities=[ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=65536,
                cost_per_input_token=0.00005,
                cost_per_output_token=0.0001,
            ),
            ModelInfo(
                name="o4-mini",
                provider="openai",
                capabilities=[ModelCapability.REASONING, ModelCapability.TEXT_GENERATION],
                context_window=200000,
                max_output_tokens=65536,
                cost_per_input_token=0.00005,
                cost_per_output_token=0.0001,
            ),
        ]

        return models

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available."""
        try:
            # Test with minimal request
            self.client.chat.completions.create(model=model_name, messages=[{"role": "user", "content": "test"}], max_tokens=1)
            return True
        except Exception:
            return False
