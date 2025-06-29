# src/alfred/tools/plan_task.py
from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.lib.task_utils import load_task, update_task_status
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.core.workflow import PlanTaskTool, PlanTaskState
from src.alfred.core.prompter import prompter
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import setup_task_logging


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool."""
    # --- ADD LOGGING INITIATION ---
    setup_task_logging(task_id)
    
    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    # Precondition Check
    if task.task_status != TaskStatus.NEW:
        return ToolResponse(
            status="error",
            message=f"Task '{task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' task."
        )

    tool_instance = PlanTaskTool(task_id=task_id)
    orchestrator.active_tools[task_id] = tool_instance
    
    try:
        # The persona for plan_task is 'planning'
        persona_config = load_persona("planning") 
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    initial_prompt = prompter.generate_prompt(
        task=task,
        tool_name="plan_task",
        state=PlanTaskState.CONTEXTUALIZE,
        persona_config=persona_config
    )

    update_task_status(task_id, TaskStatus.PLANNING)

    return ToolResponse(
        status="success",
        message=f"Planning initiated for task '{task_id}'.",
        next_prompt=initial_prompt
    )