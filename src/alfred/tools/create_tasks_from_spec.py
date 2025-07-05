# src/alfred/tools/create_tasks_from_spec.py
from alfred.models.schemas import ToolResponse
from alfred.constants import ToolName
from alfred.core.workflow import CreateTasksTool
from alfred.models.engineering_spec import EngineeringSpec
from alfred.lib.structured_logger import get_logger
from alfred.state.manager import state_manager

logger = get_logger(__name__)


# New logic function for GenericWorkflowHandler
async def create_tasks_logic(task_id: str, **kwargs) -> ToolResponse:
    """Logic function for create_tasks_from_spec compatible with GenericWorkflowHandler."""
    return await create_tasks_from_spec_impl(task_id)


# Note: create_tasks_from_spec_impl is still used as it contains workflow-specific logic


async def create_tasks_from_spec_impl(task_id: str) -> ToolResponse:
    """
    Creates a list of actionable tasks from a completed engineering specification.

    This is the second tool in the "idea-to-code" pipeline. It takes a completed
    engineering specification and breaks it down into individual Task objects that
    can be tracked, assigned, and implemented independently.

    The tool guides through creating tasks that are:
    - Atomic and focused
    - Properly ordered with dependencies
    - Sized appropriately (1-3 days of work)
    - Complete with acceptance criteria

    Args:
        task_id: The unique identifier for the epic/feature with a completed engineering spec

    Returns:
        ToolResponse containing the first prompt to guide task breakdown

    Preconditions:
        - Engineering specification must be completed (via create_spec)
        - Task status must be "spec_completed"
    """
    # Load the task state
    task_state = state_manager.load_or_create_task_state(task_id)

    from alfred.models.schemas import TaskStatus

    # Check if we have a completed technical spec
    if task_state.task_status != TaskStatus.SPEC_COMPLETED:
        return ToolResponse(status="error", message=f"Task {task_id} does not have a completed technical specification. Current status: {task_state.task_status.value}")

    # Load the engineering spec from archive
    archive_path = state_manager.get_archive_path(task_id)
    spec_file = archive_path / "engineering_spec.json"

    if not spec_file.exists():
        return ToolResponse(status="error", message=f"Technical specification not found for task {task_id}. Please complete create_spec first.")

    try:
        import json

        with open(spec_file, "r") as f:
            spec_data = json.load(f)
        tech_spec = EngineeringSpec(**spec_data)
    except Exception as e:
        logger.error(f"Failed to load technical spec for {task_id}: {e}")
        return ToolResponse(status="error", message=f"Failed to load technical specification: {str(e)}")

    # Update status
    state_manager.update_task_status(task_id, TaskStatus.CREATING_TASKS)

    # Initialize the create_tasks_from_spec tool
    tool = CreateTasksTool(task_id)

    # Store the technical spec in context
    tool.context_store["technical_spec"] = tech_spec

    # Register the tool
    state_manager.register_tool(task_id, tool)

    # Dispatch immediately to drafting state
    tool.dispatch()
    state_manager.update_tool_state(task_id, tool)

    # Load the drafting prompt with the technical spec
    from alfred.core.prompter import generate_prompt
    from alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the task creation phase
        from alfred.models.schemas import Task

        task = Task(
            task_id=task_id,
            title=f"Create tasks for {task_id}",
            context="Breaking down engineering specification into tasks",
            implementation_details="Transform engineering spec into actionable tasks",
            task_status=TaskStatus.CREATING_TASKS,
        )

    prompt = generate_prompt(
        task=task,
        tool_name=tool.tool_name,
        state=tool.state,
        additional_context={
            "task_id": task_id,
            "technical_spec": tech_spec.model_dump(),
        },
    )

    return ToolResponse(status="success", message=f"Starting task breakdown for '{task_id}'.", next_prompt=prompt)
