# TASK: ${task_id}
# STATE: dispatching

The Execution Plan is ready. Please execute all subtasks from the plan.

**Execution Plan:**
{{ task.completed_tool_outputs.plan_task.execution_plan | tojson(indent=2) }}

Once all subtasks are complete, call `alfred.submit_work` with an `ImplementationManifestArtifact` containing:
- summary: Brief summary of what was implemented
- completed_subtasks: List of completed subtask IDs
- testing_notes: Any notes for the testing phase