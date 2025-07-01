# TASK: ${task_id}
# STATE: dispatching

Please review the implementation that was just completed.

**Implementation Summary:**
{{ task.completed_tool_outputs.implement_task.summary }}

**Completed Subtasks:**
{{ task.completed_tool_outputs.implement_task.completed_subtasks | tojson(indent=2) }}

Review the code changes for:
- Correctness and completeness
- Code quality and standards
- Security considerations
- Performance implications

Once your review is complete, call `alfred.submit_work` with a `ReviewArtifact` containing:
- summary: Review summary
- approved: true/false
- feedback: List of feedback items