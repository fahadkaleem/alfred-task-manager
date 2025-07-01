# src/alfred/server.py
"""
MCP Server for Alfred
This version preserves the original comprehensive docstrings while maintaining
the clean V2 Alfred architecture.
"""

import functools
import inspect
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from fastmcp import FastMCP

from src.alfred.config.settings import settings
from src.alfred.core.prompter import prompt_library  # Import the prompt library
from src.alfred.lib.logger import get_logger
from src.alfred.lib.transaction_logger import transaction_logger
from src.alfred.models.schemas import TaskStatus, ToolResponse
from src.alfred.tools.approve_and_advance import approve_and_advance_impl
from src.alfred.constants import ToolName
from src.alfred.tools.registry import tool_registry
from src.alfred.tools.create_spec import create_spec_impl
from src.alfred.tools.create_tasks import create_tasks_from_spec_impl
from src.alfred.tools.finalize_task import finalize_task_impl, finalize_task_handler
from src.alfred.tools.get_next_task import get_next_task_impl
from src.alfred.tools.implement_task import implement_task_impl, implement_task_handler
from src.alfred.tools.initialize import initialize_project as initialize_project_impl
from src.alfred.tools.plan_task import plan_task_impl, plan_task_handler
from src.alfred.core.workflow import PlanTaskTool, ImplementTaskTool, ReviewTaskTool, TestTaskTool, FinalizeTaskTool
from src.alfred.tools.progress import mark_subtask_complete_impl, mark_subtask_complete_handler
from src.alfred.tools.approve_review import approve_review_impl
from src.alfred.tools.request_revision import request_revision_impl
from src.alfred.tools.review_task import review_task_handler
from src.alfred.tools.submit_work import submit_work_handler
from src.alfred.tools.test_task import test_task_handler
from src.alfred.tools.work_on import work_on_impl
from src.alfred.tools.workflow_config import WORKFLOW_TOOL_CONFIGS

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Lifespan context manager for FastMCP server."""
    # Startup
    logger.info(f"Starting Alfred server with {len(prompt_library._cache)} prompts loaded")

    yield

    # Shutdown (if needed in the future)
    logger.info("Server shutting down")


app = FastMCP(settings.server_name, lifespan=lifespan)


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
@log_tool_transaction(create_tasks_from_spec_impl)
async def create_tasks_from_spec(task_id: str) -> ToolResponse:
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


# THIS IS THE FIX for Blocker #2
@app.tool()
@tool_registry.register(name=ToolName.PLAN_TASK, handler_class=lambda: plan_task_handler, tool_class=PlanTaskTool, entry_status_map=WORKFLOW_TOOL_CONFIGS[ToolName.PLAN_TASK].entry_status_map)
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
    return await plan_task_impl(task_id)


@app.tool()
@log_tool_transaction(submit_work_handler.execute)
async def submit_work(task_id: str, artifact: dict) -> ToolResponse:
    """
    Submits a structured work artifact for the current step of a workflow tool.

    - Generic state-advancing tool for any active workflow (plan, implement, review, test)
    - Automatically determines correct state transition based on current state
    - Validates artifact structure against expected schema for current state
    - Advances the tool's state machine to next step or review phase
    - Works with all workflow tools: plan_task, implement_task, review_task, test_task

    The artifact structure varies by tool and state:
    - **Planning states**: context_analysis, strategy, design, subtasks
    - **Implementation**: progress updates, completion status
    - **Review**: findings, issues, recommendations
    - **Testing**: test results, coverage, validation status

    Parameters:
        task_id (str): The unique identifier for the task (e.g., "AL-01", "TS-123")
        artifact (dict): Structured data matching the current state's expected schema

    Returns:
        ToolResponse: Contains:
            - success: Whether submission was accepted
            - data.next_action: The next tool/action to take
            - data.state: New state after transition
            - data.prompt: Next prompt for user interaction

    Examples:
        # Planning context submission
        submit_work("AL-01", {
            "understanding": "Task requires refactoring auth module...",
            "constraints": ["Must maintain backward compatibility"],
            "risks": ["Potential breaking changes to API"]
        })

        # Implementation progress
        submit_work("AL-02", {
            "progress": "Completed authentication refactor",
            "subtasks_completed": ["subtask-1", "subtask-2"]
        })

    Next Actions:
        - If in review state: Use approve_review or request_revision
        - If advancing to new phase: Tool will indicate next tool to use
        - If complete: No further action needed
    """
    return await submit_work_handler.execute(task_id, artifact=artifact)


@app.tool()
@log_tool_transaction(approve_review_impl)
async def approve_review(task_id: str) -> ToolResponse:
    """
    Approves the artifact in the current review step and advances the workflow.

    - Approves work in any review state (AI self-review or human review)
    - Advances workflow to next phase or completion
    - Works with all review states across all workflow tools
    - Automatically determines next state based on current workflow phase

    Applicable States:
    - **Planning**: review_context, review_strategy, review_design, review_plan
    - **Implementation**: awaiting_human_review after completion
    - **Review**: awaiting_ai_review, awaiting_human_review
    - **Testing**: awaiting_ai_review, awaiting_human_review

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether approval was successful
            - data.next_action: Next tool to use (if any)
            - data.new_state: State after approval
            - data.message: Guidance for next steps

    Examples:
        # Approve planning context analysis
        approve_review("AL-01")  # Advances to strategy phase

        # Approve final implementation
        approve_review("AL-02")  # Advances to review phase

    Next Actions:
        - Planning phases: Continues to next planning step via submit_work
        - Phase transitions: Use the indicated next tool (review_task, test_task, etc.)
        - Final approval: Task moves to completed state

    Preconditions:
        - Must be in a review state (awaiting_ai_review or awaiting_human_review)
        - Artifact must have been submitted for current state
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(request_revision_impl)
async def request_revision(task_id: str, feedback_notes: str) -> ToolResponse:
    """
    Rejects the artifact in the current review step and sends it back for revision.

    - Requests revision for work in any review state
    - Sends workflow back to previous working state for improvements
    - Requires detailed, actionable feedback for the implementer
    - Preserves revision history for audit trail

    Feedback Guidelines:
    - Be specific about what needs improvement
    - Provide concrete examples when possible
    - Suggest specific solutions or approaches
    - Focus on actionable items, not vague concerns
    - Prioritize critical issues over minor improvements

    Parameters:
        task_id (str): The unique identifier for the task
        feedback_notes (str): Detailed, actionable feedback explaining required changes

    Returns:
        ToolResponse: Contains:
            - success: Whether revision request was processed
            - data.state: State returned to for revision
            - data.prompt: Updated prompt including feedback
            - data.feedback: The feedback provided for reference

    Examples:
        # Request planning revision
        request_revision("AL-01",
            "The context analysis is missing critical dependency information. "
            "Please add: 1) List of dependent services, 2) API contracts that "
            "might be affected, 3) Database schema dependencies"
        )

        # Request implementation fixes
        request_revision("AL-02",
            "The error handling is incomplete. Specifically: "
            "1) No timeout handling in API calls (add 30s timeout), "
            "2) Missing rollback logic for failed transactions, "
            "3) No retry mechanism for transient failures"
        )

    Next Actions:
        - Implementer should address feedback using submit_work
        - After revision, work returns to review state
        - Process repeats until approved

    Good Feedback Examples:
        - "Add input validation for email field using regex pattern"
        - "Refactor calculateTotal() to handle null values in items array"
        - "Add unit tests for error cases in auth middleware"

    Poor Feedback Examples:
        - "Code needs improvement" (too vague)
        - "Don't like the approach" (not actionable)
        - "Try again" (no guidance)
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(mark_subtask_complete_handler.execute)
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
@tool_registry.register(
    name=ToolName.IMPLEMENT_TASK,
    handler_class=lambda: implement_task_handler,
    tool_class=ImplementTaskTool,
    entry_status_map=WORKFLOW_TOOL_CONFIGS[ToolName.IMPLEMENT_TASK].entry_status_map,
)
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
    return await implement_task_handler.execute(task_id)


@app.tool()
@tool_registry.register(
    name=ToolName.REVIEW_TASK,
    handler_class=lambda: review_task_handler,
    tool_class=ReviewTaskTool,
    entry_status_map=WORKFLOW_TOOL_CONFIGS[ToolName.REVIEW_TASK].entry_status_map,
)
async def review_task(task_id: str) -> ToolResponse:
    """
    Initiates the code review phase for a task that has completed implementation.

    - Comprehensive code review against requirements and best practices
    - Checks implementation completeness, quality, and correctness
    - Validates against original task requirements and acceptance criteria
    - Reviews code style, patterns, error handling, and edge cases
    - Ensures tests are present and passing

    Review Criteria:
    - **Functionality**: Does the code fulfill all requirements?
    - **Completeness**: Are all subtasks from the plan implemented?
    - **Code Quality**: Follows project patterns and best practices?
    - **Error Handling**: Proper error handling and edge cases?
    - **Testing**: Adequate test coverage for new functionality?
    - **Performance**: No obvious performance issues?
    - **Security**: No security vulnerabilities introduced?

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether review was initiated
            - data.prompt: Review checklist and guidance
            - data.state: Current review state
            - data.requirements: Original requirements for reference

    Examples:
        review_task("AL-01")  # Starts comprehensive code review

    Review Process:
    1. Tool loads implementation details and original requirements
    2. Presents comprehensive review checklist
    3. Reviewer performs thorough code review
    4. Reviewer submits findings via submit_work
    5. AI reviews the human review for completeness
    6. Final approval/revision via approve_review or request_revision

    Next Actions:
        - Use submit_work to provide review findings
        - After review submission, use approve_review or request_revision
        - If approved, advances to test_task

    Preconditions:
        - Task must be in READY_FOR_REVIEW status
        - Implementation must be complete
        - All subtasks should be marked complete
    """
    return await review_task_handler.execute(task_id)


@app.tool()
@tool_registry.register(
    name=ToolName.TEST_TASK,
    handler_class=lambda: test_task_handler,
    tool_class=TestTaskTool,
    entry_status_map=WORKFLOW_TOOL_CONFIGS[ToolName.TEST_TASK].entry_status_map,
)
async def test_task(task_id: str) -> ToolResponse:
    """
    Initiates the testing phase for a task that has passed code review.

    - Executes comprehensive test suite for the implementation
    - Runs unit tests, integration tests, and validation checks
    - Verifies implementation against acceptance criteria
    - Checks for regressions in existing functionality
    - Validates edge cases and error scenarios

    Testing Scope:
    - **Unit Tests**: Test individual functions/methods
    - **Integration Tests**: Test component interactions
    - **Regression Tests**: Ensure no existing functionality broken
    - **Edge Cases**: Validate boundary conditions
    - **Error Scenarios**: Test error handling paths
    - **Performance**: Basic performance validation
    - **Manual Testing**: UI/UX validation if applicable

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether testing was initiated
            - data.prompt: Testing checklist and guidance
            - data.test_requirements: What needs to be tested
            - data.acceptance_criteria: Original criteria to validate

    Examples:
        test_task("AL-01")  # Starts comprehensive testing phase

    Testing Process:
    1. Tool provides testing checklist and requirements
    2. Tester runs automated test suites
    3. Tester performs manual validation if needed
    4. Tester documents results via submit_work
    5. Results are reviewed for completeness
    6. Approval/revision via approve_review or request_revision

    Test Result Structure (for submit_work):
        {
            "test_summary": "All tests passing with 95% coverage",
            "unit_tests": {"passed": 45, "failed": 0},
            "integration_tests": {"passed": 12, "failed": 0},
            "manual_tests": ["UI responsive on mobile", "Forms validate correctly"],
            "issues_found": [],
            "coverage": "95%"
        }

    Next Actions:
        - Use submit_work to provide test results
        - After submission, use approve_review or request_revision
        - If approved, advances to finalize_task

    Preconditions:
        - Task must be in READY_FOR_TESTING status
        - Code review must be complete and approved
        - Implementation should be stable
    """
    return await test_task_handler.execute(task_id)


@app.tool()
@tool_registry.register(
    name=ToolName.FINALIZE_TASK,
    handler_class=lambda: finalize_task_handler,
    tool_class=FinalizeTaskTool,
    entry_status_map=WORKFLOW_TOOL_CONFIGS[ToolName.FINALIZE_TASK].entry_status_map,
)
@log_tool_transaction(finalize_task_impl)
async def finalize_task(task_id: str) -> ToolResponse:
    """
    Completes the task by creating a commit and pull request.

    - Creates comprehensive git commit with all changes
    - Generates pull request with detailed description
    - Links PR to original task/issue
    - Updates task status to completed
    - Archives all task artifacts and history

    Finalization Process:
    1. **Commit Creation**:
       - Stages all modified files
       - Creates descriptive commit message
       - Includes task ID and summary

    2. **Pull Request**:
       - Auto-generates PR description from task history
       - Includes implementation summary
       - Lists all changes made
       - References original requirements
       - Adds testing notes

    3. **Task Completion**:
       - Updates task status to COMPLETED
       - Archives all workflow artifacts
       - Preserves audit trail

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether finalization succeeded
            - data.commit_sha: Git commit hash
            - data.pr_url: Pull request URL
            - data.pr_number: PR number for reference
            - data.summary: Summary of completed work

    Examples:
        finalize_task("AL-01")
        # Creates commit and PR with:
        # - Title: "AL-01: Implement user authentication refactor"
        # - Description: Auto-generated from task history
        # - Links: References to original issue/task

    PR Description Includes:
        - Task summary and objectives
        - List of changes made
        - Testing performed
        - Any breaking changes
        - Deployment notes

    Next Actions:
        - Review pull request in version control system
        - Merge PR when approved by reviewers
        - Deploy changes according to process
        - Close related issues/tickets

    Preconditions:
        - Task must be in READY_FOR_FINALIZATION status
        - All tests must be passing
        - All reviews must be approved
        - No uncommitted changes in working directory

    Note: This tool does NOT push to remote or merge the PR.
    Manual review and merge is required per team process.
    """
    pass  # Implementation handled by decorator


@app.tool()
@log_tool_transaction(approve_and_advance_impl)
async def approve_and_advance(task_id: str) -> ToolResponse:
    """
    Approves the current phase and advances to the next phase in the workflow.

    - Convenience tool combining approve_review + automatic phase transition
    - Skips intermediate approval states for faster workflow
    - Ideal for when you're confident in the current work
    - Automatically determines and initiates next phase

    Phase Transitions:
    - **Planning** → Implementation (via implement_task)
    - **Implementation** → Review (via review_task)
    - **Review** → Testing (via test_task)
    - **Testing** → Finalization (via finalize_task)
    - **Finalization** → Completed (task done)

    This tool handles:
    1. Approves current review state
    2. Determines next logical phase
    3. Automatically initiates next phase
    4. Returns guidance for next steps

    Parameters:
        task_id (str): The unique identifier for the task

    Returns:
        ToolResponse: Contains:
            - success: Whether advancement succeeded
            - data.from_phase: Phase completed
            - data.to_phase: New phase started
            - data.next_tool: Tool to use for new phase
            - data.prompt: Guidance for next phase

    Examples:
        # After planning completion
        approve_and_advance("AL-01")
        # Approves plan and starts implement_task

        # After implementation
        approve_and_advance("AL-02")
        # Approves implementation and starts review_task

    When to Use:
        - You've reviewed the work and it's ready to proceed
        - You want to skip manual approval steps
        - You're confident no revisions are needed

    When NOT to Use:
        - You need to review the work carefully first
        - You might need revisions
        - You want to pause between phases

    Next Actions:
        - Follow the guidance for the next phase
        - Use the indicated tool for the new phase
        - Continue workflow until task completion

    Preconditions:
        - Must be in a review state
        - Current phase work must be submitted
        - Cannot skip required phases

    Note: This tool enforces the standard workflow order.
    You cannot skip phases or move backward.
    """
    pass  # Implementation handled by decorator


if __name__ == "__main__":
    app.run()
