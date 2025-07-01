# src/alfred/tools/create_spec.py
from src.alfred.models.schemas import ToolResponse
from src.alfred.constants import ToolName
from src.alfred.core.workflow import CreateSpecTool
from src.alfred.models.planning_artifacts import PRDInputArtifact
from src.alfred.models.engineering_spec import EngineeringSpec
from src.alfred.state.manager import state_manager


async def create_spec_impl(task_id: str, prd_content: str) -> ToolResponse:
    """
    Initializes the workflow for creating a technical specification from a PRD.

    This is the first tool in the "idea-to-code" pipeline. It takes a Product
    Requirements Document (PRD) and guides the transformation into a structured
    Technical Specification that can be used for engineering planning.

    Args:
        task_id: The unique identifier for the epic/feature (e.g., "EPIC-01")
        prd_content: The raw PRD content to analyze

    Returns:
        ToolResponse containing the first prompt to guide spec creation
    """
    # Load or create task state
    task_state = state_manager.load_or_create_task_state(task_id)

    # Update status to creating_spec
    from src.alfred.models.schemas import TaskStatus

    state_manager.update_task_status(task_id, TaskStatus.CREATING_SPEC)

    # Initialize the create_spec tool
    tool = CreateSpecTool(task_id)

    # Store the PRD content in context
    prd_artifact = PRDInputArtifact(prd_content=prd_content)
    tool.context_store["prd_input"] = prd_artifact

    # Register the tool
    state_manager.register_tool(task_id, tool)

    # Dispatch immediately to drafting state
    tool.dispatch()
    state_manager.update_tool_state(task_id, tool)

    # Load the drafting prompt
    from src.alfred.core.prompter import generate_prompt
    from src.alfred.lib.task_utils import load_task

    task = load_task(task_id)
    if not task:
        # Create a basic task object for the spec creation phase
        from src.alfred.models.schemas import Task

        task = Task(
            task_id=task_id,
            title=f"Create specification for {task_id}",
            context="Creating engineering specification from PRD",
            implementation_details="Transform PRD into engineering specification",
            task_status=TaskStatus.CREATING_SPEC,
        )

    prompt = generate_prompt(
        task=task,
        tool_name=tool.tool_name,
        state=tool.state,
        additional_context={
            "task_id": task_id,
            "prd_content": prd_content,
        },
    )

    return ToolResponse(status="success", message=f"Starting specification creation for task '{task_id}'.", next_prompt=prompt)
