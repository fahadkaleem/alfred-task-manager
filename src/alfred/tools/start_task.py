# src/alfred/tools/start_task.py
"""
The start_task tool, re-architected as a stateful workflow tool.
"""
from src.alfred.core.prompter import prompter
from src.alfred.core.workflow import StartTaskTool
from src.alfred.lib.logger import get_logger, setup_task_logging
from src.alfred.lib.task_utils import load_task
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.orchestration.persona_loader import load_persona
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery

logger = get_logger(__name__)


def start_task_impl(task_id: str) -> ToolResponse:
    """Implementation logic for the interactive start_task tool."""
    setup_task_logging(task_id)

    task = load_task(task_id)
    if not task:
        return ToolResponse(status="error", message=f"Task '{task_id}' not found.")

    if task_id in orchestrator.active_tools:
        tool_instance = orchestrator.active_tools[task_id]
        logger.info(f"Found active tool for task {task_id} in state {tool_instance.state}")
    else:
        tool_instance = ToolRecovery.recover_tool(task_id)
        if tool_instance:
            orchestrator.active_tools[task_id] = tool_instance
            logger.info(f"Recovered tool for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status not in [TaskStatus.NEW, TaskStatus.PLANNING]:
                return ToolResponse(
                    status="error",
                    message=f"Task '{task_id}' has status '{task.task_status.value}'. Setup can only start on a 'new' task.",
                )

            tool_instance = StartTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new start_task tool for task {task_id}")

    try:
        persona_config = load_persona(tool_instance.persona_name)
    except FileNotFoundError as e:
        return ToolResponse(status="error", message=str(e))

    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        persona_config=persona_config,
    )

    message = f"Starting setup for task '{task_id}'. Current step: {tool_instance.state}."

    return ToolResponse(status="success", message=message, next_prompt=prompt)