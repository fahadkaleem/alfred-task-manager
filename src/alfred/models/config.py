# src/alfred/models/config.py
"""
Pydantic models for parsing workflow configurations.
"""

from typing import Dict, List

from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    """
    Represents the validated configuration of a workflow.
    """

    # Add any workflow-specific configuration here if needed
    pass
