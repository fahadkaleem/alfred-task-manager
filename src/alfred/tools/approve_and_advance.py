from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.constants import ToolName
from src.alfred.lib.artifact_manager import artifact_manager
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)

STATUS_TRANSITION_MAP = {
    TaskStatus.CREATING_SPEC: TaskStatus.SPEC_COMPLETED,
    TaskStatus.CREATING_TASKS: TaskStatus.TASKS_CREATED,
    TaskStatus.PLANNING: TaskStatus.READY_FOR_DEVELOPMENT,
    TaskStatus.IN_DEVELOPMENT: TaskStatus.READY_FOR_REVIEW,
    TaskStatus.IN_REVIEW: TaskStatus.READY_FOR_TESTING,
    TaskStatus.IN_TESTING: TaskStatus.READY_FOR_FINALIZATION,
    TaskStatus.IN_FINALIZATION: TaskStatus.DONE,
}

ARTIFACT_PRODUCER_MAP = {
    TaskStatus.CREATING_SPEC: ToolName.CREATE_SPEC,
    TaskStatus.CREATING_TASKS: ToolName.CREATE_TASKS_FROM_SPEC,
    TaskStatus.PLANNING: ToolName.PLAN_TASK,
    TaskStatus.IN_DEVELOPMENT: ToolName.IMPLEMENT_TASK,
    TaskStatus.IN_REVIEW: ToolName.REVIEW_TASK,
    TaskStatus.IN_TESTING: ToolName.TEST_TASK,
    TaskStatus.IN_FINALIZATION: ToolName.FINALIZE_TASK,
}


def approve_and_advance_impl(task_id: str) -> ToolResponse:
    task_state = state_manager.load_or_create(task_id)
    current_status = task_state.task_status

    if current_status not in STATUS_TRANSITION_MAP:
        # Provide helpful guidance based on current status
        if current_status in [TaskStatus.NEW, TaskStatus.READY_FOR_DEVELOPMENT, TaskStatus.READY_FOR_REVIEW, TaskStatus.READY_FOR_TESTING, TaskStatus.READY_FOR_FINALIZATION]:
            suggestion = f"Call `alfred.work_on_task(task_id='{task_id}')` to start the next workflow phase."
        elif current_status == TaskStatus.DONE:
            suggestion = "Task is already complete. No further action needed."
        else:
            suggestion = f"Complete the current '{current_status.value}' phase first, then try again."
        
        return ToolResponse(
            status="error", 
            message=f"""Cannot advance task '{task_id}' - Current status is '{current_status.value}', which is not a completed phase.

**What this means:** 
- Task status: {current_status.value} (not a completing state)
- Only phases ending with 'in_*' can be advanced (e.g., in_development, in_review)

**Next Action:** {suggestion}

**Valid advance states:** {', '.join([s.value for s in STATUS_TRANSITION_MAP.keys()])}"""
        )

    producer_tool_name = ARTIFACT_PRODUCER_MAP.get(current_status)
    if producer_tool_name:
        # Determine workflow step number based on status
        workflow_step_map = {
            TaskStatus.CREATING_SPEC: 1,
            TaskStatus.CREATING_TASKS: 2,
            TaskStatus.PLANNING: 3,
            TaskStatus.IN_DEVELOPMENT: 4,
            TaskStatus.IN_REVIEW: 5,
            TaskStatus.IN_TESTING: 6,
            TaskStatus.IN_FINALIZATION: 7,
        }
        workflow_step = workflow_step_map.get(current_status, 0)

        # Archive the scratchpad BEFORE transitioning
        artifact_manager.archive_scratchpad(task_id, producer_tool_name, workflow_step)
        logger.info(f"Archived scratchpad for tool '{producer_tool_name}' at workflow step {workflow_step}")

        final_artifact = task_state.completed_tool_outputs.get(producer_tool_name)
        if final_artifact:
            artifact_manager.archive_final_artifact(task_id, producer_tool_name, final_artifact)
            logger.info(f"Archived final artifact for phase '{current_status.value}'.")
        else:
            logger.warning(f"No final artifact found for tool '{producer_tool_name}' to archive.")

    next_status = STATUS_TRANSITION_MAP[current_status]
    state_manager.update_task_status(task_id, next_status)

    message = f"Phase '{current_status.value}' approved. Task '{task_id}' is now in status '{next_status.value}'."
    logger.info(message)

    if next_status == TaskStatus.DONE:
        message += "\n\nThe task is fully complete."
        return ToolResponse(status="success", message=message)

    return ToolResponse(status="success", message=message, next_prompt=f"To proceed, call `alfred.work_on(task_id='{task_id}')` to get the next action.")
