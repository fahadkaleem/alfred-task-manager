# src/alfred/tools/submit_work.py
from typing import Optional, Any
from pydantic import ValidationError

from alfred.core.prompter import generate_prompt
from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.turn_manager import turn_manager
from alfred.lib.structured_logger import get_logger
from alfred.lib.task_utils import load_task
from alfred.models.schemas import Task, ToolResponse
from alfred.orchestration.orchestrator import orchestrator
from alfred.state.manager import state_manager
from alfred.state.recovery import ToolRecovery
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


class SubmitWorkHandler(BaseToolHandler):
    """Handler for the generic submit_work tool."""

    def __init__(self):
        super().__init__(
            tool_name="submit_work",  # Not from constants, as it's a generic name
            tool_class=None,
            required_status=None,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        raise NotImplementedError("submit_work does not create new workflow tools.")

    def _get_or_create_tool(self, task_id: str, task: Task) -> BaseWorkflowTool | ToolResponse:
        """For submit_work, we only get an existing tool."""
        if task_id in orchestrator.active_tools:
            return orchestrator.active_tools[task_id]
        recovered_tool = ToolRecovery.recover_tool(task_id)
        if recovered_tool:
            orchestrator.active_tools[task_id] = recovered_tool
            return recovered_tool
        return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """The core logic for submitting an artifact and transitioning state."""
        artifact = kwargs.get("artifact")
        if artifact is None:
            return ToolResponse(status=ResponseStatus.ERROR, message="`artifact` is a required argument for submit_work.")

        current_state_enum = tool_instance.state
        current_state_val = tool_instance.state.value if hasattr(tool_instance.state, "value") else tool_instance.state

        # 1. Normalize artifact fields before validation
        normalized_artifact = self._normalize_artifact(artifact)

        # 2. Validate the artifact against the model for the current state
        artifact_model = tool_instance.artifact_map.get(current_state_enum)
        if artifact_model:
            try:
                validated_artifact = artifact_model.model_validate(normalized_artifact)
                logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state_val, model=artifact_model.__name__))
                
                # Additional validation for ImplementationManifestArtifact
                from alfred.models.planning_artifacts import ImplementationManifestArtifact
                if isinstance(validated_artifact, ImplementationManifestArtifact):
                    # Get the planned subtasks from the execution plan
                    execution_plan = tool_instance.context_store.get("artifact_content", {})
                    planned_subtasks = [st["subtask_id"] for st in execution_plan.get("subtasks", [])]
                    
                    if planned_subtasks:
                        validation_error = validated_artifact.validate_against_plan(planned_subtasks)
                        if validation_error:
                            return ToolResponse(status=ResponseStatus.ERROR, message=f"Implementation validation failed: {validation_error}")
                        
                        # Log successful validation
                        completed_count = len(validated_artifact.completed_subtasks)
                        total_count = len(planned_subtasks)
                        logger.info(f"Implementation validation passed: {completed_count}/{total_count} subtasks completed")
                        
            except ValidationError as e:
                error_msg = f"{ErrorMessages.VALIDATION_FAILED.format(state=current_state_val)}. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
                return ToolResponse(status=ResponseStatus.ERROR, message=error_msg)
        else:
            validated_artifact = normalized_artifact  # No model to validate against

        # 2. Store artifact and update turn-based storage
        artifact_key = ArtifactKeys.get_artifact_key(current_state_val)
        tool_instance.context_store[artifact_key] = validated_artifact
        # For review states, we need the artifact as an object, not a string
        tool_instance.context_store[ArtifactKeys.ARTIFACT_CONTENT_KEY] = validated_artifact
        # Store the last state for generic templates
        tool_instance.context_store["last_state"] = current_state_val

        # Use the turn-based storage system
        tool_name = tool_instance.__class__.__name__

        # Check if this is a revision (has revision_turn_number in context)
        revision_of = tool_instance.context_store.get("revision_turn_number")
        revision_feedback = tool_instance.context_store.get("revision_feedback")
        if revision_of:
            # Clear revision context after use so it doesn't persist to next submissions
            del tool_instance.context_store["revision_turn_number"]
            if revision_feedback and "revision_feedback" in tool_instance.context_store:
                del tool_instance.context_store["revision_feedback"]

        # Convert Pydantic models to dict for storage
        if hasattr(validated_artifact, "model_dump"):
            artifact_dict = validated_artifact.model_dump()
        else:
            artifact_dict = validated_artifact if isinstance(validated_artifact, dict) else {"content": str(validated_artifact)}

        turn_manager.append_turn(task_id=task.task_id, state_name=current_state_val, tool_name=tool_name, artifact_data=artifact_dict, revision_of=revision_of, revision_feedback=revision_feedback)

        # Generate human-readable scratchpad from turns
        turn_manager.generate_scratchpad(task.task_id)

        # 3. Determine the correct trigger and fire it
        trigger_name = Triggers.submit_trigger(current_state_val)
        if not hasattr(tool_instance, trigger_name):
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger_name}' exists.")

        # Check if transition is valid
        next_transitions = tool_instance.machine.get_transitions(source=tool_instance.state, trigger=trigger_name)
        if not next_transitions:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger_name}' from state '{tool_instance.state}'.")

        getattr(tool_instance, trigger_name)()
        logger.info(LogMessages.STATE_TRANSITION.format(task_id=task.task_id, trigger=trigger_name, state=tool_instance.state))

        # 4. Persist the new state
        state_manager.update_tool_state(task.task_id, tool_instance)

        # This handler's job is done; we return None to let the main execute method generate the response
        return None

    def _normalize_artifact(self, artifact: dict) -> dict:
        """Normalize artifact fields to handle case-insensitive inputs."""
        if not isinstance(artifact, dict):
            return artifact

        normalized = artifact.copy()

        # Normalize file_breakdown operations (for ContractDesignArtifact and ImplementationPlanArtifact from discovery planning)
        if "file_breakdown" in normalized and isinstance(normalized["file_breakdown"], list):
            for file_change in normalized["file_breakdown"]:
                if isinstance(file_change, dict) and "operation" in file_change:
                    # Normalize operation to uppercase
                    file_change["operation"] = file_change["operation"].upper()

        # Normalize subtasks operations (for ImplementationPlanArtifact)
        if "subtasks" in normalized and isinstance(normalized["subtasks"], list):
            for subtask in normalized["subtasks"]:
                if isinstance(subtask, dict) and "operation" in subtask:
                    # Normalize operation to uppercase
                    subtask["operation"] = subtask["operation"].upper()

        return normalized


submit_work_handler = SubmitWorkHandler()


# Keep the legacy function for backwards compatibility if needed
def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """Legacy implementation - redirects to the handler."""
    import asyncio

    return asyncio.run(submit_work_handler.execute(task_id, artifact=artifact))
