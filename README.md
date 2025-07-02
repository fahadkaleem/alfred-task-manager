# Alfred Task Manager

A sophisticated MCP (Model Context Protocol) server that orchestrates complex software development workflows through structured, multi-phase processes from planning to deployment.

## What Alfred Task Manager Is

**Alfred Task Manager** is an AI-first workflow orchestration system designed to guide AI agents and developers through rigorous, state machine-driven software development processes. It transforms chaotic development workflows into structured, repeatable, and high-quality processes.

## Core Functionality

### 1. **Structured Development Workflow**
Alfred implements a comprehensive state machine-driven workflow with these phases:
- **Planning**: Deep contextual analysis, strategy, design, and subtask generation using the LOST framework
- **Implementation**: Executing planned work with granular progress tracking
- **Review**: Comprehensive code review and quality validation
- **Testing**: Automated and manual test execution with validation
- **Finalization**: Git commit creation and pull request generation

### 2. **Task Management System**
- **LOST Framework**: Tasks broken into atomic units (Location, Operation, Specification, Test)
- **Standardized Templates**: All tasks follow consistent markdown templates with defined sections
- **Epic Support**: Handles both individual tasks and epic-level specifications that break into multiple tasks
- **Status Progression**: NEW → PLANNING → READY_FOR_DEVELOPMENT → IN_DEVELOPMENT → READY_FOR_REVIEW → etc.

### 3. **State Machine Architecture**
- **Pattern-Based**: Two rigid workflow patterns enforced by builder system
  - Multi-step with reviews (e.g., planning: contextualize → strategize → design → subtasks)
  - Simple dispatch-work-done (e.g., implement, review, test)
- **Automatic Review Cycles**: Every work state includes built-in AI and human review phases
- **Declarative Transitions**: All state transitions are builder-generated (no manual transitions allowed)

### 4. **AI-First Design**
- **Context Preservation**: Maintains comprehensive development context across sessions
- **Artifact Management**: Archives all work products with full audit trail
- **Template-Driven**: Extensive prompt library ensures consistent AI interactions
- **Recovery Support**: Can restore and continue interrupted workflows

## Architecture

Built with modern Python best practices:
- **FastMCP 2.0** - Latest MCP framework with clean decorator-based API
- **Transitions** - State machine library for robust workflow management
- **Pydantic** - Data validation and settings management
- **LOST Framework** - Atomic work unit specification
- **Builder Pattern** - Enforced state machine construction

## Key Design Principles

### **Enforced Patterns**
The system has strict architectural principles (documented in `docs/principles/`):
- State machines must use the builder pattern exclusively
- No custom transitions or handlers allowed
- Two workflow patterns only - no exceptions
- Templates and prompts are centralized and immutable

### **Context Awareness**
- Maintains development context across all phases
- Comprehensive artifact archival system
- Transaction logging for full audit trail
- Supports workflow recovery and continuation

### **Quality Gates**
- Built-in review cycles at every phase
- AI self-review followed by human approval
- Revision loops with detailed feedback
- Progress tracking with subtask completion

## Installation

```bash
pip install -e .
```

## Usage

### Core Workflow Tools

#### 1. Initialize Project
```bash
# Creates .alfred directory structure
initialize_project(provider="local")  # or "jira", "linear"
```

#### 2. Create Tasks
```bash
# Create individual task
create_task(task_content="# TASK: AL-001\n## Title\n...")

# Or create from spec
create_spec(task_id="EPIC-01", prd_content="...")
create_tasks_from_spec(task_id="EPIC-01")
```

#### 3. Execute Workflow
```bash
# Start working on any task
work_on_task(task_id="AL-001")

# Plan the task (contextualize → strategize → design → subtasks)
plan_task(task_id="AL-001")
submit_work(task_id="AL-001", artifact={...})
approve_review(task_id="AL-001")

# Implement the planned work
implement_task(task_id="AL-001")
mark_subtask_complete(task_id="AL-001", subtask_id="subtask-1")
submit_work(task_id="AL-001", artifact={...})

# Review, test, and finalize
review_task(task_id="AL-001")
test_task(task_id="AL-001")
finalize_task(task_id="AL-001")

# Or use the convenience function
approve_and_advance(task_id="AL-001")  # Approves current phase and advances
```

#### 4. Task Management
```bash
# Get intelligent task recommendations
get_next_task()

# Request revisions during review
request_revision(task_id="AL-001", feedback_notes="...")
```

## Directory Structure

