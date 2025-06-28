# Standard library imports
from pathlib import Path
import re

from pydantic import ValidationError

# Local application imports
from epic_task_manager.config.config_manager import config_manager
from epic_task_manager.config.settings import settings
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.execution.constants import (
    ERROR_SECTION_NOT_FOUND,
    ERROR_VERIFIED_ARTIFACT_NOT_FOUND,
    PHASE_CODING,
    PHASE_GITSETUP,
    PHASE_REQUIREMENTS,
    PHASE_TESTING,
    SECTION_PLANNING_STRATEGY,
    SECTION_SOLUTION_DESIGN,
    TASK_SOURCE_GENERIC,
    TEMPLATE_SUFFIX_AI_REVIEW,
    TEMPLATE_SUFFIX_EXECUTION_PLAN,
    TEMPLATE_SUFFIX_SOLUTION_DESIGN,
    TEMPLATE_SUFFIX_STRATEGY,
    TEMPLATE_SUFFIX_WORK,
    TEMPLATE_TYPE_PROMPTS,
    WORKFLOW_STAGE_AI_REVIEW,
    WORKFLOW_STAGE_DEV_REVIEW,
    WORKFLOW_STAGE_EXECUTION_PLAN,
    WORKFLOW_STAGE_SOLUTION_DESIGN,
    WORKFLOW_STAGE_STRATEGY,
    WORKFLOW_STAGE_VERIFIED,
    WORKFLOW_STAGE_WORKING,
)
from epic_task_manager.execution.exceptions import ArtifactNotFoundError, InvalidArtifactError
from epic_task_manager.models.artifacts import ExecutionPlanArtifact


