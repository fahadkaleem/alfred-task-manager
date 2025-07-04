# Epic Task Manager: Comprehensive Project Overview

## Executive Summary

Epic Task Manager is an intelligent workflow orchestration system designed to guide software developers through a structured development process from initial task assignment to pull request creation. The system leverages Model Context Protocol (MCP) technology to maintain development context across multiple work sessions while enforcing quality checkpoints at each phase of the development lifecycle.

The core innovation lies in solving a fundamental challenge in AI-assisted development: maintaining coherent context and workflow discipline when using Large Language Models for complex, multi-phase software projects. By implementing a state machine with persistent context storage and comprehensive developer verification points through an integrated review-feedback system, the system ensures that AI assistance enhances rather than disrupts established development practices.

## Problem Statement and Business Rationale

Modern software development teams increasingly rely on AI assistants such as Claude and GitHub Copilot through interfaces like Cursor IDE. However, these tools suffer from critical limitations that reduce their effectiveness on complex projects. The primary challenge is context fragmentation - each new conversation with an AI assistant starts with a blank slate, losing all previous decisions, requirements, and implementation details. This forces developers to repeatedly reconstruct context, leading to inconsistent implementations and wasted time.

Additionally, without structured workflow enforcement, developers often skip crucial phases such as proper planning or thorough self-review before creating pull requests. This lack of discipline results in increased rework, more review cycles, and ultimately slower delivery of quality software.

The Epic Task Manager addresses these challenges by providing a persistent state management layer that maintains context across sessions and enforces a proven development workflow. This approach ensures that every task follows the same quality standards regardless of interruptions, team member changes, or time elapsed between work sessions.

## System Architecture and Core Features

The system implements a sophisticated state machine that tracks each development task through five distinct phases: Retrieved, Planning, Coding, Self-Review, and Ready for Pull Request. Each phase serves a specific purpose in the development lifecycle and includes appropriate prompts, context preservation, and verification requirements.

### State Management and Persistence

At the heart of the system lies a robust state management architecture built on DuckDB for persistence. The state tracking maintains two parallel status systems - the internal MCP workflow phases and the external Jira ticket statuses. This dual-tracking ensures that the development workflow aligns with project management requirements while maintaining the flexibility needed for effective development.

The persistence layer stores all tasks in a single `.alfred/state.json` file, enabling quick retrieval of the current active task based on the most recent timestamp. This approach supports natural task switching while maintaining a clear audit trail of all phase transitions and review cycles. Context for each task is preserved in dedicated markdown files that serve as living documentation of the development journey, including all review feedback and iteration cycles.

### Workflow Orchestration Tools

The system exposes eleven comprehensive MCP tools that orchestrate the development workflow. The initialize_alfred tool creates the necessary directory structure and prepares the system for use. The start_new_task tool begins work on a new task, creating the initial context file and setting up the workflow state. The continue_current_task tool enables developers to resume work after interruptions by automatically identifying the most recent active task.

Phase progression is managed through specialized tools including approve_and_advance for standard transitions and mark_task_ready_for_pr for final preparation. The system includes a comprehensive review-feedback system with four dedicated tools: request_phase_review for requesting developer verification, provide_feedback for submitting review feedback, address_feedback for resolving review concerns, and get_review_status for tracking review cycles.

Task switching capabilities are provided through the switch_to_task tool, which updates timestamps to change the active task while preserving all context and review history. This feature addresses the common scenario where developers must temporarily switch between multiple assignments. The get_current_status tool provides comprehensive visibility into all tasks, their current phases, and review states.

### Integration Architecture

The system integrates seamlessly with existing development tools through a carefully designed architecture. Jira integration is achieved through the Atlassian MCP, allowing the system to fetch ticket details and update statuses at appropriate workflow points. The integration maintains clear boundaries - Epic Task Manager manages the development workflow while Jira handles project management concerns.

The prompt system uses file-based templates that can be referenced directly by Cursor IDE through @ mentions. This approach works around Cursor's limitation of not supporting dynamic MCP prompts while providing a flexible system that teams can customize for their specific needs. Each phase has a dedicated prompt file that guides developers through the expected activities and deliverables.

### Context Preservation and Documentation

Perhaps the most valuable feature is the comprehensive context preservation system enhanced by the integrated review-feedback cycle. Each task maintains a detailed markdown file that chronicles the entire development journey, including all review iterations, feedback received, and resolution approaches. These files capture not only what was done but why decisions were made, what challenges were encountered, how they were resolved, and what feedback was incorporated. This creates invaluable documentation for future maintenance and serves as a knowledge base for similar tasks.

The context files are designed to be developer-editable, recognizing that developers possess domain knowledge that AI assistants cannot infer. This hybrid approach combines the efficiency of AI assistance with the irreplaceable value of developer expertise and judgment.

