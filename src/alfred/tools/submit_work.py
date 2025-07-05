# src/alfred/tools/submit_work.py
from typing import Optional, Any
from pydantic import ValidationError

from alfred.core.prompter import generate_prompt
from alfred.core.workflow import BaseWorkflowTool
from alfred.lib.turn_manager import turn_manager
from alfred.lib.structured_logger import get_logger
from alfred.lib.task_utils import load_task
from alfred.models.schemas import Task, ToolResponse
from alfred.models.state import TaskState, WorkflowState
from alfred.state.manager import state_manager
from alfred.tools.base_tool_handler import BaseToolHandler
from alfred.constants import ArtifactKeys, Triggers, ResponseStatus, LogMessages, ErrorMessages

logger = get_logger(__name__)


class SubmitWorkHandler(BaseToolHandler):
    """Handler for the generic submit_work tool using stateless WorkflowEngine pattern."""

    def __init__(self):
        super().__init__(
            tool_name="submit_work",  # Not from constants, as it's a generic name
            tool_class=None,
            required_status=None,
        )

    def _create_new_tool(self, task_id: str, task: Task) -> BaseWorkflowTool:
        raise NotImplementedError("submit_work does not create new workflow tools.")

    async def execute(self, task_id: str = None, **kwargs: Any) -> ToolResponse:
        """Execute submit_work using stateless WorkflowEngine pattern."""
        task = load_task(task_id)
        if not task:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Task '{task_id}' not found.")

        # Load task state
        task_state = state_manager.load_or_create(task_id)
        
        # Check if we have an active workflow state
        if not task_state.active_tool_state:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"{LogMessages.NO_ACTIVE_TOOL.format(task_id=task_id)} Cannot submit work.")

        workflow_state = task_state.active_tool_state
        
        # Execute the submit work logic
        return await self._execute_submit_work(task, task_state, workflow_state, **kwargs)

    async def _execute_submit_work(self, task: Task, task_state: TaskState, workflow_state: WorkflowState, **kwargs: Any) -> ToolResponse:
        """The core logic for submitting an artifact and transitioning state using stateless pattern."""
        artifact = kwargs.get("artifact")
        if artifact is None:
            return ToolResponse(status=ResponseStatus.ERROR, message="`artifact` is a required argument for submit_work.")

        current_state_val = workflow_state.current_state

        # 1. Normalize artifact fields before validation
        normalized_artifact = self._normalize_artifact(artifact)

        # 2. Create stateless tool instance for artifact validation (local import to avoid circular dependency)
        from alfred.tools.tool_definitions import tool_definitions
        tool_definition = tool_definitions.get_tool_definition(workflow_state.tool_name)
        if not tool_definition:
            return ToolResponse(status=ResponseStatus.ERROR, message=f"No tool definition found for {workflow_state.tool_name}")
        
        # Create temporary tool instance for artifact_map access
        tool_class = tool_definition.tool_class
        temp_tool = tool_class(task_id=task.task_id)

        # 3. Validate the artifact against the model for the current state
        # Convert state string back to enum for artifact_map lookup
        current_state_enum = None
        for state_enum in temp_tool.artifact_map.keys():
            if (hasattr(state_enum, 'value') and state_enum.value == current_state_val) or str(state_enum) == current_state_val:
                current_state_enum = state_enum
                break

        artifact_model = temp_tool.artifact_map.get(current_state_enum) if current_state_enum else None
        if artifact_model:
            try:
                validated_artifact = artifact_model.model_validate(normalized_artifact)
                logger.info(LogMessages.ARTIFACT_VALIDATED.format(state=current_state_val, model=artifact_model.__name__))

                # Additional validation for ImplementationManifestArtifact
                from alfred.models.planning_artifacts import ImplementationManifestArtifact

                if isinstance(validated_artifact, ImplementationManifestArtifact):
                    # Get the planned subtasks from the execution plan in context_store
                    execution_plan = workflow_state.context_store.get("artifact_content", {})
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

        # 4. Store artifact and update context_store
        artifact_key = ArtifactKeys.get_artifact_key(current_state_val)
        workflow_state.context_store[artifact_key] = validated_artifact
        # For review states, we need the artifact as an object, not a string
        workflow_state.context_store[ArtifactKeys.ARTIFACT_CONTENT_KEY] = validated_artifact
        # Store the last state for generic templates
        workflow_state.context_store["last_state"] = current_state_val

        # Use the turn-based storage system
        tool_name = temp_tool.__class__.__name__

        # Check if this is a revision (has revision_turn_number in context)
        revision_of = workflow_state.context_store.get("revision_turn_number")
        revision_feedback = workflow_state.context_store.get("revision_feedback")
        if revision_of:
            # Clear revision context after use so it doesn't persist to next submissions
            del workflow_state.context_store["revision_turn_number"]
            if revision_feedback and "revision_feedback" in workflow_state.context_store:
                del workflow_state.context_store["revision_feedback"]

        # Convert Pydantic models to dict for storage
        if hasattr(validated_artifact, "model_dump"):
            artifact_dict = validated_artifact.model_dump()
        else:
            artifact_dict = validated_artifact if isinstance(validated_artifact, dict) else {"content": str(validated_artifact)}

        turn_manager.append_turn(task_id=task.task_id, state_name=current_state_val, tool_name=tool_name, artifact_data=artifact_dict, revision_of=revision_of, revision_feedback=revision_feedback)

        # Generate human-readable scratchpad from turns
        turn_manager.generate_scratchpad(task.task_id)

        # 5. Use WorkflowEngine for state transition
        trigger_name = Triggers.submit_trigger(current_state_val)
        
        try:
            # Local import to avoid circular dependency
            from alfred.core.workflow_engine import WorkflowEngine
            
            # Create WorkflowEngine and execute transition
            engine = WorkflowEngine(tool_definition)
            
            # Check if transition is valid
            valid_triggers = engine.get_valid_triggers(current_state_val)
            if trigger_name not in valid_triggers:
                return ToolResponse(status=ResponseStatus.ERROR, message=f"No valid transition for trigger '{trigger_name}' from state '{current_state_val}'.")
            
            # Execute the transition
            new_state = engine.execute_trigger(current_state_val, trigger_name)
            workflow_state.current_state = new_state
            
            logger.info(LogMessages.STATE_TRANSITION.format(task_id=task.task_id, trigger=trigger_name, state=new_state))

        except Exception as e:
            logger.error("State transition failed", task_id=task.task_id, trigger=trigger_name, error=str(e))
            return ToolResponse(status=ResponseStatus.ERROR, message=f"State transition failed: {str(e)}")

        # 6. Persist the new state
        task_state.active_tool_state = workflow_state
        state_manager.save_task_state(task_state)

        # 7. Generate response
        try:
            prompt = generate_prompt(
                task_id=task.task_id,
                tool_name=workflow_state.tool_name,
                state=workflow_state.current_state,
                task=task,
                additional_context=workflow_state.context_store.copy(),
            )
            message = f"Work submitted successfully for task '{task.task_id}'. Transitioned to state: {workflow_state.current_state}."
            return ToolResponse(status=ResponseStatus.SUCCESS, message=message, next_prompt=prompt)
        except Exception as e:
            logger.error("Prompt generation failed", task_id=task.task_id, error=str(e))
            return ToolResponse(status=ResponseStatus.ERROR, message=f"Work submitted but failed to generate next prompt: {str(e)}")

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

    # Legacy methods for BaseToolHandler compatibility - not used in stateless path
    async def _setup_tool(self, tool_instance: BaseWorkflowTool, task: Task, **kwargs: Any) -> Optional[ToolResponse]:
        """Legacy setup method - not used in stateless path."""
        return None


submit_work_handler = SubmitWorkHandler()


# Keep the legacy function for backwards compatibility if needed
def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """Legacy implementation - redirects to the handler."""
    import asyncio

    return asyncio.run(submit_work_handler.execute(task_id, artifact=artifact))
