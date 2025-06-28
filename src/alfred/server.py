"""
MCP Server for Alfred
"""

import inspect

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl
# --- COMMENTED OUT LEGACY TOOL IMPORTS ---
# from src.alfred.tools.progress_tools import mark_step_complete as mark_step_complete_impl
# from src.alfred.tools.review_tools import approve_and_advance_stage as approve_and_advance_stage_impl
# from src.alfred.tools.review_tools import approve_and_handoff as approve_and_handoff_impl
# from src.alfred.tools.task_tools import begin_task as begin_task_impl

# New generic state-advancing tool implementations
from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.tools.provide_review import provide_review_impl

app = FastMCP(settings.server_name)


@app.tool()
async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initializes the project workspace for Alfred by creating the .alfred directory with default configurations for personas and workflows.

    - **Primary Function**: Sets up a new project for use with the Alfred workflow system.
    - **Key Features**:
      - Interactive provider selection when no provider is specified.
      - Creates the necessary `.alfred` directory structure.
      - Deploys default `workflow.yml` and persona configuration files.
      - Copies default prompt templates for user customization.
      - Configures the selected task provider (Jira, Linear, or Local).
    - **Use this tool when**: You are starting a brand new project and need to set up the Alfred environment.
    - **Crucial Guardrails**:
      - This tool MUST be the very first tool called in a new project. Other tools will fail until initialization is complete.
      - Do NOT use this tool if the project is already initialized (it will return success but make no changes).

    ## Parameters
    - **provider** `[string]` (optional): The task source provider to configure. Valid values: "jira", "linear", or "local". 
      If not provided, the tool will return available choices for interactive selection.
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"provider": provider} if provider else {}
    response = initialize_project_impl(provider)
    transaction_logger.log(task_id=None, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def plan_task(task_id: str) -> ToolResponse:
    """
    Initiates the detailed technical planning for a specific task.

    This is the primary tool for transforming a high-level task or user story
    into a concrete, machine-executable 'Execution Plan' composed of SLOTs.
    A SLOT (Spec, Location, Operation, Taskflow) is an atomic unit of work.

    This tool manages a multi-step, interactive planning process:
    1. **Contextualize**: Deep analysis of the task requirements and codebase context
    2. **Strategize**: High-level technical approach and architecture decisions  
    3. **Design**: Detailed technical design and component specifications
    4. **Generate SLOTs**: Break down into atomic, executable work units

    Each step includes AI self-review followed by human approval gates to ensure quality.
    The final output is a validated execution plan ready for implementation.

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")

    Returns:
        ToolResponse: Contains success/error status and the next prompt to guide planning

    Preconditions:
        - Task must exist and be in 'new' or 'planning' status
        - Project must be initialized with Alfred

    Postconditions:
        - Task status updated to 'planning'
        - Planning tool instance registered and active
        - First planning prompt returned for contextualization phase
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    
    response = await plan_task_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step of a workflow tool.

    This is the generic state-advancing tool that handles work submission for any active workflow tool.
    It automatically determines the correct state transition based on the current state and advances 
    the tool's state machine accordingly.

    Args:
        task_id (str): The unique identifier for the task
        artifact (dict): A dictionary containing the structured work data

    Returns:
        ToolResponse: Contains success/error status and the next prompt
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "artifact": artifact}
    response = submit_work_impl(task_id, artifact)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def provide_review(task_id: str, is_approved: bool, feedback_notes: str = "") -> ToolResponse:
    """
    Provides feedback on a work artifact during a review step.

    This is the generic state-advancing tool that handles review feedback for any active workflow tool.
    It automatically determines the correct state transition based on the approval status and advances
    the tool's state machine accordingly.

    Args:
        task_id (str): The unique identifier for the task
        is_approved (bool): True to approve, False to request revisions
        feedback_notes (str): Specific feedback for revision (required if is_approved=False)

    Returns:
        ToolResponse: Contains success/error status and the next prompt
    """
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "is_approved": is_approved, "feedback_notes": feedback_notes}
    response = provide_review_impl(task_id, is_approved, feedback_notes)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


# --- LEGACY TOOLS COMMENTED OUT ---

"""
@app.tool()
async def begin_task(task_id: str) -> ToolResponse:
    '''
    Begins or resumes a task in the Alfred workflow, activating the correct persona based on the task's current state.

    - **Primary Function**: This is the main entry point for starting or continuing work on a specific task.
    - **Key Features**:
      - Creates a new task record and workspace if the task is new.
      - Resumes an existing task from its last saved state, loading the correct persona and phase.
      - Returns a `ToolResponse` containing the `next_prompt` to guide the AI's first action on the task.
    - **Use this tool EXCLUSIVELY when**:
      - You are beginning work on a task for the very first time.
      - You are returning to a task after a break and need to re-establish your context.
    - **CRITICAL GUARDRAILS**:
      - **This is your ENTRY POINT:** Call this tool first when interacting with a `task_id`.
      - **Do NOT call this repeatedly:** Once a task is started, follow the instructions from the server's `next_prompt`. Do not call `begin_task` again for the same task unless you are intentionally resuming a session.

    ## Parameters
    - **task_id** `[string]` (required): The unique identifier for the task (e.g., "PROJ-123").
    '''
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = begin_task_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response




@app.tool()
async def approve_and_handoff(task_id: str) -> ToolResponse:
    '''
    Gives final approval for a persona's entire workflow and hands the task off to the next persona in the sequence.

    - **Primary Function**: This is the "human approval" gate for an entire persona's completed work. It archives the current persona's work and activates the next persona.
    - **Use this tool when**: A persona has reached its final `_devreview` or `_verified` state, and the user has approved all work done by that persona.
    - **Distinction**: This tool moves *between personas*. Use `approve_and_advance_stage` for internal stage progression.

    ## Example
    - The Developer persona is in the `coding_devreview` state. User says "The code is perfect, hand it off to QA."
    - You call `approve_and_handoff(task_id="...")`.
    - The task status becomes `ready_for_qa`, and the next prompt will be from the QA persona.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    '''
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = approve_and_handoff_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def approve_and_advance_stage(task_id: str) -> ToolResponse:
    '''
    Gives human approval to an internal stage and advances to the next stage *within the same persona*.

    - **Primary Function**: This is the "human approval" gate for multi-stage personas like Planning. It triggers the `human_approve` transition.
    - **Use this tool when**: You are in a `_devreview` state within a multi-stage persona (e.g., `strategy_devreview`) and the user has explicitly approved the work for that stage.
    - **Distinction**: This tool advances *internally*. Use `approve_and_handoff` to move to a completely new persona.

    ## Example
    - State is `strategy_devreview`. User says "The strategy looks good, proceed."
    - You call `approve_and_advance_stage(task_id="...")`.
    - State becomes `solution_design_working`. The persona is still "Alex" the Planner.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    '''
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id}
    response = approve_and_advance_stage_impl(task_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response


@app.tool()
async def mark_step_complete(task_id: str, step_id: str) -> ToolResponse:
    '''
    Marks a single execution step as complete during a multi-step ("stepwise") persona workflow, like coding.

    - **Primary Function**: Acts as a checkpoint. Persists the completion of one atomic step and provides the prompt for the very next step.
    - **Use this tool when**: You are in a `stepwise` persona (like Developer) and have just executed a single step from the plan.
    - **CRITICAL GUARDRAILS**: This tool MUST be called for each step in the exact order they are provided by the server.

    ## Parameters
    - **task_id** `[string]` (required): The task identifier.
    - **step_id** `[string]` (required): The unique ID of the step that has just been completed. The ID will be in the prompt.
    '''
    tool_name = inspect.currentframe().f_code.co_name
    request_data = {"task_id": task_id, "step_id": step_id}
    response = mark_step_complete_impl(task_id, step_id)
    transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)
    return response
"""


if __name__ == "__main__":
    app.run()