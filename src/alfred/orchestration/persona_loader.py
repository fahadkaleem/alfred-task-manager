# src/alfred/orchestration/persona_loader.py
"""
A simple utility to load a single persona configuration from a YAML file.
"""
import yaml
from pydantic import ValidationError
from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.models.config import PersonaConfig # Uses the new, simplified model

logger = get_logger(__name__)

def load_persona(persona_name: str) -> PersonaConfig:
    """
    Loads and validates a single persona YAML file.

    Args:
        persona_name: Name of the persona file (without .yml extension).

    Returns:
        A validated PersonaConfig object.

    Raises:
        FileNotFoundError: If the persona file doesn't exist.
        ValueError: If the persona file is invalid.
    """
    # First, check for a user-customized persona
    user_persona_file = settings.alfred_dir / "personas" / f"{persona_name}.yml"
    
    # Fallback to the packaged persona if user one doesn't exist
    persona_file = user_persona_file if user_persona_file.exists() else settings.packaged_personas_dir / f"{persona_name}.yml"

    if not persona_file.exists():
        raise FileNotFoundError(f"Persona config '{persona_name}.yml' not found in user or package directories.")

    try:
        with persona_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                raise ValueError(f"Persona file '{persona_file.name}' is empty.")
            
            config = PersonaConfig(**data)
            return config
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML for persona '{persona_name}': {e}")
        raise ValueError(f"Invalid YAML in '{persona_name}.yml'.") from e
    except ValidationError as e:
        logger.error(f"Validation failed for persona '{persona_name}': {e}")
        raise ValueError(f"Invalid structure in '{persona_name}.yml'.") from e