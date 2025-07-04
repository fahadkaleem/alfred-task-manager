"""
Registry for mapping states to template classes.

This maintains the explicit path principle - each state maps to one template.
"""

from typing import Dict, Type, Optional

from alfred.core.template_base import BasePromptTemplate
from alfred.core.prompt_templates import PlanTaskContextualizeTemplate, PlanTaskStrategizeTemplate, AIReviewTemplate, HumanReviewTemplate, SimpleDispatchingTemplate


class TemplateRegistry:
    """Maps tool.state combinations to template classes."""

    def __init__(self):
        self._templates: Dict[str, Type[BasePromptTemplate]] = {}
        self._register_default_templates()

    def _register_default_templates(self):
        """Register all default templates."""
        # Plan task templates
        self.register("plan_task.contextualize", PlanTaskContextualizeTemplate)
        self.register("plan_task.strategize", PlanTaskStrategizeTemplate)

        # Generic review templates
        self.register("review.ai_review", AIReviewTemplate)
        self.register("review.human_review", HumanReviewTemplate)

        # Add more registrations as we migrate templates

    def register(self, key: str, template_class: Type[BasePromptTemplate]):
        """Register a template class for a tool.state combination."""
        self._templates[key] = template_class

    def get_template(self, tool_name: str, state: str) -> Optional[Type[BasePromptTemplate]]:
        """Get template class for the given tool and state."""
        # Try exact match first
        key = f"{tool_name}.{state}"
        if key in self._templates:
            return self._templates[key]

        # Handle review states
        if state.endswith("_awaiting_ai_review"):
            return self._templates.get("review.ai_review")
        elif state.endswith("_awaiting_human_review"):
            return self._templates.get("review.human_review")

        return None

    def has_template_class(self, tool_name: str, state: str) -> bool:
        """Check if a template class exists for this state."""
        return self.get_template(tool_name, state) is not None


template_registry = TemplateRegistry()