## Current Implementation Status

The system has been successfully implemented with comprehensive test coverage including a sophisticated review-feedback system. The implementation includes extensive unit and integration tests with 421+ lines of test code specifically for the review cycle functionality. Key implemented features include automatic task switching (EP-34), review-feedback cycles with multi-iteration support, and comprehensive state management with proper error handling and validation.

The implementation includes comprehensive error handling, type safety through Python enums, and a clean architecture that separates concerns appropriately. The codebase follows professional standards with proper documentation, testing infrastructure, and extensibility considerations built in from the foundation.

## Business Value and Impact

The Epic Task Manager delivers significant business value through multiple dimensions. Development velocity increases as developers spend less time reconstructing context and more time writing code. Quality improvements result from enforced planning and review phases, reducing defects that reach production. The standardized workflow ensures consistent practices across the team, making onboarding easier and reducing variance in code quality.

The system also provides valuable metrics and insights. By tracking time spent in each phase and the number of review cycles required, teams can identify bottlenecks and continuously improve their processes. The comprehensive documentation trail created by the context files reduces knowledge silos and makes maintenance significantly easier.

## Current Implementation Status

The developer verification system has been fully implemented and is production-ready with comprehensive review-feedback cycles. This system enables review cycles within each phase, ensuring that developer judgment validates AI-generated work before progression. The system supports multi-iteration feedback loops where developers can request revisions, provide detailed feedback with reviewer notes, and track resolution of concerns before phase completion.

## Future Development Roadmap

Planned enhancements include automated git operations for branch creation and pull request generation, integration with continuous integration systems for automated testing, DuckDB implementation for advanced analytics, and dashboards that visualize team productivity patterns. The architecture has been designed to support these enhancements without requiring fundamental changes to the core system.

## Conclusion

Epic Task Manager represents a significant advancement in AI-assisted software development. By addressing the fundamental challenges of context persistence and workflow discipline, it enables teams to leverage AI assistance effectively while maintaining high quality standards. The system's success in managing real development tasks demonstrates its practical value and positions it as an essential tool for modern development teams seeking to maximize the benefits of AI assistance while maintaining control over their development process.

# Epic Task Manager - Feature Documentation

## System Overview

**Name**: Epic Task Manager
**Version**: 0.1.0
**Type**: MCP (Model Context Protocol) Server
**Purpose**: Orchestrate software development workflows with persistent state management

## Core Features

### 1. State Management System

#### 1.1 Dual Status Tracking
- **MCP Phases**: `retrieved` → `planning` → `coding` → `self_review` → `ready_for_pr`
- **Jira Statuses**: `TO DO` → `In Progress` → `Code Review`
- Maintains synchronization points between MCP and Jira workflows

#### 1.2 Persistence Layer
- **State File**: `.alfred/state.json` - Single file tracking all tasks and review cycles
- **Storage Format**: JSON with task IDs as keys, includes review state and feedback history
- **Current Task Detection**: Automatically determined by most recent `last_updated` timestamp
- **Database**: JSON-based persistence (DuckDB planned for future analytics)

#### 1.3 Task State Schema
```python
TaskState:
  - current_phase: WorkflowPhase (enum)
  - phase_history: List[WorkflowPhase]
  - last_updated: datetime
  - created_at: datetime
  - completed_at: Optional[datetime]
  - review_cycles: List[ReviewCycleData]  # NEW: Review-feedback history
  - metadata: Dict[str, Any]

ReviewCycleData:
  - phase: WorkflowPhase
  - state: PhaseState (working|pending_review|needs_revision|verified)
  - work_summary: str
  - feedback_entries: List[FeedbackEntry]
  - iteration_count: int
```

### 2. MCP Tools (API Endpoints)

#### 2.1 initialize_alfred()
- **Purpose**: Set up directory structure
- **Creates**:
  - `.epic/` directory
  - `.epic/contexts/` for task documentation
  - `.epic/state.json` for state tracking
- **Templates**: Embedded in package (not written to disk)
- **Returns**: List of created directories and confirmation

#### 2.2 start_new_task(task_id: str)
- **Purpose**: Begin work on a new task
- **Actions**:
  - Creates task in state.json
  - Initializes context file with template
  - Sets phase to `retrieved`
- **Returns**: TaskResponse with prompt and context file paths

#### 2.3 continue_current_task()
- **Purpose**: Resume work on most recent task
- **Actions**:
  - Finds task with latest timestamp
  - Returns current phase info
- **No parameters needed** - automatically detects current task

#### 2.4 approve_and_advance()
- **Purpose**: Progress to next workflow phase
- **Validation**: Enforces linear progression
- **Updates**: State file and last_updated timestamp
- **Returns**: New phase info and appropriate prompt

