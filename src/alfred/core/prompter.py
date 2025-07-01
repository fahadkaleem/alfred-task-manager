# src/alfred/core/prompter_new.py
import json
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum

from src.alfred.config.settings import settings
from src.alfred.lib.logger import get_logger
from src.alfred.core.template_registry import template_registry

logger = get_logger(__name__)


class PromptTemplate:
    """A simple template wrapper that provides clear error messages."""

    def __init__(self, content: str, source_file: Path):
        self.content = content
        self.source_file = source_file
        self.template = Template(content)
        self._required_vars = self._extract_variables()

    def _extract_variables(self) -> Set[str]:
        """Extract all ${var} placeholders from template."""
        import re

        # Match ${var} but not $${var} (escaped)
        return set(re.findall(r"(?<!\$)\$\{(\w+)\}", self.content))

    def render(self, context: Dict[str, Any]) -> str:
        """Render the template with context."""
        # Check for missing required variables
        provided_vars = set(context.keys())
        missing_vars = self._required_vars - provided_vars

        if missing_vars:
            raise ValueError(f"Missing required variables for {self.source_file.name}: {', '.join(sorted(missing_vars))}\nProvided: {', '.join(sorted(provided_vars))}")

        try:
            # safe_substitute won't fail on extra vars
            return self.template.safe_substitute(**context)
        except Exception as e:
            raise RuntimeError(f"Failed to render template {self.source_file.name}: {e}")


