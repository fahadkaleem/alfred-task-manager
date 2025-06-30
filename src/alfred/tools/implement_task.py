from src.alfred.models.schemas import ToolResponse, TaskStatus
from src.alfred.orchestration.orchestrator import orchestrator
from src.alfred.lib.logger import get_logger
from src.alfred.lib.task_utils import load_task
from src.alfred.state.manager import state_manager
from src.alfred.state.recovery import ToolRecovery
from src.alfred.core.workflow import ImplementTaskTool
from src.alfred.core.prompter import prompter
from src.alfred.constants import ToolName

logger = get_logger(__name__)


async def implement_task_impl(task_id: str) -> ToolResponse:
    """
    Implementation task entry point - handles the development phase
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
            if task.task_status != TaskStatus.READY_FOR_DEVELOPMENT:
                return ToolResponse(status="error", message=f"Task '{task_id}' has status '{task.task_status.value}'. Implementation can only start on a 'ready_for_development' task.")

            tool_instance = ImplementTaskTool(task_id=task_id)
            orchestrator.active_tools[task_id] = tool_instance
            state_manager.update_task_status(task_id, TaskStatus.IN_DEVELOPMENT)

            # Dispatch immediately to implementing state
            tool_instance.dispatch()
            state_manager.update_tool_state(task_id, tool_instance)
            logger.info(f"Created new implementation tool for task {task_id}")

    # Load execution plan from previous phase
    task_state = state_manager.load_or_create(task_id)
    logger.info(f"Completed tool outputs: {list(task_state.completed_tool_outputs.keys())}")
    plan_task_outputs = task_state.completed_tool_outputs.get(ToolName.PLAN_TASK, {})
    logger.info(f"Plan task outputs type: {type(plan_task_outputs)}")

    # The execution plan IS the plan_task output (it's the ExecutionPlanArtifact)
    if plan_task_outputs and isinstance(plan_task_outputs, dict) and "subtasks" in plan_task_outputs:
        # Store with the key that mark_subtask_complete expects
        tool_instance.context_store["execution_plan_artifact"] = plan_task_outputs
        logger.info(f"Loaded execution plan with {len(plan_task_outputs.get('subtasks', []))} subtasks")
    else:
        logger.warning("No execution plan found from plan_task phase")

    prompt_context = tool_instance.context_store.copy()
    prompt = prompter.generate_prompt(
        task=task,
        tool_name=tool_instance.tool_name,
        state=tool_instance.state,
        additional_context=prompt_context,
    )

    message = f"Implementation initiated for task '{task_id}'."
    return ToolResponse(status="success", message=message, next_prompt=prompt)
