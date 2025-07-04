"""
Base template system for reducing prompt duplication.

This system respects the template principles:
- Templates are data, not code
- Simple variable substitution only
- No conditional logic in templates
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

from alfred.lib.logger import get_logger

logger = get_logger(__name__)


class TemplateSection:
    """Represents a single section of a template."""

    def __init__(self, name: str, content: str = ""):
        self.name = name
        self.content = content

    def render(self, context: Dict[str, Any]) -> str:
        """Render this section with variable substitution."""
        if not self.content:
            return ""

        # Simple variable substitution using regex
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                value = context[var_name]
                return str(value) if value is not None else ""
            return match.group(0)  # Return unchanged if var not found

        rendered = re.sub(r"\$\{(\w+)\}", replace_var, self.content)
        return f"# {self.name}\n{rendered}"


class BasePromptTemplate(ABC):
    """
    Base class for all prompt templates.

    This provides the standard structure while allowing customization
    of individual sections. No logic in templates - only data.
    """

    # Standard sections in order
    SECTION_NAMES = ["CONTEXT", "OBJECTIVE", "BACKGROUND", "INSTRUCTIONS", "CONSTRAINTS", "OUTPUT", "EXAMPLES"]

    def __init__(self):
        self.sections: Dict[str, TemplateSection] = {}
        self._initialize_sections()

    def _initialize_sections(self):
        """Initialize all sections, subclasses override to provide content."""
        for section_name in self.SECTION_NAMES:
            method_name = f"_get_{section_name.lower()}_content"
            if hasattr(self, method_name):
                content = getattr(self, method_name)()
            else:
                content = ""
            self.sections[section_name] = TemplateSection(section_name, content)

    @abstractmethod
    def get_required_variables(self) -> List[str]:
        """Return list of required variables for this template."""
        pass

    def render(self, context: Dict[str, Any]) -> str:
        """Render the complete template with the given context."""
        # Validate required variables
        required = set(self.get_required_variables())
        provided = set(context.keys())
        missing = required - provided

        if missing:
            raise ValueError(f"Missing required variables: {', '.join(sorted(missing))}\nRequired: {', '.join(sorted(required))}\nProvided: {', '.join(sorted(provided))}")

        # Render each section
        rendered_sections = []
        for section_name in self.SECTION_NAMES:
            if section_name in self.sections:
                rendered = self.sections[section_name].render(context)
                if rendered:  # Only include non-empty sections
                    rendered_sections.append(rendered)

        return "\n\n".join(rendered_sections)


class WorkflowPromptTemplate(BasePromptTemplate):
    """Base template for all workflow state prompts."""

    def _get_context_content(self) -> str:
        """Standard context section for workflow prompts."""
        return """Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}"""

    def get_required_variables(self) -> List[str]:
        """Base required variables for workflow prompts."""
        return ["task_id", "tool_name", "current_state", "task_title"]


class WorkflowWithTaskDetailsTemplate(WorkflowPromptTemplate):
    """Base template for workflow prompts that need task details."""

    def _get_background_content(self) -> str:
        """Standard background with task details."""
        return """**Task Requirements:**
- Goal: ${task_context}
- Implementation Overview: ${implementation_details}
- Acceptance Criteria:
${acceptance_criteria}

${feedback_section}"""

    def get_required_variables(self) -> List[str]:
        """Extended required variables including task details."""
        base_vars = super().get_required_variables()
        return base_vars + ["task_context", "implementation_details", "acceptance_criteria", "feedback_section"]


class SubmitWorkPromptTemplate(WorkflowWithTaskDetailsTemplate):
    """Base template for prompts that end with submit_work."""

    def _get_output_content(self) -> str:
        """Standard output section for submit_work prompts."""
        return """Create a ${artifact_type} with:
${artifact_fields}

**Required Action:** Call `alfred.submit_work` with a `${artifact_type}`"""

    def get_required_variables(self) -> List[str]:
        """Add artifact-related variables."""
        base_vars = super().get_required_variables()
        return base_vars + ["artifact_type", "artifact_fields"]


class ReviewPromptTemplate(BasePromptTemplate):
    """Base template for review state prompts."""

    def _get_context_content(self) -> str:
        """Standard context for review prompts."""
        return """Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}"""

    def _get_objective_content(self) -> str:
        """Standard objective for review prompts."""
        return """${review_objective}"""

    def _get_background_content(self) -> str:
        """Standard background for review prompts."""
        return """${review_background}"""

    def _get_constraints_content(self) -> str:
        """Standard constraints for review prompts."""
        return """- ${review_constraints}"""

    def _get_output_content(self) -> str:
        """Standard output for review prompts."""
        return """${review_action}

**Required Action:** Call `alfred.provide_review` with your decision
- For approval: `is_approved=true`
- For revision: `is_approved=false` with detailed `feedback_notes`"""

    def get_required_variables(self) -> List[str]:
        return ["task_id", "tool_name", "current_state", "review_objective", "review_background", "review_constraints", "review_action"]
