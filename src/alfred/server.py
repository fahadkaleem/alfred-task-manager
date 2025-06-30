# src/alfred/server.py
"""
MCP Server for Alfred
This version preserves the original comprehensive docstrings while maintaining
the clean V2 Alfred architecture.
"""

import functools
import inspect
from typing import Callable

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import ToolResponse
from src.alfred.tools.approve_and_advance import approve_and_advance_impl
from src.alfred.tools.create_spec import create_spec_impl
from src.alfred.tools.create_tasks import create_tasks_impl
from src.alfred.tools.finalize_task import finalize_task_impl
from src.alfred.tools.get_next_task import get_next_task_impl
from src.alfred.tools.implement_task import implement_task_impl
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl
from src.alfred.tools.progress import mark_subtask_complete_impl
from src.alfred.tools.provide_review import provide_review_impl
from src.alfred.tools.review_task import review_task_impl
from src.alfred.tools.submit_work import submit_work_impl
from src.alfred.tools.test_task import test_task_impl
from src.alfred.tools.work_on import work_on_impl

app = FastMCP(settings.server_name)


def log_tool_transaction(impl_func: Callable) -> Callable:
    """Decorator factory that creates a logging wrapper for tool functions.

    This decorator expects the implementation function to be passed as an argument.
    It handles both sync and async implementation functions.
    """

    def decorator(tool_func: Callable) -> Callable:
        @functools.wraps(tool_func)
        async def wrapper(*args, **kwargs) -> ToolResponse:
            tool_name = tool_func.__name__

            # Extract task_id from kwargs if present
            task_id = kwargs.get("task_id", None)

            # Build request data from kwargs
            request_data = {k: v for k, v in kwargs.items() if v is not None}

            # Call the implementation function (handle both async and sync)
            if inspect.iscoroutinefunction(impl_func):
                response = await impl_func(**kwargs)
            else:
                response = impl_func(**kwargs)

            # Log the transaction
            transaction_logger.log(task_id=task_id, tool_name=tool_name, request_data=request_data, response=response)

            return response

        return wrapper

    return decorator


