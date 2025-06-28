# src/alfred/tools/submit_work.py
import json

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

    # --- Artifact Persistence ---
    # Reuse the existing ArtifactManager to append to the human-readable scratchpad.
    # We create a simple, clean representation of the submitted artifact.
    rendered_artifact = f"### Submission for State: `{active_tool.state}`\n\n```json\n{json.dumps(artifact, indent=2)}\n```"
    artifact_manager.append_to_scratchpad(task_id, rendered_artifact)
    
    # --- State Transition ---
    current_state_val = active_tool.state.value if hasattr(active_tool.state, 'value') else active_tool.state
    trigger = f"submit_{current_state_val}"
    
    if not hasattr(active_tool, trigger):
        return ToolResponse(status="error", message=f"Invalid action: cannot submit from state '{current_state_val}'. No trigger '{trigger}' exists.")
    
    # Trigger the state transition (e.g., tool.submit_contextualize())
    getattr(active_tool, trigger)()
    logger.info(f"Task {task_id}: State transitioned via trigger '{trigger}' to '{active_tool.state}'.")
    
    # --- Generate Next Prompt for the new review state ---
    try:
        persona_config = load_persona(active_tool.persona_name)
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))
        
    next_prompt = prompter.generate_prompt(
        task=task,
        tool_name=active_tool.tool_name,
        state=active_tool.state,
        persona_config=persona_config,
        # Pass the submitted artifact into the context for the AI review prompt
        additional_context={"artifact_content": json.dumps(artifact, indent=2)}
    )

    return ToolResponse(status="success", message="Work submitted. Awaiting review.", next_prompt=next_prompt)
