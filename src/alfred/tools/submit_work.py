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

logger = get_logger(__name__)

def submit_work_impl(task_id: str, artifact: dict) -> ToolResponse:
    """
    Implements the logic for submitting a work artifact to the active tool.
    """
    if task_id not in orchestrator.active_tools:
        return ToolResponse(status="error", message=f"No active tool found for task '{task_id}'. Cannot submit work.")
    
    active_tool = orchestrator.active_tools[task_id]
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # --- NEW: Artifact Validation ---
    current_state = active_tool.state
    artifact_model = active_tool.artifact_map.get(current_state)

    if artifact_model:
        try:
            # Validate the submitted dictionary against the Pydantic model
            validated_artifact = artifact_model.model_validate(artifact)
            logger.info(f"Artifact for state '{current_state.value if hasattr(current_state, 'value') else current_state}' validated successfully against {artifact_model.__name__}.")
        except ValidationError as e:
            error_msg = f"Artifact validation failed for state '{current_state.value if hasattr(current_state, 'value') else current_state}'. The submitted artifact does not match the required structure.\n\nValidation Errors:\n{e}"
            return ToolResponse(status="error", message=error_msg)
    else:
        validated_artifact = artifact  # No validator for this state, proceed

    # --- NEW: Store validated artifact in the tool's context ---
    state_key = f"{current_state.value if hasattr(current_state, 'value') else current_state}_artifact"
    active_tool.context_store[state_key] = validated_artifact
    logger.info(f"Stored artifact in context_store with key '{state_key}'.")

    # --- Load persona config (used for both persistence and prompt generation) ---
    try:
        persona_config = load_persona(active_tool.persona_name)
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))
        
    # --- Artifact Persistence ---
    # The tool no longer renders anything. It just passes the validated
    # artifact model to the manager.
    current_state_val = active_tool.state.value if hasattr(active_tool.state, 'value') else active_tool.state
    artifact_manager.append_to_scratchpad(
        task_id=task_id,
        state_name=current_state_val,
        artifact=validated_artifact,
        persona_config=persona_config
    )
    
    # --- State Transition ---
    trigger = f"submit_{current_state_val}"
    
    if not hasattr(active_tool, trigger):
        return ToolResponse(status="error", message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")
    
    # Trigger the state transition (e.g., tool.submit_contextualize())
    getattr(active_tool, trigger)()
    logger.info(f"Task {task_id}: State transitioned via trigger '{trigger}' to '{active_tool.state}'.")
    
    # --- Generate Next Prompt for the new review state ---
        
    # For review states, we need to provide the artifact_content and context_store
    additional_context = active_tool.context_store.copy()
    additional_context["artifact_content"] = json.dumps(artifact, indent=2)
    
    next_prompt = prompter.generate_prompt(
        task=task,
        tool_name=active_tool.tool_name,
        state=active_tool.state,
        persona_config=persona_config,
        additional_context=additional_context
    )

    return ToolResponse(status="success", message="Work submitted. Awaiting review.", next_prompt=next_prompt)
