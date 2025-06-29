# src/alfred/tools/plan_task.py
import json

from src.alfred.core.prompter import prompter
from src.alfred.core.workflow import PlanTaskState, PlanTaskTool
from src.alfred.lib.logger import get_logger, setup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery

logger = get_logger(__name__)


async def plan_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the plan_task tool with unified state."""
    setup_task_logging(task_id)

    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(
            f"Found active tool for task {task_id} in state {tool_instance.state}"
        )
    else:
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(
                f"Recovered tool from disk for task {task_id} in state {tool_instance.state}"
            )
        else:
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task_id}' has status '{task.task_status.value}'. Planning can only start on a 'new' task or resume a 'planning' task.",
                )

            tool_instance = PlanTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance

            if task.task_status == TaskStatus.NEW:
                state_manager.update_task_status(task_id, TaskStatus.PLANNING)

            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new planning tool for task {task_id}")

    try:
        persona_config = load_persona(tool_instance.persona_name or "planning")
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        persona_config=persona_config,
        additional_context=prompt_context,
    )

    message = (
        f"Planning initiated for task '{task_id}'."
        if tool_instance.state == PlanTaskState.CONTEXTUALIZE.value
        else f"Resumed planning for task '{task_id}' from state '{tool_instance.state}'."
    )

    return ToolResponse(status="success", message=message, next_prompt=prompt)