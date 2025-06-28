# File: src/epic_task_manager/tools/task_tools.py

from pydantic import ValidationError

from epic_task_manager.config.config_manager import config_manager
from epic_task_manager.config.settings import settings
from epic_task_manager.constants import (
    ADVANCE_TRIGGERS,
    DEFAULT_AI_MODEL,
    DEFAULT_ARTIFACT_VERSION,
    STATUS_ERROR,
    STATUS_SUCCESS,
)
from epic_task_manager.exceptions import TaskNotFoundError
from epic_task_manager.execution.artifact_behavior import ArtifactBehaviorConfig
from epic_task_manager.execution.artifact_manager import ArtifactManager
from epic_task_manager.execution.prompter import Prompter
from epic_task_manager.models import artifacts
from epic_task_manager.models.schemas import ToolResponse
from epic_task_manager.state.machine import STATE_VERIFIED
from epic_task_manager.state.manager import StateManager
from epic_task_manager.task_sources.local.provider import LocalProvider

state_manager = StateManager()
artifact_manager = ArtifactManager()
prompter = Prompter()


def _is_project_initialized() -> bool:
    """Check if project has been initialized."""
    return settings.config_file.exists()


def _error_response(message: str) -> ToolResponse:
    """Create standardized error response."""
    return ToolResponse(status=STATUS_ERROR, message=message)


def _get_pydantic_model_for_state(state: str) -> type[artifacts.BaseModel] | None:
    """Maps a state string to its corresponding Pydantic artifact model."""
    pydantic_model_map = {
        "requirements_working": artifacts.RequirementsArtifact,
        "gitsetup_working": artifacts.GitSetupArtifact,
        "planning_strategy": artifacts.StrategyArtifact,
        "planning_solutiondesign": artifacts.SolutionDesignArtifact,
        "planning_executionplan": artifacts.ExecutionPlanArtifact,
        "scaffolding_working": artifacts.ScaffoldingArtifact,
        "coding_working": artifacts.CodingArtifact,
        "testing_working": artifacts.TestingArtifact,
        "finalize_working": artifacts.FinalizeArtifact,
    }
    # Normalize state for lookup (e.g., 'planning_strategy' from 'planning_strategy_devreview')
    base_state = state.split("_")[0] + "_" + state.split("_")[1] if "_" in state else state
    if base_state in pydantic_model_map:
        return pydantic_model_map[base_state]

    planning_substage_state = state.replace("devreview", "")
    if planning_substage_state in pydantic_model_map:
        return pydantic_model_map[planning_substage_state]

    return None


async def begin_or_resume_task(task_id: str) -> ToolResponse:
    """Initializes a new task or returns the status of an existing one."""
    if not _is_project_initialized():
        return _error_response("Project not initialized. Please run the 'initialize_project' tool first.")

    try:
        model = state_manager.get_machine(task_id)

        # Handle completed tasks gracefully
        if model and model.state == "done":
            state_manager.deactivate_all_tasks()  # Ensure it's not active
            return ToolResponse(
                status=STATUS_SUCCESS,
                message=f"Task {task_id} is already complete.",
                next_prompt=(
                    "<objective>Inform the user that the task is complete and find the next available task.</objective>\n"
                    "<instructions>\n"
                    f"1. Report to the user that task `{task_id}` is already done.\n"
                    "2. Call the `list_available_tasks` tool to discover what to work on next.\n"
                    "</instructions>"
                ),
            )

        if not model:
            model = state_manager.create_machine(task_id)
            artifact_manager.create_task_structure(task_id)
            message = f"Task {task_id} created. Current state: {model.state}"
        else:
            message = f"Resuming task {task_id}. Current state: {model.state}"

        state_manager.set_active_task(task_id)
        prompt = prompter.generate_prompt(task_id, model.state)
        return ToolResponse(status=STATUS_SUCCESS, message=message, next_prompt=prompt)
    except TaskNotFoundError as e:
        return _error_response(str(e))


