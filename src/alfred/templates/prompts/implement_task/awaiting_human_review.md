# Human Review Required

## Task: {{ task.task_id }}

Your implementation has passed AI review and now requires human approval.

### Implementation Summary

{% if additional_context.implementing_artifact %}
{{ additional_context.implementing_artifact.summary }}

### Completed Subtasks
{% for subtask_id in additional_context.implementing_artifact.completed_subtasks %}
- {{ subtask_id }}
{% endfor %}

### Testing Notes
{{ additional_context.implementing_artifact.testing_notes }}
{% else %}
Implementation artifact not found in context.
{% endif %}

### Next Steps

Please wait for human review and approval to proceed to the next phase.