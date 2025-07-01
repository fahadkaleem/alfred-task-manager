# TASK: ${task_id}
# STATE: dispatching

All phases are complete. Please finalize the task.

**Test Results:**
Exit Code: {{ task.completed_tool_outputs.test_task.exit_code }}
Output: {{ task.completed_tool_outputs.test_task.output }}

If tests passed, please:
1. Create a git commit with the changes
2. Create a pull request if appropriate

Once finalization is complete, call `alfred.submit_work` with a `FinalizeArtifact` containing:
- commit_hash: The git commit hash (or "N/A" if not applicable)
- pr_url: The PR URL (or "N/A" if not applicable)