#### 2.5 mark_task_ready_for_pr(task_id: str)
- **Purpose**: Explicitly mark task ready for pull request
- **Special Features**:
  - Adds PR checklist to context
  - Includes Jira transition instructions
  - Provides clear next steps
- **Marks task as**: `completed`

#### 2.6 switch_to_task(task_id: str)
- **Purpose**: Change active task (new feature from EP-34)
- **Validation**:
  - Task must exist
  - Task must not be completed
- **Updates**: Task timestamp to make it current

#### 2.7 get_current_status()
- **Purpose**: View all tasks and states
- **Returns**:
  - Total task count
  - Active/completed breakdown
  - Current task details
  - All task summaries
  - Review status for each task

#### 2.8 request_phase_review(task_id: str, work_summary: str)
- **Purpose**: Request developer review of completed phase work
- **Actions**:
  - Sets task to pending_review state
  - Records work summary
  - Creates review entry with timestamp
- **Returns**: Review request confirmation and instructions

#### 2.9 provide_feedback(task_id: str, feedback: str, needs_revision: bool, reviewer_notes: str)
- **Purpose**: Provide feedback on current phase work
- **Actions**:
  - Records detailed feedback
  - Sets verification status (verified/needs_revision)
  - Stores optional reviewer notes
- **Returns**: Feedback confirmation and next steps

#### 2.10 address_feedback(task_id: str, resolution_notes: str)
- **Purpose**: Mark feedback as addressed and request re-review
- **Actions**:
  - Records resolution approach
  - Resets to pending_review state
  - Increments review iteration
- **Returns**: Re-review request confirmation

#### 2.11 get_review_status(task_id: str)
- **Purpose**: Get current review cycle status
- **Returns**:
  - Current review state
  - Review iteration count
  - Feedback history
  - Pending actions

### 3. Context Management

#### 3.1 Context Files
- **Location**: `.alfred/contexts/[TASK-ID].md`
- **Format**: Markdown with timestamp sections
- **Contents**:
  - Jira ticket details
  - Phase progression history
  - Implementation decisions
  - Review feedback and cycles
  - Resolution notes for each review iteration
  - Completion notes

#### 3.2 Context Features
- **developer-editable**: Developers can add domain knowledge
- **Auto-generated sections**: Phase transitions add timestamps
- **Living documentation**: Captures entire development journey

### 4. Prompt System

#### 4.1 Phase Prompts
- **Retrieved**: `prompts/retrieved.md` - Initial task assessment
- **Planning**: `prompts/planning.md` - Implementation planning guide
- **Coding**: `prompts/coding.md` - Development instructions
- **Self Review**: `prompts/self_review.md` - Local review checklist
- **Ready for PR**: `prompts/ready_for_pr.md` - PR preparation guide

#### 4.2 Prompt Features
- **File-based**: Compatible with Cursor @ mentions
- **Customizable**: Teams can modify templates
- **Context injection**: `{task_id}` and `{context}` placeholders

### 5. Workflow Integration

#### 5.1 Jira Integration Points
- **Manual transitions required at**:
  - Coding phase start → Update Jira to "In Progress"
  - Ready for PR → Update Jira to "Code Review"
- **Future automation**: Prepared for API integration

#### 5.2 Git Workflow Support
- **Branch naming**: Supports task ID conventions
- **PR preparation**: Checklists and templates
- **Future**: Automated branch/PR creation planned

### 6. Utility Systems

#### 6.1 Jira Sync Utilities
```python
jira_sync.py functions:
- get_suggested_jira_status(mcp_phase) → Optional[JiraStatus]
- get_phase_instructions(mcp_phase) → str
- format_status_summary(mcp_phase, jira_status) → str
```

#### 6.2 Prompt Loader (EP-35 Feature)
- **Automatic context extraction** from previous phases
- **Phase-specific content parsing**
- **Caching system** for performance
- **Regex-based markdown parsing**

### 7. Error Handling

#### 7.1 Validation Rules
- Cannot skip phases (strict linear progression)
- Cannot switch to non-existent tasks
- Cannot switch to completed tasks
- Cannot advance beyond final phase

#### 7.2 Error Responses
- Consistent `TaskResponse` format
- Clear error messages
- Appropriate status codes

## Standard Workflows

### Workflow 1: New Task Development

```
1. start_new_task("TASK-123")
   → Creates context file, sets to 'retrieved'

2. [Add Jira details to context manually or via Atlassian MCP]

3. approve_and_advance()
   → Moves to 'planning'
   → Create implementation plan

4. approve_and_advance()
   → Moves to 'coding'
   → [UPDATE JIRA TO "In Progress"]
   → Implement solution

5. approve_and_advance()
   → Moves to 'self_review'
   → Test locally, review code

6. mark_task_ready_for_pr("TASK-123")
   → Moves to 'ready_for_pr'
   → Adds PR checklist
   → [CREATE PR, UPDATE JIRA TO "Code Review"]
```

