# src/alfred/tools/create_spec.py
from alfred.models.schemas import ToolResponse, TaskStatus, Task
from alfred.constants import ToolName
from alfred.models.planning_artifacts import PRDInputArtifact
from alfred.state.manager import state_manager


def create_spec_logic(task_id: str, prd_content: str, **kwargs) -> ToolResponse:
    """
    Pure context loader function for create_spec tool.

    This function provides the logic for creating a technical specification from a PRD
    using the stateless context loader pattern. It returns data for the workflow handler
    to process instead of manipulating context directly.

    Args:
        task_id: The unique identifier for the epic/feature (e.g., "EPIC-01")
        prd_content: The raw PRD content to analyze
        **kwargs: Additional parameters from the workflow handler

    Returns:
        ToolResponse containing the initialization data and next prompt
    """
    # Update status to creating_spec
    state_manager.update_task_status(task_id, TaskStatus.CREATING_SPEC)

    # Create PRD artifact for context
    prd_artifact = PRDInputArtifact(prd_content=prd_content)

    # Load or create task for prompt generation
    from alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the spec creation phase
        task = Task(
            task_id=task_id,
            title=f"Create specification for {task_id}",
            context="Creating engineering specification from PRD",
            implementation_details="Transform PRD into engineering specification",
            task_status=TaskStatus.CREATING_SPEC,
        )

    # Generate the initial prompt
    from alfred.core.prompter import generate_prompt

    prompt = generate_prompt(
        task_id=task_id,
        tool_name=ToolName.CREATE_SPEC,
        state="dispatching",
        task=task,
        additional_context={
            "task_id": task_id,
            "prd_content": prd_content,
        },
    )

    # Return response with context data for the workflow handler
    return ToolResponse(
        status="success",
        message=f"Starting specification creation for task '{task_id}'.",
        next_prompt=prompt,
        data={
            "prd_input": prd_artifact.model_dump(),
            "task_id": task_id,
        },
    )
