from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import ReviewTaskTool
from src.alfred.core.prompter import prompter
from src.alfred.constants import ToolName

logger = get_logger(__name__)


async def review_task_impl(task_id: str) -> ToolResponse:
    """
    Review task entry point - handles the code review phase
    """
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
            logger.info(f"Recovered tool from disk for task {task_id} in state {tool_instance.state}")
        else:
            if task.task_status != TaskStatus.READY_FOR_REVIEW:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Review can only start on a 'ready_for_review' task.")

            tool_instance = ReviewTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_task_status(task_id, TaskStatus.IN_REVIEW)

            # Dispatch immediately to reviewing state
            tool_instance.dispatch()
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new review tool for task {task_id}")

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Code review initiated for task '{task_id}'."
    return ToolResponse(status="success", message=message, next_prompt=prompt)
