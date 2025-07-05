"""
Anthropic Claude Provider Implementation for Alfred Task Manager

Following Alfred's principles:
- Data normalization to standard ModelResponse
- Uniform error mapping
- No provider-specific extensions
"""

import anthropic
from typing import List, Optional, Dict, Any

from .base import BaseAIProvider, ModelResponse, ModelInfo, ModelCapability, ProviderError, ModelNotFoundError, QuotaExceededError, AuthenticationError


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude API provider implementation."""

    def __init__(self, api_key: str):
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            raise AuthenticationError(f"Failed to initialize Anthropic client: {e}")

    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using Anthropic Claude models."""
        try:
            # Claude uses a messages API format
            response = self.client.messages.create(model=model_name, max_tokens=max_tokens or 4096, temperature=temperature, messages=[{"role": "user", "content": prompt}])

            content = response.content[0].text if response.content else ""

            # Normalize usage data
            usage = {}
            if response.usage:
                usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens, "total_tokens": response.usage.input_tokens + response.usage.output_tokens}

            # Provider-specific metadata
            metadata = {"stop_reason": response.stop_reason, "model": response.model, "response_id": response.id}

            return ModelResponse(content=content, model_name=model_name, usage=usage, metadata=metadata)

        except anthropic.AuthenticationError as e:
            raise AuthenticationError(f"Anthropic authentication failed: {e}")
        except anthropic.NotFoundError as e:
            raise ModelNotFoundError(f"Model {model_name} not found: {e}")
        except anthropic.RateLimitError as e:
            raise QuotaExceededError(f"Anthropic rate limit exceeded: {e}")
        except anthropic.APIError as e:
            raise ProviderError(f"Anthropic API error: {e}")
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower():
                raise AuthenticationError(f"Anthropic API key error: {error_msg}")
            else:
                raise ProviderError(f"Anthropic error: {error_msg}")

    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens using Anthropic's token counting."""
        try:
            # Anthropic provides a count_tokens method
            count = self.client.count_tokens(text)
            return count

        except Exception as e:
            # Fallback: rough estimation (Claude uses similar tokenization to GPT)
            # This is approximate - about 4 characters per token
            return len(text) // 4

    def get_available_models(self) -> List[ModelInfo]:
        """Get available Anthropic Claude models."""
        # Static model definitions based on Anthropic API
        models = [
            ModelInfo(
                name="claude-3-5-sonnet-20241022",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=200000,
                max_output_tokens=8192,
                cost_per_input_token=0.003,
                cost_per_output_token=0.015,
            ),
            ModelInfo(
                name="claude-3-opus-20240229",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.ANALYSIS],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_input_token=0.015,
                cost_per_output_token=0.075,
            ),
            ModelInfo(
                name="claude-3-sonnet-20240229",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_input_token=0.003,
                cost_per_output_token=0.015,
            ),
            ModelInfo(
                name="claude-3-haiku-20240307",
                provider="anthropic",
                capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CODE_GENERATION],
                context_window=200000,
                max_output_tokens=4096,
                cost_per_input_token=0.00025,
                cost_per_output_token=0.00125,
            ),
        ]

        return models

    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available."""
        try:
            # Test with minimal request
            self.client.messages.create(model=model_name, max_tokens=1, messages=[{"role": "user", "content": "test"}])
            return True
        except Exception:
            return False