async def submit_for_review(task_id: str, work_artifact: dict) -> ToolResponse:
    """Validates submitted work, saves machine/human artifacts, and transitions state."""
    if not _is_project_initialized():
        return _error_response("Project not initialized.")
    model = state_manager.get_machine(task_id)
    if not model:
        return _error_response(f"Task {task_id} not found.")

    current_state_before_submit = model.state
    phase_name = current_state_before_submit.split("_")[0]

    try:
        # 1. Validate incoming data against the Pydantic model for the current state.
        pydantic_model = _get_pydantic_model_for_state(current_state_before_submit)
        validated_data = None
        if pydantic_model:
            try:
                full_artifact_data = {"metadata": {"task_id": task_id, "phase": phase_name, "status": "working"}, **work_artifact}
                validated_data = pydantic_model(**full_artifact_data)
            except ValidationError as e:
                return _error_response(f"Work artifact validation failed: {e}")

        # 2. If this is the final planning step, save the validated, machine-readable JSON object.
        #    This is the only data the 'coding' phase will read.
        if current_state_before_submit == "planning_executionplan" and validated_data:
            json_path = artifact_manager.get_task_dir(task_id) / "execution_plan.json"
            json_path.write_text(validated_data.model_dump_json(indent=2), encoding="utf-8")

        # 3. Build and write the human-readable markdown artifact to the scratchpad.
        template_name = _get_artifact_template_name(phase_name, current_state_before_submit.split("_", 1)[1])
        template = prompter._load_template("artifacts", template_name)

        # Add metadata and task_id to work_artifact for template building
        enriched_work_artifact = {
            "metadata": {"task_id": task_id, "phase": phase_name, "status": "working", "version": DEFAULT_ARTIFACT_VERSION, "ai_model": DEFAULT_AI_MODEL},
            "task_id": task_id,
            **work_artifact,
        }

        final_markdown = artifact_manager.build_structured_artifact(template, enriched_work_artifact)

        behavior_config = ArtifactBehaviorConfig()
        if behavior_config.should_append(current_state_before_submit):
            artifact_manager.append_to_artifact(task_id, final_markdown)
        else:
            artifact_manager.write_artifact(task_id, final_markdown)

        # 4. Transition the state and save.
        model.submit_for_ai_review()
        state_manager.save_machine_state(task_id, model)

        # 5. Generate the next prompt for the new state.
        prompt = prompter.generate_prompt(task_id, model.state)
        return ToolResponse(
            status=STATUS_SUCCESS,
            message=f"Work submitted for {task_id}. State is now '{model.state}'.",
            next_prompt=prompt,
        )
    except Exception as e:
        return _error_response(f"Could not submit work from state '{current_state_before_submit}'. Error: {e}")


async def approve_and_advance(task_id: str) -> ToolResponse:
    """Advances a task to the next major phase, signifying human approval."""
    if not _is_project_initialized():
        return _error_response("Project not initialized.")
    machine = state_manager.get_machine(task_id)
    if not machine:
        return _error_response(f"Task {task_id} not found.")

    current_state = machine.state
    if not (current_state.endswith(("_devreview", "_verified"))):
        return _error_response(f"Cannot advance. Task must be in a review or verified state. Current: {current_state}")

    try:
        current_phase = current_state.split("_")[0]

        if current_state.endswith("_devreview"):
            machine.human_approves()
            state_manager.save_machine_state(task_id, machine)

        # --- THIS IS THE CORRECTED LOGIC ---
        # There is no parsing. We simply move the pre-validated files.
        json_data_to_archive = None
        if current_phase == "planning":
            try:
                live_json_path = artifact_manager.get_task_dir(task_id) / "execution_plan.json"
                if not live_json_path.exists():
                    raise FileNotFoundError("Critical Error: execution_plan.json was not created during the planning phase.")

                # Load the raw text and re-validate into a Pydantic object for the archiver.
                json_content = live_json_path.read_text(encoding="utf-8")
                json_data_to_archive = artifacts.ExecutionPlanArtifact.model_validate_json(json_content)
                live_json_path.unlink()  # Clean up the temporary file.

            except (FileNotFoundError, ValidationError) as e:
                return _error_response(f"Could not finalize and archive planning data. Error: {e}")

        # Archive the human-readable scratchpad and, if applicable, the machine-readable JSON.
        artifact_manager.archive_artifact(task_id, current_phase, json_data=json_data_to_archive)
        # --- END CORRECTION ---

        # Conditional routing logic for scaffolding feature
        if machine.state == f"planning_{STATE_VERIFIED}":
            config = config_manager.load_config()
            if config.features.scaffolding_mode:
                machine.advance_to_scaffold()
            else:
                machine.advance_to_code()
        elif machine.state == f"scaffolding_{STATE_VERIFIED}":
            machine.advance_from_scaffold()
        else:
            # Fallback to existing generic advance logic
            advance_trigger = ADVANCE_TRIGGERS.get(machine.state)
            if not advance_trigger:
                return _error_response(f"No advance trigger found for state: {machine.state}")
            getattr(machine, advance_trigger)()

        if machine.state == "coding_working":
            state_file = state_manager._load_state_file()
            if task_id in state_file.tasks:
                task_state = state_file.tasks[task_id]
                task_state.current_step = 0
                task_state.completed_steps = []
                state_manager._save_state_file(state_file)

        state_manager.save_machine_state(task_id, machine)

        if machine.state == "done":
            state_manager.deactivate_all_tasks()  # Deactivate on completion
            return ToolResponse(
                status=STATUS_SUCCESS,
                message=f"Phase '{current_phase}' approved. Task completed!",
                next_prompt=(
                    "<objective>Inform the user the task is complete and look for the next one.</objective>\n"
                    "<instructions>\n"
                    f"1. Report to the user that task `{task_id}` is now complete.\n"
                    "2. Call `list_available_tasks` to discover what to work on next.\n"
                    "</instructions>"
                ),
            )

        artifact_manager.write_artifact(task_id, f"# {machine.state.split('_')[0].title()} Artifact\n\nWaiting for AI to generate content...")
        prompt = prompter.generate_prompt(task_id, machine.state)
        return ToolResponse(status=STATUS_SUCCESS, message=f"Phase approved. Advanced to '{machine.state}'.", next_prompt=prompt)

    except Exception as e:
        return _error_response(f"Failed to advance phase. Error: {e}")


