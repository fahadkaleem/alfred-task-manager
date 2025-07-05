# src/alfred/tools/create_tasks_from_spec.py
from alfred.models.schemas import ToolResponse, TaskStatus, Task
from alfred.constants import ToolName
from alfred.models.engineering_spec import EngineeringSpec
from alfred.lib.structured_logger import get_logger
from alfred.state.manager import state_manager

logger = get_logger(__name__)


def create_tasks_logic(task_id: str, **kwargs) -> ToolResponse:
    """
    Pure context loader function for create_tasks_from_spec tool.
    
    This function provides the logic for creating tasks from a completed engineering spec
    using the stateless context loader pattern. It returns data for the workflow handler
    to process instead of manipulating context directly.
    
    Args:
        task_id: The unique identifier for the epic/feature with a completed engineering spec
        **kwargs: Additional parameters from the workflow handler
        
    Returns:
        ToolResponse containing the initialization data and next prompt
    """
    # Load the task state
    task_state = state_manager.load_or_create_task_state(task_id)

    # Check if we have a completed technical spec
    if task_state.task_status != TaskStatus.SPEC_COMPLETED:
        return ToolResponse(
            status="error", 
            message=f"Task {task_id} does not have a completed technical specification. Current status: {task_state.task_status.value}"
        )

    # Load the engineering spec from archive
    archive_path = state_manager.get_archive_path(task_id)
    spec_file = archive_path / "engineering_spec.json"

    if not spec_file.exists():
        return ToolResponse(
            status="error", 
            message=f"Technical specification not found for task {task_id}. Please complete create_spec first."
        )

    try:
        import json

        with open(spec_file, "r") as f:
            spec_data = json.load(f)
        tech_spec = EngineeringSpec(**spec_data)
    except Exception as e:
        logger.error(f"Failed to load technical spec for {task_id}: {e}")
        return ToolResponse(
            status="error", 
            message=f"Failed to load technical specification: {str(e)}"
        )

    # Update status to creating_tasks
    state_manager.update_task_status(task_id, TaskStatus.CREATING_TASKS)

    # Load or create task for prompt generation
    from alfred.lib.task_utils import load_task
    task = load_task(task_id)
    if not task:
        # Create a basic task object for the task creation phase
        task = Task(
            task_id=task_id,
            title=f"Create tasks for {task_id}",
            context="Breaking down engineering specification into tasks",
            implementation_details="Transform engineering spec into actionable tasks",
            task_status=TaskStatus.CREATING_TASKS,
        )

    # Generate the initial prompt
    from alfred.core.prompter import generate_prompt
    prompt = generate_prompt(
        task_id=task_id,
        tool_name=ToolName.CREATE_TASKS_FROM_SPEC,
        state="dispatching",  # Initial state for workflow tools
        task=task,
        additional_context={
            "task_id": task_id,
            "technical_spec": tech_spec.model_dump(),
        },
    )

    # Return response with context data for the workflow handler
    return ToolResponse(
        status="success",
        message=f"Starting task breakdown for '{task_id}'.",
        next_prompt=prompt,
        data={
            "technical_spec": tech_spec.model_dump(),
            "task_id": task_id,
        }
    )
