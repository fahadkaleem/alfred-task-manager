"""
Pydantic models for Epic Task Manager tool responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    """
    The single, standardized response object for all tools in the Epic Task Manager.
    This model provides a predictable, reliable contract between our server and the AI client.
    """

    status: str = Field(description="The status of the operation, typically 'success' or 'error'.")
    message: str = Field(description="A clear, human-readable message describing the result of the tool call. This can be displayed in a UI.")
    data: dict[str, Any] | None = Field(default=None, description="An optional, structured data payload. Used by informational tools like 'get_task_summary'.")
    next_prompt: str | None = Field(default=None, description="The complete, self-contained prompt for the AI's very next action. This is the core of the MCP-driven workflow.")
