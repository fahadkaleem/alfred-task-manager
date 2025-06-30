# src/alfred/core/prompter.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Optional
import json
from pydantic import BaseModel

from src.alfred.config.settings import settings
from src.alfred.models.schemas import Task
from src.alfred.constants import TemplatePaths
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


class Prompter:
    """Generates state-aware prompts for the AI agent."""

    def __init__(self):
        # Reuse existing settings to find the templates directory
        search_paths = []

        # Check for user-initialized templates first
        user_templates_path = settings.alfred_dir / "templates"
        if user_templates_path.exists():
            search_paths.append(str(user_templates_path))

        # Always include packaged templates as fallback
        search_paths.append(str(settings.packaged_templates_dir))

        self.template_loader = FileSystemLoader(searchpath=search_paths)
        self.jinja_env = Environment(loader=self.template_loader, trim_blocks=True, lstrip_blocks=True)

        # Add custom filters
        self.jinja_env.filters["fromjson"] = json.loads
        self.jinja_env.filters["tojson"] = self._pydantic_safe_tojson

    def _pydantic_safe_tojson(self, obj, indent=2):
        """Custom JSON filter that handles Pydantic models"""
        if isinstance(obj, BaseModel):
            return json.dumps(obj.model_dump(), indent=indent)
        return json.dumps(obj, indent=indent)

    def generate_prompt(
        self,
        task: Task,
        tool_name: str,
        state,  # Can be Enum or str
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generates a prompt by rendering a template with the given context.

        Args:
            task: The full structured Task object.
            tool_name: The name of the active tool (e.g., 'plan_task').
            state: The current state from the tool's SM (Enum or str).
            additional_context: Ad-hoc data like review feedback.

        Returns:
            The rendered prompt string.
        """
        # Handle both Enum and string state values
        state_value = state.value if hasattr(state, "value") else state

        # Map dynamic review states to generic templates
        template_state = state_value
        if state_value.endswith("_awaiting_ai_review"):
            template_state = "awaiting_ai_review"
        elif state_value.endswith("_awaiting_human_review"):
            template_state = "awaiting_human_review"

        template_path = TemplatePaths.PROMPT_PATTERN.format(tool_name=tool_name, state=template_state)

        logger.info(f"[PROMPTER] Generating prompt for tool='{tool_name}', state='{state_value}'")
        logger.info(f"[PROMPTER] Additional context keys: {list(additional_context.keys()) if additional_context else 'None'}")

        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            # Proper error handling is crucial
            error_message = f"CRITICAL ERROR: Prompt template not found at '{template_path}'. Details: {e}"
            logger.error(error_message)
            return error_message

        # Build the comprehensive context for the template
        render_context = {
            "task": task,
            "tool_name": tool_name,
            "state": state_value,
            "additional_context": additional_context or {},
        }

        # Log important context details for debugging
        if additional_context and "feedback_notes" in additional_context:
            logger.info(f"[PROMPTER DEBUG] Feedback notes present (first 100 chars): {additional_context['feedback_notes'][:100]}")
        if additional_context:
            artifact_keys = [k for k in additional_context.keys() if k.endswith("_artifact")]
            if artifact_keys:
                logger.info(f"[PROMPTER DEBUG] Artifact keys in context: {artifact_keys}")

        # Log what's being passed to template
        logger.info(f"[PROMPTER DEBUG] Rendering template with additional_context keys: {list(additional_context.keys()) if additional_context else 'None'}")

        rendered = template.render(render_context)

        # Check if feedback section was rendered
        if additional_context and "feedback_notes" in additional_context:
            if "Building on Your Previous Analysis" in rendered:
                logger.info("[PROMPTER DEBUG] Feedback section successfully rendered in template")
            else:
                logger.warning("[PROMPTER DEBUG] Feedback section NOT rendered despite feedback_notes present!")

        return rendered


# Singleton instance to be used across the application
prompter = Prompter()