class PromptLibrary:
    """Manages file-based prompt templates."""

    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt library.

        Args:
            prompts_dir: Directory containing prompts. Defaults to checking
                        user customization first, then packaged prompts.
        """
        if prompts_dir is None:
            # Check for user customization first
            user_prompts = settings.alfred_dir / "templates" / "prompts"
            if user_prompts.exists():
                prompts_dir = user_prompts
                logger.info(f"Using user prompt templates from {user_prompts}")
            else:
                # Fall back to packaged prompts
                prompts_dir = Path(__file__).parent.parent / "templates" / "prompts"
                logger.info(f"Using default prompt templates from {prompts_dir}")

        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptTemplate] = {}
        self._load_all_prompts()

    def _load_all_prompts(self) -> None:
        """Pre-load all prompts for validation."""
        count = 0
        for prompt_file in self.prompts_dir.rglob("*.md"):
            if prompt_file.name.startswith("_"):
                continue  # Skip special files

            try:
                content = prompt_file.read_text(encoding="utf-8")
                # Build key from relative path
                key = self._path_to_key(prompt_file)
                self._cache[key] = PromptTemplate(content, prompt_file)
                count += 1
            except Exception as e:
                logger.error(f"Failed to load prompt {prompt_file}: {e}")

        logger.info(f"Loaded {count} prompt templates")

    def _path_to_key(self, path: Path) -> str:
        """Convert file path to prompt key."""
        # Remove .md extension and convert path to dot notation
        relative = path.relative_to(self.prompts_dir)
        parts = list(relative.parts[:-1]) + [relative.stem]
        return ".".join(parts)

    def get(self, prompt_key: str, context: Dict[str, Any] = None) -> Union[PromptTemplate, str]:
        """
        Get a prompt template by key.
        
        First checks for file-based template, then falls back to template class.
        """
        # Check file-based cache first
        if prompt_key in self._cache:
            return self._cache[prompt_key]
        
        # Check if we have a template class
        if context and "." in prompt_key:
            tool_name, state = prompt_key.rsplit(".", 1)
            template_class = template_registry.get_template(tool_name, state)
            if template_class:
                # Render directly from template class
                template_instance = template_class()
                return template_instance.render(context)
        
        # Fallback to not found
        available = ", ".join(sorted(self._cache.keys()))
        raise KeyError(
            f"Prompt '{prompt_key}' not found in files or template registry.\n"
            f"Available file prompts: {available}"
        )

    def get_prompt_key(self, tool_name: str, state: str) -> str:
        """Map tool and state to the correct prompt key."""
        # Handle dynamic review states
        if state.endswith("_awaiting_ai_review"):
            return "review.ai_review"
        elif state.endswith("_awaiting_human_review"):
            return "review.human_review"

        # Direct mapping
        direct_key = f"{tool_name}.{state}"

        # Check if it exists
        if direct_key in self._cache:
            return direct_key

        # Try without tool name for shared prompts
        if state in self._cache:
            return state

        # Default fallback
        return "errors.not_found"

    def render(self, prompt_key: str, context: Dict[str, Any], strict: bool = True) -> str:
        """Render a prompt with context."""
        template = self.get(prompt_key, context)
        
        # If we got a string back, it's already rendered
        if isinstance(template, str):
            return template
        
        # Otherwise it's a file-based PromptTemplate
        if not strict:
            # Add empty strings for missing vars
            for var in template._required_vars:
                if var not in context:
                    context[var] = ""
        
        return template.render(context)

    def list_prompts(self) -> Dict[str, Dict[str, Any]]:
        """List all available prompts with metadata."""
        result = {}
        for key, template in self._cache.items():
            result[key] = {"file": str(template.source_file.relative_to(self.prompts_dir)), "required_vars": sorted(template._required_vars), "size": len(template.content)}
        return result

    def reload(self) -> None:
        """Reload all prompts (useful for development)."""
        logger.info("Reloading prompt templates...")
        self._cache.clear()
        self._load_all_prompts()


# Global instance
prompt_library = PromptLibrary()


class PromptBuilder:
    """Helper class to build consistent prompt contexts."""

    def __init__(self, task_id: str, tool_name: str, state: str):
        self.context = {
            "task_id": task_id,
            "tool_name": tool_name,
            "current_state": state,
            "feedback_section": "",
        }

    def with_task(self, task) -> "PromptBuilder":
        """Add task information to context."""
        self.context.update(
            {
                "task_title": task.title,
                "task_context": task.context,
                "implementation_details": task.implementation_details,
                "acceptance_criteria": self._format_list(task.acceptance_criteria),
                "task_status": task.task_status.value if hasattr(task.task_status, "value") else str(task.task_status),
            }
        )
        return self

    def with_artifact(self, artifact: Any, as_json: bool = True) -> "PromptBuilder":
        """Add artifact to context."""
        if as_json:
            if hasattr(artifact, "model_dump"):
                artifact_data = artifact.model_dump()
            else:
                artifact_data = artifact

            self.context["artifact_json"] = json.dumps(artifact_data, indent=2, default=str)
            self.context["artifact_summary"] = self._summarize_artifact(artifact_data)
        else:
            self.context["artifact"] = artifact
        return self

    def with_feedback(self, feedback: str) -> "PromptBuilder":
        """Add feedback to context."""
        if feedback:
            # Format feedback as a complete markdown section
            feedback_section = f"\n## REVISION FEEDBACK\nThe previous submission was reviewed and requires changes:\n\n{feedback}\n\nPlease address this feedback and resubmit.\n"
            self.context["feedback_section"] = feedback_section
        else:
            self.context["feedback_section"] = ""

        # Keep raw feedback for compatibility
        self.context["feedback"] = feedback
        self.context["has_feedback"] = bool(feedback)
        return self

    def with_custom(self, **kwargs) -> "PromptBuilder":
        """Add custom context variables."""
        self.context.update(kwargs)
        return self

    def build(self) -> Dict[str, Any]:
        """Return the built context."""
        return self.context.copy()

    @staticmethod
    def _format_list(items: list) -> str:
        """Format a list for prompt display."""
        if not items:
            return "- None specified"
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def _summarize_artifact(artifact: Any) -> str:
        """Create a summary of an artifact for human review."""
        if isinstance(artifact, dict):
            # Try to extract key information
            if "summary" in artifact:
                return artifact["summary"]
            elif "title" in artifact:
                return artifact["title"]
            else:
                # Show first few keys
                keys = list(artifact.keys())[:5]
                return f"Artifact with fields: {', '.join(keys)}"
        return str(artifact)[:200]


def generate_prompt(task_id: str, tool_name: str, state: str, task: Any, additional_context: Optional[Dict[str, Any]] = None) -> str:
    """Main function to generate prompts - backward compatible wrapper."""

    # Handle both Enum and string state values
    state_value = state.value if hasattr(state, "value") else state

    # Get the correct prompt key
    prompt_key = prompt_library.get_prompt_key(tool_name, state_value)

    # Build context using the builder
    builder = PromptBuilder(task_id, tool_name, state_value).with_task(task)

    # Add additional context
    if additional_context:
        if "artifact_content" in additional_context:
            builder.with_artifact(additional_context["artifact_content"])
        if "feedback_notes" in additional_context:
            builder.with_feedback(additional_context["feedback_notes"])

        # Add everything else
        remaining = {k: v for k, v in additional_context.items() if k not in ["artifact_content", "feedback_notes"]}
        builder.with_custom(**remaining)

    # Render the prompt
    try:
        return prompt_library.render(prompt_key, builder.build())
    except KeyError:
        # Fallback for missing prompts
        logger.warning(f"Prompt not found for {prompt_key}, using fallback")
        return f"# {tool_name} - {state_value}\n\nNo prompt configured for this state.\nTask: {task_id}"
