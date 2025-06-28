"""
Loads and validates persona configurations from YAML files.
"""

from pydantic import ValidationError
import yaml

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.models.config import PersonaConfig

logger = get_logger(__name__)


class PersonaLoader:
    """A utility to load all persona configurations from the filesystem."""

    @staticmethod
    def load_all() -> dict[str, PersonaConfig]:
        """
        Scans the personas directory, loads all .yml files, and validates them.
        """
        personas: dict[str, PersonaConfig] = {}
        personas_dir = settings.packaged_personas_dir

        if not personas_dir.exists():
            logger.error(f"Personas directory not found at: {personas_dir}")
            return {}

        for persona_file in personas_dir.glob("*.yml"):
            persona_name = persona_file.stem
            try:
                with persona_file.open("r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if not data:
                        logger.warning(f"Persona file '{persona_file.name}' is empty. Skipping.")
                        continue
                    config = PersonaConfig(**data)
                    personas[persona_name] = config
            except yaml.YAMLError as e:
                logger.exception(f"Failed to parse YAML for persona '{persona_name}': {e}")
            except ValidationError as e:
                logger.exception(f"Validation failed for persona '{persona_name}': {e}")
            except Exception as e:
                logger.exception(f"An unexpected error occurred loading persona '{persona_name}': {e}")

        return personas
