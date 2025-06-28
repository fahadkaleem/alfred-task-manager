# src/alfred/core/prompter.py
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from enum import Enum
from typing import Dict, Any, Optional

from src.alfred.config.settings import settings
from src.alfred.models.schemas import Task


class Prompter:
    """Generates persona-driven, state-aware prompts for the AI agent."""

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

    def generate_prompt(
        self,
        task: Task,
        tool_name: str,
        state: Enum,
        persona_config: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generates a prompt by rendering a template with the given context.

        Args:
            task: The full structured Task object.
            tool_name: The name of the active tool (e.g., 'plan_task').
            state: The current state from the tool's SM.
            persona_config: The loaded YAML config for the tool's persona.
            additional_context: Ad-hoc data like review feedback.

        Returns:
            The rendered prompt string.
        """
        template_path = f"prompts/{tool_name}/{state.value}.md"
        
        try:
            template = self.jinja_env.get_template(template_path)
        except Exception as e:
            # Proper error handling is crucial
            error_message = f"CRITICAL ERROR: Prompt template not found at '{template_path}'. Details: {e}"
            print(error_message)  # Or use logger
            return error_message

        # Build the comprehensive context for the template
        render_context = {
            "task": task,
            "tool_name": tool_name,
            "state": state.value,
            "persona": persona_config,
            **(additional_context or {})
        }

        return template.render(render_context)


# Singleton instance to be used across the application
prompter = Prompter()