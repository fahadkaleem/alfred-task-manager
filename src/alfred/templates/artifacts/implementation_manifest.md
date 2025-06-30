# Implementation Manifest

## Summary
{{ artifact.summary }}

## Completed Subtasks
{% for subtask_id in artifact.completed_subtasks %}
- {{ subtask_id }}
{% endfor %}

## Testing Notes
{{ artifact.testing_notes }}