def _get_artifact_template_name(phase_name: str, sub_state: str) -> str:
    """Get the appropriate artifact template name for a phase and sub-state."""
    _TEMPLATE_NAME_MAP = {
        "planning": {
            "strategy": "planning_strategy_artifact",
            "solutiondesign": "planning_solution_design_artifact",
            "executionplan": "planning_execution_plan_artifact",
        },
    }
    if phase_name == "planning" and sub_state in _TEMPLATE_NAME_MAP["planning"]:
        return _TEMPLATE_NAME_MAP["planning"][sub_state]
    if phase_name == "gitsetup":
        return "git_setup_artifact"
    if phase_name == "scaffolding":
        return "scaffolding_artifact"
    return f"{phase_name}_artifact"


async def list_available_tasks() -> ToolResponse:
    """
    Lists available tasks from the configured provider that are not yet complete.
    For the 'local' provider, this means any task file in the inbox that isn't 'done'.
    """
    if not _is_project_initialized():
        return _error_response("Project not initialized.")

    config = config_manager.load_config()
    state_file = state_manager._load_state_file()
    completed_task_ids = {tid for tid, tstate in state_file.tasks.items() if tstate.current_state == "done"}

    available_tasks = []
    if config.get_task_source() == "local":
        provider = LocalProvider({"tasks_inbox_directory": settings.tasks_inbox_dir})
        all_local_tasks = provider.list_available_tasks()
        available_tasks = [task for task in all_local_tasks if task["id"] not in completed_task_ids]
    # Add logic for Jira/Linear providers here in the future
    # else:
    #     # Call remote provider
    #     pass

    if not available_tasks:
        return ToolResponse(
            status=STATUS_SUCCESS, message="No available tasks found.", data={"available_tasks": []}, next_prompt="<objective>Inform the user that there are no new tasks in the inbox.</objective>"
        )

    return ToolResponse(
        status=STATUS_SUCCESS,
        message=f"Found {len(available_tasks)} available tasks.",
        data={"available_tasks": available_tasks},
        next_prompt=(
            "<objective>Present the available tasks to the user and await instruction.</objective>\n"
            "<instructions>\n"
            "1. Present the `available_tasks` from the `data` field to the user. The `summary` field should be used for display.\n"
            "2. If the user asks for more details about a specific task, you MUST use the `get_task_details` tool with the corresponding `task_id`.\n"
            "3. If the user confirms they want to start a task, call `begin_or_resume_task` with their chosen task ID.\n"
            "</instructions>"
        ),
    )


async def get_task_details(task_id: str) -> ToolResponse:
    """
    Retrieves the full details for a single task from the configured provider.
    """
    if not _is_project_initialized():
        return _error_response("Project not initialized.")

    config = config_manager.load_config()
    provider_type = config.get_task_source()

    try:
        details = {}
        if provider_type == "local":
            provider = LocalProvider({"tasks_inbox_directory": settings.tasks_inbox_dir})
            details = provider.get_task_details(task_id)
        # Add logic for Jira/Linear here in the future

        if not details:
            return _error_response(f"Could not retrieve details for task '{task_id}'.")

        return ToolResponse(
            status=STATUS_SUCCESS,
            message="Task details retrieved successfully.",
            data=details,
            next_prompt=None,  # This is an informational tool, no next action prescribed.
        )
    except FileNotFoundError:
        return _error_response(f"Task file for '{task_id}' not found in the tasks inbox.")
    except Exception as e:
        return _error_response(f"An error occurred while getting task details: {e}")
