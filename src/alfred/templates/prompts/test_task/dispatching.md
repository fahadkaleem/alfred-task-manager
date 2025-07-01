# TASK: ${task_id}
# STATE: dispatching

Please run the test suite to verify the implementation.

**Testing Notes from Implementation:**
{{ task.completed_tool_outputs.implement_task.testing_notes }}

Run the appropriate test command (e.g., `uv run python -m pytest tests/ -v`) and report the results.

Once testing is complete, call `alfred.submit_work` with a `TestResultArtifact` containing:
- command: The test command that was run
- exit_code: The exit code (0 for success)
- output: The test output