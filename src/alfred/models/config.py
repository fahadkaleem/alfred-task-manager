# src/alfred/models/config.py
"""
Pydantic models for parsing persona configurations, including the
new dual-mode (Human/AI) interaction structure.
"""
from typing import Dict, List

from pydantic import BaseModel, Field


class HumanInteraction(BaseModel):
    """Configuration for human-facing communication."""

    greeting: str = Field(description="The persona's introductory greeting.")
    communication_style: str = Field(
        description="A description of the persona's conversational style and tone with humans."
    )


class AIInteraction(BaseModel):
    """Configuration for AI agent directives."""

    style: str = Field(
        default="precise, technical, directive",
        description="The persona's communication style when issuing instructions to the AI agent.",
    )
    analysis_patterns: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="A dictionary mapping a tool's state to a list of specific analysis commands or patterns for the AI.",
    )
    validation_criteria: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="A dictionary mapping a tool's state to a list of specific validation criteria for AI self-review.",
    )


class PersonaConfig(BaseModel):
    """
    Represents the validated configuration of a single persona.yml file,
    supporting dual-mode communication.
    """

    name: str = Field(description="The persona's first name, e.g., 'Alex'.")
    title: str = Field(description="The persona's job title, e.g., 'Solution Architect'.")
    thinking_methodology: List[str] = Field(
        default_factory=list,
        description="A list of core principles that guide the persona's reasoning.",
    )
    human: HumanInteraction
    ai: AIInteraction