"""
Base AI Provider Interface for Alfred Task Manager

Following Alfred's Task Provider Principles:
- ONE INTERFACE TO RULE THEM ALL
- DATA NORMALIZATION IS SACRED
- NO PROVIDER LEAKAGE
- ERROR HANDLING IS UNIFORM
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ModelCapability(str, Enum):
    """Model capabilities for routing decisions."""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    ANALYSIS = "analysis"


class ModelResponse(BaseModel):
    """Normalized response from any AI provider."""

    content: str
    model_name: str
    usage: Dict[str, int] = Field(default_factory=dict)  # {input_tokens: int, output_tokens: int}
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Provider-specific data
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": True}  # Immutable value object


class ModelInfo(BaseModel):
    """Model information for registry."""

    name: str
    provider: str
    capabilities: List[ModelCapability]
    context_window: int
    max_output_tokens: Optional[int] = None
    cost_per_input_token: Optional[float] = None
    cost_per_output_token: Optional[float] = None

    model_config = {"frozen": True}


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI model providers.

    Following Task Provider Principles:
    - EXACTLY FOUR METHODS (like BaseTaskProvider)
    - Uniform behavior across all implementations
    - No provider-specific methods or extensions
    """

    @abstractmethod
    def generate_content(self, prompt: str, model_name: str, temperature: float = 0.5, max_tokens: Optional[int] = None) -> ModelResponse:
        """Generate content using the specified model."""
        pass

    @abstractmethod
    def count_tokens(self, text: str, model_name: str) -> int:
        """Count tokens for a given model."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models from this provider."""
        pass

    @abstractmethod
    def validate_model(self, model_name: str) -> bool:
        """Validate if model is available and accessible."""
        pass


class ProviderError(Exception):
    """Standard error for all provider operations."""

    pass


class ModelNotFoundError(ProviderError):
    """Model not found or not available."""

    pass


class QuotaExceededError(ProviderError):
    """API quota or rate limit exceeded."""

    pass


class AuthenticationError(ProviderError):
    """Provider authentication failed."""

    pass
