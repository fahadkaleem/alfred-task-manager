# src/alfred/tools/submit_work.py
import json

from pydantic import ValidationError
from src.alfred.core.prompter import prompter
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager
from src.alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """
    Implements the logic for submitting a work artifact to the active tool.

    IMPORTANT: This implementation uses atomic state transitions to prevent
    state corruption if any operation fails.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.TASK_NOT_FOUND.format(task_id=task_id))

    # Save current state for potential rollback
    original_state = active_tool.state
    original_context = active_tool.context_store.copy()

    try:
        # PHASE 1: Prepare - validate and prepare everything that could fail

        # Artifact Validation
        current_state = active_tool.state
        artifact_model = active_tool.artifact_map.get(current_state)

        if artifact_model:
            # Normalize operation values to uppercase for consistency
            if artifact_model.__name__ == "ExecutionPlanArtifact" and "subtasks" in artifact:
                # Normalize Subtask operation values
                for subtask in artifact["subtasks"]:
                    if "operation" in subtask and isinstance(subtask["operation"], str):
                        subtask["operation"] = subtask["operation"].upper()
            elif artifact_model.__name__ == "DesignArtifact" and "file_breakdown" in artifact:
                # Normalize FileChange operation values
                for file_change in artifact["file_breakdown"]:
                    if "operation" in file_change and isinstance(file_change["operation"], str):
                        file_change["operation"] = file_change["operation"].upper()

            try:
                # Validate the submitted dictionary against the Pydantic model
                validated_artifact = artifact_model.model_validate(artifact)
                logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state.value if hasattr(current_state, "value") else current_state, model=artifact_model.__name__))
            except ValidationError as e:
                error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state.value if hasattr(current_state, 'value') else current_state)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
                return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
        else:
            validated_artifact = artifact  # No validator for this state, proceed

        # Load persona config (used for both persistence and prompt generation)
        try:
            persona_config = load_persona(active_tool.persona_name)
        except FileNotFoundError as e:
            return ToolResponse(status=ResponseStatus.ERROR, message=str(e))

        # Calculate next state
        current_state_val = active_tool.state.value if hasattr(active_tool.state, "value") else active_tool.state
        trigger = Triggers.submit_trigger(current_state_val)

        if not hasattr(active_tool, trigger):
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")

        # Get the next state
        next_transitions = active_tool.machine.get_transitions(source=active_tool.state, trigger=trigger)
        if not next_transitions:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger}' from state '{active_tool.state}'.")
        next_state = next_transitions[0].dest

        # Prepare additional context for prompt generation
        temp_context = active_tool.context_store.copy()

        # Use the centralized artifact key generation
        artifact_key = ArtifactKeys.get_artifact_key(current_state_val)

        temp_context[artifact_key] = validated_artifact
        temp_context[ArtifactKeys.ARTIFACT_CONTENT_KEY] = json.dumps(artifact, indent=2)

        # Generate prompt for the NEXT state (most likely to fail)
        next_prompt = prompter.generate_prompt(
            task=task,
            tool_name=active_tool.tool_name,
            state=next_state,  # Use calculated next state
            persona_config=persona_config,
            additional_context=temp_context,
        )

        # PHASE 2: Commit - only if everything succeeded

        # Store validated artifact in the tool's context using the same clean name
        active_tool.context_store[artifact_key] = validated_artifact
        # Convert Pydantic model to dict for JSON serialization
        artifact_dict = validated_artifact.model_dump() if hasattr(validated_artifact, "model_dump") else validated_artifact
        active_tool.context_store[ArtifactKeys.ARTIFACT_CONTENT_KEY] = json.dumps(artifact_dict, indent=2)
        logger.info(f"Stored artifact in context_store with key '{artifact_key}' and {ArtifactKeys.ARTIFACT_CONTENT_KEY}.")

        # Persist artifact to scratchpad
        artifact_manager.append_to_scratchpad(task_id=task_id, state_name=current_state_val, artifact=validated_artifact, persona_config=persona_config)

        # Trigger the state transition
        getattr(active_tool, trigger)()
        logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))

        # Persist the new state immediately
        state_manager.save_tool_state(task_id, active_tool)

        return ToolResponse(status=ResponseStatus.SUCCESS, message="Work submitted. Awaiting review.", next_prompt=next_prompt)

    except Exception as e:
        # Rollback on any failure
        logger.error(f"Work submission failed for task {task_id}: {e}")
        active_tool.state = original_state
        active_tool.context_store = original_context

        # Save the rolled-back state
        try:
            state_manager.save_tool_state(task_id, active_tool)
        except:
            pass  # Don't fail the error response if state save fails

        return ToolResponse(status=ResponseStatus.ERROR, message=f"Failed to submit work: {str(e)}")
