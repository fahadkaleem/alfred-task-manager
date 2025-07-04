<!--
Template: plan_task.contracts
Purpose: Design interfaces and contracts
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Design the interfaces and contracts for this task.

# BACKGROUND
We've discovered the codebase structure and clarified requirements. Now design the interfaces before implementation.

# INSTRUCTIONS
1. Define key interfaces/APIs in markdown
2. List the main contracts being created
3. Note any important design decisions

# OUTPUT
Submit a simple artifact with:
- **interface_design**: Markdown describing interfaces
- **contracts_defined**: List of main contracts
- **design_notes**: Any important notes

## Example
```json
{
  "interface_design": "## Interface Design\n\n### TaskPriority Enum\n- HIGH = 'high'\n- MEDIUM = 'medium'\n- LOW = 'low'\n\n### Task Model\n- priority: Optional[TaskPriority] = MEDIUM\n\n### Parser Updates\n- Parse '## Priority' section\n- Case-insensitive\n\n### Ranking Algorithm\n- New tuple: (in_progress, priority, ready, age)",
  
  "contracts_defined": [
    "TaskPriority enum with 3 levels",
    "Task.priority optional field",
    "Parser handles Priority section",
    "Ranking considers priority score"
  ],
  
  "design_notes": [
    "Backward compatible via default value",
    "No migration needed"
  ]
}
```

**Action**: Call `alfred.submit_work` with interface design