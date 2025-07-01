# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}
Title: ${task_title}

# OBJECTIVE
Perform code review and provide structured feedback on the implementation.

# BACKGROUND
Review the completed implementation for code quality, correctness, and adherence to requirements. The implementation details and acceptance criteria are available for reference.

# INSTRUCTIONS
1. Review the implementation thoroughly
2. Check for code quality, bugs, performance, and security issues
3. Determine if the implementation meets the requirements
4. Provide specific feedback if changes are needed

# CONSTRAINTS
- Be thorough but focus on substantive issues
- Provide actionable feedback if requesting changes
- Base approval decision on code quality and completeness

# OUTPUT
Create a ReviewArtifact with these exact fields:
- **summary**: Overall assessment of the implementation quality
- **approved**: Boolean - true if code passes review, false if changes needed  
- **feedback**: Array of specific feedback strings (empty array if approved)

**Required Action:** Call `alfred.submit_work` with a `ReviewArtifact`

# EXAMPLES
```json
{
  "summary": "Implementation looks good with proper error handling",
  "approved": true,
  "feedback": []
}
```

```json
{
  "summary": "Several issues found that need to be addressed",
  "approved": false,
  "feedback": [
    "Add input validation for user email field",
    "Fix potential null pointer exception in line 45",
    "Add unit tests for error handling scenarios"
  ]
}
```