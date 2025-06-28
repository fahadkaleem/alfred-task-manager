# Epic Task Manager

An MCP server built with FastMCP 2.0 that orchestrates epic software development workflows, maintaining context and state across development phases.

## Overview

Epic Task Manager acts as a workflow orchestrator for software development tasks. It guides developers through a structured process from Jira ticket assignment to code deployment, ensuring each phase is completed properly before moving to the next.

## Architecture

Built with modern Python best practices:
- **FastMCP 2.0** - Latest MCP framework with clean decorator-based API
- **Transitions** - State machine library for workflow management
- **Pydantic** - Data validation and settings management
- **Pydantic Settings** - Configuration with environment variable support

## Features

- **State Machine**: Uses `transitions` library for robust state management
- **JSON Persistence**: Single `state.json` file tracking all tasks
- **Context Preservation**: Markdown files maintain development context
- **Flexible Configuration**: Environment-based settings with Pydantic
- **Clean Architecture**: Modular design with clear separation of concerns

## Installation

```bash
pip install -e .
```

## Usage

### Initialize the system
```bash
# This creates the .epic folder structure
mcp call epic-task-manager initialize_epic_task_manager
```

### Start working on a task
```bash
mcp call epic-task-manager start_new_task '{"task_id": "TEST-123"}'
```

### Continue working on the current task
```bash
mcp call epic-task-manager continue_current_task
```

### Move to the next phase
```bash
mcp call epic-task-manager approve_and_advance
```

### Check current status
```bash
mcp call epic-task-manager get_current_status
```

## Directory Structure

```
epic-task-manager/
├── src/
│   └── epic_task_manager/    # Main package
│       ├── config/                # Pydantic settings
│       ├── models/                # Pydantic models
│       ├── state/                 # State machine implementation
│       ├── tools/                 # MCP tool implementations
│       ├── resources/             # MCP resources (future)
│       └── server.py             # FastMCP 2.0 server
├── prompts/                       # Markdown prompt templates
│   ├── retrieved.md
│   ├── planning.md
│   ├── coding.md
│   ├── self_review.md
│   └── ready_for_pr.md
└── tests/                         # Test suite
```

## Runtime Structure

```
.epictaskmanager/
├── state.json          # Master state tracker for all tasks
├── contexts/           # Task-specific context files
│   └── TEST-123.md
└── prompts/            # Copied prompt templates
```

## Development Workflow

1. **Retrieved**: Task details fetched from Jira
2. **Planning**: Create implementation plan
3. **Coding**: Implement the solution
4. **Review**: Code review phase
5. **Complete**: Task marked as done

## Configuration

Settings can be configured via environment variables:

```bash
CONDUCTOR_SERVER_NAME=my-epic_task_manager
CONDUCTOR_CONDUCTOR_DIR_NAME=.my-epic
CONDUCTOR_WORKFLOW_PHASES=["draft","develop","test","deploy"]
```

## Testing

```bash
python test_server.py
```

## Next Steps

- Add Jira MCP integration for automatic ticket fetching
- Implement git branch creation and PR tracking
- Add workflow analytics and reporting
- Create team-specific workflow templates
