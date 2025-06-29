## {{ state_description }}

**Task:** {{ task.task_id }} - {{ task.title }}

### Analysis Summary
{{ artifact.context_summary }}

### Affected Components
{% for file in artifact.affected_files -%}
- `{{ file }}`
{% endfor %}

### Clarification Requirements
{% for question in artifact.questions_for_developer -%}
- {{ question }}
{% endfor %}