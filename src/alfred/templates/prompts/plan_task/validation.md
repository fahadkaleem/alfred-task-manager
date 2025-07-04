<!--
Template: plan_task.validation
Purpose: Final plan validation
Variables:
  - task_id: The task identifier
  - tool_name: Current tool name
  - current_state: Current workflow state
  - task_title: Task title
  - discovery_artifact: Results from discovery phase
  - clarification_artifact: Results from clarification phase
  - contracts_artifact: Results from contracts phase (if available)
  - implementation_artifact: Results from implementation planning phase
-->

# CONTEXT
Task: ${task_id} - ${task_title}
State: ${current_state}

# OBJECTIVE
Validate the complete plan before implementation.

# BACKGROUND
All planning phases are complete. Review the plan end-to-end to ensure it's ready for implementation.

# INSTRUCTIONS
1. Summarize the complete plan
2. Check what validations were performed
3. Identify any remaining issues
4. Confirm if ready for implementation

# OUTPUT
Submit a simple artifact with:
- **validation_summary**: Markdown summary of validation results
- **validations_performed**: List of checks performed
- **issues_found**: Any issues or concerns found
- **ready_for_implementation**: Boolean (true/false)

## Example
```json
{
  "validation_summary": "## Validation Complete\n\nThe plan for adding task priority is comprehensive and ready:\n- Task model changes are backward compatible\n- Parser handles missing Priority section gracefully\n- Ranking algorithm integration is well-designed\n- Test coverage is adequate",
  
  "validations_performed": [
    "Verified all acceptance criteria are covered",
    "Checked backward compatibility approach",
    "Validated interface consistency",
    "Reviewed risk mitigation strategies"
  ],
  
  "issues_found": [],
  
  "ready_for_implementation": true
}
```

**Action**: Call `alfred.submit_work` with validation results