### Workflow 2: Task Switching

```
1. get_current_status()
   → See all active tasks

2. switch_to_task("OTHER-456")
   → Makes OTHER-456 current

3. continue_current_task()
   → Resume work on OTHER-456
```

### Workflow 3: Resuming After Break

```
1. get_current_status()
   → Find current task and phase

2. continue_current_task()
   → Get prompt and context for current phase

3. [Continue work from where you left off]
```

## File Structure

```
project_root/
├── .epic/                      # Epic Task Manager workspace
│   ├── state.json              # All task states and review cycles
│   └── contexts/               # Task documentation with review history
│       ├── TASK-123.md
│       └── TASK-456.md
├── src/alfred/
│   ├── config/
│   │   └── settings.py         # Configuration with EPIC_ env vars
│   ├── models/
│   │   └── schemas.py          # Comprehensive data models
│   ├── state/
│   │   └── manager.py          # State machine with review cycles
│   ├── tools/                  # 11 MCP endpoints
│   │   ├── initialize.py
│   │   ├── begin_or_resume_task.py
│   │   ├── continue_task.py
│   │   ├── next_phase.py
│   │   ├── mark_ready_for_pr.py
│   │   ├── switch_task.py
│   │   ├── get_status.py
│   │   ├── request_review.py    # NEW: Request phase review
│   │   ├── provide_feedback.py  # NEW: Provide review feedback
│   │   ├── address_feedback.py  # NEW: Address feedback
│   │   └── review_status.py     # NEW: Get review status
│   ├── templates/              # Embedded templates (not on disk)
│   │   ├── initial_context.md
│   │   └── ready_for_pr_marker.md
│   └── utils/
│       ├── jira_sync.py        # Jira helpers
│       ├── serialization.py    # DateTime serialization
│       └── template_loader.py  # Template system
├── tests/                      # Comprehensive test suite
│   ├── conftest.py
│   ├── test_review_feedback_cycle.py  # 421+ lines
│   └── tools/
│       └── test_state_manager.py
```

## Configuration

### Environment Variables
- `EPIC_PROJECT_ROOT`: Override project directory (default: current working directory)
- `EPIC_TASK_MANAGER_DIR_NAME`: Change .alfred directory name (default: ".alfred")
- `LOG_LEVEL`: Set logging level (default: "INFO")

### Workflow Phases (settings.py)
```python
workflow_phases = [
    WorkflowPhase.RETRIEVED,
    WorkflowPhase.PLANNING,
    WorkflowPhase.CODING,
    WorkflowPhase.SELF_REVIEW,
    WorkflowPhase.READY_FOR_PR
]
```

## Usage Requirements

### Prerequisites
- Python 3.10+
- FastMCP 2.0+
- Cursor IDE or Claude Desktop
- Atlassian MCP (for Jira integration)

### MCP Client Configuration
```json
{
  "mcpServers": {
    "alfred": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/mohammedfahadkaleem/Documents/Workspace/alfred",
        "run",
        "python",
        "main.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    },
  }
}
```

## ✅ Fully Implemented Features

### Review-Feedback System (Production Ready)
- **Multi-iteration review cycles** within each phase
- **Detailed feedback tracking** with reviewer notes
- **Explicit verification** before phase advancement
- **Complete audit trail** of all review iterations
- **Four dedicated MCP tools** for review management
- **Comprehensive test coverage** (421+ lines of tests)

### Core Workflow Management
- **11 MCP tools** covering complete development lifecycle
- **State machine** with proper transition validation
- **Task switching** with timestamp-based current task detection
- **Context preservation** across all phases and review cycles
- **Template system** with dynamic variable substitution

### Robust Architecture
- **Type-safe data models** using Pydantic schemas
- **Comprehensive error handling** with custom exception hierarchy
- **JSON persistence** with proper datetime serialization
- **Async/await support** throughout the codebase
- **Extensive test suite** with pytest-asyncio

## Current Limitations

1. **Manual Jira Updates**: Status transitions not automated (utilities exist)
2. **No Git Integration**: PR creation is manual
3. **JSON Storage**: No DuckDB analytics yet (planned)
4. **No Backward Transitions**: Cannot go back to previous phases
5. **Local Storage Only**: Not designed for team sharing yet

## 📋 Planned Enhancements

### Near-term Roadmap
- **DuckDB persistence** for advanced analytics and querying
- **Automated Jira integration** using existing utility functions
- **Git branch/PR automation** with GitHub API integration
- **Prompt files on disk** for easier customization

### Future Vision
- **Team collaboration features** with shared state
- **Analytics dashboards** visualizing productivity patterns
- **Web UI interface** for non-CLI users
- **CI/CD integration** for automated testing workflows