```
alfred-task-manager/
├── src/alfred/                    # Main package
│   ├── config/                    # Settings and configuration
│   ├── core/                      # Core workflow and state machine logic
│   │   ├── workflow.py           # BaseWorkflowTool and tool classes
│   │   ├── state_machine_builder.py  # State machine construction
│   │   └── prompt_templates.py   # Template management
│   ├── models/                    # Pydantic models and schemas
│   │   ├── schemas.py            # Task, Subtask, ToolResponse models
│   │   └── planning_artifacts.py # Workflow artifact definitions
│   ├── tools/                     # MCP tool implementations
│   │   ├── tool_definitions.py   # Declarative tool definitions
│   │   ├── plan_task.py          # Planning workflow
│   │   ├── implement_task.py     # Implementation workflow
│   │   └── ...                   # Other workflow tools
│   ├── templates/                 # Prompt and artifact templates
│   │   ├── prompts/              # Phase-specific prompts
│   │   └── artifacts/            # Artifact templates
│   └── server.py                 # FastMCP 2.0 server
├── docs/
│   └── principles/               # Architectural principles (MANDATORY)
│       ├── state_machine_principles.md  # State machine rules
│       ├── handler_principles.md        # Handler design rules
│       └── template_system_principles.md # Template guidelines
└── tests/                        # Test suite
```

## Runtime Structure

```
.alfred/                          # Created by initialize_project
├── config.json                   # Project configuration
├── tasks/                        # Task definitions
│   └── AL-001.md                 # Individual task files
├── workspace/{task_id}/          # Active task workspaces
│   ├── task_state.json           # Task state and progress
│   ├── scratchpad.md            # Working notes
│   └── archive/                  # Completed artifacts
├── debug/{task_id}/              # Debug logs and traces
    ├── alfred.log               # Tool execution logs
    └── transactions.jsonl       # Transaction history
```

## LOST Framework

Alfred uses the **LOST Framework** for breaking down work into atomic units:

- **L**ocation: File/directory where work happens
- **O**peration: Type of change (CREATE, MODIFY, DELETE, REVIEW)
- **S**pecification: Step-by-step procedural instructions
- **T**est: Verification steps and validation criteria

Example Subtask:
```json
{
  "subtask_id": "ST-1",
  "title": "Add authentication middleware",
  "location": "src/middleware/auth.py",
  "operation": "CREATE",
  "specification": [
    "Create new file src/middleware/auth.py",
    "Implement JWT token validation",
    "Add role-based access control"
  ],
  "test": [
    "Verify JWT validation works",
    "Test role permissions are enforced"
  ]
}
```

## Development Workflow Phases

### 1. **Planning Phase** (Multi-step with reviews)
- **Contextualize**: Deep analysis of task requirements and codebase
- **Strategize**: High-level technical approach and architecture
- **Design**: Detailed technical design and component specifications
- **Generate Subtasks**: Break down into atomic LOST units

### 2. **Implementation Phase** (Simple workflow)
- Load execution plan from planning phase
- Execute subtasks with progress tracking
- Create implementation manifest

### 3. **Review Phase** (Simple workflow)
- Comprehensive code review against requirements
- Validate completeness and quality
- Check security, performance, testing

### 4. **Testing Phase** (Simple workflow)
- Execute test suites (unit, integration, regression)
- Validate against acceptance criteria
- Document test results and coverage

### 5. **Finalization Phase** (Simple workflow)
- Create git commit with descriptive message
- Generate pull request with detailed description
- Archive all workflow artifacts

## Configuration

Alfred can be configured through multiple task providers:

### Local Provider (Default)
```bash
initialize_project(provider="local")
```
Tasks stored in `.alfred/tasks/` directory as markdown files.

### Jira Provider
```bash
initialize_project(provider="jira")
```
Integrates with Jira for ticket management.

### Linear Provider  
```bash
initialize_project(provider="linear")
```
Integrates with Linear for issue tracking.

## Testing

### Run Test Suite
```bash
uv run python -m pytest tests/ -v
```

### End-to-End Validation
```bash
# Follow the comprehensive testing protocol
cat TESTING_PROTOCOL.md
```

The testing protocol validates the entire workflow from project initialization through task completion, ensuring all state transitions work correctly.

## What Makes Alfred Special

### **AI-First Architecture**
- Designed specifically for AI agents to follow structured workflows
- Comprehensive context preservation across development phases
- Template-driven interactions ensure consistency

### **Rigorous State Management** 
- Enforced state machine patterns prevent workflow chaos
- Built-in review cycles ensure quality at every phase
- Automatic artifact archival and audit trails

### **Scalable Design**
- Supports both simple tasks and complex epic-level features
- LOST framework ensures atomic, testable work units
- Declarative tool definitions make adding new workflows trivial

### **Quality Assurance**
- Every work state includes AI and human review cycles
- Revision loops with detailed feedback mechanisms
- Progress tracking and validation at each step

## Key Files to Understand

- `src/alfred/server.py` - MCP server with all tool definitions
- `src/alfred/core/workflow.py` - Workflow tool classes and state definitions
- `src/alfred/tools/tool_definitions.py` - Declarative tool configuration
- `docs/principles/state_machine_principles.md` - **MANDATORY** architectural rules
- `TESTING_PROTOCOL.md` - Comprehensive end-to-end validation
- `CLAUDE.md` - Development guidelines and commands

This system transforms chaotic development processes into structured, repeatable, and high-quality workflows optimized for AI-human collaboration.
