from src.alfred.state.manager import state_manager
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.constants import ToolName
from src.alfred.lib.task_utils import does_task_exist_locally, write_task_to_markdown
from src.alfred.task_providers.factory import get_provider
from src.alfred.lib.logger import get_logger

logger = get_logger(__name__)


def work_on_impl(task_id: str) -> ToolResponse:
    # Step 1: Check if the task exists locally first (cache-first architecture)
    if not does_task_exist_locally(task_id):
        logger.info(f"Task '{task_id}' not found in local cache. Fetching from provider...")

        # Task is not in our local cache, fetch from provider
        provider = get_provider()

        try:
            # Delegate to the provider to fetch the task
            task = provider.get_task(task_id)

            if not task:
                return ToolResponse(
                    status="error", 
                    message=f"Task '{task_id}' could not be found. Please check:\n"
                            f"1. Task ID is correct (case-sensitive)\n"
                            f"2. For local tasks: File exists at .alfred/tasks/{task_id}.md\n"
                            f"3. For remote tasks: Task exists in your configured provider (Jira/Linear)\n"
                            f"4. Task file format is valid (see .alfred/tasks/README.md)\n"
                            f"5. Run 'alfred.get_next_task()' to see available tasks"
                )

            # Step 2: Cache the fetched task locally
            write_task_to_markdown(task)
            logger.info(f"Successfully cached task '{task_id}' from provider")

        except Exception as e:
            logger.error(f"Failed to fetch task from provider: {e}")
            return ToolResponse(status="error", message=f"Failed to fetch task '{task_id}' from provider: {str(e)}")

    # Step 3: Now that the task is guaranteed to be local, proceed with the
    # original "Smart Dispatch" logic
    task_state = state_manager.load_or_create_task_state(task_id)
    task_status = task_state.task_status

    handoff_tool_map = {
        TaskStatus.NEW: ToolName.PLAN_TASK,  # Start with creating spec for new epics
        TaskStatus.CREATING_SPEC: ToolName.CREATE_SPEC,
        TaskStatus.SPEC_COMPLETED: ToolName.CREATE_TASKS,
        TaskStatus.CREATING_TASKS: ToolName.CREATE_TASKS,
        TaskStatus.TASKS_CREATED: ToolName.PLAN_TASK,  # After tasks are created, plan the first one
        TaskStatus.PLANNING: ToolName.PLAN_TASK,
        TaskStatus.READY_FOR_DEVELOPMENT: ToolName.IMPLEMENT_TASK,
        TaskStatus.IN_DEVELOPMENT: ToolName.IMPLEMENT_TASK,
        TaskStatus.READY_FOR_REVIEW: ToolName.REVIEW_TASK,
        TaskStatus.IN_REVIEW: ToolName.REVIEW_TASK,
        TaskStatus.READY_FOR_TESTING: ToolName.TEST_TASK,
        TaskStatus.IN_TESTING: ToolName.TEST_TASK,
        TaskStatus.READY_FOR_FINALIZATION: ToolName.FINALIZE_TASK,
    }

    if task_status in handoff_tool_map:
        handoff_tool = handoff_tool_map[task_status]
        message = f"Task '{task_id}' is in status '{task_status.value}'. The next action is to use the '{handoff_tool}' tool."
        next_prompt = f"To proceed with task '{task_id}', call `alfred.{handoff_tool}(task_id='{task_id}')`."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)

    if task_status == TaskStatus.DONE:
        return ToolResponse(status="success", message=f"Task '{task_id}' is already done. No further action is required.")

    return ToolResponse(status="error", message=f"Unhandled status '{task_status.value}' for task '{task_id}'.")
