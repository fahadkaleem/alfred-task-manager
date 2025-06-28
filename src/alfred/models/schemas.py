"""
Pydantic models for Alfred tool responses.
"""

from typing import Any

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """The standardized response object for all Alfred tools."""

    status: str = Field(description="The status of the operation, typically 'success' or 'error'.")
    message: str = Field(description="A clear, human-readable message describing the result.")
    data: dict[str, Any] | None = Field(default=None)
    next_prompt: str | None = Field(default=None)