@app.tool()
@log_tool_transaction(initialize_project_impl)
async def initialize_project(provider: str | None = None) -> ToolResponse:
    """
    Initializes the project workspace for Alfred by creating the .alfred directory with default configurations for workflows.

    - **Primary Function**: Sets up a new project for use with the Alfred workflow system.
    - **Key Features**:
      - Interactive provider selection when no provider is specified.
      - Creates the necessary `.alfred` directory structure.
      - Deploys default `workflow.yml` configuration file.
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
    return initialize_project_impl(provider)


@app.tool()
@log_tool_transaction(get_next_task_impl)
async def get_next_task() -> ToolResponse:
    """
    Intelligently determines and recommends the next task to work on.

    This tool analyzes all available tasks and their current states to provide
    an intelligent recommendation for what to work on next. It prioritizes based on:

    - Tasks already in progress (to avoid context switching)
    - Tasks ready for immediate action
    - Task dependencies and blockers
    - Task age and priority

    The recommendation includes reasoning for why this task was chosen and
    alternatives if you prefer to work on something else.

    Returns:
        ToolResponse: Contains the recommended task with:
        - task_id: The recommended task identifier
        - title: Task title for context
        - status: Current task status
        - reasoning: Why this task was recommended
        - alternatives: Other tasks you could work on
        - next_prompt: Suggested command to start working

    Example:
        get_next_task() -> Recommends "AL-42" with reasoning and alternatives
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(work_on_impl)
async def work_on_task(task_id: str) -> ToolResponse:
    """
    Primary entry point for working on any task - the Smart Dispatch model.

    This tool intelligently routes users to the appropriate specialized tool
    based on the current task status. It examines the task state and provides
    clear guidance on which tool to use next.

    Task Status Routing:
    - NEW: Routes to plan_task for creating execution plan
    - PLANNING: Routes to plan_task to continue planning
    - READY_FOR_DEVELOPMENT: Routes to implement_task to start implementation
    - IN_PROGRESS: Routes to implement_task to continue implementation
    - COMPLETED: Informs user the task is complete

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")

    Returns:
        ToolResponse: Contains routing guidance to the appropriate specialized tool

    Example:
        work_on_task("TS-01") -> Guides to plan_task if task is new
        work_on_task("TS-02") -> Guides to implement_task if planning is complete
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(create_spec_impl)
async def create_spec(task_id: str, prd_content: str) -> ToolResponse:
    """
    Creates a technical specification from a Product Requirements Document (PRD).

    This is the first tool in the "idea-to-code" pipeline. It transforms a PRD
    into a structured Technical Specification that serves as the foundation for
    engineering planning and implementation.

    The tool guides through creating a comprehensive spec including:
    - Background and business context
    - Technical goals and non-goals
    - Proposed architecture
    - System boundaries and APIs
    - Data model changes
    - Security considerations
    - Open questions

    Args:
        task_id (str): The unique identifier for the epic/feature (e.g., "EPIC-01")
        prd_content (str): The raw PRD content to analyze and transform

    Returns:
        ToolResponse: Contains the first prompt to guide spec creation

    Example:
        create_spec("EPIC-01", "Build a notification system...") -> Guides spec creation
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(create_tasks_impl)
async def create_tasks(task_id: str) -> ToolResponse:
    """
    Creates a list of actionable tasks from a Technical Specification.

    This is the second tool in the "idea-to-code" pipeline. It takes a completed
    Technical Specification and breaks it down into individual Task objects that
    can be tracked, assigned, and implemented independently.

    The tool guides through creating tasks that are:
    - Atomic and focused
    - Properly ordered with dependencies
    - Sized appropriately (1-3 days of work)
    - Complete with acceptance criteria

    Args:
        task_id (str): The unique identifier for the epic/feature with a completed spec

    Returns:
        ToolResponse: Contains the first prompt to guide task breakdown

    Preconditions:
        - Technical specification must be completed (via create_spec)
        - Task status must be "spec_completed"

    Example:
        create_tasks("EPIC-01") -> Guides creation of task list from spec
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(plan_task_impl)
async def plan_task(task_id: str) -> ToolResponse:
    """
    Initiates the detailed technical planning for a specific task.

    This is the primary tool for transforming a high-level task or user story
    into a concrete, machine-executable 'Execution Plan' composed of Subtasks.
    A Subtask (based on LOST framework) is an atomic unit of work.

    This tool manages a multi-step, interactive planning process:
    1. **Contextualize**: Deep analysis of the task requirements and codebase context
    2. **Strategize**: High-level technical approach and architecture decisions
    3. **Design**: Detailed technical design and component specifications
    4. **Generate Subtasks**: Break down into atomic, executable work units

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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(submit_work_impl)
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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(provide_review_impl)
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
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(mark_subtask_complete_impl)
async def mark_subtask_complete(task_id: str, subtask_id: str) -> ToolResponse:
    """
    Marks a specific subtask as complete during the implementation phase.

    This tool is used to track progress while implementing the execution plan generated
    by the planning phase. It helps monitor which subtasks have been completed and
    calculates overall progress.

    The tool validates that:
    - An active workflow tool exists for the task
    - The subtask_id corresponds to a valid subtask in the execution plan
    - The state is properly persisted after marking completion

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")
        subtask_id (str): The subtask identifier to mark as complete (e.g., "subtask-1")

    Returns:
        ToolResponse: Success/error status with progress information including:
            - Current progress percentage
            - Number of completed vs total subtasks
            - List of remaining subtasks

    Example:
        mark_subtask_complete("TS-01", "subtask-1")
        # Returns progress update showing 1/5 subtasks complete (20%)
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(implement_task_impl)
async def implement_task(task_id: str) -> ToolResponse:
    """
    Executes the implementation phase for a task that has completed planning.

    This tool is used after the planning phase is complete and the task status
    is READY_FOR_DEVELOPMENT. It guides the implementation of the execution plan
    created during the planning phase.

    Prerequisites:
    - Task must have status READY_FOR_DEVELOPMENT
    - Execution plan must exist from completed planning phase

    The tool manages:
    - Loading the execution plan from the planning phase
    - Tracking progress on individual subtasks
    - Maintaining implementation state across sessions

    Args:
        task_id (str): The unique identifier for the task (e.g., "TS-01", "PROJ-123")

    Returns:
        ToolResponse: Contains success/error status and implementation guidance

    Example:
        implement_task("TS-01") -> Starts implementation of planned task
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(review_task_impl)
async def review_task(task_id: str) -> ToolResponse:
    """
    Initiates the code review phase for a task that has completed implementation.

    This tool manages the review process where the implementation is checked
    against requirements, best practices, and quality standards.

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status and review guidance
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(test_task_impl)
async def test_task(task_id: str) -> ToolResponse:
    """
    Initiates the testing phase for a task that has passed code review.

    This tool manages the test execution process including unit tests,
    integration tests, and verification of the implementation.

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status and test results
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(finalize_task_impl)
async def finalize_task(task_id: str) -> ToolResponse:
    """
    Completes the task by creating a commit and pull request.

    This tool manages the finalization process including:
    - Creating a git commit with changes
    - Creating a pull request
    - Updating task status to completed

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status with PR details
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(approve_and_advance_impl)
async def approve_and_advance(task_id: str) -> ToolResponse:
    """
    Approves the current phase and advances to the next phase in the workflow.

    This is a convenience tool that automatically approves the current review
    step and advances the workflow to the next phase.

    Args:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains success/error status and next phase guidance
    """
    pass  # Implementation handled by decorator


if __name__ == "__main__":
    app.run()
