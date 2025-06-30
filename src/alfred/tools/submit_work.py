# src/alfred/tools/submit_work.py
import json

from pydantic import ValidationError

from src.alfred.core.prompter import prompter
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.state.manager import state_manager
from src.alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """Implements the logic for submitting a work artifact to the active tool."""
    # Try to get active tool or recover it from state
    if task_id not in orchestrator.active_tools:
        # Try to recover the tool from persisted state
        from src.alfred.state.recovery import ToolRecovery

        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            logger.info(f"Recovered tool for task {task_id} from persisted state")
        else:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status=ResponseStatus.ERROR, message=LogMessages.TASK_NOT_FOUND.format(task_id=task_id))

    current_state_enum = active_tool.state
    current_state_val = active_tool.state.value if hasattr(active_tool.state, "value") else active_tool.state
    artifact_model = active_tool.artifact_map.get(current_state_enum)

    if artifact_model:
        try:
            validated_artifact = artifact_model.model_validate(artifact)
            logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state_val, model=artifact_model.__name__))
        except ValidationError as e:
            error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state_val)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
            return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
    else:
        validated_artifact = artifact

    trigger = Triggers.submit_trigger(current_state_val)
    if not hasattr(active_tool, trigger):
        return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")

    next_transitions = active_tool.machine.get_transitions(source=active_tool.state, trigger=trigger)
    if not next_transitions:
        return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger}' from state '{active_tool.state}'.")
    next_state = next_transitions[0].dest

    temp_context = active_tool.context_store.copy()
    artifact_key = ArtifactKeys.get_artifact_key(current_state_val)
    temp_context[artifact_key] = validated_artifact
    # For review states, we need the artifact as an object, not a string
    temp_context[ArtifactKeys.ARTIFACT_CONTENT_KEY] = validated_artifact

    next_prompt = prompter.generate_prompt(
        task=task,
        tool_name=active_tool.tool_name,
        state=next_state,
        additional_context=temp_context,
    )

    active_tool.context_store[artifact_key] = validated_artifact
    artifact_manager.append_to_scratchpad(task_id=task_id, state_name=current_state_val, artifact=validated_artifact)

    getattr(active_tool, trigger)()
    logger.info(LogMessages.STATE_TRANSITION.format(task_id=task_id, trigger=trigger, state=active_tool.state))

    state_manager.update_tool_state(task_id, active_tool)

    return ToolResponse(status=ResponseStatus.SUCCESS, message="Work submitted. Awaiting review.", next_prompt=next_prompt)
