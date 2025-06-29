# src/alfred/models/config.py
"""
Pydantic models for parsing persona configurations.
This has been simplified to only contain conversational and identity fields.
"""

from pydantic import BaseModel, Field
from typing import List, Optional

class PersonaConfig(BaseModel):
    """
    Represents the validated configuration of a single persona.yml file.
    Its sole purpose is to define the "character" and "voice" of the AI for a given tool.
    """
    name: str = Field(description="The persona's first name, e.g., 'Alex'.")
    title: str = Field(description="The persona's job title, e.g., 'Solution Architect'.")
    
    greeting: Optional[str] = Field(None, description="An example greeting the persona can use to introduce itself.")
    communication_style: Optional[str] = Field(None, description="A description of the persona's conversational style and tone.")
    
    thinking_methodology: List[str] = Field(default_factory=list, description="A list of core principles that guide the persona's reasoning.")
    personality_traits: List[str] = Field(default_factory=list, description="A list of traits that define the persona's character.")