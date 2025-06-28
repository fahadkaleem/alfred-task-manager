"""
Jira synchronization utilities for mapping MCP phases to Jira statuses
"""

from __future__ import annotations

from epic_task_manager.models.enums import TaskPhase

from .schemas import JiraStatus


def get_suggested_jira_status(mcp_phase: TaskPhase) -> JiraStatus | None:
    """
    Determine what Jira status should be based on MCP phase.
    Returns the suggested Jira status, or None if no change recommended.

    This is for MVP - users manually update Jira based on these suggestions.
    """
    phase_to_jira: dict[TaskPhase, JiraStatus | None] = {
        TaskPhase.GATHER_REQUIREMENTS: None,  # Stay in TO DO
        TaskPhase.GIT_SETUP: None,  # Stay in TO DO
        TaskPhase.PLANNING: None,  # Stay in TO DO
        TaskPhase.SCAFFOLDING: None,  # Stay in TO DO
        TaskPhase.CODING: JiraStatus.IN_PROGRESS,  # First code work starts
        TaskPhase.TESTING: None,  # Stay in In Progress
        TaskPhase.FINALIZE: JiraStatus.CODE_REVIEW,  # Ready for team review
    }

    return phase_to_jira.get(mcp_phase)


def get_jira_phase_instructions(mcp_phase: TaskPhase) -> str:
    """
    Get developer-readable instructions for what to do in each phase,
    including Jira status updates.
    """
    instructions = {
        TaskPhase.GATHER_REQUIREMENTS: """
**Phase: Gather Requirements**
- Task has been fetched from Jira
- Review requirements and acceptance criteria
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.GIT_SETUP: """
**Phase: Git Setup**
- Setting up git environment for the task
- Creating feature branch
- Ensuring clean working directory
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.PLANNING: """
**Phase: Planning**
- Create implementation plan
- Identify files to modify/create
- Plan approach and architecture
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.SCAFFOLDING: """
**Phase: Scaffolding**
- Set up project structure and boilerplate
- Create necessary directories and basic files
- Prepare development environment
- Jira Status: Keep as "TO DO"
        """.strip(),
        TaskPhase.CODING: """
**Phase: Coding**
- Implement the planned solution
- Write/modify code
- **ACTION REQUIRED: Update Jira status to "In Progress"**
        """.strip(),
        TaskPhase.TESTING: """
**Phase: Testing**
- Test your implementation locally
- Review code quality and completeness
- Fix any issues found
- Jira Status: Keep as "In Progress"
        """.strip(),
        TaskPhase.FINALIZE: """
**Phase: Finalize**
- Code is complete and tested
- Ready to create pull request
- **ACTION REQUIRED: Create PR and update Jira status to "Code Review"**
        """.strip(),
    }

    return instructions.get(mcp_phase, "Unknown phase")


def format_jira_status_summary(mcp_phase: TaskPhase) -> str:
    """
    Format a summary showing MCP phase and suggested Jira action.
    """
    suggested_jira = get_suggested_jira_status(mcp_phase)

    status_line = f"**MCP Phase**: {mcp_phase.value}"

    if suggested_jira:
        status_line += f"  |  **Suggested Jira Status**: {suggested_jira.value}"

    return status_line
