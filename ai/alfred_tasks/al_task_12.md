### **Task Directive: ALFRED-11 - Harden the Persona Loader**

**Objective:** To eliminate silent failures in the `PersonaLoader` by implementing specific, informative error handling. The current `except Exception: pass` is an unacceptable vulnerability.

**Rationale:** If a user defines a custom persona in a `.yml` file with a syntax error or a schema violation, the system currently fails silently. The persona simply won't be available, and the user will have no idea why. This is a critical failure of user experience and debuggability. The system must fail loudly and informatively.

**Implementation Plan:**

**File:** `src/alfred/orchestration/persona_loader.py`
**Action:** Replace the `load_all` method with the following hardened implementation.

```python
"""
Loads and validates persona configurations from YAML files.
"""
import yaml
from pydantic import ValidationError

from src.alfred.config.settings import settings
from src.alfred.models.config import PersonaConfig
from src.alfred.lib.logger import get_logger

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
                logger.error(f"Failed to parse YAML for persona '{persona_name}': {e}")
            except ValidationError as e:
                logger.error(f"Validation failed for persona '{persona_name}': {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred loading persona '{persona_name}': {e}")

        return personas

```
