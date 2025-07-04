from alfred.state.manager import state_manager
from alfred.models.schemas import TaskStatus, ToolResponse
from alfred.core.workflow_config import WorkflowConfiguration
from alfred.lib.task_utils import does_task_exist_locally, write_task_to_markdown
from alfred.task_providers.factory import get_provider
from alfred.lib.structured_logger import get_logger

logger = get_logger(__name__)


def work_on_impl(task_id: str) -> ToolResponse:
    """Smart dispatch using centralized workflow configuration."""

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
                    f"5. Run 'alfred.get_next_task()' to see available tasks",
                )

            # Step 2: Cache the fetched task locally
            write_task_to_markdown(task)
            logger.info(f"Successfully cached task '{task_id}' from provider")

        except Exception as e:
            logger.error(f"Failed to fetch task from provider: {e}")
            return ToolResponse(status="error", message=f"Failed to fetch task '{task_id}' from provider: {str(e)}")

    # Step 3: Use centralized workflow config for smart dispatch
    task_state = state_manager.load_or_create_task_state(task_id)
    task_status = task_state.task_status

    # Get the appropriate tool from workflow configuration
    next_tool = WorkflowConfiguration.get_tool_for_status(task_status)

    if next_tool:
        phase = WorkflowConfiguration.get_phase(task_status)
        message = f"Task '{task_id}' is in status '{task_status.value}'. The next action is to use the '{next_tool}' tool."

        if phase and phase.description:
            message += f"\nPhase: {phase.description}"

        next_prompt = f"To proceed with task '{task_id}', call `alfred.{next_tool}(task_id='{task_id}')`."
        return ToolResponse(status="success", message=message, next_prompt=next_prompt)

    # Check if task is done
    if WorkflowConfiguration.is_terminal_status(task_status):
        return ToolResponse(status="success", message=f"Task '{task_id}' is already done. No further action is required.")

    # Unknown status
    return ToolResponse(status="error", message=f"Unhandled status '{task_status.value}' for task '{task_id}'. This may be a configuration error.")
