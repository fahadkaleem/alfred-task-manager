"""
Represents the live, stateful instance of a persona for a specific task.
"""

import importlib
import json

from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
from transitions.extensions import HierarchicalMachine

from src.alfred.config.settings import settings
from src.alfred.models.config import PersonaConfig


class PersonaRuntime:
    """Manages the state and execution of a single persona for one task."""

    def __init__(self, task_id: str, config: PersonaConfig):
        self.task_id = task_id
        self.config = config
        
        # Ensure transitions have source as list
        transitions = []
        for t in config.hsm.transitions:
            transition = t.copy()
            if isinstance(transition.get("source"), str):
                transition["source"] = [transition["source"]]
            transitions.append(transition)
        
        self.machine = HierarchicalMachine(
            model=self,
            states=config.hsm.states,
            transitions=transitions,
            initial=config.hsm.initial_state,
            auto_transitions=False,
        )
        self.submitted_artifact_data: dict | None = None

    def get_current_prompt(self, revision_feedback: str | None = None, additional_context: dict | None = None) -> str:
        """
        Generates the prompt for the current state of the persona's HSM,
        now with support for additional, ad-hoc context.
        """
        prompt_template_path = self.config.prompts.get(self.state)
        
        # Special handling for requirements persona to select provider-specific prompt
        if self.config.name == "Intake Analyst" and additional_context and "task_provider" in additional_context:
            provider = additional_context["task_provider"]
            provider_specific_key = f"{self.state}_{provider}"
            if provider_specific_key in self.config.prompts:
                prompt_template_path = self.config.prompts.get(provider_specific_key)

        if not prompt_template_path:
            return f"Error: No prompt template found for state '{self.state}' in persona '{self.config.name}'."

        # Setup Jinja2 environment to load templates from the packaged source
        template_loader = FileSystemLoader(searchpath=str(settings.packaged_templates_dir))
        jinja_env = Environment(loader=template_loader)

        template = jinja_env.get_template(prompt_template_path)

        # --- NEW: Inject submitted artifact for review prompts ---
        artifact_content_for_review = ""
        if self.state.endswith("aireview") and self.submitted_artifact_data:
            artifact_content_for_review = json.dumps(self.submitted_artifact_data, indent=2)
        # --- END NEW ---

        # Prepare base context for rendering
        context = {
            "task_id": self.task_id,
            "persona": self.config,
            "revision_feedback": revision_feedback or "No feedback provided.",
            # --- NEW ---
            "artifact_content_for_review": artifact_content_for_review,
        }

        # --- NEW: Merge additional context from the orchestrator ---
        if additional_context:
            context.update(additional_context)
        # --- END NEW ---

        return template.render(context)

    def validate_artifact(self, artifact_data: dict) -> BaseModel | None:
        """Validates artifact data against the configured Pydantic model for the current state."""
        validator_config = next((a for a in self.config.artifacts if a.state == self.state), None)
        if not validator_config:
            # If no validator is defined for this state, return the raw data as a simple namespace
            from types import SimpleNamespace
            return SimpleNamespace(**artifact_data)
        try:
            module_path, class_name = validator_config.model_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            validator_class = getattr(module, class_name)
            return validator_class(**artifact_data)
        except Exception as e:
            from src.alfred.lib.logger import get_logger

            logger = get_logger(__name__)
            logger.exception(f"Artifact validation failed for state '{self.state}': {e}")
            return None

    def trigger_submission(self) -> tuple[bool, str]:
        """Triggers the appropriate submission transition on the HSM."""
        try:
            trigger = "submit_manifest" if self.state.endswith("_submission") else "submit"
            trigger_method = getattr(self, trigger, None)
            if not trigger_method:
                return False, f"No trigger '{trigger}' found for state '{self.state}'."

            trigger_method()
            return True, f"Work submitted. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not trigger submission from state '{self.state}': {e}"

    def process_review(self, is_approved: bool) -> tuple[bool, str | dict]:
        """
        Processes a review. Returns a signal if a handoff is required.
        """
        # Determine the correct trigger based on state and approval
        if self.state.endswith("devreview") and is_approved:
            trigger_name = "human_approve"
        else:
            trigger_name = "ai_approve" if is_approved else "request_revision"
            
        transition_config = None
        
        for t in self.config.hsm.transitions:
            if t["trigger"] == trigger_name:
                source = t["source"]
                if isinstance(source, str) and source == self.state:
                    transition_config = t
                    break
                elif isinstance(source, list) and self.state in source:
                    transition_config = t
                    break

        if not transition_config:
            return False, f"No valid transition for trigger '{trigger_name}' from state '{self.state}'."

        destination = transition_config.get("dest")
        if isinstance(destination, dict) and "handoff_to" in destination:
            return True, destination  # Signal for cross-persona handoff

        try:
            getattr(self, trigger_name)()
            return True, f"Review processed. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not process review from state '{self.state}': {e}"

    def process_human_approval(self) -> tuple[bool, str]:
        """Processes human approval for an internal stage or a final handoff."""
        try:
            self.human_approve()
            return True, f"Human approval processed. New state is '{self.state}'."
        except Exception as e:
            return False, f"Could not process human approval from state '{self.state}': {e}"