class Prompter:
    """Generates dynamic, state-aware prompts for the AI."""

    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.artifact_manager = ArtifactManager()
        # --- CENTRALIZED CONTEXT MAP ---
        # This map is the single source of truth for context dependencies.
        # Key: The state that needs context.
        # Value: A list of tuples (source_phase_of_artifact, key_for_prompt_context)
        self._CONTEXT_REQUIREMENTS = {
            "planning_strategy": [("gatherrequirements", "verified_gatherrequirements_artifact")],
            "planning_solutiondesign": [
                ("gatherrequirements", "verified_gatherrequirements_artifact"),
                ("planning", "approved_strategy_artifact"),  # Special case: from scratchpad
            ],
            "planning_executionplan": [("planning", "approved_solution_design_artifact")],  # Special case: from scratchpad
            "finalize": [("testing", "verified_testing_artifact")],
            # Phases like gitsetup, coding, testing operate on the repository state
            # and do not require prior artifact context to be injected into their main work prompt.
        }

    def _safe_format_template(self, template: str, context: dict) -> str:
        """Safely format template by only replacing placeholders that exist in context."""
        pattern = re.compile(r"\{([^}]+)\}")

        def safe_replace(match):
            placeholder = match.group(1)
            return str(context.get(placeholder, match.group(0)))

        return pattern.sub(safe_replace, template)

    def _extract_section_from_scratchpad(self, scratchpad_content: str, section_title: str) -> str:
        """Extract a specific section from the scratchpad content or raise ArtifactNotFoundError."""
        pattern = rf"# {section_title}:.*?\n(.*?)(?=\n# |\Z)"
        match = re.search(pattern, scratchpad_content, re.DOTALL)

        if match:
            return match.group(0).strip()

        raise ArtifactNotFoundError(ERROR_SECTION_NOT_FOUND.format(section_title=section_title))

    def _get_local_template_path(self, template_type: str, name: str) -> Path:
        """Get the path to a template in the local user workspace."""
        return settings.prompts_dir / template_type / f"{name}.md"

    def _get_package_template_path(self, template_type: str, name: str) -> Path:
        """Get the path to a template in the package templates directory."""
        return self.template_dir / template_type / f"{name}.md"

    def _load_template(self, template_type: str, name: str) -> str:
        """Loads a template file with local-first resolution strategy."""
        if template_type == TEMPLATE_TYPE_PROMPTS:
            return self._load_prompt_template(name)

        # Check local template first
        local_path = self._get_local_template_path(template_type, name)
        if local_path.exists():
            return local_path.read_text(encoding="utf-8")

        # Fallback to package template
        package_path = self._get_package_template_path(template_type, name)
        if package_path.exists():
            return package_path.read_text(encoding="utf-8")

        raise FileNotFoundError(f"Template not found: {template_type}/{name}.md")

    def _load_prompt_template(self, name: str) -> str:
        """Loads a prompt template with local-first resolution and phase-specific logic."""
        # Check local template first
        local_root_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / f"{name}.md"
        if local_root_path.exists():
            return local_root_path.read_text(encoding="utf-8")

        # Check package template
        package_root_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / f"{name}.md"
        if package_root_path.exists():
            return package_root_path.read_text(encoding="utf-8")

        phase_name, suffix = self._parse_template_name(name)

        if phase_name == PHASE_REQUIREMENTS:
            return self._load_requirements_template(suffix)

        return self._load_phase_template(phase_name, suffix)

    def _parse_template_name(self, name: str) -> tuple[str, str]:
        """Parses template name into phase and suffix."""
        if "_" in name:
            parts = name.split("_", 1)
            return parts[0], parts[1]
        return name, TEMPLATE_SUFFIX_WORK

    def _load_requirements_template(self, suffix: str) -> str:
        """Loads requirements template with local-first resolution and task source fallback."""
        config = config_manager.load_config()
        task_source = config.get_task_source()

        # Check local templates first
        local_task_source_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{task_source.value}_{suffix}.md"
        if local_task_source_path.exists():
            return local_task_source_path.read_text(encoding="utf-8")

        local_generic_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{TASK_SOURCE_GENERIC}_{suffix}.md"
        if local_generic_path.exists():
            return local_generic_path.read_text(encoding="utf-8")

        # Fallback to package templates
        task_source_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{task_source.value}_{suffix}.md"
        if task_source_path.exists():
            return task_source_path.read_text(encoding="utf-8")

        generic_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / PHASE_REQUIREMENTS / f"{TASK_SOURCE_GENERIC}_{suffix}.md"
        if generic_path.exists():
            return generic_path.read_text(encoding="utf-8")

        return self._generate_dynamic_template(PHASE_REQUIREMENTS, suffix)

    def _load_phase_template(self, phase_name: str, suffix: str) -> str:
        """Loads template for a specific phase with local-first resolution."""
        # Check local template first
        local_phase_path = settings.prompts_dir / TEMPLATE_TYPE_PROMPTS / phase_name / f"{suffix}.md"
        if local_phase_path.exists():
            return local_phase_path.read_text(encoding="utf-8")

        # Fallback to package template
        phase_path = self.template_dir / TEMPLATE_TYPE_PROMPTS / phase_name / f"{suffix}.md"
        if phase_path.exists():
            return phase_path.read_text(encoding="utf-8")

        return self._generate_dynamic_template(phase_name, suffix)

    def _generate_dynamic_template(self, phase_name: str, suffix: str) -> str:
        """Generates a dynamic template when file not found."""
        if suffix == TEMPLATE_SUFFIX_WORK:
            return (
                f"# Role: AI Assistant\n\n"
                f"Please work on task {{task_id}} for the {phase_name} phase.\n\n"
                f"**Revision Feedback:** {{revision_feedback}}\n\n"
                f"Please complete the work and call the `submit_for_review` tool with your artifact."
            )

        if suffix == TEMPLATE_SUFFIX_AI_REVIEW:
            return (
                f"# Role: QA Reviewer\n\n"
                f"Please review the artifact for task {{task_id}} in the {phase_name} phase.\n\n"
                f"**Artifact to Review:**\n```markdown\n{{artifact_content}}\n```\n\n"
                f"Call the `approve_or_request_changes` tool with your assessment."
            )

        raise FileNotFoundError(f"Template not found: {phase_name}_{suffix}")

    def generate_prompt(self, task_id: str, machine_state: str, revision_feedback: str | None = None) -> str:
        """The main method to generate a prompt based on the current state."""
        if revision_feedback is None:
            revision_feedback = self._get_stored_revision_feedback(task_id)

        phase_name, sub_state = self._parse_machine_state(machine_state)

        # Handle new phase starts with 'Clean Slate' instruction
        if sub_state == WORKFLOW_STAGE_WORKING:
            prompt = self._generate_coding_step_prompt(task_id) if phase_name == PHASE_CODING else self._generate_working_prompt(task_id, phase_name, revision_feedback)

            # Append formatting guidelines to work prompts
            prompt = self._append_formatting_guidelines(prompt)

            # Prepend clean slate instruction if it's not the very first state
            if machine_state != "gatherrequirements_working":
                return self._prepend_clean_slate_instruction(task_id, prompt)
            return prompt

        # Handle planning sub-stages
        if sub_state in [WORKFLOW_STAGE_STRATEGY, WORKFLOW_STAGE_SOLUTION_DESIGN, WORKFLOW_STAGE_EXECUTION_PLAN]:
            prompt = self._generate_planning_substage_prompt(task_id, sub_state, revision_feedback)
            # Append formatting guidelines to work prompts
            prompt = self._append_formatting_guidelines(prompt)
            # Add clean slate for the first planning sub-stage (strategy)
            if sub_state == WORKFLOW_STAGE_STRATEGY:
                return self._prepend_clean_slate_instruction(task_id, prompt)
            return prompt

        # Handle AI review states
        if sub_state == WORKFLOW_STAGE_AI_REVIEW:
            return self._generate_ai_review_prompt(task_id, phase_name)

        # Handle human/YOLO review states
        if sub_state.endswith(WORKFLOW_STAGE_DEV_REVIEW):
            config = config_manager.load_config()
            if config.features.yolo_mode:
                # YOLO mode is active, generate auto-approval prompt
                template = self._load_template(TEMPLATE_TYPE_PROMPTS, "utils/yolo_auto_approve")
                context = {"task_id": task_id, "current_state": machine_state}
                return self._safe_format_template(template, context)
            # YOLO mode is off, generate standard human review message
            return self._generate_dev_review_message(task_id, phase_name, sub_state)

        # NEW: Handle verified states to bridge the gap to the next phase
        if sub_state == WORKFLOW_STAGE_VERIFIED:
            return self._generate_verified_message(task_id, phase_name)

        return f"Task is in state '{machine_state}'. No further AI action is required."

    def _parse_machine_state(self, machine_state: str) -> tuple[str, str]:
        """Parses machine state into phase and sub-state."""
        if "_" not in machine_state:
            raise ValueError(f"Invalid machine state format: {machine_state}")

        parts = machine_state.split("_", 1)
        return parts[0], parts[1]

    def _generate_planning_substage_prompt(self, task_id: str, sub_state: str, revision_feedback: str | None) -> str:
        """Generates prompt for planning sub-stages."""
        template_suffix = self._get_planning_template_suffix(sub_state)
        template_name = f"planning_{template_suffix}"
        template = self._load_template(TEMPLATE_TYPE_PROMPTS, template_name)

        context = self._build_base_context(task_id, revision_feedback)
        # --- MODIFICATION: SINGLE CALL TO NEW METHOD ---
        machine_state = f"planning_{sub_state}"
        self._inject_context(context, task_id, machine_state)

        return self._safe_format_template(template, context)

    def _get_planning_template_suffix(self, sub_state: str) -> str:
        """Maps planning sub-state to template suffix."""
        mapping = {
            WORKFLOW_STAGE_SOLUTION_DESIGN: TEMPLATE_SUFFIX_SOLUTION_DESIGN,
            WORKFLOW_STAGE_EXECUTION_PLAN: TEMPLATE_SUFFIX_EXECUTION_PLAN,
            WORKFLOW_STAGE_STRATEGY: TEMPLATE_SUFFIX_STRATEGY,
        }
        return mapping.get(sub_state, f"{sub_state}_work")

    def _build_base_context(self, task_id: str, revision_feedback: str | None) -> dict:
        """Builds base context for prompts."""
        # Always load formatting guidelines for all phases
        formatting_guidelines = self._load_guidelines("formatting_guidelines")

        return {
            "task_id": task_id,
            "revision_feedback": revision_feedback or "No feedback provided. Please generate the initial artifact.",
            "formatting_guidelines": formatting_guidelines,
        }

    # --- UNIFIED CONTEXT INJECTION METHOD ---
    def _inject_context(self, context: dict, task_id: str, machine_state: str) -> None:
        """Injects required context into the prompt based on the current state."""
        # Normalize state to match the keys in our context map
        state_key = machine_state.replace("_working", "").replace("devreview", "")

        if state_key not in self._CONTEXT_REQUIREMENTS:
            return

        for source_phase, context_key in self._CONTEXT_REQUIREMENTS[state_key]:
            try:
                # Special handling for planning sub-stages that read from the live scratchpad
                if "approved_" in context_key:
                    scratchpad = self._load_scratchpad(task_id)
                    section_title = ""
                    if "strategy" in context_key:
                        section_title = SECTION_PLANNING_STRATEGY
                    elif "solution_design" in context_key:
                        section_title = SECTION_SOLUTION_DESIGN

                    if scratchpad and section_title:
                        context[context_key] = self._extract_section_from_scratchpad(scratchpad, section_title)
                    else:
                        context[context_key] = f"Error: Could not load required scratchpad section '{section_title}'."
                else:
                    # Standard loading from archived artifacts
                    # We assume for now this loads the .md file. This could be enhanced
                    # to specify .json or .md in the future.
                    context[context_key] = self._load_archived_artifact(task_id, source_phase)

            except ArtifactNotFoundError as e:
                context[context_key] = str(e)

    def _generate_working_prompt(self, task_id: str, phase_name: str, revision_feedback: str | None) -> str:
        """Generates prompt for working states."""
        template_name = f"{phase_name}_{TEMPLATE_SUFFIX_WORK}"
        template = self._load_template(TEMPLATE_TYPE_PROMPTS, template_name)

        context = self._build_base_context(task_id, revision_feedback)
        # --- MODIFICATION: SINGLE CALL TO NEW METHOD ---
        machine_state = f"{phase_name}_working"
        self._inject_context(context, task_id, machine_state)

        # Add guidelines based on phase
        guideline_mapping = {
            PHASE_GITSETUP: "git_guidelines",
            PHASE_CODING: "coding_guidelines",
            PHASE_TESTING: "testing_guidelines",
        }

        if phase_name in guideline_mapping:
            context["guidelines"] = self._load_guidelines(guideline_mapping[phase_name])
        else:
            context["guidelines"] = "No specific guidelines for this phase."

        return self._safe_format_template(template, context)

    def _generate_coding_step_prompt(self, task_id: str) -> str:
        """Generates a prompt for a single coding step."""
        try:
            # --- START REFACTOR ---
            # REMOVE all old regex and parsing logic here.
            # REPLACE with direct JSON loading.
            from epic_task_manager.state.manager import StateManager

            state_manager = StateManager()
            state_file = state_manager._load_state_file()
            task_state = state_file.tasks[task_id]
            current_step_index = task_state.current_step

            # Load the execution plan DIRECTLY from the JSON artifact
            plan_data = self.artifact_manager.read_json_artifact(task_id, "planning")
            plan = ExecutionPlanArtifact(**plan_data)
            # --- END REFACTOR ---

            if not plan.execution_steps:
                return "Error: The execution plan contains no steps."

            total_steps = len(plan.execution_steps)
            if current_step_index >= total_steps:
                return (
                    "# All Execution Steps Complete\n\n"
                    "You have successfully executed all steps in the plan. The final action is to submit a lightweight completion manifest.\n\n"
                    "Please call the `submit_for_review` tool now."
                )

            current_step_obj = plan.execution_steps[current_step_index]

            template = self._load_template(TEMPLATE_TYPE_PROMPTS, "coding_work_single_step")

            context = {
                "task_id": task_id,
                "step_number": current_step_index + 1,
                "total_steps": total_steps,
                "step_id": current_step_obj.prompt_id,
                "step_instruction": current_step_obj.prompt_text,
            }
            return self._safe_format_template(template, context)

        except (ArtifactNotFoundError, InvalidArtifactError, KeyError, IndexError, ValidationError) as e:
            return f"Error generating coding step prompt: {e}"

    def _generate_ai_review_prompt(self, task_id: str, phase_name: str) -> str:
        """Generates prompt for AI review states."""
        template_name = f"{phase_name}_{TEMPLATE_SUFFIX_AI_REVIEW}"
        template = self._load_template(TEMPLATE_TYPE_PROMPTS, template_name)

        artifact_content = self.artifact_manager.read_artifact(task_id)
        context = {
            "task_id": task_id,
            "artifact_content": artifact_content or "Artifact is empty.",
        }

        return self._safe_format_template(template, context)

    def _generate_dev_review_message(self, task_id: str, phase_name: str, sub_state: str) -> str:
        """Generates developer review messages."""
        artifact_path = self.artifact_manager.get_artifact_path(task_id)

        review_messages = {
            "strategydevreview": (
                f"Planning strategy is ready for your review. Please review '{artifact_path}' "
                "and then use the 'approve_or_request_changes' tool with is_approved=true to advance "
                "to solution design, or request revisions."
            ),
            "solutiondesigndevreview": (
                f"Solution design is ready for your review. Please review '{artifact_path}' "
                "and then use the 'approve_or_request_changes' tool with is_approved=true to advance "
                "to execution plan generation, or request revisions."
            ),
            "executionplandevreview": (
                f"Execution plan is ready for your review. Please review '{artifact_path}' "
                "and then use the 'approve_or_request_changes' tool with is_approved=true to complete "
                "planning and advance to coding, or request revisions."
            ),
        }

        return review_messages.get(sub_state, f"Artifact for {phase_name} is ready for your review. Please review '{artifact_path}' and then use the appropriate review tool.")

    def _generate_verified_message(self, task_id: str, phase_name: str) -> str:
        """Generates the prompt for a _verified state, prompting for advancement."""
        config = config_manager.load_config()
        if config.features.yolo_mode:
            return f"# Role: Autonomous Agent (YOLO Mode)\n\nPhase '{phase_name}' for task {task_id} is verified. Automatically advancing to the next phase.\n\nCall the `approve_and_advance` tool to proceed."
        return (
            f"Phase '{phase_name}' is complete and verified. "
            f"The final artifact for this phase is located at `.epictaskmanager/workspace/{task_id}/archive/`. "
            f"Please call `approve_and_advance` to proceed."
        )

    def _prepend_clean_slate_instruction(self, task_id: str, prompt: str) -> str:
        """Prepends the 'Clean Slate' instruction to a prompt."""
        try:
            # Load the XML-based clean_slate template
            clean_slate_template = self._load_template(TEMPLATE_TYPE_PROMPTS, "utils/clean_slate")
            clean_slate_instruction = self._safe_format_template(clean_slate_template, {"task_id": task_id})
            # Combine the two XML-structured prompts.
            # The client AI will see two distinct command blocks.
            return f"{clean_slate_instruction}\n\n---\n\n{prompt}"
        except FileNotFoundError:
            # If the template is missing, don't block the main prompt.
            # This is a non-critical enhancement.
            return prompt

    def _append_formatting_guidelines(self, prompt: str) -> str:
        """Appends formatting guidelines to work prompts."""
        # Load formatting guidelines
        formatting_guidelines = self._load_guidelines("formatting_guidelines")

        if formatting_guidelines:
            # Find the position before "## Required Work Artifact Structure" or at the end
            import re

            artifact_pattern = r"(## Required Work Artifact Structure)"
            match = re.search(artifact_pattern, prompt)

            if match:
                # Insert before the artifact structure section
                position = match.start()
                return prompt[:position] + f"## Formatting Guidelines\n\n{formatting_guidelines}\n\n" + prompt[position:]
            # Append at the end
            return prompt + f"\n\n## Formatting Guidelines\n\n{formatting_guidelines}"

        return prompt

    def _load_archived_artifact(self, task_id: str, phase_name: str) -> str:
        """Loads an archived artifact or raises ArtifactNotFoundError."""
        archived_path = self.artifact_manager.get_archive_path(task_id, phase_name, 1)

        if archived_path.exists():
            return archived_path.read_text()

        raise ArtifactNotFoundError(ERROR_VERIFIED_ARTIFACT_NOT_FOUND.format(phase=phase_name))

    def _load_scratchpad(self, task_id: str) -> str | None:
        """Loads the current scratchpad content."""
        scratchpad_path = self.artifact_manager.get_artifact_path(task_id)

        if scratchpad_path.exists():
            return scratchpad_path.read_text()

        return None

    def _load_guidelines(self, guideline_name: str) -> str:
        """Loads a guideline file or returns an empty string if not found."""
        guideline_path = self.template_dir / "guidelines" / f"{guideline_name}.md"
        if guideline_path.exists():
            return guideline_path.read_text(encoding="utf-8")
        return ""

    def _get_stored_revision_feedback(self, task_id: str) -> str | None:
        """Retrieves stored revision feedback for a task."""
        try:
            from epic_task_manager.state.manager import StateManager

            state_manager = StateManager()
            state_file = state_manager._load_state_file()
            task_state = state_file.tasks.get(task_id)
            if task_state:
                return task_state.revision_feedback
        except Exception:
            # If we can't load the state for any reason, just return None
            pass
        return None
