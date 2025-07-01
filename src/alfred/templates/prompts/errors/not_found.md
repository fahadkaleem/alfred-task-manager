# CONTEXT
Task: ${task_id}
Tool: ${tool_name}
State: ${current_state}

# OBJECTIVE
No prompt template was found for the current tool and state combination.

# BACKGROUND
This is a fallback prompt that indicates a missing template configuration. The system attempted to find a prompt for tool "${tool_name}" in state "${current_state}" but could not locate the appropriate template file.

# INSTRUCTIONS
1. This is likely a configuration error
2. Check that the prompt file exists at the expected location
3. Verify the tool and state names are correct
4. Contact the development team if this persists

# CONSTRAINTS
- This is not a normal operational state
- Do not attempt to proceed with the workflow

# OUTPUT
No action can be taken. Please resolve the missing template issue.