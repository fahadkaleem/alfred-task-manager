# Epic Task Manager - Development Guidelines

## Task Source Configuration Approach

Epic Task Manager uses a **configuration-based approach** for task source integration, NOT auto-detection.

### Key Design Decisions:

1. **Explicit User Choice During Initialization**
   - When running `initialize`, users are prompted to select their task management system
   - Options: (1) Jira, (2) Linear, (3) Local/None
   - This choice is stored in `.epictaskmanager/config.json`

2. **Configuration-Driven Behavior**
   - The system loads task-source-specific prompts based on config.json
   - Example: If configured for Jira, load prompts from `prompts/jira/`
   - Example: If configured for Linear, load prompts from `prompts/linear/`

3. **MVP Scope**
   - Support only Jira and Linear for initial release (plus local mode)
   - Check for required MCP tools based on configuration
   - Allow users to reconfigure later without full re-initialization

4. **No Auto-Detection**
   - The system does NOT scan for available MCP tools
   - It only checks for the specific MCP tool the user selected
   - This makes behavior predictable and debugging easier

### Configuration Schema:
```json
{
  "task_source": "jira" | "linear" | "local",
  "task_source_config": {
    "jira": {
      "cloud_id": "...",
      "project_key": "EP",
      "default_issue_type": "Task"
    },
    "linear": {
      "team_id": "...",
      "workspace": "..."
    }
  },
  "created_at": "2025-01-21T...",
  "version": "1.0"
}
```

### Implementation Notes:
- All Jira-specific code should be moved to a task source abstraction
- Prompts should be templated to work with any task source
- The core workflow (gather_requirements → git_setup → planning → coding → self_review → ready_for_pr) remains the same
- Only the external integrations change based on configuration

### Backward Compatibility:
- If no config.json exists, assume Jira (for existing users)
- Prompt users to run configuration on next initialize

# Testing and Development Commands

- Use `uv run python -m pytest tests/ -v` to run tests
- Use `uv` package manager for all Python operations instead of pip/python directly
