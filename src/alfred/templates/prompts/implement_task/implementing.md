# Implementation Phase

You are now in the implementation phase for task {{ task.task_id }}.

## Your Execution Plan

{% if additional_context.execution_plan %}
{{ additional_context.execution_plan | tojson(indent=2) }}
{% else %}
No execution plan found. Please check the planning phase outputs.
{% endif %}

## Your Mission

Implement the subtasks from the execution plan. As you complete each subtask, call `mark_subtask_complete` to track progress.

When all subtasks are complete, submit an `ImplementationManifestArtifact` with:
- **summary**: Brief summary of what was implemented
- **completed_subtasks**: List of completed subtask IDs
- **testing_notes**: Any notes about testing or validation

Call `submit_work` with your final implementation manifest.