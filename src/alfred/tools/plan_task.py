# src/alfred/tools/plan_task.py
import json
from typing import Optional
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.core.workflow import PlanTaskTool, PlanTaskState
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import setup_task_logging, get_logger
from src.alfred.state.recovery import ToolRecovery
from src.alfred.state.manager import state_manager

logger = get_logger(__name__)


def _get_previous_state(current_state: str) -> Optional[str]:
    """Helper to get the previous state for a review state"""
    state_map = {
        "review_context": "contextualize",
        "review_strategy": "strategize",
        "review_design": "design",
        "review_plan": "generate_slots"
    }
    return state_map.get(current_state)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """
    Implementation logic for the plan_task tool.
    
    This implementation includes recovery capability - if the tool
    crashes mid-workflow, it can be recovered from persisted state.
    """
    # Setup logging for this task
    setup_task_logging(task_id)
    
    # Check if tool already exists in memory
    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
    else:
        # Try to recover from disk
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            # No existing tool - create new one
            task = load_task(task_id)
            if not task:
                return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

            # Check preconditions for new planning
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' task or resume a 'planning' task."
                )

            # Create new tool instance
            tool_instance = PlanTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            
            # Update task status to planning
            if task.task_status == TaskStatus.NEW:
                update_task_status(task_id, TaskStatus.PLANNING)
            
            # Save initial state
            state_manager.save_tool_state(task_id, tool_instance)
            logger.info(f"Created new planning tool for task {task_id}")
    
    # Load persona config
    try:
        persona_config = load_persona(tool_instance.persona_name or "planning")
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))
    
    # Reload task to get latest state
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")
    
    # Generate appropriate prompt for current state
    logger.info(f"[PLAN_TASK] Generating prompt for state: {tool_instance.state}")
    logger.info(f"[PLAN_TASK] Context store keys: {list(tool_instance.context_store.keys())}")
    
    # Prepare context for prompt generation
    prompt_context = tool_instance.context_store.copy()
    
    # For review states, ensure artifact_content is available
    if "review" in tool_instance.state and "artifact_content" not in prompt_context:
        # Try to reconstruct artifact_content from the previous state's artifact
        prev_state = _get_previous_state(tool_instance.state)
        if prev_state:
            artifact_key = f"{prev_state}_artifact"
            if artifact_key in prompt_context:
                prompt_context["artifact_content"] = json.dumps(prompt_context[artifact_key], indent=2)
                logger.info(f"[PLAN_TASK] Reconstructed artifact_content from {artifact_key}")
    
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        persona_config=persona_config,
        additional_context=prompt_context
    )
    
    # Determine appropriate message based on whether we're resuming
    if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value:
        message = f"Planning initiated for task '{task_id}'."
    else:
        message = f"Resumed planning for task '{task_id}' from state '{tool_instance.state}'."

    return ToolResponse(
        status="success",
        message=message,
        next_prompt=prompt
    )