<!--
Template: plan_task.discovery
Purpose: Explore codebase and discover what needs to be done
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - task_context: Task goal/context
  - implementation_details: Implementation overview
  - acceptance_criteria: Formatted AC list
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Explore the codebase to understand what needs to be done for this task.

# TASK REQUIREMENTS
**Goal**: ${task_context}

**Implementation Notes**: ${implementation_details}

**Success Criteria**:
${acceptance_criteria}

# INSTRUCTIONS
1. Use Glob/Grep/Read tools to explore relevant code
2. Document what you find in markdown
3. Note any questions you need answered
4. List files that need changes
5. Assess complexity (LOW/MEDIUM/HIGH)

# OUTPUT
Submit a simple artifact with:
- **findings**: Your discoveries in markdown format
- **questions**: List of questions (must end with ?)
- **files_to_modify**: List of file paths
- **complexity**: LOW, MEDIUM, or HIGH
- **implementation_context**: Any code/patterns for later use

## Example
```json
{
  "findings": "## Discovery Results\n\n### Current State\n- Task model is in `schemas.py` with Pydantic\n- Uses string-based enums for JSON compatibility\n- No priority field exists currently\n\n### Patterns Found\n- All enums inherit from (str, Enum)\n- Models use Field() for validation\n- Error handling returns ToolResponse",
  
  "questions": [
    "Should priority be required or optional with default?",
    "Where should priority rank in the recommendation algorithm?"
  ],
  
  "files_to_modify": [
    "src/alfred/models/schemas.py",
    "src/alfred/lib/md_parser.py",
    "src/alfred/task_providers/local_provider.py"
  ],
  
  "complexity": "MEDIUM",
  
  "implementation_context": {
    "enum_pattern": "class TaskStatus(str, Enum):\n    NEW = \"new\"",
    "validation_example": "Field(default=TaskStatus.NEW)"
  }
}
```

**Action**: Call `alfred.submit_work` with your discovery results
