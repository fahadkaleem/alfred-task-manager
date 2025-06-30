# AI Review Required

## Task: {{ task.task_id }}

Your implementation manifest has been submitted and is now ready for AI review.

### Submitted Implementation Manifest

{% if artifact_content %}
{{ artifact_content | tojson(indent=2) }}
{% elif additional_context.artifact_content %}
{{ additional_context.artifact_content | tojson(indent=2) }}
{% else %}
Error: No artifact content found
{% endif %}

### Review Process

The AI will now review your implementation for:
- Completeness of subtask completion
- Quality of implementation summary
- Adequacy of testing notes

Please wait for the AI review to complete.