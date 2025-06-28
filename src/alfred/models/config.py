"""
Pydantic models for parsing persona and workflow configurations.
"""

from typing import Any

from pydantic import BaseModel, Field


class HSMConfig(BaseModel):
    """Defines the structure for a Hierarchical State Machine in YAML."""

    initial_state: str
    states: list[str | dict[str, Any]]  # Can be simple strings or complex state dicts
    transitions: list[dict[str, Any]]


class ArtifactValidationConfig(BaseModel):
    """Defines which artifact model to use for validation in a given state."""

    state: str
    model_path: str  # e.g., "src.alfred.models.artifacts.GitSetupArtifact"


class PersonaConfig(BaseModel):
    """Represents the validated configuration of a single persona.yml file."""

    name: str
    title: str
    target_status: str
    completion_status: str
    hsm: HSMConfig
    prompts: dict[str, str] = Field(default_factory=dict)
    core_principles: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactValidationConfig] = Field(default_factory=list)
    execution_mode: str = Field(default="sequential")  # sequential or stepwise
