"""
The central orchestrator for Alfred. Manages tasks and persona runtimes.
"""

import yaml

from src.alfred.config import ConfigManager
from src.alfred.config.settings import settings
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import cleanup_task_logging, get_logger, setup_task_logging
from src.alfred.models.config import PersonaConfig
from src.alfred.models.state import StateFile, TaskState
from src.alfred.orchestration.persona_loader import PersonaLoader
from src.alfred.orchestration.persona_runtime import PersonaRuntime

logger = get_logger(__name__)


class Orchestrator:
    """Singleton class to manage the application's main logic."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._validate_configuration()
        self.persona_registry = PersonaLoader.load_all()
        self.active_runtimes: dict[str, PersonaRuntime] = {}
        self.config_manager = ConfigManager(settings.alfred_dir)
        self._load_workflow_sequence()
        self._initialized = True

    def _validate_configuration(self):
        """
        Validates the Alfred configuration during startup.
        
        This method:
        1. Parses workflow.yml to get the persona sequence
        2. Ensures corresponding persona .yml files exist in the personas/ directory
        3. Validates that PersonaLoader can parse each required YAML file against PersonaConfig
        
        Raises:
            SystemExit: If any persona is missing or misconfigured
        """
        try:
            # Parse workflow.yml
            if not settings.packaged_workflow_file.exists():
                logger.critical(f"workflow.yml not found at: {settings.packaged_workflow_file}")
                raise SystemExit("CRITICAL ERROR: workflow.yml file is missing. Alfred cannot start.")
            
            with settings.packaged_workflow_file.open("r", encoding="utf-8") as f:
                workflow_data = yaml.safe_load(f)
            
            if not workflow_data or "sequence" not in workflow_data:
                logger.critical("workflow.yml is missing required 'sequence' field")
                raise SystemExit("CRITICAL ERROR: workflow.yml is malformed - missing 'sequence' field. Alfred cannot start.")
            
            sequence = workflow_data["sequence"]
            if not isinstance(sequence, list) or not sequence:
                logger.critical("workflow.yml 'sequence' field must be a non-empty list")
                raise SystemExit("CRITICAL ERROR: workflow.yml 'sequence' field must be a non-empty list. Alfred cannot start.")
            
            # Validate personas directory exists
            if not settings.packaged_personas_dir.exists():
                logger.critical(f"Personas directory not found at: {settings.packaged_personas_dir}")
                raise SystemExit(f"CRITICAL ERROR: Personas directory missing at {settings.packaged_personas_dir}. Alfred cannot start.")
            
            # Check each persona in the sequence
            missing_personas = []
            invalid_personas = []
            
            for persona_name in sequence:
                persona_file = settings.packaged_personas_dir / f"{persona_name}.yml"
                
                # Check if persona file exists
                if not persona_file.exists():
                    missing_personas.append(persona_name)
                    continue
                
                # Validate persona file can be parsed
                try:
                    with persona_file.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    
                    if not data:
                        invalid_personas.append(f"{persona_name} (empty file)")
                        continue
                    
                    # Validate against PersonaConfig model
                    PersonaConfig(**data)
                    logger.debug(f"Successfully validated persona: {persona_name}")
                    
                except yaml.YAMLError as e:
                    invalid_personas.append(f"{persona_name} (YAML parsing error: {e})")
                except Exception as e:
                    invalid_personas.append(f"{persona_name} (validation error: {e})")
            
            # Report all validation errors
            if missing_personas or invalid_personas:
                error_msg = "CRITICAL ERROR: Alfred configuration validation failed:\n"
                
                if missing_personas:
                    error_msg += f"Missing persona files: {', '.join(missing_personas)}\n"
                    error_msg += f"Expected location: {settings.packaged_personas_dir}/\n"
                
                if invalid_personas:
                    error_msg += f"Invalid persona configurations: {', '.join(invalid_personas)}\n"
                
                error_msg += "Alfred cannot start until all personas are properly configured."
                logger.critical(error_msg)
                raise SystemExit(error_msg)
            
            logger.info(f"Configuration validation successful. Validated {len(sequence)} personas: {', '.join(sequence)}")
            
        except SystemExit:
            raise
        except Exception as e:
            logger.critical(f"Unexpected error during configuration validation: {e}")
            raise SystemExit(f"CRITICAL ERROR: Configuration validation failed with unexpected error: {e}")

    def _load_workflow_sequence(self):
        """Loads the persona sequence from workflow.yml and applies configuration."""
        try:
            with settings.packaged_workflow_file.open("r", encoding="utf-8") as f:
                base_sequence = yaml.safe_load(f).get("sequence", [])
        except FileNotFoundError:
            base_sequence = []

        try:
            config = self.config_manager.load()
        except FileNotFoundError:
            self.workflow_sequence = base_sequence
            return

        self.workflow_sequence = base_sequence.copy()

        if config.features.scaffolding_mode and "scaffolder" not in self.workflow_sequence:
            try:
                planning_idx = self.workflow_sequence.index("planning")
                self.workflow_sequence.insert(planning_idx + 1, "scaffolder")
                logger.info("Scaffolding mode enabled - inserted scaffolder persona into workflow")
            except ValueError:
                logger.warning("Could not find 'planning' persona in workflow sequence")

    def _get_or_create_runtime(self, task_id: str) -> PersonaRuntime | None:
        """Gets a live runtime or creates one based on the task's persisted state."""
        if task_id in self.active_runtimes:
            return self.active_runtimes[task_id]

        state_file = self._load_state(task_id)
        task_state = state_file.tasks.get(task_id)

        if not task_state:
            task_state = TaskState(task_id=task_id)
            artifact_manager.create_task_workspace(task_id)
            if not self.workflow_sequence:
                return None
            initial_persona_name = self.workflow_sequence[0]
            persona_config = self.persona_registry.get(initial_persona_name)
            if not persona_config:
                return None
            task_state.persona_state = persona_config.hsm.initial_state
            self._save_task_state(task_state)

        current_persona_name = self.workflow_sequence[task_state.workflow_step]
        persona_config = self.persona_registry.get(current_persona_name)
        if not persona_config:
            return None

        runtime = PersonaRuntime(task_id=task_id, config=persona_config)
        runtime.state = task_state.persona_state
        self.active_runtimes[task_id] = runtime
        return runtime

    def _load_state(self, task_id: str | None = None) -> StateFile:
        """Loads the state from a per-task state.json file or returns default state."""
        if task_id:
            task_state_file = settings.workspace_dir / task_id / "state.json"
            if task_state_file.exists():
                try:
                    task_state = TaskState.model_validate_json(task_state_file.read_text())
                    return StateFile(tasks={task_id: task_state})
                except Exception as e:
                    logger.error(f"Failed to load state for task {task_id}: {e}")
        
        # Return empty state file for new tasks or when no task_id provided
        return StateFile()

    def _save_task_state(self, task_state: TaskState):
        """Saves a single task's state to its dedicated state.json file."""
        task_dir = settings.workspace_dir / task_state.task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        
        task_state_file = task_dir / "state.json"
        with task_state_file.open("w", encoding="utf-8") as f:
            f.write(task_state.model_dump_json(indent=2))
        
        logger.debug(f"Saved state for task {task_state.task_id} to {task_state_file}")

    def begin_task(self, task_id: str) -> tuple[str, str | None]:
        """Begins or resumes a task, returning an initial prompt."""
        setup_task_logging(task_id)
        logger.info(f"Orchestrator beginning/resuming task {task_id}.")
        
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            logger.error(f"Failed to get or create runtime for task {task_id}.")
            return ("Error: Could not create or find a runtime for this task. Check workflow/persona configuration.", None)

        additional_context = self._build_task_context(runtime, task_id)
        message = f"Resuming task {task_id} with persona '{runtime.config.name}'. Current state: {runtime.state}"
        prompt = runtime.get_current_prompt(additional_context=additional_context if additional_context else None)
        return (message, prompt)

    def _build_task_context(self, runtime, task_id: str) -> dict:
        """Builds additional context for task execution."""
        additional_context = {}
        
        self._add_provider_context(runtime, additional_context)
        self._add_stepwise_context(runtime, task_id, additional_context)
        
        return additional_context

    def _add_provider_context(self, runtime, additional_context: dict) -> None:
        """Adds provider information for requirements persona."""
        if runtime.config.name == "Intake Analyst":
            try:
                config = self.config_manager.load()
                additional_context["task_provider"] = config.providers.task_provider.value
            except:
                additional_context["task_provider"] = "local"

    def _add_stepwise_context(self, runtime, task_id: str, additional_context: dict) -> None:
        """Adds stepwise execution context for stepwise personas."""
        if runtime.config.execution_mode == "stepwise" and runtime.state.endswith("_working"):
            task_state = self._load_state(task_id).tasks.get(task_id)
            if task_state and task_state.execution_plan:
                steps = task_state.execution_plan.get("implementation_steps", [])
                if task_state.current_step < len(steps):
                    step = steps[task_state.current_step]
                    additional_context.update({
                        "step_id": f"step_{task_state.current_step + 1}",
                        "step_instruction": str(step),
                        "step_number": task_state.current_step + 1,
                        "total_steps": len(steps),
                    })

    def submit_work_for_task(self, task_id: str, artifact_data: dict) -> tuple[str, str | None]:
        """Routes a work submission, validating and persisting the artifact."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        validated_artifact = runtime.validate_artifact(artifact_data)
        if not validated_artifact:
            return f"Artifact validation failed for state '{runtime.state}'.", None

        artifact_type = type(validated_artifact).__name__.lower().replace("artifact", "")
        artifact_manager.append_to_scratchpad(task_id, artifact_type, validated_artifact, runtime.config)
        runtime.submitted_artifact_data = artifact_data

        success, message = runtime.trigger_submission()
        if not success:
            return (message, None)

        task_state = self._load_state(task_id).tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)

        return (message, runtime.get_current_prompt())

    def _perform_handoff(self, task_id: str, task_state: TaskState, target_persona: str, target_state: str, feedback: str | None = None) -> tuple[str, str | None]:
        """Centralized method to handle all persona handoffs."""
        try:
            target_step_index = self.workflow_sequence.index(target_persona)
        except ValueError:
            return f"Error: Target persona '{target_persona}' not found in workflow.", None

        target_config = self.persona_registry.get(target_persona)
        if not target_config:
            return f"Error: Could not load config for target persona '{target_persona}'.", None

        task_state.workflow_step = target_step_index
        task_state.persona_state = target_state
        task_state.revision_feedback = feedback
        task_state.current_step = 0
        task_state.completed_steps = []

        if target_config.execution_mode == "stepwise":
            plan = artifact_manager.read_execution_plan(task_id)
            if not plan:
                return f"CRITICAL ERROR: Handoff to stepwise persona '{target_persona}' failed. Could not read execution_plan.json.", None
            task_state.execution_plan = plan
        else:
            task_state.execution_plan = None

        self._save_task_state(task_state)
        self.active_runtimes.pop(task_id, None)
        next_runtime = self._get_or_create_runtime(task_id)
        if not next_runtime:
            return f"Error: Could not create runtime for '{target_persona}'.", None

        next_prompt = next_runtime.get_current_prompt(revision_feedback=feedback)
        message = f"Handoff complete. Task is now with '{next_runtime.config.name}' in state '{next_runtime.state}'."
        return message, next_prompt

    def process_review(self, task_id: str, is_approved: bool, feedback: str) -> tuple[str, str | None]:
        """Routes a review, handling internal transitions and backward handoffs."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None
        task_state = self._load_state(task_id).tasks.get(task_id)
        if not task_state:
            return "Error: Task state not found.", None

        success, result = runtime.process_review(is_approved)
        if not success:
            return result, None

        if isinstance(result, dict) and "handoff_to" in result:
            return self._perform_handoff(task_id, task_state, result["handoff_to"], result["target_state"], feedback=feedback)

        task_state.persona_state = runtime.state
        task_state.revision_feedback = feedback if not is_approved else None
        self._save_task_state(task_state)
        return result, runtime.get_current_prompt(revision_feedback=task_state.revision_feedback)

    def process_human_approval(self, task_id: str) -> tuple[str, str | None]:
        """Handles human approval for an intra-persona stage advance."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        success, message = runtime.process_human_approval()
        if not success:
            return message, None

        task_state = self._load_state(task_id).tasks.get(task_id)
        if task_state:
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)
        return message, runtime.get_current_prompt()

    def process_handoff(self, task_id: str) -> tuple[str, str | None]:
        """Processes final approval and hands off to the next persona."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None

        # If we are in a devreview state, first trigger the final human_approve.
        if runtime.state.endswith("devreview"):
            success, message = runtime.process_human_approval()
            if not success:
                return f"Handoff failed: could not process final approval. Error: {message}", None

        if not runtime.state.endswith("verified"):
            return f"Error: Handoff requires persona to be in a verified state. Current state: '{runtime.state}'.", None

        task_state = self._load_state(task_id).tasks.get(task_id)
        if not task_state:
            return "Error: Cannot find task state to update.", None

        artifact_manager.archive_scratchpad(task_id, runtime.config.name, task_state.workflow_step)

        if runtime.config.name == "Alex" and runtime.submitted_artifact_data:
            artifact_manager.write_json_artifact(task_id, "planning_execution_plan.json", runtime.submitted_artifact_data)

        next_step_index = task_state.workflow_step + 1
        if next_step_index >= len(self.workflow_sequence):
            cleanup_task_logging(task_id)
            return "Workflow complete!", "Task is fully complete."

        target_persona = self.workflow_sequence[next_step_index]
        target_config = self.persona_registry.get(target_persona)
        if not target_config:
            return f"Error: Next persona '{target_persona}' not found.", None

        return self._perform_handoff(task_id, task_state, target_persona, target_config.hsm.initial_state)

    def process_step_completion(self, task_id: str, step_id: str) -> tuple[str, str | None]:
        """Processes a step completion for any stepwise persona."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Task runtime not found.", None
        if runtime.config.execution_mode != "stepwise":
            return f"Error: Step completion is not valid for the '{runtime.config.name}' persona.", None

        task_state = self._load_state(task_id).tasks.get(task_id)
        if not task_state:
            return "Error: Task state not found.", None

        execution_plan = task_state.execution_plan
        if not execution_plan or "implementation_steps" not in execution_plan:
            return "Error: Execution plan not found in the current task state.", None

        steps = execution_plan.get("implementation_steps", [])
        if task_state.current_step >= len(steps):
            return "Error: All steps already completed.", None

        expected_step_id = f"step_{task_state.current_step + 1}"
        if step_id != expected_step_id:
            return f"Error: Incorrect step ID. Expected '{expected_step_id}', got '{step_id}'.", None

        return self._update_step_state_and_get_next(task_id, task_state, execution_plan, step_id)

    def _update_step_state_and_get_next(self, task_id: str, task_state, execution_plan: dict, step_id: str) -> tuple[str, str | None]:
        """Updates step state and gets the next prompt via the runtime."""
        runtime = self._get_or_create_runtime(task_id)
        if not runtime:
            return "Error: Could not get runtime.", None

        self._complete_current_step(task_state, step_id)
        steps = execution_plan.get("implementation_steps", [])
        
        if task_state.current_step >= len(steps):
            return self._handle_all_steps_complete(runtime, task_state)
        else:
            return self._get_next_step_prompt(runtime, task_state, steps, step_id)

    def _complete_current_step(self, task_state, step_id: str) -> None:
        """Marks the current step as complete and updates state."""
        task_state.completed_steps.append(step_id)
        task_state.current_step += 1
        self._save_task_state(task_state)

    def _handle_all_steps_complete(self, runtime, task_state) -> tuple[str, str | None]:
        """Handles completion of all steps and transitions to submission state."""
        try:
            runtime.step_complete()
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)
            message = "All steps complete. Ready for final manifest submission."
            next_prompt = runtime.get_current_prompt()
        except Exception:
            runtime.state = f"{runtime.state.split('_')[0]}_submission"
            task_state.persona_state = runtime.state
            self._save_task_state(task_state)
            message = "All steps complete. Ready for final manifest submission."
            next_prompt = runtime.get_current_prompt()
        return message, next_prompt

    def _get_next_step_prompt(self, runtime, task_state, steps: list, completed_step_id: str) -> tuple[str, str | None]:
        """Gets the prompt for the next step in execution."""
        step = steps[task_state.current_step]
        step_context = {
            "step_id": f"step_{task_state.current_step + 1}",
            "step_instruction": str(step),
            "step_number": task_state.current_step + 1,
            "total_steps": len(steps),
        }
        message = f"Step '{completed_step_id}' complete."
        next_prompt = runtime.get_current_prompt(additional_context=step_context)
        return message, next_prompt


orchestrator = Orchestrator()
